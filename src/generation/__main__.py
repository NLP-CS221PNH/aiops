import argparse
import os
import sys

from src.generation.runner import run_generation


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local generation runner")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--config", default="configs/generation.yaml")
    parser.add_argument("--freeze", help="Frozen F1-style manifest that must match live hashes")
    parser.add_argument("--input-manifest", help="Safe inference input-manifest.json")
    parser.add_argument("--inference-root", help="Safe inference directory")
    parser.add_argument("--condition", default="G0")
    parser.add_argument("--incident-list", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)

    if args.command != "run":
        return 2
    if args.input_manifest and not args.freeze:
        print("input-manifest requires --freeze")
        return 2
    if os.path.exists(args.incident_list):
        with open(args.incident_list, "r", encoding="utf-8") as handle:
            incident_ids = [line.strip() for line in handle if line.strip()]
    else:
        incident_ids = [item.strip() for item in args.incident_list.split(",") if item.strip()]
    try:
        manifest = run_generation(
            args.run_id,
            incident_ids,
            args.config,
            inference_root=args.inference_root,
            condition=args.condition,
            freeze_path=args.freeze,
            input_manifest=args.input_manifest,
        )
    except SystemExit as exc:
        print(str(exc))
        return 4 if "mismatch" in str(exc) or "requires" in str(exc) else 2
    if manifest.get("failed", 0) > 0 or manifest.get("stopped", 0) > 0:
        print(f"Run completed with issues: {manifest['failed']} failed, {manifest['stopped']} stopped")
        return 5 if manifest.get("failed", 0) else 3
    print("Run completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
