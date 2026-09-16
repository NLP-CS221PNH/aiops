"""Kaggle GPU Runner and Diagnostics for CS221 AIOps RAG.

Enables automated verification and execution of heavy neural inference
(E5-small-v2 embeddings and LLM generators) on Kaggle GPU instances (NVIDIA T4 / P100).
"""
import json
import os
import sys
import time
from pathlib import Path


def check_gpu_environment():
    """Detects GPU availability, CUDA version, device specs, and PyTorch runtime."""
    env_info = {
        "platform": sys.platform,
        "python_version": sys.version,
        "cuda_available": False,
        "device_count": 0,
        "device_name": "CPU",
        "gpu_memory_gb": 0.0,
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
        env_info["torch_version"] = "not_installed"
        
    return env_info


def save_kaggle_environment_report(output_dir: Path):
    """Outputs environment report to JSON for audit."""
    info = check_gpu_environment()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "kaggle-gpu-environment.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    return info, report_file


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[1]
    reports_dir = base / "reports"
    info, path = save_kaggle_environment_report(reports_dir)
    print("=== Kaggle GPU Runtime Diagnostic ===")
    print(json.dumps(info, indent=2))
    print(f"Report saved to: {path}")
