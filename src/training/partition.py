"""Administrative split partition writer. Trainer join must not import test rows from here."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from src.data.common import sha256, write_json, write_jsonl


def write_split_tsv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=['incident_id', 'scenario_family_id', 'split', 'split_version'],
            delimiter='\t',
            lineterminator='\n',
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in writer.fieldnames})


def file_entry(path: Path, rows: int) -> dict:
    return {'path': path.name, 'sha256': sha256(path), 'bytes': path.stat().st_size, 'rows': rows}


def write_partition(staging: Path, split: str, gold_rows: list[dict], split_rows: list[dict],
                    data_config: dict, role: str = 'research') -> dict:
    root = Path(staging) / f'private-{split}'
    root.mkdir(parents=True, exist_ok=True)
    gold_path = root / 'ground_truth.jsonl'
    split_path = root / 'split-map.tsv'
    ordered_gold = sorted(gold_rows, key=lambda row: row['incident_id'])
    ordered_split = sorted(split_rows, key=lambda row: row['incident_id'])
    write_jsonl(gold_path, ordered_gold)
    write_split_tsv(split_path, ordered_split)
    families = sorted({row['scenario_family_id'] for row in ordered_split})
    manifest = {
        'schema_version': 'cs221-training-partition-v1',
        'role': role,
        'split': split,
        'split_version': data_config['split_version'],
        'label_revision': data_config['source_revision'],
        'incident_count': len(ordered_gold),
        'family_count': len(families),
        'incident_ids': [row['incident_id'] for row in ordered_gold],
        'family_ids': families,
        'service_counts': dict(Counter(row['root_cause_service'] for row in ordered_gold)),
        'parent_ground_truth_sha256': data_config['private_sources']['ground_truth.jsonl']['sha256'],
        'parent_split_map_sha256': data_config['private_sources']['split-map.tsv']['sha256'],
        'files': [file_entry(gold_path, len(ordered_gold)), file_entry(split_path, len(ordered_split))],
    }
    write_json(root / 'partition-manifest.json', manifest)
    return manifest
