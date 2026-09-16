import argparse
import sys
import os
from src.generation.runner import run_pilot

def main():
    parser = argparse.ArgumentParser(description="Generation Runner")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--config", help="Path to config file", default="configs/generation.yaml")
    parser.add_argument("--freeze", help="Path to freeze file for test mode")
    parser.add_argument("--input-manifest", help="Path to input manifest for test mode")
    parser.add_argument("--incident-list", required=True, help="Path to incident list file or comma separated string")
    parser.add_argument("--run-id", required=True, help="Run ID")
    
    args = parser.parse_args()
    
    if args.command == "run":
        if args.freeze and args.config != "configs/generation.yaml" and args.config != parser.get_default("config"):
            print("--config and --freeze are mutually exclusive")
            sys.exit(2)
            
        incident_ids = []
        if os.path.exists(args.incident_list):
            with open(args.incident_list, "r", encoding="utf-8") as f:
                incident_ids = [line.strip() for line in f if line.strip()]
        else:
            incident_ids = [x.strip() for x in args.incident_list.split(",") if x.strip()]
            
        manifest = run_pilot(args.run_id, incident_ids, args.config)
        
        if manifest["failed"] > 0 or manifest["stopped"] > 0:
            print(f"Run completed with issues: {manifest['failed']} failed, {manifest['stopped']} stopped")
            sys.exit(1)
        else:
            print("Run completed successfully")
            sys.exit(0)

if __name__ == "__main__":
    main()
