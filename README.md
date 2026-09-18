# CS221 · AIOps / RCA / Hybrid RAG — Kaggle source

**Nguyễn Văn Nam - 24521120
Nguyễn Đình Phát - 23521144
Lê Vũ Thiêm Hoàng - 25520584
Bùi Đặng Nhật Nguyên - 23521037**


This Git **tip** is Kaggle-runnable source at the repository root, plus one reading folder: [`docs/`](docs/README.md). Do not `cd 06_implementation`.

## Read this first

- Reading index: [`docs/README.md`](docs/README.md)
- Publication / history caveat: [`docs/publication.md`](docs/publication.md)
- Runbook: [`docs/kaggle-runbook.md`](docs/kaggle-runbook.md)
- Gold roles: [`docs/gold-type-contract.md`](docs/gold-type-contract.md)
- Reports (blank metrics): [`docs/report-vi.md`](docs/report-vi.md), [`docs/report-en.md`](docs/report-en.md)

**History still contains G1-equivalent catalogs and `inject_time.txt` blobs.** Untracking is not a leak control. Decision `HIST-2026-09-16-NO-REWRITE`: this tree was not rewritten.

Root `LICENSE` is MIT for project Software. It does not relicense third-party data or gold labels.

## Run

From the repository root:

```powershell
python -m src.training --help
python -m src.training preflight --config configs/kaggle.resolved.json --data-only
python -m pytest -q -o pythonpath=. tests/test_public_source_tree.py tests/test_training_isolation.py
python scripts/validate-public-source-tree.py
```

Private trainer partitions live in gitignored `data/training-inputs/` and must be attached **outside** the source ZIP. `private-test` stays unmounted for train/preflight. Write `configs/kaggle.resolved.json` from the notebook; that file is gitignored.

Kaggle: extract the packaged source ZIP (`aiops-kaggle-source.zip`) into `/kaggle/working`. Attach private train/dev as a **separate** dataset. Do not assume `/kaggle/input` contains `src/`.

Local ZIP pack:

```powershell
python scripts/build-bilingual-reports.py --contract configs/report-contract.json --blank-results --output artifacts/kaggle-delivery/v1
python scripts/package-kaggle-source.py --config configs/kaggle.yaml --output artifacts/kaggle-delivery/v1
```

`kaggle_execution_verified` stays false until an actual Kaggle run.
