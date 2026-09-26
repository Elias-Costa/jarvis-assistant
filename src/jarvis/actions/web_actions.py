from __future__ import annotations

from urllib.parse import quote_plus
import webbrowser

from jarvis.models import AssistantConfig


class WebActions:
    def __init__(self, config: AssistantConfig) -> None:
        self.config = config

    def open_site(self, target_name: str) -> str:
        alias = target_name.strip().lower()
        url = self.config.sites.get(alias, target_name.strip())

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        webbrowser.open(url)
        return f"Abrindo {alias}."

    def google_search(self, query: str) -> str:
        sanitized_query = query.strip()
        if not sanitized_query:
            raise ValueError("Nao entendi o que voce quer pesquisar.")

        url = f"https://www.google.com/search?q={quote_plus(sanitized_query)}"
        webbrowser.open(url)
        return f"Pesquisando por {sanitized_query} no Google."
