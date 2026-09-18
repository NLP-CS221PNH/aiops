"""Compare git ls-files to exact public_git_files and fail on denylist hits."""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

_IMPL = Path(__file__).resolve().parents[1]
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

from src.data.common import IMPL


def posix(path: str) -> str:
    return path.replace("\\", "/")


def load_lists(config_path: Path) -> tuple[set[str], list[str]]:
    payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
    files = {posix(item) for item in payload.get("public_git_files") or []}
    denylist = [posix(item) for item in payload.get("denylist") or []]
    if not files:
        raise SystemExit("missing_public_git_files")
    return files, denylist


def denylist_hits(paths: list[str], denylist: list[str]) -> list[str]:
    return [
        path for path in paths
        if any(fnmatch.fnmatch(path, pattern) for pattern in denylist)
    ]


def compare(tracked: list[str], expected: set[str], denylist: list[str]) -> dict:
    tracked_set = {posix(item) for item in tracked if item}
    extra = sorted(tracked_set - expected)
    missing = sorted(expected - tracked_set)
    denied = denylist_hits(sorted(tracked_set), denylist)
    return {
        "ok": not extra and not missing and not denied,
        "extra": extra,
        "missing": missing,
        "denied": denied,
        "tracked": len(tracked_set),
        "expected": len(expected),
    }


def git_ls_files(root: Path) -> list[str]:
    out = subprocess.check_output(["git", "ls-files", "-z"], cwd=root)
    return [posix(item) for item in out.decode().split("\0") if item]


def _read_listing(path: Path) -> list[str]:
    return [
        posix(line.strip())
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate public Git tip file set")
    parser.add_argument("--config", default=str(IMPL / "configs" / "kaggle.yaml"))
    parser.add_argument("--files-from", default=None, help="optional path list; skips git")
    args = parser.parse_args(argv)
    expected, denylist = load_lists(Path(args.config))
    tracked = _read_listing(Path(args.files_from)) if args.files_from else git_ls_files(IMPL)
    result = compare(tracked, expected, denylist)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
