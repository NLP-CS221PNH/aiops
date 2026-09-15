# Local CPU environment and replay

Run commands from the research pack root. The data dependency is PyArrow only;
configuration files use the JSON-compatible subset of YAML and load with the
Python standard library. No model, API, tokenizer, GPU or notebook-server stack
is installed by this recipe.

The measured local environment is CPython 3.11.9 on Windows AMD64. A fresh venv
was created without system site packages. PyArrow 21.0.0 was installed offline
from the existing pip HTTP cache, after checking the wheel ZIP integrity and
its `cp311-cp311-win_amd64` tag. Its SHA256 is
`555ca6935b2cbca2c0e932bedd853e9bc523098c39636de9ad4693b5b1df86d6`.
The cache copy is `06_implementation/.wheelhouse/pyarrow-21.0.0-cp311-cp311-win_amd64.whl`.
The bootstrap distributions measured in this venv are pip 24.0 and setuptools
65.5.0; PyArrow is its only data runtime distribution. Generated `.venv` and
`.wheelhouse` directories are local tooling and must stay outside dataset archives.

To create another fresh local environment, use an unused destination; the
commands below neither delete nor overwrite the tested venv:

```powershell
python -c "import platform; assert platform.python_version() == '3.11.9'; print(platform.python_version())"
python -m venv 06_implementation/.venv-replay
./06_implementation/.venv-replay/Scripts/python.exe -m pip install --no-index --no-deps --require-hashes --find-links 06_implementation/.wheelhouse -r 06_implementation/configs/requirements-lock.txt
./06_implementation/.venv-replay/Scripts/python.exe -I -B 06_implementation/src/data/build_environment_report.py
```

To rerun using the environment already created for this implementation:

```powershell
./06_implementation/.venv/Scripts/python.exe -I -B 06_implementation/src/data/build_environment_report.py
```

Run source validation, export and private sidecar export as described in the
data handoff before this command. The environment command invokes the full
inference schema validator, then its management-only caller reads
`data/private/split-map.tsv` to choose the first two train IDs in lexical order.
The two IDs are written to `reports/environment-check.json`. The notebook gets
only those opaque IDs and the inference root; it never reads a private sidecar
or raw telemetry file.

The command executes the code cells from
`notebooks/00-environment-smoke.ipynb` twice, in two fresh isolated CPython `-I`
processes with distinct empty temporary working directories and an environment
containing only operating-system necessities. Each worker checks the five exact
manifest filenames, canonical paths, hashes, byte sizes, row counts, 90 unique
index/observation IDs and the presence of both selected incidents in every
derivative. Both runs must produce identical IDs, all file hashes, manifest hash
and the canonical selected-record hash. No Parquet raw traces are reopened.

This is direct execution of notebook code cells, not a Jupyter kernel run.
The receipt explicitly records that distinction. The notebook can also be
opened in an existing compatible notebook environment: supply `INFERENCE_ROOT`
and `SMOKE_IDS` from the receipt before running its code cell. Its saved outputs
and execution counts stay empty. Only aggregate counts, hashes and opaque IDs
are emitted during the automated replay; no telemetry payload is written into
the receipt or notebook.

The receipt measures OS, Python version, interpreter/extension ABI fields,
pointer width, isolated/venv settings, actual installed package versions, CPU
description/logical count and physical RAM. Available RAM and elapsed time are
time-dependent measurements, excluded from deterministic content comparison.
GPU is unused and unprobed; a null GPU field does not claim the machine lacks a
GPU. It records exact hashes of the manifest, runtime config, lock and notebook.
Any input change invalidates the previous receipt and requires a fresh replay.

`configs/runtime.yaml` keeps CPU, two incidents, two fresh runs, seed 221 and
API/network/GPU disabled. The content cache key uses manifest `source_hash`,
`transform_hash` and `config_hash`; verify every manifest file hash before reuse.
A cache with mismatched hashes must be rebuilt into a new validated derivative
version. Do not combine files from old and new manifests. Model/corpus cache
keys and execution belong to plans 05/07.

Kaggle is **deferred**, owner **C**. No upload, account/quota check, Linux
installation or Kaggle execution was performed. Sharing authorization remains
separate from this local gate. When that branch is authorized, C must create a
fresh Linux Python 3.11 environment, obtain a compatible Linux PyArrow 21.0.0
wheel, record its own hash and actual platform/package versions, and rerun the
same inference-only smoke. The Windows wheel and its hash lock cannot serve as
a Linux lock. GPU access is not a prerequisite for this data-only CPU check.

Human B/C independent runtime and payload review remains pending until those
people actually review the manifest named in the receipt. The automated local
gate does not imply a human signature or permission to share data or call APIs.
