# Plan 05 independent technical code review

**Decision: PASS for the user-authorized build/test tooling slice. Score: 9.3/10. Open material findings: 0.** This is an automated Codex review by `/root/audit_inputs`, dated 2026-09-13. It does not accept the full `05.runners` milestone, approve a real pilot, or supply human A/B/C signatures.

The reviewed stop condition is the user's clarification: **build and test runners now; wait for a reviewed corpus before the pilot**. The complete Plan05 pilot and consumer acceptance remain pending. The current 440-chunk corpus has zero released/indexable chunks and is rejected before indexing.

## Scope and acceptance

Reviewed `src/retrieval/{common,inputs,bm25,dense,fusion,rerank,cache,runner,consumer,__main__,__init__}.py`, the retrieval config and run schema, independent fixtures/tests, verification script, notebook wrapper and runbook. The implementation follows the repository's local Python/JSON configuration conventions and introduces no changes to the existing upstream data/corpus/representation APIs.

| Acceptance area | Review result |
|---|---|
| Safe input contract | Strict config/schema parsing, exact manifest and text hashes, explicit opaque allowlists, duplicate/private-field rejection, path restrictions and local-only schema references. No retrieval import or call reads a private split map, labels, qrels or evaluator. |
| Release and test boundaries | Current candidate fails before chunk reads/index work. Both CLI indexing and running enforce the same released-corpus/tokenizer policy. Frozen mode requires independently supplied F1 and later test-input digests, current code/environment/config/input/schema/tokenizer bindings, and actual query hashes. |
| Scoring | BM25 matches independently calculated scores and technical-token behavior; query terms are sorted for reproducibility. Exact cosine search validates matrices and uses stable ties. RRF combines reciprocal ranks, handles absent branch candidates, rejects duplicates and never adds incompatible raw scores. |
| Model and token budgets | Local-only pinned model adapters, explicit missing-model behavior, real E5-tokenizer budget tests, complete-body removal guards, and pair/candidate guards. All branches receive the same unchanged query text. Neural E5/BGE execution is explicitly unperformed. |
| Cache and checkpoint integrity | Fingerprints bind ordered content, configuration, assets, implementation and runtime. Shared-key publication is locked. Record attempts have immutable content-derived filenames; a failed retry interrupted before index commit retains the previous committed record. Resume checks committed bytes and fingerprint. |
| Complete outputs and readers | Every requested incident/condition has complete, failed or pending state. Reader verifies schema, hashes, record population, IDs, document/content provenance, ranks/ties, depth, counts and error/empty/short semantics. Failed or empty results are not padded. |
| CLI, notebook and documentation | Reproducible synthetic recipes use the same CLI; current candidate and missing-F1 commands fail as intended. Documentation distinguishes structural validation from successful neural execution and identifies owner03/08 handshakes as proposed interfaces awaiting acceptance. |
| Side effects and existing workflows | All 225 upstream file hashes checked against existing corpus/query manifests matched. Full regression testing passed. Only new retrieval implementation/tooling/artifacts were added; upstream source contracts, release flags and tests were not rewritten to obtain a pass. |

## Verified evidence

- The independent tester passed **66 retrieval tests** and **269 full-suite tests**, with zero failures, errors or skips. The full suite includes the retrieval tests; these are not 335 distinct tests. [Test receipt](retrieval-tests.json) retains all 269 outcomes and unchanged before/after source/config/schema/test hashes.
- Independently verified all **28 artifact hashes**, all **11 current implementation hashes**, and all **15 expected command exit codes** in the [reproducibility receipt](retrieval-reproducibility.json).
- Re-read all four archived synthetic run manifests through `read_run` using the trusted receipt hashes. Fresh, repeat and resumed BM25 runs each contain two complete records. The missing-model run contains two complete BM25 records and four explicitly failed dense/hybrid records; every manifest is labeled synthetic.
- Independently reproduced and then verified fixes for concurrent cache publication, interrupted failed-record retry, and external schema references. The final seven targeted assertions pass in [independent review checks](retrieval-independent-review-checks.json), without model inference or actual corpus indexing.
- Reviewed notebook code-cell execution and the verification script. The notebook retains empty saved outputs and calls the same CLI. Synthetic stage timings are measured execution evidence, not estimates of real pilot throughput or quality.

No separate lint, type-check or application build pipeline is configured for this Python research package. Module import/discovery, CLI execution, schema validation and the full test suite provide the applicable syntax/runtime checks. No missing neural backend is misrepresented as a successfully tested model.

## Findings resolved during review

The implementation was corrected before this acceptance to:

1. Separate F1's pre-test policy from the later immutable test-input receipt, without requiring post-F1 query hashes inside F1 itself.
2. Check current retrieval code, environment, safe export, schema and tokenizer identities against F1, so a stale freeze cannot authorize changed dependencies.
3. Align the recorded BM25 tokenizer version with its implementation and bind active/query/corpus E5 tokenizer identities.
4. Apply the same real-corpus tokenizer gate to both `index` and `run` entry points.
5. Reject external `$ref` and `$dynamicRef` resolution before JSON Schema validation can retrieve files or network resources.
6. Serialize shared cache publication so two run directories cannot overwrite the same immutable cache key.
7. Preserve committed failed attempts when a retry is interrupted between record creation and checkpoint-index publication.
8. Check the actual cached vector dimension against the encoder dimension before query encoding.
9. Preserve the original prerequisite failure category in per-condition records instead of labeling every cache/computation failure as a missing model.
10. Define a strict run specification schema and validate immutable record content identities in both checkpoint and consumer readers.

These were defects in the newly developed retrieval slice, not changes to existing upstream business behavior. The final tests retain and exercise the relevant guards; no test was weakened or skipped to obtain acceptance.

## Explicitly deferred acceptance

No real incident BM25/dense/hybrid pilot, E5/BGE model inference, BGE-tokenizer run, quality metric, human qrel, winning representation, frozen test execution or full `05.runners` acceptance is claimed. Exact-search tests use labeled synthetic vectors; generic pair accounting uses the real E5 BERT tokenizer and is not evidence of the unavailable BGE tokenizer/model.

Owner A/B must supply a reviewed corpus release and authentic acceptance evidence. The future released-manifest status/field handshake is a proposal for owner03, not an artifact already supplied by its current candidate builder. Owner B/C must provision and validate pinned neural assets/runtime; controller/06 supplies train/dev allowlists; 06/07/08 must confirm their actual handoff. Owner08 independently authenticates its F1 and post-F1 input receipt. Checksums establish consistency, so consumers must supply expected hashes/provenance from their trusted handoff rather than treating a self-consistent replaced bundle as authenticated.
