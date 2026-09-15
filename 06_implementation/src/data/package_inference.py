"""Create a deterministic local ZIP from the exact validated inference allowlist."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

from .common import DEFAULT_CONFIG, IMPL, DataContractError, load_config, sha256, validate_inference
from .export_inference_data import INFERENCE_FILES, _output_path


def package_inference(
    inference_dir: Path = IMPL / "data/inference",
    output_path: Path = IMPL / "artifacts/inference-package.zip",
    config_path: Path = DEFAULT_CONFIG,
) -> dict:
    """Package no raw data, private sidecars, notebooks, or unlisted files."""
    source = Path(inference_dir).resolve()
    validate_inference(source, load_config(Path(config_path)))
    manifest_bytes = (source / "input-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    entries = manifest["files"]
    if len(entries) != len(INFERENCE_FILES) or {entry["path"] for entry in entries} != set(INFERENCE_FILES):
        raise DataContractError("PACKAGE_ALLOWLIST")
    # Snapshot only the allowlist into memory and hash those exact archive bytes.
    payloads = {"input-manifest.json": manifest_bytes}
    for entry in entries:
        path = source / entry["path"]
        if path.is_symlink() or path.resolve().parent != source:
            raise DataContractError("PATH_NOT_ALLOWED")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"] or len(data) != entry["bytes"]:
            raise DataContractError("HASH_MISMATCH")
        payloads[entry["path"]] = data
    output = _output_path(output_path)
    if output.resolve().is_relative_to(source):
        raise DataContractError("PATH_NOT_ALLOWED")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".package-staging-", suffix=".zip",
                                     dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(payloads.items()):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(temporary) as archive:
            if archive.namelist() != sorted(payloads) or archive.testzip() is not None:
                raise DataContractError("PACKAGE_VERIFICATION")
        digest, size = sha256(temporary), temporary.stat().st_size
        if output.exists():
            if not output.is_file() or sha256(output) != digest:
                raise DataContractError("OUTPUT_VERSION_CHANGE_REQUIRED")
        else:
            temporary.rename(output)
        return {"path": str(output), "sha256": digest, "bytes": size,
                "files": sorted(payloads), "manifest_hash": hashlib.sha256(manifest_bytes).hexdigest()}
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inference", type=Path, default=IMPL / "data/inference")
    parser.add_argument("--output", type=Path, default=IMPL / "artifacts/inference-package.zip")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    try:
        receipt = package_inference(args.inference, args.output, args.config)
    except (DataContractError, OSError) as error:
        print(json.dumps({"status": "failed", "code": getattr(error, "code", "IO_ERROR")}))
        raise SystemExit(1) from None
    print(json.dumps({"status": "pass", "sha256": receipt["sha256"], "files": receipt["files"]}))


if __name__ == "__main__":
    main()
