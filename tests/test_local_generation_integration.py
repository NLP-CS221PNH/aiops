"""Local generation plumbing. Receipts do not claim a live Qwen forward unless assets exist."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from src.generation.provider import LocalCausalLMProvider, generate_response, load_config
from src.generation.runner import run_generation

IMPL = Path(__file__).resolve().parents[1]


class FakeLocalProvider:
    def generate(self, prompt, context, config):
        return json.dumps({
            "candidate_causes": [{"service_id": "cartservice", "fault_type": None, "reason": None}],
            "supported_claims": [],
        }), {
            "status": "success",
            "usage": {"prompt_tokens": 4, "completion_tokens": 3, "total_tokens": 7},
            "model_returned": "fake-local",
            "mock": False,
        }


class LocalGenerationTests(unittest.TestCase):
    def test_production_config_keeps_historical_provider_model(self):
        config = load_config(str(IMPL / "configs" / "generation.yaml"))
        self.assertEqual(config["provider"]["name"], "deepseek")
        self.assertEqual(config["provider"]["model"], "deepseek-flash")
        self.assertEqual(config["provider"]["temperature"], 0.1)
        self.assertEqual(config["local_qwen"]["model"], "Qwen/Qwen2.5-1.5B-Instruct")
        self.assertEqual(config["local_qwen"]["revision"], "989aa7980e4cf806f80c7fef2b1adb7bc71aa306")
        self.assertEqual(config["permissions"]["local"], "approved")

    def test_missing_assets_are_explicit(self):
        config = {
            "permissions": {"local": "approved"},
            "local_qwen": {"revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306", "assets": None},
        }
        raw, meta = generate_response("hello", {"incident_id": "i"}, config)
        self.assertEqual(meta["status"], "missing_assets")
        self.assertFalse(raw)

    def test_plumbing_provider_writes_usage_from_injected_backend(self, tmp_path=None):
        # Contract mock only; receipt is not actual-model verified.
        manifest = run_generation(
            "plumbing-local",
            ["inc-plumbing"],
            str(IMPL / "configs" / "generation.yaml"),
            provider=FakeLocalProvider(),
        )
        self.assertGreaterEqual(manifest["attempted"], 1)
        responses = (IMPL / "runs" / "plumbing-local" / "responses.jsonl").read_text(encoding="utf-8")
        record = json.loads(responses.strip().splitlines()[-1])
        self.assertEqual(record["status"], "success")
        self.assertEqual(record["usage"]["total_tokens"], 7)
        self.assertNotIn("svc_a", record["raw_response"])

    def test_from_config_requires_directory(self):
        with self.assertRaises(Exception) as caught:
            LocalCausalLMProvider.from_config({
                "local_qwen": {"assets": str(IMPL / "does-not-exist-qwen"), "revision": "x"},
            })
        self.assertEqual(caught.exception.code, "missing_assets")


if __name__ == "__main__":
    unittest.main()
