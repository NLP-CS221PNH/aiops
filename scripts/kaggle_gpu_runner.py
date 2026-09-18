"""GPU/runtime receipt for Kaggle and local Windows. Never claims unverified runs."""
from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

IMPL = Path(__file__).resolve().parents[1]
SAIGON_OFFSET = "+07:00"


def check_gpu_environment() -> dict:
    env_info = {
        "platform": sys.platform,
        "python_version": sys.version.split()[0],
        "machine": platform.machine(),
        "cuda_available": False,
        "device_count": 0,
        "device_name": "CPU",
        "gpu_memory_gb": 0.0,
        "torch_version": "not_installed",
        "cuda_version": None,
    }
    try:
        import torch
        env_info["torch_version"] = torch.__version__
        if torch.cuda.is_available():
            env_info["cuda_available"] = True
            env_info["device_count"] = torch.cuda.device_count()
            env_info["device_name"] = torch.cuda.get_device_name(0)
            mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            env_info["gpu_memory_gb"] = round(mem, 2)
            env_info["cuda_version"] = torch.version.cuda
    except ImportError:
        pass
    return env_info


def linux_install_status() -> dict:
    is_linux = sys.platform.startswith("linux")
    return {
        "linux_install_verified": False,
        "reason": (
            "Linux pip-check and tokenizer/tiny-forward receipt not captured on this host"
            if not is_linux
            else "Linux host present but pip-check/tiny-forward receipt has not been recorded"
        ),
        "next_command": "python -m pip check && python -m src.training preflight --require-gpu",
    }


def kaggle_execution_status() -> dict:
    return {
        "kaggle_execution_verified": False,
        "reason": "No actual Kaggle session receipt is attached",
        "next_command": "Open notebooks/03_kaggle_train.ipynb on Kaggle and run setup/preflight cells",
    }


def save_kaggle_environment_report(output_dir: Path) -> tuple[dict, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).astimezone().isoformat()
    payload = {
        "schema_version": "cs221-kaggle-runtime-receipt-v1",
        "created_at": now,
        "timezone": "Asia/Saigon",
        "environment": check_gpu_environment(),
        "linux": linux_install_status(),
        "kaggle": kaggle_execution_status(),
        "candidate_requirements": str(IMPL / "configs" / "kaggle-requirements.in"),
        "qwen_pin": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
        "e5_pin": "ffb93f3bd4047442299a41ebb6fa998a38507c52",
    }
    report_file = output_dir / "kaggle-gpu-environment.json"
    report_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload, report_file


if __name__ == "__main__":
    info, path = save_kaggle_environment_report(IMPL / "reports")
    print("=== Kaggle GPU Runtime Diagnostic ===")
    print(json.dumps(info, indent=2))
    print(f"Report saved to: {path}")
