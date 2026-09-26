from __future__ import annotations

from jarvis.brains.base import Brain
from jarvis.core.router import CommandRouter
from jarvis.models import CommandIntent


class RuleBasedBrain(Brain):
    def __init__(self, router: CommandRouter) -> None:
        self.router = router

    @property
    def backend_name(self) -> str:
        return "regras"

    def interpret(self, text: str) -> CommandIntent:
        return self.router.route(text)
