from __future__ import annotations

import argparse
from datetime import datetime
import os

from jarvis.actions.system_actions import SystemActions
from jarvis.actions.web_actions import WebActions
from jarvis.brains.factory import build_brain
from jarvis.config import load_config
from jarvis.core.router import CommandRouter
from jarvis.interfaces.text_io import ConsoleIO
from jarvis.interfaces.voice_io import JarvisVoiceIO, VoiceIOError
from jarvis.models import AssistantResponse, CommandIntent


class JarvisAssistant:
    def __init__(self, mode: str) -> None:
        self.config = load_config()
        self.mode = mode
        self.console = ConsoleIO()
        self.router = CommandRouter(self.config)
        self.brain, self.brain_warning = build_brain(self.config, self.router)
        self.system_actions = SystemActions(self.config)
        self.web_actions = WebActions(self.config)
        self.voice = JarvisVoiceIO(self.config)
        self.voice_warning = self._build_voice_warning()

    def run(self) -> int:
        greeting = (
            f"{self.config.assistant_name} iniciado em modo {self.mode}. "
            f"Cerebro: {self.brain.backend_name}. "
            f"Entrada de voz: {self.voice.input_backend_name}. "
            "Digite um comando, use /voz no modo hibrido ou diga 'sair' para encerrar."
        )
        self._respond(AssistantResponse(text=greeting, speak=self.config.voice_enabled and self.mode != "text"))
        if self.brain_warning:
            self._respond(AssistantResponse(text=self.brain_warning, speak=False))
        if self.voice_warning:
            self._respond(AssistantResponse(text=self.voice_warning, speak=False))

        while True:
            try:
                command = self._get_user_command()
                intent = self.brain.interpret(command)
                response = self._handle_intent(intent)
                self._respond(response)
                self.brain.remember(command, response.text)

                if response.should_exit:
                    return 0
            except KeyboardInterrupt:
                self._respond(AssistantResponse(text="Encerrando o assistente.", should_exit=True))
                return 0
            except Exception as exc:  # noqa: BLE001
                self._respond(AssistantResponse(text=f"Encontrei um problema: {exc}"))

    def _get_user_command(self) -> str:
        if self.mode == "voice":
            self.console.show("Ouvindo pelo microfone...")
            command = self.voice.listen()
            if not command:
                raise ValueError("Nao ouvi nenhum comando.")
            self.console.show(f"Voce: {command}")
            return command

        prompt = "Voce: "
        command = self.console.prompt(prompt).strip()

        if self.mode == "hybrid" and (not command or command.lower() == "/voz"):
            self.console.show("Ouvindo pelo microfone...")
            command = self.voice.listen()
            if not command:
                raise ValueError("Nao ouvi nenhum comando.")
            self.console.show(f"Voce: {command}")
            return command

        return command

    def _handle_intent(self, intent: CommandIntent) -> AssistantResponse:
        if intent.name == "empty":
            return AssistantResponse(text="Estou aguardando um comando.", speak=False)

        if intent.name == "help":
            return AssistantResponse(text=self._help_text())

        if intent.name == "exit":
            return AssistantResponse(text="Ate logo.", should_exit=True)

        if intent.name == "reply":
            return AssistantResponse(text=intent.slots.get("answer", "Certo."))

        if intent.name == "time":
            now = datetime.now().strftime("%H:%M")
            return AssistantResponse(text=f"Agora sao {now}.")

        if intent.name == "google_search":
            message = self.web_actions.google_search(intent.slots["query"])
            return AssistantResponse(text=message)

        if intent.name == "open_site":
            message = self.web_actions.open_site(intent.slots["target"])
            return AssistantResponse(text=message)

        if intent.name == "open_app":
            message = self.system_actions.open_app(intent.slots["target"])
            return AssistantResponse(text=message)

        if intent.name == "open_folder":
            message = self.system_actions.open_folder(intent.slots["target"])
            return AssistantResponse(text=message)

        return AssistantResponse(
            text="Nao entendi esse comando ainda. Use 'ajuda' para ver exemplos do que eu consigo fazer."
        )

    def _respond(self, response: AssistantResponse) -> None:
        self.console.show(f"{self.config.assistant_name}: {response.text}")

        if response.speak and self.config.voice_enabled:
            try:
                self.voice.speak(response.text)
            except VoiceIOError as exc:
                self.console.show(f"{self.config.assistant_name}: Falha na fala do Windows: {exc}")

    def _help_text(self) -> str:
        return (
            "Comandos disponiveis: abrir um app configurado, abrir um site, abrir uma pasta, "
            "pesquisar no Google, consultar as horas, conversar comigo e encerrar."
        )

    def _build_voice_warning(self) -> str | None:
        provider = self.config.stt_provider
        if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            return "OPENAI_API_KEY ausente; a entrada de voz por OpenAI nao vai funcionar."
        if provider == "auto" and not os.getenv("OPENAI_API_KEY"):
            return "Sem OPENAI_API_KEY, a entrada de voz dependera do reconhecimento do Windows."
        return None

    def show_audio_devices(self) -> int:
        devices = self.voice.list_input_devices()
        if not devices:
            self.console.show("Nenhum dispositivo de entrada encontrado ou sounddevice indisponivel.")
            return 1

        self.console.show("Microfones disponiveis:")
        for device in devices:
            self.console.show(f"- {device}")
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assistente JARVIS em Python.")
    parser.add_argument(
        "--mode",
        choices=("text", "voice", "hybrid"),
        default="hybrid",
        help="Define como o assistente recebe os comandos.",
    )
    parser.add_argument(
        "--list-audio-devices",
        action="store_true",
        help="Lista os dispositivos de entrada de audio detectados.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    assistant = JarvisAssistant(mode=args.mode)
    if args.list_audio_devices:
        return assistant.show_audio_devices()
    return assistant.run()
