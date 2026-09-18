import argparse
import json
from pathlib import Path

from src.evaluation.freeze import generate_f1_freeze, select_dev
from src.evaluation.cli_ops import IMPL, analyze, score_runs, validate_handoff, verify_freezes
from src.evaluation.tables import write_headline_tables


def main():
    parser = argparse.ArgumentParser(description="Evaluation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    select_parser = subparsers.add_parser("select-dev")
    select_parser.add_argument("--config", required=True)
    select_parser.add_argument("--qrels", required=True)

    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("--stage", required=True)
    freeze_parser.add_argument("--config", required=True)
    freeze_parser.add_argument("--output-root", default="freezes")
    freeze_parser.add_argument("--run-id", default=None)

    verify_parser = subparsers.add_parser("verify-freezes")
    verify_parser.add_argument("--system", required=True)
    verify_parser.add_argument("--qrels", required=True)

    score_parser = subparsers.add_parser("score")
    score_parser.add_argument("--system", required=True)
    score_parser.add_argument("--qrels", required=True)
    score_parser.add_argument("--runs", required=True)
    score_parser.add_argument("--output", required=True)

    review_parser = subparsers.add_parser("review-import")
    review_parser.add_argument("--judgments", required=True)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--results", required=True)
    analyze_parser.add_argument("--group", required=True)
    analyze_parser.add_argument("--output", required=True)

    handoff_parser = subparsers.add_parser("validate-handoff")
    handoff_parser.add_argument("--manifest", required=True)

    tables_parser = subparsers.add_parser("write-tables")
    tables_parser.add_argument("--impl", default=str(IMPL))

    args = parser.parse_args()

    if args.command == "select-dev":
        select_dev(args.config, args.qrels)
    elif args.command == "freeze":
        if args.stage != "F1":
            raise SystemExit(f"unsupported freeze stage: {args.stage}")
        output = Path(args.output_root) / (f"{args.run_id}-F1.json" if args.run_id else "F1.json")
        generate_f1_freeze(args.config, str(output))
    elif args.command == "verify-freezes":
        verify_freezes(args.system, args.qrels)
    elif args.command == "score":
        score_runs(args.system, args.qrels, args.runs, args.output)
    elif args.command == "review-import":
        raise SystemExit("unsupported: review-import is not implemented")
    elif args.command == "analyze":
        analyze(args.results, args.group, args.output)
    elif args.command == "validate-handoff":
        validate_handoff(args.manifest)
    elif args.command == "write-tables":
        print(json.dumps(write_headline_tables(Path(args.impl))))


if __name__ == "__main__":
    main()
