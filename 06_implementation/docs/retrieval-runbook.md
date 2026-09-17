# Retrieval runners: build, verify, and hand off

The current delivery implements and tests the retrieval tooling. The user chose to wait for a reviewed corpus before running the real pilot. The existing corpus is a candidate with no released/indexable documents; production preflight must reject it before indexing. The full `05.runners` milestone remains pending until real pilot evidence and consumer acceptance exist. See the [execution contract](../reports/retrieval-goal-contract.md) and [Plan05 progress](../reports/plan05-progress.md).

No real BM25/dense/hybrid pilot rankings, retrieval-quality metrics, human judgments, final model selection, or test execution are established by synthetic fixtures. E5 and BGE neural inference remain unverified because their model weights and PyTorch/Transformers runtime have not been provisioned.

## Local environment

Run commands from `06_implementation` in PowerShell. The measured interpreter is `.venv/Scripts/python.exe`, CPython 3.11.9 on Windows AMD64. Retrieval tooling is isolated under `.retrieval-deps`; the real E5 Rust tokenizer is under `.corpus-deps`.

```powershell
Set-Location '\06_implementation'
$env:PYTHONPATH = '.retrieval-deps;.corpus-deps'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_retrieval*.py' -v
```

The [tooling lock](../configs/retrieval-requirements-lock.txt) and [dependency receipt](../reports/retrieval-dependency-provisioning.json) record actual wheel hashes and import evidence. If the isolated tooling directory must be rebuilt from the already provisioned wheelhouse:

```powershell
.\.venv\Scripts\python.exe -m pip install --no-index --no-deps --require-hashes --find-links .retrieval-wheelhouse --target .retrieval-deps -r configs/retrieval-requirements-lock.txt
```

The lock is for this Windows environment. A Kaggle/Linux environment needs a separately provisioned, pinned runtime and receipt. No Kaggle, GPU, PyTorch, Transformers, or model execution is claimed for this delivery; the adapters implement CPU float32 execution. `sentence-transformers` and a vector database are unnecessary for these adapters.

## CLI recipes

The CLI automatically includes `.retrieval-deps` and `.corpus-deps`; direct library/unit-test imports use the explicit `PYTHONPATH` shown above. Inspect current flags with:

```powershell
.\.venv\Scripts\python.exe -B -m src.retrieval --help
.\.venv\Scripts\python.exe -B -m src.retrieval run --help
```

Production preflight is read-only. It validates the configured corpus release/identity and reports model declaration state; it does not encode text, establish model availability, or validate the query/allowlist bundle. The current candidate corpus must return exit code 1 with `CORPUS_RELEASE_PENDING`:

```powershell
.\.venv\Scripts\python.exe -B -m src.retrieval preflight --config configs/retrieval.yaml --mode pilot
```

For a runnable synthetic BM25 example, generate a fresh fixture directory. The builder writes three invented chunks, two invented incident queries (one has no lexical match), and explicitly synthetic manifests; it does not materialize real telemetry.

```powershell
$retrievalFixture = '.test-work/retrieval/runbook-' + [guid]::NewGuid().ToString('N')
.\.venv\Scripts\python.exe -B tests/fixtures/retrieval/build_fixture.py --output $retrievalFixture
.\.venv\Scripts\python.exe -B -m src.retrieval preflight --mode fixture --config "$retrievalFixture/retrieval.json"
.\.venv\Scripts\python.exe -B -m src.retrieval index --mode fixture --methods bm25 --config "$retrievalFixture/retrieval.json"
.\.venv\Scripts\python.exe -B -m src.retrieval run --mode fixture --methods bm25 --config "$retrievalFixture/retrieval.json" --incident-list "$retrievalFixture/allowlist.json" --run-id smoke
.\.venv\Scripts\python.exe -B -m src.retrieval validate-run --manifest "$retrievalFixture/runs/fixture/smoke/run-manifest.json"
.\.venv\Scripts\python.exe -B -m src.retrieval run --mode fixture --methods bm25 --config "$retrievalFixture/retrieval.json" --incident-list "$retrievalFixture/allowlist.json" --run-id smoke --resume
```

The BM25 example should produce two complete records, including the empty ranking. `index` rebuilds the BM25 postings deterministically from canonical content; it does not persist a separate lexical index. Requesting `dense` or `hybrid` additionally prepares a fingerprinted embedding cache and requires the real pinned model.

To exercise honest missing-model records, reuse that fixture with a new run ID and `--methods bm25,dense,hybrid`. With this delivery's absent model assets, `run` returns exit code 1, `state: complete_with_errors`, two complete BM25 records, and four failed dense/hybrid records. `validate-run` can still return exit code 0 because it verifies a structurally valid report containing explicit failures. Always inspect `state`, `counts`, and each record's status rather than treating validation success as successful neural execution.

