"""Measure the local CPU runtime and replay the inference-only notebook twice.

This is a management caller: only select_train_ids reads a private sidecar. Each
fresh worker receives two opaque IDs and reads the inference package and notebook.
No raw source telemetry, models, credentials, networks or GPU runtime are used.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import ctypes
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import site
import subprocess
import sys
import sysconfig
import tempfile
import time
from datetime import datetime, timezone


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def select_train_ids(split_map: Path) -> list[str]:
    """Private management operation; never called by notebook/smoke workers."""
    with split_map.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    all_ids = [row["incident_id"] for row in rows]
    if len(all_ids) != 90 or len(set(all_ids)) != 90:
        raise ValueError("SMOKE_SPLIT_MAP_IDS")
    train_ids = sorted(row["incident_id"] for row in rows if row["split"] == "train")
    if len(train_ids) != 54:
        raise ValueError("SMOKE_TRAIN_COUNT")
    return train_ids[:2]


def memory_snapshot() -> dict:
    """Report measured physical memory without an optional monitoring package."""
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in (
                    "total_physical", "available_physical", "total_page_file",
                    "available_page_file", "total_virtual", "available_virtual",
                    "available_extended_virtual",
                )
            ]
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return {"total_bytes": status.total_physical,
                    "available_bytes_at_probe": status.available_physical,
                    "measurement": "Windows GlobalMemoryStatusEx"}
    if Path("/proc/meminfo").is_file():
        values = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            values[key] = int(value.strip().split()[0]) * 1024
        return {"total_bytes": values["MemTotal"],
                "available_bytes_at_probe": values.get("MemAvailable"),
                "measurement": "/proc/meminfo"}
    return {"total_bytes": None, "available_bytes_at_probe": None,
            "measurement": "unavailable on this platform"}


def runtime_snapshot() -> dict:
    import pyarrow
    cfg = Path(sys.prefix) / "pyvenv.cfg"
    config_text = cfg.read_text(encoding="utf-8") if cfg.is_file() else ""
    system_site = "include-system-site-packages = true" in config_text.lower()
    return {
        "os": {"system": platform.system(), "release": platform.release(),
               "version": platform.version(), "machine": platform.machine()},
        "python": {"version": platform.python_version(),
                   "implementation": platform.python_implementation(),
                   "executable": sys.executable,
                   "cache_tag": sys.implementation.cache_tag,
                   "soabi": sysconfig.get_config_var("SOABI"),
                   "extension_suffix": sysconfig.get_config_var("EXT_SUFFIX"),
                   "pointer_bits": ctypes.sizeof(ctypes.c_void_p) * 8,
                   "isolated_mode": bool(sys.flags.isolated),
                   "user_site_enabled": bool(site.ENABLE_USER_SITE),
                   "venv": sys.prefix != sys.base_prefix,
                   "system_site_packages": system_site},
        "packages": dict(sorted((d.metadata["Name"], d.version)
                                for d in importlib.metadata.distributions())),
        "pyarrow": {"version": pyarrow.__version__,
                    "cpp_version": pyarrow.cpp_version},
        "cpu": {"processor": platform.processor() or None,
                "logical_cores": os.cpu_count(), "device_used": "cpu"},
        "ram": memory_snapshot(),
        "gpu": {"device": None, "used": False, "state": "not_probed"},
    }


def run_notebook_worker(notebook_path: Path, inference_root: Path,
                        incident_ids: list[str]) -> dict:
    notebook = read_json(notebook_path)
    if notebook.get("nbformat") != 4:
        raise ValueError("SMOKE_NOTEBOOK_FORMAT")
    cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    if any(cell.get("outputs") for cell in cells):
        raise ValueError("SMOKE_NOTEBOOK_OUTPUTS_NOT_EMPTY")
    runtime = runtime_snapshot()
    if (runtime["python"]["implementation"] != "CPython"
            or not runtime["python"]["version"].startswith("3.11.")
            or runtime["python"]["pointer_bits"] != 64
            or runtime["pyarrow"]["version"] != "21.0.0"):
        raise ValueError("SMOKE_PYTHON_ABI_VERSION")
    if (not runtime["python"]["venv"] or not runtime["python"]["isolated_mode"]
            or runtime["python"]["user_site_enabled"]
            or runtime["python"]["system_site_packages"]):
        raise ValueError("SMOKE_ENVIRONMENT_NOT_ISOLATED")
    context = {"INFERENCE_ROOT": inference_root.resolve(), "SMOKE_IDS": incident_ids}
    started = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        for cell in cells:
            exec(compile("".join(cell["source"]), str(notebook_path), "exec"), context)
    return {"pid": os.getpid(), "runtime": runtime,
            "elapsed_seconds": round(time.perf_counter() - started, 6),
            "result": context["smoke_result"]}


def build_environment_report(implementation_root: Path = IMPLEMENTATION_ROOT,
                             python_executable: Path | None = None,
                             output_path: Path | None = None) -> dict:
    root = implementation_root.resolve()
    runtime_path = root / "configs/runtime.yaml"
    runtime_config = read_json(runtime_path)  # JSON is the supported YAML subset.
    if (runtime_config["device"] != "cpu" or runtime_config["api_enabled"]
            or runtime_config["gpu_enabled"] or runtime_config["network_enabled"]
            or runtime_config["smoke_incident_count"] != 2
            or runtime_config["clean_process_runs"] != 2):
        raise ValueError("SMOKE_RUNTIME_POLICY")
    inference_root = root / "data/inference"
    manifest_path = inference_root / "input-manifest.json"
    manifest = read_json(manifest_path)
    # This schema check is management-only. Notebook execution below uses only
    # the inference package, so it works without source or private sidecars.
    sys.path.insert(0, str(IMPLEMENTATION_ROOT))
    from src.data.common import validate_inference, writable_path, load_config
    schema_result = validate_inference(inference_root)
    split_map = root / "data/private/split-map.tsv"
    data_config = load_config(root / "configs/data.yaml")
    if sha256(split_map) != data_config['private_sources']['split-map.tsv']['sha256']:
        raise ValueError("SMOKE_SPLIT_HASH")
    smoke_ids = select_train_ids(split_map)
    notebook_path = root / "notebooks/00-environment-smoke.ipynb"
    python_executable = python_executable or Path(sys.executable)
    # Keep only operating-system necessities; do not copy API keys or Python
    # package path overrides into the smoke subprocess environment.
    child_env = {key: value for key, value in os.environ.items()
                 if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC"}}
    runs = []
    for _ in range(2):
        # A distinct empty working directory proves no notebook/kernel state
        # and no relative lookup of the repository's raw/source data is needed.
        with tempfile.TemporaryDirectory(prefix="cs221-smoke-") as workdir:
            completed = subprocess.run(
                [str(python_executable), "-I", "-B", str(Path(__file__).resolve()),
                 "--smoke-worker", "--notebook", str(notebook_path),
                 "--inference-root", str(inference_root), "--incident-ids", *smoke_ids],
                cwd=workdir, env=child_env, check=False, text=True,
                capture_output=True, timeout=60,
            )
        if completed.returncode:
            # Never copy arbitrary child stderr, notebook content or raw rows.
            raise RuntimeError("SMOKE_CHILD_FAILED")
        runs.append(json.loads(completed.stdout))
    if runs[0]["result"] != runs[1]["result"]:
        raise ValueError("SMOKE_NONDETERMINISTIC")
    if len({run["pid"] for run in runs}) != 2:
        raise ValueError("SMOKE_PROCESS_NOT_RESTARTED")
    if any(run["runtime"]["packages"] != runs[0]["runtime"]["packages"] for run in runs):
        raise ValueError("SMOKE_PACKAGE_DRIFT")
    manifest_hash = sha256(manifest_path)
    if any(run["result"]["manifest_sha256"] != manifest_hash for run in runs):
        raise ValueError("SMOKE_MANIFEST_CHANGED")
    report = {
        "schema_version": "cs221-environment-check-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "local_gate": "pass", "execution_scope": "CPU data loading; no model execution",
        "manifest_sha256": manifest_hash,
        "data_content_hash": manifest["content_hash"],
        "source_revision": manifest["source_revision"],
        "source_hash": manifest["source_hash"], "config_hash": manifest["config_hash"],
        "transform_hash": manifest["transform_hash"],
        "runtime_config_sha256": sha256(runtime_path),
        "requirements_lock_sha256": sha256(root / "configs/requirements-lock.txt"),
        "notebook_sha256": sha256(notebook_path),
        "smoke_ids": smoke_ids,
        "selection": {"scope": "private management caller", "partition": "train",
                      "method": "first two lexicographically sorted opaque IDs",
                      "split_map_sha256": sha256(split_map)},
        "schema_validation": schema_result,
        "notebook_outputs": "empty; only aggregate hashes/counts/opaque IDs emitted during replay",
        "reproducibility": {"fresh_isolated_processes": 2,
                            "same_ids_and_content_hashes": True,
                            "same_runtime_packages": True,
                            "execution_engine": "sequential code cells in two fresh CPython -I processes",
                            "jupyter_kernel_execution": False},
        "runtime": runs[0]["runtime"], "smoke_runs": runs,
        "api_enabled": False, "network_used": False,
        "kaggle": runtime_config["kaggle"],
        "human_review": {"state": "pending", "owners": ["B", "C"],
                         "scope": "independent replay and hardware/payload review"},
    }
    output_path = writable_path(output_path or root / "reports/environment-check.json")
    if not output_path.is_relative_to((IMPLEMENTATION_ROOT / "reports").resolve()):
        raise ValueError("SMOKE_OUTPUT_PATH")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = writable_path(output_path.with_suffix(".json.tmp"))
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                         encoding="utf-8")
    temporary.replace(output_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--implementation-root", type=Path, default=IMPLEMENTATION_ROOT)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--notebook", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--inference-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--incident-ids", nargs=2, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.smoke_worker:
            result = run_notebook_worker(args.notebook, args.inference_root, args.incident_ids)
        else:
            report = build_environment_report(args.implementation_root, args.python, args.output)
            result = {"local_gate": report["local_gate"], "smoke_ids": report["smoke_ids"],
                      "manifest_sha256": report["manifest_sha256"],
                      "kaggle_state": report["kaggle"]["state"]}
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except Exception as error:
        # Rule-shaped messages only; unexpected errors never dump payload/paths.
        code = str(error) if str(error).startswith("SMOKE_") else type(error).__name__
        print(json.dumps({"status": "failed", "code": code}), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
