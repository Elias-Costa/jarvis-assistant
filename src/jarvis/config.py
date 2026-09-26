from __future__ import annotations

import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover
    load_dotenv = None

from jarvis.models import AppTarget, AssistantConfig


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_PATH = CONFIG_DIR / "jarvis.json"
EXAMPLE_CONFIG_PATH = CONFIG_DIR / "jarvis.example.json"
DOTENV_PATH = PROJECT_ROOT / ".env"


def _normalize_mapping(mapping: dict[str, str | dict]) -> dict[str, str | AppTarget]:
    normalized: dict[str, str | AppTarget] = {}

    for key, value in mapping.items():
        alias = key.strip().lower()
        if isinstance(value, dict):
            normalized[alias] = AppTarget(
                path=value.get("path"),
                command=value.get("command"),
            )
        else:
            normalized[alias] = value

    return normalized


def ensure_config_file() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(EXAMPLE_CONFIG_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    return CONFIG_PATH


def load_config() -> AssistantConfig:
    if load_dotenv is not None:
        load_dotenv(DOTENV_PATH)

    path = ensure_config_file()
    raw = json.loads(path.read_text(encoding="utf-8"))

    app_map = _normalize_mapping(raw.get("apps", {}))
    apps = {
        name: value if isinstance(value, AppTarget) else AppTarget(command=[str(value)])
        for name, value in app_map.items()
    }

    sites = {
        key.strip().lower(): str(value)
        for key, value in raw.get("sites", {}).items()
    }
    folders = {
        key.strip().lower(): str(value)
        for key, value in raw.get("folders", {}).items()
    }

    return AssistantConfig(
        assistant_name=raw.get("assistant_name", "Jarvis"),
        brain_provider=str(raw.get("brain_provider", "auto")).strip().lower(),
        voice_enabled=bool(raw.get("voice_enabled", True)),
        stt_provider=str(raw.get("stt_provider", "auto")).strip().lower(),
        speech_culture=str(raw.get("speech_culture", "pt-BR")),
        voice_rate=int(raw.get("voice_rate", 1)),
        voice_volume=int(raw.get("voice_volume", 100)),
        openai_model=str(raw.get("openai_model", os.getenv("OPENAI_MODEL", "gpt-5.4-mini"))),
        openai_reasoning_effort=str(raw.get("openai_reasoning_effort", "medium")).strip().lower(),
        openai_transcription_model=str(
            raw.get("openai_transcription_model", os.getenv("OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-transcribe"))
        ),
        microphone_device=raw.get("microphone_device"),
        microphone_record_seconds=int(raw.get("microphone_record_seconds", 6)),
        microphone_sample_rate=int(raw.get("microphone_sample_rate", 16000)),
        sites=sites,
        folders=folders,
        apps=apps,
    )
