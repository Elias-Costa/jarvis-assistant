from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from jarvis.models import AssistantConfig, CommandIntent


SEARCH_PREFIXES = (
    "pesquise ",
    "pesquisar ",
    "procure ",
    "buscar ",
    "busque ",
    "google ",
)

EXIT_COMMANDS = {
    "sair",
    "encerrar",
    "fechar jarvis",
    "tchau",
    "ate mais",
}

HELP_COMMANDS = {"ajuda", "comandos", "o que voce faz"}

TIME_COMMANDS = {"que horas sao", "hora", "horas"}


def normalize_text(value: str) -> str:
    value = value.strip().lower()
    normalized = unicodedata.normalize("NFD", value)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", normalized)


class CommandRouter:
    def __init__(self, config: AssistantConfig) -> None:
        self.config = config

    def route(self, text: str) -> CommandIntent:
        raw_text = text.strip()
        normalized = normalize_text(raw_text)

        if not normalized:
            return CommandIntent(name="empty", raw_text=raw_text)

        if normalized in EXIT_COMMANDS:
            return CommandIntent(name="exit", raw_text=raw_text)

        if normalized in HELP_COMMANDS:
            return CommandIntent(name="help", raw_text=raw_text)

        if normalized in TIME_COMMANDS:
            return CommandIntent(name="time", raw_text=raw_text)

        for prefix in SEARCH_PREFIXES:
            if normalized.startswith(prefix):
                query = raw_text[len(prefix) :].strip()
                query = re.sub(r"\s+no google$", "", query, flags=re.IGNORECASE)
                return CommandIntent(name="google_search", raw_text=raw_text, slots={"query": query})

        if match := re.match(r"^(?:abrir|abra|acessar|acesse)\s+(?:a\s+|o\s+)?pasta\s+(.+)$", normalized):
            target = match.group(1).strip()
            return CommandIntent(name="open_folder", raw_text=raw_text, slots={"target": target})

        if match := re.match(
            r"^(?:abrir|abra|acessar|acesse|iniciar|inicie|executar|execute)\s+(.+)$",
            normalized,
        ):
            target = match.group(1).strip()
            return self._resolve_open_target(raw_text=raw_text, normalized_target=target)

        if normalized.startswith("http://") or normalized.startswith("https://"):
            return CommandIntent(name="open_site", raw_text=raw_text, slots={"target": raw_text})

        return CommandIntent(name="unknown", raw_text=raw_text)

    def _resolve_open_target(self, raw_text: str, normalized_target: str) -> CommandIntent:
        target = normalized_target.removeprefix("o ").removeprefix("a ").strip()
        target = target.removeprefix("site ").removeprefix("programa ").removeprefix("aplicativo ").strip()

        if target in self.config.folders:
            return CommandIntent(name="open_folder", raw_text=raw_text, slots={"target": target})

        if target in self.config.apps:
            return CommandIntent(name="open_app", raw_text=raw_text, slots={"target": target})

        if target in self.config.sites or "." in target or target.startswith("http"):
            return CommandIntent(name="open_site", raw_text=raw_text, slots={"target": target})

        if Path(target).expanduser().exists():
            return CommandIntent(name="open_folder", raw_text=raw_text, slots={"target": target})

        return CommandIntent(name="open_app", raw_text=raw_text, slots={"target": target})
