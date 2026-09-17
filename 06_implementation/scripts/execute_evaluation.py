"""F1/F2 freeze helpers and evaluation table orchestration.

Synthetic generation scoring is disabled. Headline tables come from src.evaluation.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
import sys
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.data.common import sha256
from src.retrieval.inputs import frozen_policy_hash, load_config as load_retrieval_config
from src.retrieval.runner import TOKENIZER_HASH, digest, environment, implementation_hashes
from src.annotations.freeze_f2 import build_f2_freeze
from src.evaluation.tables import write_headline_tables


def load_corpus_chunks(path: Path):
    """Load only reviewed, allowlisted chunks through the shared input gate."""
    from src.retrieval.inputs import load_config, load_corpus

    config = load_config(BASE_DIR / "configs" / "retrieval.yaml")
    expected = BASE_DIR / Path(config["corpus_manifest"]).parent / "chunks.jsonl"
    if path.resolve() != expected.resolve():
        raise ValueError("CORPUS_PATH_MISMATCH")
    chunks, _ = load_corpus(config)
    return chunks


def execute_f1_freeze(f1_path: Path, retrieval_cfg_path: Path) -> Dict[str, Any]:
    """Generates the authenticated F1 freeze manifest."""
    cfg = load_retrieval_config(retrieval_cfg_path)
    load_corpus_chunks(BASE_DIR / "data" / "knowledge" / "chunks.jsonl")
    impl_hashes = implementation_hashes()
    env_info = environment()
    f1_data = {
        "schema_version": "cs221-freeze-f1-v1",
        "gate": "F1",
        "status": "frozen",
        "owner_plan": "08",
        "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "retrieval_policy_hash": frozen_policy_hash(cfg),
        "corpus_manifest_hash": cfg["corpus_manifest_sha256"],
        "input_manifest_hash": cfg["input_manifest_sha256"],
        "implementation_hash": digest(impl_hashes),
        "environment_hash": digest(env_info),
        "query_schema_hash": cfg["query_schema_sha256"],
        "tokenizer_hash": TOKENIZER_HASH,
        "description": "F1 Freeze linking retrieval policy, model assets, corpus, and environment.",
        "config": {
            "primary_endpoint": "passage_ndcg_5",
            "comparator_tie_break": "BM25",
            "conditions": ["IR-B", "IR-D", "IR-H", "G0", "GB", "GD", "GH"],
        },
        "hashes": {
            "retriever": digest(impl_hashes),
            "generator": "deepseek-flash-v1",
            "renderer": "whole-evidence-representations-v1",
            "train_dev_bundle": cfg["input_manifest_sha256"],
        },
        "selected_conditions": ["IR-B", "IR-D", "IR-H", "G0", "GB", "GD", "GH"],
        "comparator": "BM25",
    }
    locked = BASE_DIR / "freezes" / "F1.json"
    if f1_path.resolve() == locked.resolve() and locked.exists():
        raise SystemExit("f1_overwrite_forbidden")
    f1_path.parent.mkdir(parents=True, exist_ok=True)
    with open(f1_path, "w", encoding="utf-8") as handle:
        json.dump(f1_data, handle, indent=2)
    print(f"Saved F1 freeze to {f1_path} (SHA256: {sha256(f1_path)})")
    return f1_data


def execute_f2_freeze(f1_path: Path, test_pool_manifest_path: Path, test_qrels_path: Path, f2_path: Path) -> Dict[str, Any]:
    return build_f2_freeze(
        f1_path=f1_path,
        test_pool_manifest_path=test_pool_manifest_path,
        test_qrels_path=test_qrels_path,
        rubric_version="rubric-v1",
        annotation_version="06.F2-v1",
        provenance="llm_lexical_proxy",
        provenance_sidecar_path=Path(__file__).resolve().parents[1] / "freezes" / "F2.provenance.json",
        coverage_info={
            "top5_coverage_ratio": None,
            "top10_coverage_ratio": None,
            "required_pairs_count": None,
            "judged_pairs_count": None,
            "note": "refusing fabricated 1.0 coverage; existing F2.json bytes are historical",
        },
        out_f2_path=None,
    )


def run_grounded_generation_and_scoring():
    load_corpus_chunks(BASE_DIR / "data" / "knowledge" / "chunks.jsonl")
    write_headline_tables(BASE_DIR)
    raise RuntimeError("SYNTHETIC_EVALUATION_DISABLED: historical proxy outputs are forensics only")


if __name__ == "__main__":
    run_grounded_generation_and_scoring()
