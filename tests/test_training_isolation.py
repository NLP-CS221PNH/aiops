"""Synthetic G1 train/dev fixture. Train code must not touch private-test."""
from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.data.common import DataContractError, sha256
from src.training.access import TrainingAccessGuard
from src.training.config import load_resolved_kaggle
from src.training.preflight import preflight


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _write_split(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["incident_id", "split", "split_version", "scenario_family_id"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


def _file_record(path: Path, rows: int) -> dict:
    return {
        "path": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "rows": rows,
    }


def _partition(root: Path, split: str, incident_id: str, family: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    gold_path = root / "ground_truth.jsonl"
    split_path = root / "split-map.tsv"
    _write_jsonl(gold_path, [{
        "incident_id": incident_id,
        "root_cause_service": "cartservice",
        "scenario_family_id": family,
        "label_release_revision": "synthetic",
    }])
    _write_split(split_path, [{
        "incident_id": incident_id,
        "split": split,
        "split_version": "synthetic-v1",
        "scenario_family_id": family,
    }])
    manifest = {
        "schema_version": "cs221-training-partition-v1",
        "split": split,
        "role": "synthetic-fixture",
        "incident_count": 1,
        "family_count": 1,
        "family_ids": [family],
        "incident_ids": [incident_id],
        "split_version": "synthetic-v1",
        "files": [_file_record(gold_path, 1), _file_record(split_path, 1)],
    }
    (root / "partition-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _write_train_preflight_config(base: Path, train: Path, dev: Path, inference: Path) -> Path:
    resolved = {
        "schema_version": "cs221-kaggle-resolved-v1",
        "inference_root": str(inference),
        "private_train_root": str(train),
        "private_dev_root": str(dev),
        "output_root": str(base / "out"),
    }
    cfg = base / "kaggle.resolved.json"
    cfg.write_text(json.dumps(resolved, indent=2), encoding="utf-8")
    return cfg


class TrainingIsolationTests(unittest.TestCase):
    def test_preflight_does_not_stat_sibling_private_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            train = base / "private-train"
            dev = base / "private-dev"
            test = base / "private-test"
            inference = base / "inference"
            inference.mkdir()
            (inference / "input-manifest.json").write_text("{}", encoding="utf-8")
            _partition(train, "train", "inc_aaaaaaaaaaaaaaaa", "fam_train")
            _partition(dev, "dev", "inc_bbbbbbbbbbbbbbbb", "fam_dev")
            _partition(test, "test", "inc_cccccccccccccccc", "fam_test")
            sentinel = test / "ground_truth.jsonl"
            before = sentinel.stat().st_mtime_ns
            cfg = _write_train_preflight_config(base, train, dev, inference)
            result = preflight(cfg, data_only=True, require_gpu=False)
            self.assertEqual(result["status"], "pass")
            self.assertFalse(result["test_root_accessed"])
            loaded = load_resolved_kaggle(cfg)
            self.assertNotIn("private_test_root", loaded)
            test_root = test.resolve()
            for _op, path in result["touched"]:
                self.assertFalse(Path(path).resolve().is_relative_to(test_root), path)
            self.assertEqual(sentinel.stat().st_mtime_ns, before)

    def test_guard_records_private_test_stat(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            train = base / "private-train"
            test = base / "private-test"
            _partition(train, "train", "inc_aaaaaaaaaaaaaaaa", "fam_train")
            _partition(test, "test", "inc_cccccccccccccccc", "fam_test")
            guard = TrainingAccessGuard([train], ())
            with self.assertRaises(DataContractError):
                guard.stat(test / "ground_truth.jsonl")
            test_root = test.resolve()
            self.assertTrue(any(Path(path).resolve().is_relative_to(test_root) for _op, path in guard.touched))


if __name__ == "__main__":
    unittest.main()
