from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CommandIntent:
    name: str
    raw_text: str
    slots: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class AssistantResponse:
    text: str
    speak: bool = True
    should_exit: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AppTarget:
    path: str | None = None
    command: list[str] | None = None


@dataclass(slots=True)
class AssistantConfig:
    assistant_name: str
    brain_provider: str
    voice_enabled: bool
    stt_provider: str
    speech_culture: str
    voice_rate: int
    voice_volume: int
    openai_model: str
    openai_reasoning_effort: str
    openai_transcription_model: str
    microphone_device: int | str | None
    microphone_record_seconds: int
    microphone_sample_rate: int
    sites: dict[str, str]
    folders: dict[str, str]
    apps: dict[str, AppTarget]
