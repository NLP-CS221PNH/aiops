"""Local in-process generation. Production never returns fixture text."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


class GenerationUnavailable(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def load_config(config_path: str = "configs/generation.yaml") -> Dict[str, Any]:
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as handle:
        if yaml is None:
            return json.loads(handle.read())
        return yaml.safe_load(handle) or {}


def check_permissions(config: Dict[str, Any]) -> bool:
    perms = config.get("permissions", {})
    return perms.get("api") == "approved" or perms.get("local") == "approved"


def _local_enabled(config: Mapping[str, Any]) -> bool:
    return config.get("permissions", {}).get("local") == "approved"


def _api_enabled(config: Mapping[str, Any]) -> bool:
    return config.get("permissions", {}).get("api") == "approved"


def generate_response(
    prompt: str | Sequence[Mapping[str, str]],
    context: Dict[str, Any],
    config: Dict[str, Any],
    provider: Any = None,
) -> Tuple[str, Dict[str, Any]]:
    if not check_permissions(config):
        return "", {"status": "blocked_permission", "error": "API/Local permission not approved."}
    if _api_enabled(config) and not _local_enabled(config):
        if config.get("approved_cap_usd") is None:
            return "", {"status": "budget_stopped", "error": "approved_cap_usd is null"}
        return "", {
            "status": "remote_api_disabled",
            "error": "Remote model APIs are out of scope; provision local Qwen assets.",
        }
    if not _local_enabled(config):
        return "", {"status": "blocked_permission", "error": "local permission not approved"}
    if provider is None:
        try:
            provider = LocalCausalLMProvider.from_config(config)
        except GenerationUnavailable as exc:
            return "", {"status": exc.code, "error": str(exc), "usage": None}
    raw, metadata = provider.generate(prompt, context, config)
    if "svc_a" in (raw or "") or "mock logic" in (raw or ""):
        return "", {"status": "refusing_mock_as_result", "error": "production provider returned fixture text"}
    metadata.setdefault("usage", None)
    return raw, metadata


class LocalCausalLMProvider:
    def __init__(self, assets_dir: Path, revision: str):
        self.assets_dir = Path(assets_dir)
        self.revision = revision
        self.tokenizer = None
        self.model = None

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "LocalCausalLMProvider":
        provider = config.get("local_qwen") or config.get("provider") or {}
        assets = provider.get("assets") or os.environ.get("QWEN_ASSETS")
        if not assets:
            raise GenerationUnavailable("missing_assets", "Qwen assets path is not configured")
        root = Path(assets)
        if not root.is_dir():
            raise GenerationUnavailable("missing_assets", f"Qwen assets missing: {root}")
        instance = cls(root, str(provider.get("revision") or ""))
        instance._load()
        return instance

    def _load(self) -> None:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
        except ImportError as exc:
            raise GenerationUnavailable("missing_runtime", f"transformers/torch unavailable: {exc}") from exc
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.assets_dir, local_files_only=True, trust_remote_code=False)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.assets_dir, local_files_only=True, trust_remote_code=False)
        self.model.eval()
        self._torch = torch

    def generate(self, prompt, context: Mapping[str, Any], config: Mapping[str, Any]) -> Tuple[str, Dict[str, Any]]:
        if self.model is None or self.tokenizer is None:
            self._load()
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = list(prompt)
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        encoded = self.tokenizer(text, return_tensors="pt")
        decoding = (config.get("decoding") or {})
        temperature = float(decoding.get("temperature", 0.1))
        seed = int(context.get("seed") or config.get("seed") or 221)
        self._torch.manual_seed(seed)
        with self._torch.no_grad():
            output = self.model.generate(
                **encoded,
                max_new_tokens=int((config.get("budgets") or {}).get("output", 768)),
                do_sample=temperature > 0,
                temperature=max(temperature, 1e-5),
                top_p=1.0,
            )
        prompt_len = encoded["input_ids"].shape[-1]
        generated = output[0][prompt_len:]
        raw = self.tokenizer.decode(generated, skip_special_tokens=True)
        return raw, {
            "status": "success",
            "usage": {
                "prompt_tokens": int(prompt_len),
                "completion_tokens": int(generated.shape[-1]),
                "total_tokens": int(output.shape[-1]),
            },
            "model_returned": str((config.get("local_qwen") or config.get("provider") or {}).get("model")),
            "mock": False,
        }
