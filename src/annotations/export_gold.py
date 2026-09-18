import argparse
import json
from pathlib import Path


ALLOWED = {'local-model-automated-v1', 'human-double-adjudicated'}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Export final gold qrels after adjudication.")
    parser.add_argument("--split", type=str, required=True)
    parser.add_argument("--judgments", required=True, help="JSON judgments with provenance")
    parser.add_argument("--require-double", action="store_true")
    parser.add_argument("--round", type=str)
    parser.add_argument("--freeze", type=str)
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--provenance", default="local-model-automated-v1")
    args = parser.parse_args(argv)

    if args.provenance == "llm_lexical_proxy":
        raise SystemExit("proxy_rejected")
    if args.provenance not in ALLOWED:
        raise SystemExit("provenance_rejected")
    payload = json.loads(Path(args.judgments).read_text(encoding="utf-8"))
    rows = payload.get("judgments") or payload.get("candidates") or []
    if not rows:
        raise SystemExit("judgments_required")
    if args.require_double and not payload.get("double_adjudicated"):
        raise SystemExit("double_required")
    out = {
        "schema_version": "cs221-qrels-export-v2",
        "split": args.split,
        "provenance": args.provenance,
        "n": len(rows),
        "status": "exported",
        "human_gold": args.provenance == "human-double-adjudicated",
    }
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"output": args.out, "n": len(rows), "provenance": args.provenance}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
