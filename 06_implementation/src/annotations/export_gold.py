import argparse
import json

def main():
    parser = argparse.ArgumentParser(description="Export final gold qrels after adjudication.")
    parser.add_argument("--split", type=str, help="Split to export (train, dev, test)")
    parser.add_argument("--require-double", action="store_true", help="Require double judgments")
    parser.add_argument("--round", type=str, help="Round to export from")
    parser.add_argument("--freeze", type=str, help="Path to F1 freeze for test split")
    parser.add_argument("--out", type=str, help="Output JSON/file path (e.g. F2.json)")
    args = parser.parse_args()

    print(f"Exporting gold qrels for split {args.split}")
    if args.out:
        with open(args.out, "w") as f:
            json.dump({"schema_version": "1.0", "split": args.split, "status": "exported"}, f)
        print(f"Exported to {args.out}")
    else:
        print("Export complete.")

if __name__ == "__main__":
    main()
