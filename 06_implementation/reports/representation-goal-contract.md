# Plan 04 execution contract

User request: execute the accepted incident-representation plan with
`/goal`, `ak:codex-goal`, `ak:cook` and `--auto`.

Outcome: complete milestone `04.variants`: 72 train/dev incidents, three
representations each, shared R1/R2 evidence selection after real token budgeting,
auditable selection/provenance, one common generation bundle per incident,
reproducible manifests, tests, review receipt and downstream handoff.

Read first: the plan and all three phases; safe-export data handoff and exact
manifest; protocol/shared contracts; existing Python data/corpus validators and
pinned tokenizer implementation. This repository is a Python research pack with
JSON-as-YAML configurations, standard-library unittest checks, local PyArrow
data environment and vendored tokenizer assets. There is no Git repository or
application server/build toolchain. No existing public API is changed.

Constraints: runtime sees only safe export schemas and opaque IDs; manager
split selection remains separate. Preserve source windows, unknown units/status
semantics, literals and original files. Use whole evidence blocks, exact token
counts and stable serialization. Do not weaken, narrow, skip or delete tests to
satisfy the goal. Record evidence for every acceptance criterion.

Non-goals: new raw telemetry export, model calls, external data transfer,
retrieval/ranking runs, qrels, causal labels, dev winner selection, F1/F2 and test
query materialization. Bundles use a named candidate planning tokenizer until
plan 07 supplies its actual generator tokenizer.

The explicit `--auto` authorizes independent automated local review of the
technical milestone. It does not claim A/B/C human signatures or alter plan
02's administrative state. The safe candidate's local technical gate is checked
for this use. The exact authorization and upstream pending status are recorded
in [representation-execution-authorization.json](../configs/representation-execution-authorization.json).

Checkpoints: six-train source/specification audit; pure renderer and real-token
smoke; train/dev materialization; independent tester/debugger/reviewer evidence;
complete phase sync, journal and hash-bound handoff. Validate with the CLI's
`validate` command (with final receipt), representation contract tests, and
existing data/corpus/protocol test suites using their compatible local runtimes.

Stop when all local milestone artifacts, invariants, independent review and
validation pass, the receipt binds the current bytes, and plan status reflects
that evidence. Record downstream human review, actual generator budget and dev
selection as future owner work rather than pretending those events happened.
