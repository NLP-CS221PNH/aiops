# Kaggle / local Qwen runbook

Timezone: Asia/Saigon. Do not upload this package from the agent session.

## Roots

Notebook setup writes `configs/kaggle.resolved.json` from selected roots:

- `source_root`, `inference_root`, `private_train_root`, `private_dev_root`
- `private_test_root` is evaluation-only and must stay unmounted for `python -m src.training train`
- `knowledge_root`, `qwen_assets`, `e5_assets`, `output_root`

Local Windows resolves under `artifacts/kaggle-delivery/v1`, not `/kaggle`.

## Cells (Run All default)

1. Scope/status
2. Config roots
3. Setup assets/deps
4. Data/schema/hash preflight (`python -m src.training preflight --data-only` after phase 3)
5. GPU/runtime receipt (`scripts/kaggle_gpu_runner.py`)
6. Two-step smoke only when assets exist
7. Full train cell **disabled**
8. Resume/export/reload
9. Optional corpus/eval after freeze
10. User-triggered download

Missing assets must fail with the pin, file, and config key. `kaggle_execution_verified` is true only after an actual Kaggle run. `linux_install_verified` is true only after a Linux pip-check.

## Pins

- Qwen2.5-1.5B-Instruct `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
- E5-small-v2 `ffb93f3bd4047442299a41ebb6fa998a38507c52` (pretrained, not trained)
- Candidate extra Python: `configs/kaggle-requirements.in` (not a Linux hash lock)
