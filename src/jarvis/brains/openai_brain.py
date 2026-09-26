from __future__ import annotations

from collections import deque
import os
from typing import Literal

from pydantic import BaseModel, Field

from jarvis.brains.base import Brain
from jarvis.models import AssistantConfig, CommandIntent

try:
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


class BrainDecision(BaseModel):
    mode: Literal["action", "reply"] = Field(description="How Jarvis should react to the user request.")
    intent: Literal[
        "open_app",
        "open_site",
        "open_folder",
        "google_search",
        "time",
        "help",
        "exit",
        "unknown",
    ] = Field(description="The assistant intent.")
    target: str | None = Field(default=None, description="App, site, folder alias or URL when needed.")
    query: str | None = Field(default=None, description="Query for searches when needed.")
    answer: str | None = Field(default=None, description="Direct assistant reply when no action is needed.")


class OpenAIBrain(Brain):
    def __init__(self, config: AssistantConfig) -> None:
        if OpenAI is None:
            raise RuntimeError("A biblioteca openai nao esta instalada.")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY nao foi encontrada.")

        self.client = OpenAI(api_key=api_key)
        self.config = config
        self.history: deque[str] = deque(maxlen=8)

    @property
    def backend_name(self) -> str:
        return f"openai:{self.config.openai_model}"

    def interpret(self, text: str) -> CommandIntent:
        prompt = self._build_prompt(user_text=text)
        response = self.client.responses.parse(
            model=self.config.openai_model,
            instructions=self._system_instructions(),
            input=prompt,
            text_format=BrainDecision,
            reasoning={"effort": self.config.openai_reasoning_effort},
            store=False,
        )
        decision = response.output_parsed

        if decision is None:
            return CommandIntent(
                name="reply",
                raw_text=text,
                slots={"answer": "Nao consegui interpretar a resposta do cerebro da OpenAI."},
            )

        if decision.mode == "reply":
            answer = decision.answer or "Posso te ajudar com isso, mas ainda nao tenho uma acao local para executar."
            return CommandIntent(name="reply", raw_text=text, slots={"answer": answer})

        slots: dict[str, str] = {}
        if decision.target:
            slots["target"] = decision.target
        if decision.query:
            slots["query"] = decision.query

        return CommandIntent(name=decision.intent, raw_text=text, slots=slots)

    def remember(self, user_text: str, assistant_text: str) -> None:
        self.history.append(f"Usuario: {user_text}")
        self.history.append(f"Jarvis: {assistant_text}")

    def _system_instructions(self) -> str:
        known_apps = ", ".join(sorted(self.config.apps)) or "nenhum"
        known_sites = ", ".join(sorted(self.config.sites)) or "nenhum"
        known_folders = ", ".join(sorted(self.config.folders)) or "nenhum"

        return (
            "Voce e o cerebro do JARVIS, um assistente pessoal em um computador Windows. "
            "Seu trabalho e transformar pedidos do usuario em intencoes seguras para o programa executar. "
            "Quando o pedido for conversa, explicacao, opiniao ou algo que o programa ainda nao executa, "
            "responda em modo reply com uma resposta curta em portugues do Brasil. "
            "Quando o pedido puder ser executado, escolha um intent valido. "
            "Apps conhecidos: "
            f"{known_apps}. "
            "Sites conhecidos: "
            f"{known_sites}. "
            "Pastas conhecidas: "
            f"{known_folders}. "
            "Regras: use open_app para aplicativos, open_site para sites ou URLs, open_folder para pastas, "
            "google_search para pesquisas abertas, time para horas, help para ajuda, exit para encerrar. "
            "Se o usuario mencionar algo como ouvir musica, abrir editor, acessar email ou ver videos, "
            "voce pode mapear para aliases conhecidos quando fizer sentido. "
            "Nunca invente caminhos de arquivo inexistentes e nunca descreva acoes perigosas como se fossem suportadas."
        )

    def _build_prompt(self, user_text: str) -> str:
        history = "\n".join(self.history)
        if history:
            return f"Contexto recente:\n{history}\n\nPedido atual:\n{user_text}"
        return user_text
