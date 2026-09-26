from __future__ import annotations

import os

from jarvis.brains.base import Brain
from jarvis.brains.openai_brain import OpenAIBrain
from jarvis.brains.rule_based import RuleBasedBrain
from jarvis.core.router import CommandRouter
from jarvis.models import AssistantConfig


def build_brain(config: AssistantConfig, router: CommandRouter) -> tuple[Brain, str | None]:
    provider = config.brain_provider
    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))

    if provider == "rules":
        return RuleBasedBrain(router), None

    if provider == "openai":
        if has_openai_key:
            return OpenAIBrain(config), None
        return RuleBasedBrain(router), "OPENAI_API_KEY ausente; usando cerebro por regras."

    if provider == "auto":
        if has_openai_key:
            return OpenAIBrain(config), None
        return RuleBasedBrain(router), "Sem OPENAI_API_KEY; usando cerebro por regras."

    return RuleBasedBrain(router), f"brain_provider '{provider}' invalido; usando cerebro por regras."
