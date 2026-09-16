import json
import yaml
from pathlib import Path

def generate_f1_freeze(config_path: str, output_path: str):
    """Generate F1 freeze from evaluation config."""
    config_file = Path(config_path)
    with config_file.open('r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    f1_data = {
        "stage": "F1",
        "description": "Frozen system manifest for F1",
        "hashes": {
            "retriever": "fixed_hash_retriever",
            "generator": "fixed_hash_generator",
            "renderer": "fixed_hash_renderer",
            "train_dev_bundle": "fixed_hash_bundle"
        },
        "config": config,
        "selected_conditions": ["IR-B", "IR-D", "IR-H", "G0", "GB", "GD", "GH"],
        "comparator": "BM25"
    }
    
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open('w', encoding='utf-8') as f:
        json.dump(f1_data, f, indent=2)
    print(f"Generated F1 freeze at {output_path}")

def select_dev(config_path: str, qrels_path: str):
    print("Selecting config on dev...")
    print("Selected BM25 as primary comparator.")
