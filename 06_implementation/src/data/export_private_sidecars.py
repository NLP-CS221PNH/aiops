"""Management-only export. This module must never be imported by model loaders."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import shutil
import tempfile
import time

from .common import (
    DEFAULT_CONFIG, IMPL, ROOT, DataContractError, load_config, read_jsonl,
    safe_path, sha256, write_json,
)
from .validate_inputs import validate_inputs
from .export_inference_data import _cleanup_staging, _output_path


PRIVATE_FILES = ("split-map.tsv", "ground_truth.jsonl")


def _commit_staging_dir(staging: Path, output: Path, attempts: int = 12) -> None:
    """Promote a staging directory. Windows may deny the first rename while a scanner holds the tree."""
    delay = 0.05
    last_error: OSError | None = None
    for _ in range(attempts):
        try:
            staging.rename(output)
            return
        except PermissionError as error:
            last_error = error
            time.sleep(delay)
            delay = min(delay * 2, 0.5)
    if last_error is not None:
        raise last_error
    staging.rename(output)


def export_private_sidecars(
    config_path: Path = DEFAULT_CONFIG, source_root: Path = ROOT,
    output_dir: Path = IMPL / "data/private", census: dict | None = None,
) -> dict:
    """Copy checked evaluator sidecars byte-for-byte with private provenance."""
    config = load_config(Path(config_path))
    source_root = Path(source_root).resolve()
    if census is None:
        census = validate_inputs(config_path, source_root)
    ids = set(census["incident_ids"])
    specs = config.get("private_sources", {})
    if set(specs) != set(PRIVATE_FILES):
        raise DataContractError("PRIVATE_SOURCE_ALLOWLIST")
    sources, provenance = {}, []
    for name in PRIVATE_FILES:
        spec = specs[name]
        path = safe_path(source_root, spec["path"], config["allowed_roots"]["audit"])
        if sha256(path) != spec["sha256"]:
            raise DataContractError("HASH_MISMATCH")
        if name.endswith(".tsv"):
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream, delimiter="\t"))
        else:
            rows = read_jsonl(path)
        row_ids = [row["incident_id"] for row in rows]
        if set(row_ids) != ids or len(row_ids) != len(ids):
            raise DataContractError("PRIVATE_ID_MISMATCH")
        sources[name] = path
        provenance.append({"path": name, "source_path": spec["path"],
                           "sha256": spec["sha256"], "bytes": path.stat().st_size,
                           "rows": len(rows), "role": "evaluator_only"})
    audit = {
        "schema_version": "cs221-private-audit-v1", "data_version": config["data_version"],
        "source_revision": census["source_revision"], "source_hash": census["source_hash"],
        "incident_count": len(ids), "incident_ids": sorted(ids),
        "files": sorted(provenance, key=lambda row: row["path"]),
        "source_map": census["files"], "role": "audit_and_evaluator_only",
    }
    output = _output_path(output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".private-staging-", dir=output.parent))
    try:
        for name, source in sources.items():
            shutil.copyfile(source, staging / name)
            if sha256(staging / name) != specs[name]["sha256"]:
                raise DataContractError("HASH_MISMATCH")
        write_json(staging / "data-audit.json", audit)
        write_json(staging / "source-census.json", census)
        names = {*PRIVATE_FILES, "data-audit.json", "source-census.json"}
        if output.exists():
            if (not output.is_dir() or set(item.name for item in output.iterdir()) != names
                    or any((output / name).is_symlink() or not (output / name).is_file()
                           or sha256(output / name) != sha256(staging / name) for name in names)):
                raise DataContractError("OUTPUT_VERSION_CHANGE_REQUIRED")
            return audit
        _commit_staging_dir(staging, output)
        return audit
    finally:
        _cleanup_staging(staging, output.parent, ".private-staging-")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=IMPL / "data/private")
    args = parser.parse_args()
    try:
        audit = export_private_sidecars(args.config, args.source_root, args.output)
    except (DataContractError, OSError) as error:
        print(json.dumps({"status": "failed", "code": getattr(error, "code", "IO_ERROR")}))
        raise SystemExit(1) from None
    print(json.dumps({"status": "pass", "incident_count": audit["incident_count"]}))


if __name__ == "__main__":
    main()
