from __future__ import annotations

from abc import ABC, abstractmethod

from jarvis.models import CommandIntent


class Brain(ABC):
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Human-readable backend name."""

    @abstractmethod
    def interpret(self, text: str) -> CommandIntent:
        """Converts a user utterance into an assistant intent."""

    def remember(self, user_text: str, assistant_text: str) -> None:
        """Stores conversation state when supported."""
