import json
import tempfile
import unittest
from pathlib import Path

from agent_simulation.clients import DryRunClient
from agent_simulation.engine import run_simulation
from agent_simulation.io import load_config, save_result
from agent_simulation.prompts import PromptRenderError, format_transcript, render_template
from agent_simulation.runtime import apply_runtime_inputs, parse_variable_assignments
from agent_simulation.schema import AgentMessage, ConfigError, SimulationConfig


REPO_ROOT = Path(__file__).resolve().parents[1]


class ConfigLoadingTests(unittest.TestCase):
    def test_all_configs_load(self) -> None:
        for config_path in sorted((REPO_ROOT / "configs").glob("*.json")):
            with self.subTest(config=config_path.name):
                config = load_config(config_path)
                self.assertIsInstance(config, SimulationConfig)
                self.assertGreater(len(config.participants), 0)
                self.assertGreater(len(config.rounds), 0)

    def test_unknown_round_participant_is_rejected(self) -> None:
        bad_config = {
            "name": "bad",
            "scenario": {"title": "T", "question": "Q"},
            "participants": [
                {"id": "known", "name": "Known", "role": "Role", "prompt": "Prompt"}
            ],
            "rounds": [
                {
                    "id": "r1",
                    "title": "R1",
                    "prompt": "Prompt",
                    "participants": ["missing"],
                }
            ],
        }
        with self.assertRaisesRegex(ConfigError, "unknown participant"):
            SimulationConfig.from_dict(bad_config)

    def test_duplicate_participant_ids_are_rejected(self) -> None:
        bad_config = {
            "name": "bad",
            "scenario": {"title": "T", "question": "Q"},
            "participants": [
                {"id": "same", "name": "A", "role": "Role", "prompt": "Prompt"},
                {"id": "same", "name": "B", "role": "Role", "prompt": "Prompt"},
            ],
            "rounds": [{"id": "r1", "prompt": "Prompt"}],
        }
        with self.assertRaisesRegex(ConfigError, "duplicate"):
            SimulationConfig.from_dict(bad_config)


class TranscriptFormattingTests(unittest.TestCase):
    def test_hidden_transcript_does_not_expose_prior_content(self) -> None:
        transcript = [
            AgentMessage("a1", "Agent One", "Role", "round", "private answer"),
        ]
        rendered = format_transcript(transcript, visibility="hidden")
        self.assertIn("hidden", rendered)
        self.assertNotIn("private answer", rendered)

    def test_anonymous_transcript_removes_names_and_ids(self) -> None:
        transcript = [
            AgentMessage("a1", "Agent One", "Role", "round", "first answer"),
            AgentMessage("a2", "Agent Two", "Role", "round", "second answer"),
        ]
        rendered = format_transcript(transcript, visibility="anonymous")
        self.assertIn("Participant 1", rendered)
        self.assertIn("Participant 2", rendered)
        self.assertNotIn("Agent One", rendered)
        self.assertNotIn("a1", rendered)

    def test_unknown_prompt_variable_fails_loudly(self) -> None:
        with self.assertRaisesRegex(PromptRenderError, "unknown variable"):
            render_template("Hello {missing}", {"known": "value"})


class DryRunExecutionTests(unittest.TestCase):
    def test_hackathon_dry_run_writes_outputs_and_group_chat_turns(self) -> None:
        config = load_config(REPO_ROOT / "configs" / "hackathon_one_hour.json")
        config = apply_runtime_inputs(
            config,
            prompt="Design an AI assistant that helps a city triage pothole reports.",
            variables={"target_user": "City operations team"},
        )
        result = run_simulation(
            config=config,
            client=DryRunClient(),
            model="dry-run-model",
            max_participants=2,
        )
        self.assertEqual(result.config_name, "hackathon-one-hour-peer-deliberation")
        self.assertEqual(len(result.rounds), len(config.rounds))
        self.assertEqual(result.rounds[1].mode, "group_chat")
        self.assertEqual(len(result.rounds[1].messages), 8)
        self.assertEqual(result.rounds[2].messages[1].metadata["event_type"], "interruption")
        self.assertEqual(result.rounds[-1].messages[0].participant_id, "run_recorder")
        self.assertEqual(
            result.rounds[-1].messages[0].participant_role,
            "Neutral hackathon recorder",
        )

        with tempfile.TemporaryDirectory() as output_dir:
            json_path, markdown_path = save_result(result, output_dir)
            self.assertTrue(json_path.exists())
            self.assertTrue(markdown_path.exists())
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["provider"], "dry-run")

    def test_runtime_variable_assignment_parser(self) -> None:
        parsed = parse_variable_assignments(["target_user=Judges", "tone=direct"])
        self.assertEqual(parsed["target_user"], "Judges")
        self.assertEqual(parsed["tone"], "direct")

    def test_bad_runtime_variable_assignment_is_rejected(self) -> None:
        with self.assertRaisesRegex(ConfigError, "KEY=VALUE"):
            parse_variable_assignments(["not-an-assignment"])


if __name__ == "__main__":
    unittest.main()
