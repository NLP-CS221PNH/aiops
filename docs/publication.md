# Publication boundary

This repository's **current Git tip** is Kaggle-runnable source plus this `docs/` folder. It is MIT for project Software (`LICENSE`). That license does not relicense third-party data, PDFs, full text, snapshots, or gold labels.

## Default deny

- Raw RCAEval Parquet, paper caches, source PDFs, gold labels, private sidecars, and knowledge snapshot **source bytes** are not on the public tip.
- Trainer partitions under `data/training-inputs/` are local-only and gitignored. Train labels may be used by the LoRA trainer; the test partition stays evaluator-only and is omitted from train/preflight config.
- Safe observations in `data/inference/` are the only model-visible bundle in this tree.

## History is not the tip

Decision `HIST-2026-09-16-NO-REWRITE`: this plan does **not** rewrite Git history. Untracking removes bytes from the current tip only.

A clone that includes `.git` still contains historical blobs, including:

- research-pack catalogs (`00_plan`–`05_research`)
- G1-equivalent leak files (for example `02_datasets/acquired/labels/acquisition-manifest.tsv`, `cases-index.json`)
- `inject_time.txt` and other evaluator-only labels from older commits

**Untrack is not a leak control.** Anyone with the history can recover those blobs. A coordinated `git filter-repo` force-push is a later owner decision, not this delivery.

## Trainer isolation

`python -m src.training` must not `stat`, `open`, or `hash` `private-test`. Attach private train/dev **outside** the source ZIP. Do not put test gold in `configs/kaggle.resolved.json`.
