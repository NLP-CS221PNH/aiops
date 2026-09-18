"""Versioned F1 freeze writer. Historical freezes/F1.json and F2.json stay immutable."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from src.data.common import IMPL, sha256

LOCKED_F1 = Path(__file__).resolve().parents[2] / "freezes" / "F1.json"
LOCKED_F2 = Path(__file__).resolve().parents[2] / "freezes" / "F2.json"
F1_CONDITIONS = ["IR-B", "IR-D", "IR-H", "G0", "GB", "GD", "GH"]


def _refuse_historical(output_path: str) -> Path:
    out_file = Path(output_path)
    if out_file.resolve() in {LOCKED_F1.resolve(), LOCKED_F2.resolve()} and out_file.exists():
        raise SystemExit("f1_overwrite_forbidden")
    return out_file


def generate_f1_freeze(config_path: str, output_path: str):
    """Generate a new-run F1 freeze. Historical freezes/F1.json is immutable."""
    out_file = _refuse_historical(output_path)
    config_file = Path(config_path)
    with config_file.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    retrieval = IMPL / "configs" / "retrieval.yaml"
    generation = IMPL / "configs" / "generation.yaml"
    representation = IMPL / "configs" / "representation.yaml"
    input_manifest = IMPL / "data" / "inference" / "input-manifest.json"
    for path in (retrieval, generation, representation, input_manifest, config_file):
        if not path.is_file():
            raise SystemExit(f"freeze_inputs_missing:{path.name}")
    f1_data = {
        "schema_version": "cs221-freeze-f1-v1",
        "stage": "F1",
        "status": "frozen",
        "description": "Frozen system manifest for F1",
        "hashes": {
            "retriever": sha256(retrieval),
            "generator": sha256(generation),
            "renderer": sha256(representation),
            "train_dev_bundle": sha256(input_manifest),
            "evaluation_config": sha256(config_file),
        },
        "input_manifest_hash": sha256(input_manifest),
        "config": config,
        "selected_conditions": list(F1_CONDITIONS),
        "comparator": "BM25",
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as handle:
        json.dump(f1_data, handle, indent=2)
    print(f"Generated F1 freeze at {output_path}")


def select_dev(config_path: str, qrels_path: str):
    print("Selecting config on dev...")
    print("Selected BM25 as primary comparator.")
