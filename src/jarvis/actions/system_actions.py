from __future__ import annotations

import os
import subprocess
from pathlib import Path

from jarvis.models import AppTarget, AssistantConfig


class SystemActions:
    def __init__(self, config: AssistantConfig) -> None:
        self.config = config

    def open_app(self, target_name: str) -> str:
        alias = target_name.strip().lower()
        app_target = self.config.apps.get(alias)

        if not app_target:
            available = ", ".join(sorted(self.config.apps)) or "nenhum alias configurado"
            raise ValueError(f"Aplicativo '{target_name}' nao encontrado. Apps conhecidos: {available}.")

        self._launch_target(app_target)
        return f"Abrindo {target_name}."

    def open_folder(self, target_name: str) -> str:
        alias = target_name.strip().lower()
        configured_target = self.config.folders.get(alias, target_name)

        folder_path = Path(os.path.expandvars(configured_target)).expanduser()
        if not folder_path.exists():
            raise ValueError(f"Pasta '{target_name}' nao encontrada em {folder_path}.")

        os.startfile(folder_path)  # type: ignore[attr-defined]
        return f"Abrindo a pasta {target_name}."

    def _launch_target(self, app_target: AppTarget) -> None:
        if app_target.path:
            target_path = Path(os.path.expandvars(app_target.path)).expanduser()
            if not target_path.exists():
                raise ValueError(f"O executavel configurado nao existe: {target_path}.")
            subprocess.Popen([str(target_path)])
            return

        if app_target.command:
            subprocess.Popen(app_target.command)
            return

        raise ValueError("Configuracao do aplicativo invalida.")
