"""Export the four pinned observation inputs without opening evaluator metadata.

The read boundary is deliberately independent from the management census. Raw
input checksums gate reads; only the management-free projection contributes to
the public source hash. Output directories are immutable versioned releases.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path
import shutil
import tempfile

import pyarrow as pa
import pyarrow.parquet as pq

from .common import (
    DEFAULT_CONFIG, IMPL, ROOT, DataContractError, canonical_hash, load_config,
    read_jsonl, redact, safe_path, sha256, validate_inference, validate_record,
    write_json, write_jsonl,
)


INFERENCE_FILES = (
    "observations.jsonl", "logs-evidence.jsonl", "metric-summaries.jsonl",
    "trace-evidence.jsonl", "incident-index.parquet",
)
SOURCE_FILES = INFERENCE_FILES[:4]
MANAGEMENT_FIELDS = frozenset({"split", "scenario_family_id"})
SOURCE_LIST_FIELDS = frozenset({
    "service_inventory", "input_source_ids", "log_span_ids", "metric_summary_ids",
    "trace_span_ids",
})
PUBLIC_POLICY_FIELDS = (
    "schema_version", "data_version", "source_revision", "transform_version",
    "redaction_version", "seed", "api_enabled", "allowed_fields", "time_policy",
    "null_policy", "unit_policy", "alias_policy",
)


def public_policy(config: dict) -> dict:
    """Exclude paths, source/label hashes, splits and audit-only configuration."""
    return {key: config[key] for key in PUBLIC_POLICY_FIELDS if key in config}


def transform_hash() -> str:
    here = Path(__file__).resolve()
    return canonical_hash({name: sha256(here.with_name(name)) for name in (
        "common.py", "export_inference_data.py",
    )})


def _output_path(path: Path) -> Path:
    """Keep mutations within the workspace and away from immutable sources."""
    output = Path(path).absolute()
    resolved = output.resolve()
    workspace = IMPL.resolve()
    if (resolved != output or not resolved.is_relative_to(workspace)
            or resolved.is_relative_to(workspace / "02_datasets")
            or resolved.is_relative_to(workspace / "scripts")):
        raise DataContractError("PATH_NOT_ALLOWED")
    return output


def _cleanup_staging(staging: Path, parent: Path, prefix: str) -> None:
    """Check the final absolute deletion target immediately before recursion."""
    if staging.exists():
        resolved = staging.resolve()
        if (resolved != staging.absolute() or resolved.parent != parent.resolve()
                or not resolved.is_relative_to(ROOT.resolve())
                or not resolved.name.startswith(prefix)):
            raise DataContractError("PATH_NOT_ALLOWED")
        shutil.rmtree(resolved)


def _read_sources(config: dict, source_root: Path) -> dict[str, list[dict]]:
    sources = config.get("inference_sources", {})
    if set(sources) != set(SOURCE_FILES):
        raise DataContractError("SOURCE_ALLOWLIST")
    records = {}
    for filename in SOURCE_FILES:
        spec = sources[filename]
        # A broad processed root must never let an inference reader open labels.
        expected = f"02_datasets/processed/{filename}"
        if not isinstance(spec, dict) or str(spec.get("path", "")).replace("\\", "/") != expected:
            raise DataContractError("PATH_NOT_ALLOWED")
        source = safe_path(source_root, spec["path"], config["allowed_roots"]["inference"])
        if source != source_root / expected:
            # Even a link into another processed subdirectory could be private.
            raise DataContractError("PATH_NOT_ALLOWED")
        if sha256(source) != spec.get("sha256"):
            raise DataContractError("HASH_MISMATCH")
        rows = read_jsonl(source)
        accepted = set(config["source_fields"][filename])
        if filename == "observations.jsonl":
            accepted -= MANAGEMENT_FIELDS
        projected = []
        for original in rows:
            if not isinstance(original, dict):
                raise DataContractError("SOURCE_SCHEMA")
            row = {key: value for key, value in original.items()
                   if filename != "observations.jsonl" or key not in MANAGEMENT_FIELDS}
            if set(row) != accepted:
                raise DataContractError("SOURCE_SCHEMA")
            # No source schema includes objects or nested containers. Check even
            # fields that will be omitted (for example the old template query).
            for key, value in row.items():
                if key in SOURCE_LIST_FIELDS:
                    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
                        raise DataContractError("SOURCE_SCHEMA")
                elif isinstance(value, (dict, list)):
                    raise DataContractError("SOURCE_SCHEMA")
                elif isinstance(value, float) and not math.isfinite(value):
                    raise DataContractError("NONFINITE_NUMBER")
            projected.append(row)
        # Defend against a file changing while the rows are being read.
        if sha256(source) != spec["sha256"]:
            raise DataContractError("HASH_MISMATCH")
        records[filename] = sorted(projected, key=lambda row: row.get("evidence_id", row.get("incident_id", "")))
    return records


def _transform(sources: dict[str, list[dict]], config: dict) -> dict[str, list[dict]]:
    result = {}
    version = config["transform_version"]
    redaction = config["redaction_version"]
    observations = []
    for source in sources["observations.jsonl"]:
        incident = source["incident_id"]
        row = {key: source[key] for key in (
            "incident_id", "system_id", "observation_start", "window_policy",
            "input_source_ids", "log_span_ids", "metric_summary_ids", "trace_span_ids",
            "provenance_source", "release_revision", "deployment_version", "telemetry_is_synthetic",
        )}
        row.update({
            "observation_end_exclusive": source["observation_end"],
            "service_inventory": [redact(name, incident) for name in source["service_inventory"]],
            "redaction_version": redaction, "transform_version": version,
        })
        validate_record("observations", row, config)
        observations.append(row)
    result["observations.jsonl"] = observations

    logs = []
    for source in sources["logs-evidence.jsonl"]:
        row = dict(source)
        row.update({"modality": "logs", "redaction_version": redaction, "transform_version": version})
        row["text"] = redact(row["text"], row["incident_id"])
        row["service"] = redact(row["service"], row["incident_id"])
        validate_record("logs", row, config)
        logs.append(row)
    result["logs-evidence.jsonl"] = logs

    metrics = []
    for source in sources["metric-summaries.jsonl"]:
        row = dict(source)
        sample_end = row.pop("observation_end")
        try:
            end = dt.datetime.fromisoformat(sample_end) + dt.timedelta(seconds=1)
        except (TypeError, ValueError, OverflowError):
            raise DataContractError("TIME_POLICY") from None
        if not isinstance(row["row_count"], int) or not isinstance(row["null_count"], int):
            raise DataContractError("SOURCE_SCHEMA")
        if row["null_count"] == 0:
            state, reason = "complete", "none"
        elif row["null_count"] == row["row_count"]:
            state, reason = "all_missing", "all_source_values_null"
        else:
            state, reason = "partial", "source_null_values"
        row.update({
            "source_sample_end_inclusive": sample_end,
            "observation_end_exclusive": end.isoformat(), "modality": "metrics",
            "unit": "unknown", "missing_state": state, "missing_reason": reason,
            "redaction_version": redaction, "transform_version": version,
        })
        validate_record("metrics", row, config)
        metrics.append(row)
    result["metric-summaries.jsonl"] = metrics

    traces = []
    for source in sources["trace-evidence.jsonl"]:
        row = dict(source)
        row.update({
            "modality": "traces", "duration_unit": "unknown", "status_code_semantics": "unknown",
            "redaction_version": redaction, "transform_version": version,
        })
        for field in ("serviceName", "methodName", "operationName"):
            row[field] = redact(row[field], row["incident_id"])
        validate_record("traces", row, config)
        traces.append(row)
    result["trace-evidence.jsonl"] = traces

    index = []
    for observation in observations:
        row = {key: observation[key] for key in (
            "incident_id", "observation_start", "observation_end_exclusive",
        )}
        row["evidence_file_ids"] = sorted(observation["input_source_ids"])
        validate_record("index", row, config)
        index.append(row)
    result["incident-index.parquet"] = index
    return result


def _same_release(left: Path, right: Path) -> bool:
    expected = {*INFERENCE_FILES, "input-manifest.json"}
    return (set(item.name for item in left.iterdir()) == expected
            and all(not (left / name).is_symlink() and (left / name).is_file()
                    and sha256(left / name) == sha256(right / name) for name in expected))


def export_inference_data(
    config_path: Path = DEFAULT_CONFIG, source_root: Path = ROOT,
    output_dir: Path = IMPL / "data/inference",
) -> dict:
    """Validate, stage and atomically publish one immutable inference release."""
    config = load_config(Path(config_path))
    sources = _read_sources(config, Path(source_root).resolve())
    records = _transform(sources, config)
    output = _output_path(output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".inference-staging-", dir=output.parent))
    try:
        for filename in SOURCE_FILES:
            write_jsonl(staging / filename, records[filename])
        schema = pa.schema([
            pa.field("incident_id", pa.string(), nullable=False),
            pa.field("observation_start", pa.string(), nullable=False),
            pa.field("observation_end_exclusive", pa.string(), nullable=False),
            pa.field("evidence_file_ids", pa.list_(pa.string()), nullable=False),
        ])
        table = pa.Table.from_pylist(records["incident-index.parquet"], schema=schema)
        pq.write_table(table, staging / "incident-index.parquet", compression="NONE",
                       use_dictionary=False, write_statistics=False, version="2.6")
        files = [{"path": name, "sha256": sha256(staging / name),
                  "bytes": (staging / name).stat().st_size, "rows": len(records[name])}
                 for name in sorted(INFERENCE_FILES)]
        manifest = {
            "schema_version": config["schema_version"], "data_version": config["data_version"],
            "source_revision": config["source_revision"], "source_hash": canonical_hash(sources),
            "config_hash": canonical_hash(public_policy(config)), "transform_hash": transform_hash(),
            "content_hash": canonical_hash(files), "incident_count": len(records["observations.jsonl"]),
            "files": files,
        }
        write_json(staging / "input-manifest.json", manifest)
        validate_inference(staging, config)
        if output.exists():
            if not output.is_dir() or not _same_release(output, staging):
                raise DataContractError("OUTPUT_VERSION_CHANGE_REQUIRED")
            return manifest
        # Rename without replacement: a concurrent publisher must never be overwritten.
        staging.rename(output)
        return manifest
    finally:
        _cleanup_staging(staging, output.parent, ".inference-staging-")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=IMPL / "data/inference")
    args = parser.parse_args()
    try:
        manifest = export_inference_data(args.config, args.source_root, args.output)
    except (DataContractError, OSError) as error:
        # OSError text can carry paths; do not print raw exception messages.
        code = getattr(error, "code", "IO_ERROR")
        print(json.dumps({"status": "failed", "code": code}))
        raise SystemExit(1) from None
    print(json.dumps({"status": "pass", "incident_count": manifest["incident_count"],
                      "content_hash": manifest["content_hash"]}))


if __name__ == "__main__":
    main()
