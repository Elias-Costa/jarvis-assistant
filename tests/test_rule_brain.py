from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from jarvis.brains.rule_based import RuleBasedBrain  # noqa: E402
from jarvis.core.router import CommandRouter  # noqa: E402
from jarvis.models import AppTarget, AssistantConfig  # noqa: E402


class RuleBasedBrainTests(unittest.TestCase):
    def setUp(self) -> None:
        config = AssistantConfig(
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
        self.brain = RuleBasedBrain(CommandRouter(config))

    def test_reply_not_emitted_by_rule_brain_for_known_action(self) -> None:
        intent = self.brain.interpret("abrir bloco de notas")
        self.assertEqual(intent.name, "open_app")

    def test_unknown_passes_through(self) -> None:
        intent = self.brain.interpret("quero dominar o mundo")
        self.assertEqual(intent.name, "unknown")


if __name__ == "__main__":
    unittest.main()