To exercise interruption, start another synthetic run with `--run-id interrupted --stop-after 1`. Exit code 1 and `state: interrupted` are expected. Repeat that exact run/config/allowlist with `--resume` and omit `--stop-after`. The existing complete record must be preserved and the pending record completed. `--stop-after` is permitted only in fixture mode.

Future real pilot execution uses `run --mode pilot`, a newly bound release/config, and a controller-supplied JSON allowlist. The allowlist requires exactly `schema_version: cs221-retrieval-allowlist-v1`, `mode: pilot`, `incident_ids`, and the current `query_manifest_hash`. Depth defaults to 50 and may be explicitly set from 1 through 50. Methods are comma-separated names from the table below. Changes to configuration/depth/methods/input identity require a distinct run ID; never relabel a fixture as pilot.

Future frozen execution uses `run --mode frozen` with `--f1`, `--trusted-f1-sha256`, `--test-input-manifest`, and `--trusted-test-input-sha256`, as well as its frozen config/allowlist. Plan08 must provide trusted digests independently of the input files. F1 binds the pre-test retrieval policy and code/environment/corpus/input/schema/tokenizer identities; a separate later receipt binds actual test inputs/query hashes to F1. Standalone `index` and `preflight` reject frozen mode because they do not accept the required run gates. This is an implemented handshake proposal, not evidence that owner08 has accepted it or that test execution occurred.

To reproduce the complete synthetic CLI/notebook delivery checks and refresh their receipt:

```powershell
.\.venv\Scripts\python.exe -B scripts/verify_retrieval_delivery.py
```

The script creates fresh synthetic inputs/run directories, checks the real corpus release gate without indexing it, and writes [retrieval-reproducibility.json](../reports/retrieval-reproducibility.json). It verifies expected failure exits as well as success exits. See the [pilot audit](../reports/retrieval-pilot-audit.md) for the explicit distinction between this technical evidence and the unperformed real pilot, and [test report](../reports/retrieval-tests.md) for the separate full regression command/results.

## Common inputs and methods

All branches receive the same stored chunk content: `section_heading + "\n" + text`. Only this content enters indexing/encoding. IDs, URLs, applicability, and source spans remain provenance. Queries contain only the upstream observation-derived `query_text`; no incident ID or manager metadata is added to it. The runner checks the shared query budget with the pinned real E5 tokenizer before executing any branch.

| CLI method / condition | Behavior |
|---|---|
| `bm25` / `IR-B` | k1=1.2, b=0.75; technical whole tokens plus components; sorted distinct query terms; zero overlap yields an empty list. |
| `dense` / `IR-D` | Local E5 masked mean pooling, normalized embeddings, exhaustive cosine search. Zero and negative similarities remain valid hits. |
| `hybrid` / `IR-H` | RRF over BM25 and dense ranks, constant 60, weights 1:1. Raw lexical/cosine scores are not added. |
| `rerank` / `IR-R` | Optional local BGE cross-encoder over the supplied hybrid top-50 or shorter; no candidate expansion. Final inclusion belongs to Plan08. |

Rankings use one-based sequential ranks and descending scores, with chunk ID as the deterministic tie breaker. Default retrieval depth is 50, annotation designation is top-10, and context normally requests at most five hits. Short/empty rankings retain their real counts; evidence is never padded.

The configuration is strict JSON using the `.yaml` filename as a YAML-compatible subset. Unknown fields, duplicate JSON keys, nonfinite values, mismatched IDs/hashes, and unapproved paths fail validation. The schema and code are the authoritative field lists: [input/config validation](../src/retrieval/inputs.py), [run schema](../schemas/retrieval-run.schema.json), and [consumer reader](../src/retrieval/consumer.py).

## Model provisioning boundary

Models are loaded from explicitly supplied local directories with `local_files_only=True` and `trust_remote_code=False`. The runner does not download weights or substitute a model alias when a pinned revision is missing.

| Adapter | Pinned model/revision | Budget |
|---|---|---|
| `E5Encoder` | `intfloat/e5-small-v2` at `ffb93f3bd4047442299a41ebb6fa998a38507c52` | 512 tokens including `query: ` / `passage: ` and special tokens. |
| `BGEReranker` | `BAAI/bge-reranker-base` at `2cfc18c9415c912f9d8155881c133215df768a70` | 512 total query+passage+special tokens, using `longest_first` pair truncation. |

