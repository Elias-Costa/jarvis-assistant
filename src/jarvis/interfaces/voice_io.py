from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import wave

import numpy as np

try:
    import sounddevice as sd
except ModuleNotFoundError:  # pragma: no cover
    sd = None

try:
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

from jarvis.models import AssistantConfig


class VoiceIOError(RuntimeError):
    """Raised when the speech subsystem cannot process a request."""


class WindowsSpeechBackend:
    def __init__(self, culture: str = "pt-BR", rate: int = 1, volume: int = 100) -> None:
        self.culture = culture
        self.rate = rate
        self.volume = max(0, min(volume, 100))

    def speak(self, text: str) -> None:
        safe_text = text.replace("'", "''")
        script = f"""
        Add-Type -AssemblyName System.Speech
        $synth = [System.Speech.Synthesis.SpeechSynthesizer]::new()
        $synth.Rate = {self.rate}
        $synth.Volume = {self.volume}
        try {{
            $culture = [System.Globalization.CultureInfo]::GetCultureInfo('{self.culture}')
            $synth.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::NotSet, [System.Speech.Synthesis.VoiceAge]::NotSet, 0, $culture)
        }} catch {{
        }}
        $synth.Speak('{safe_text}')
        $synth.Dispose()
        """
        self._run_powershell(script)

    def listen(self, timeout_seconds: int = 8) -> str:
        script = f"""
        Add-Type -AssemblyName System.Speech
        $cultures = @('{self.culture}', [System.Globalization.CultureInfo]::CurrentCulture.Name, 'en-US')
        $engine = $null

        foreach ($name in $cultures) {{
            if ([string]::IsNullOrWhiteSpace($name)) {{ continue }}
            try {{
                $culture = [System.Globalization.CultureInfo]::GetCultureInfo($name)
                $engine = [System.Speech.Recognition.SpeechRecognitionEngine]::new($culture)
                break
            }} catch {{
            }}
        }}

        if ($null -eq $engine) {{
            throw 'Nao foi possivel iniciar o reconhecimento de voz do Windows.'
        }}

        $engine.SetInputToDefaultAudioDevice()
        $engine.LoadGrammar([System.Speech.Recognition.DictationGrammar]::new())

        try {{
            $result = $engine.Recognize([TimeSpan]::FromSeconds({timeout_seconds}))
            if ($null -ne $result) {{
                Write-Output $result.Text
            }}
        }} finally {{
            $engine.Dispose()
        }}
        """
        result = self._run_powershell(script)
        return result.stdout.strip()

    def _run_powershell(self, script: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raw_error = result.stderr.strip() or result.stdout.strip() or "Falha desconhecida no PowerShell."
            error_message = next((line.strip() for line in raw_error.splitlines() if line.strip()), raw_error)
            raise VoiceIOError(error_message)

        return result


class MicrophoneRecorder:
    def __init__(self, sample_rate: int, device: int | str | None = None) -> None:
        self.sample_rate = sample_rate
        self.device = device

    @staticmethod
    def list_input_devices() -> list[str]:
        if sd is None:
            return []

        devices = []
        for index, device in enumerate(sd.query_devices()):
            if int(device["max_input_channels"]) > 0:
                devices.append(f"{index}: {device['name']}")
        return devices

    def record_wav(self, seconds: int) -> Path:
        if sd is None:
            raise VoiceIOError("A biblioteca sounddevice nao esta instalada.")

        frame_count = max(1, int(seconds * self.sample_rate))
        try:
            recording = sd.rec(
                frame_count,
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                device=self.device,
            )
            sd.wait()
        except Exception as exc:  # noqa: BLE001
            raise VoiceIOError(f"Nao consegui gravar do microfone: {exc}") from exc

        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        with wave.open(str(temp_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(np.dtype("int16").itemsize)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(recording.tobytes())

        return temp_path


class OpenAITranscriber:
    def __init__(self, model: str) -> None:
        if OpenAI is None:
            raise VoiceIOError("A biblioteca openai nao esta instalada.")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise VoiceIOError("OPENAI_API_KEY nao configurada.")

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def transcribe(self, audio_path: Path) -> str:
        with audio_path.open("rb") as audio_file:
            transcription = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                response_format="text",
            )

        if hasattr(transcription, "text"):
            return str(transcription.text).strip()

        return str(transcription).strip()


class JarvisVoiceIO:
    def __init__(self, config: AssistantConfig) -> None:
        self.config = config
        self.windows_backend = WindowsSpeechBackend(
            culture=config.speech_culture,
            rate=config.voice_rate,
            volume=config.voice_volume,
        )
        self.recorder = MicrophoneRecorder(
            sample_rate=config.microphone_sample_rate,
            device=config.microphone_device,
        )

    @property
    def output_backend_name(self) -> str:
        return "windows-tts"

    @property
    def input_backend_name(self) -> str:
        provider = self.config.stt_provider
        if provider == "openai":
            return f"openai:{self.config.openai_transcription_model}"
        if provider == "windows":
            return "windows-stt"
        if os.getenv("OPENAI_API_KEY"):
            return f"auto->openai:{self.config.openai_transcription_model}"
        return "auto->windows-stt"

    def speak(self, text: str) -> None:
        self.windows_backend.speak(text)

    def listen(self, timeout_seconds: int | None = None) -> str:
        seconds = timeout_seconds or self.config.microphone_record_seconds
        provider = self.config.stt_provider
        errors: list[str] = []

        if provider in {"auto", "openai"}:
            try:
                return self._listen_with_openai(seconds)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"OpenAI STT: {exc}")
                if provider == "openai":
                    raise VoiceIOError(errors[-1]) from exc

        if provider in {"auto", "windows"}:
            try:
                return self.windows_backend.listen(timeout_seconds=seconds)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Windows STT: {exc}")

        details = " | ".join(errors) if errors else "Nenhum backend de voz disponivel."
        raise VoiceIOError(
            "A entrada de audio falhou. Configure OPENAI_API_KEY para usar transcricao da OpenAI "
            f"ou ajuste o reconhecimento do Windows. Detalhes: {details}"
        )

    def list_input_devices(self) -> list[str]:
        return self.recorder.list_input_devices()

    def _listen_with_openai(self, seconds: int) -> str:
        audio_path = self.recorder.record_wav(seconds)
        try:
            transcriber = OpenAITranscriber(model=self.config.openai_transcription_model)
            return transcriber.transcribe(audio_path)
        finally:
            if audio_path.exists():
                audio_path.unlink()
