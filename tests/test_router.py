from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from jarvis.core.router import CommandRouter  # noqa: E402
from jarvis.models import AppTarget, AssistantConfig  # noqa: E402


class CommandRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = AssistantConfig(
            assistant_name="Jarvis",
            brain_provider="rules",
            voice_enabled=True,
            stt_provider="windows",
            speech_culture="pt-BR",
            voice_rate=1,
            voice_volume=100,
            openai_model="gpt-5.4-mini",
            openai_reasoning_effort="medium",
            openai_transcription_model="gpt-4o-transcribe",
            microphone_device=None,
            microphone_record_seconds=6,
            microphone_sample_rate=16000,
            sites={"youtube": "https://youtube.com"},
            folders={"downloads": "~/Downloads"},
            apps={"bloco de notas": AppTarget(command=["notepad.exe"])},
        )
        self.router = CommandRouter(self.config)

    def test_routes_google_search(self) -> None:
        intent = self.router.route("pesquise python no google")
        self.assertEqual(intent.name, "google_search")
        self.assertEqual(intent.slots["query"], "python")

    def test_routes_known_site(self) -> None:
        intent = self.router.route("abra o youtube")
        self.assertEqual(intent.name, "open_site")
        self.assertEqual(intent.slots["target"], "youtube")

    def test_routes_known_app(self) -> None:
        intent = self.router.route("abrir bloco de notas")
        self.assertEqual(intent.name, "open_app")
        self.assertEqual(intent.slots["target"], "bloco de notas")

    def test_routes_folder_alias(self) -> None:
        intent = self.router.route("abrir pasta downloads")
        self.assertEqual(intent.name, "open_folder")
        self.assertEqual(intent.slots["target"], "downloads")


if __name__ == "__main__":
    unittest.main()