The E5 recipe follows the [official E5 model card](https://huggingface.co/intfloat/e5-small-v2); BGE scores are raw relevance logits according to the [official BGE reranker instructions](https://huggingface.co/BAAI/bge-reranker-base#usage-for-reranker). The revision constants are fixed by this research pack's proposal; they are not a claim of a selected winning configuration.

Before a future neural run, B/C must provision the pinned model/tokenizer files and a tested, pinned PyTorch/Transformers environment. The asset map must contain SHA256 values for `config.json`, `tokenizer_config.json`, `tokenizer.json`, and `model.safetensors` or `pytorch_model.bin`; every additional loader-relevant tokenizer/weight file present must also be tracked. The adapter verifies the bytes before loading. Missing assets/runtime raise `ModelUnavailableError`; hash or policy mismatch raises `ValueError`. A missing dense prerequisite produces explicit failed dense/hybrid records, never BM25 results relabeled as dense.

Token audits report actual before/after counts, removed tokens, prefixes/specials, and model token-ID hashes. E5 rejects complete removal of the body after its prefix. BGE audits both query and passage and rejects either side becoming empty. Tests using a real E5 tokenizer for generic pair budgeting establish the adapter accounting contract; they do not verify absent BGE tokenizer/model execution.

## Provenance, cache, and resume

Every run binds the canonical configuration, implementation file hashes, runtime versions, corpus and query manifests, incident allowlist, exact query/content identities, task/window policy, representation, and requested conditions. The ranking's `task_version` is the configured retrieval task policy; `window_hash` is the canonical hash of the upstream window object. Neither is fabricated as an existing upstream field.

Dense cache keys include the ordered chunk registry/content hashes, content policy, model/tokenizer assets/revisions, prefixes, token budget, normalization, implementation, and environment. Cached vector row IDs and dimensions are checked on load. A key mismatch requires a separate entry; a conflicting payload under the same key is rejected. Shared cache publication also uses an exclusive lock per key (`lock-<key>/.writer.lock`), so separate runs cannot concurrently overwrite an immutable entry. Actual E5 embedding-cache warm/cold performance has not been measured.

Each run has its own directory, atomic record files, a checksum-indexed checkpoint file, and a manifest covering every expected incident/condition. Each attempt's immutable filename binds the record key and complete content digest. A retry writes a new attempt before atomically switching the checkpoint index; if it dies before that switch, the previous committed failed attempt stays readable and retryable. Resume requires the same fingerprint and verifies all committed records before model/index work. Complete records are reused; failed or missing records can be retried. Changing configuration, content, implementation, environment, or input identity requires a new run. Stage times are measured with `perf_counter`; dependent conditions may reuse stage costs, so do not sum times across conditions. Synthetic timings do not estimate real pilot performance.

An exclusive `.writer.lock` prevents concurrent writes. A killed process may leave a stale lock. Verify that its recorded process is no longer an active writer, retain the affected directory for inspection, and remove only that confirmed stale lock before retrying resume. Never delete another writer's lock or rewrite checksums to make a corrupted run validate. A record written before an interrupted index update is uncommitted and may be recomputed.

## Consumers and deferred gates

Plan06 pools rankings/provenance and owns union, blinding, and judgments. Plan07 obtains bounded hits and resolves the unchanged upstream citation registry. Plan08 owns dev selection, F1, frozen test inputs, optional reranker inclusion, and evaluation.

`read_run()` validates manifest/schema identity, checkpoint and record checksums, completeness, IDs, ranks, finite scores, content hashes, counts, and query/corpus/config provenance. `read_hits(..., limit=5)` reports status and available count, including failed/short records. Consumers should supply the expected manifest hash and expected provenance obtained from their trusted handoff; checksums alone cannot authenticate an entirely replaced bundle. `comparable_runs()` rejects incompatible corpus, query, representation, task, window, registry, or mode identities.

Actual pilot prerequisites remain: A/B release a reviewed corpus with a nonempty eligible whitelist; B/C provision and measure the pinned neural runtime; controller/06 supplies opaque train/dev incident allowlists bound to the current query manifest; A/B/C and 06/07/08 provide their own acceptance. The runtime never reads private split maps, gold, qrels, or annotations. Frozen mode separately requires authenticated F1 and post-F1 test-input receipt hashes from Plan08, with actual query hashes checked after materialization. These owner approvals cannot be manufactured by editing a candidate manifest.

The earlier 20-incident/400-candidate BM25 output remains an unjudged source-era seed. It cannot discharge new corpus/representation pilot requirements. Source-era `NOT_RUN` results, upstream release flags, and human review fields must remain truthful.
