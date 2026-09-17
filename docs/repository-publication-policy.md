# Repository publication policy

This policy is a technical publication boundary. It is not a legal opinion.

## Decisions recorded 2026-09-16

| Decision | Value | ID |
|---|---|---|
| Archive target | Pinned upstream re-acquisition from recorded URL + exact git/HF/Zenodo revision + SHA-256. No GitHub Release or object-storage mirror until an owner names one. | `ARCH-2026-09-16-UPSTREAM-PIN` |
| Retention | Keep local copies that Git no longer tracks; reconstruct from upstream when the local copy is absent. | `ARCH-2026-09-16-UPSTREAM-PIN` |
| History rewrite | **No rewrite.** Untracking removes bytes from the current tip only. Historical blobs remain reachable. A coordinated `git filter-repo` force-push requires a later owner approval and the runbook in `docs/public-release-runbook.md`. `--auto` must not execute a rewrite. | `HIST-2026-09-16-NO-REWRITE` |
| Approver for project-owned Software | `repository-policy` under root `LICENSE` (MIT). | `PUB-2026-09-16-OWNED-WORK` |
| Third-party bytes | Fail-closed. A public URL, a `license_data: MIT` label, or the root MIT license does not approve redistribution. | `PUB-2026-09-16-DEFAULT-DENY` |

## Independent axes

Rights, sensitivity and disposition are independent:

- Rights: `approved`, `internal_only`, `unknown`, `conflict`, `prohibited`. Only `approved` may appear on the public allowlist.
- Sensitivity: `none`, `public_metadata_approved`, `redacted_approved`, `sensitive_internal`, `unknown`. Only the first three may be public, with a matching approval.
- Disposition: `keep_public`, `generate`, `archive_private`, `remove_public`. `archive_private` never implies public bytes.

## Public allowlist rule

A tracked path is public only when the ledger row has all of:

1. `redistribution_status=approved`
2. `sensitive_data_status` in `none | public_metadata_approved | redacted_approved`
3. `disposition=keep_public`
4. empty or unexpired `expiry`
5. file size ≤ 5 MiB, or an explicit `size_exception_mib` with owner, approver, decision id and expiry

Machine source of truth: `04_audit/public-artifact-ledger.tsv`. Validator: `python scripts/validate-public-artifacts.py --ledger 04_audit/public-artifact-ledger.tsv --tracked-only`.

## Default groups

| Group | Status | Disposition |
|---|---|---|
| Project code, schemas, hand-authored docs | approved | keep_public |
| Paper descriptive metadata and reading notes | approved / public_metadata_approved | keep_public |
| De-identified processed extracts and the canonical `data/inference` bundle | approved / redacted_approved | keep_public |
| E5 tokenizer/config/vocab (not weights) | approved | keep_public |
| Attributed knowledge manifests and processed chunks | approved | keep_public |
| Raw RCAEval Parquet | internal_only / sensitive_internal | archive_private |
| Paper cache, primary text, source PDFs | internal_only | remove_public |
| Gold labels and `data/private` | internal_only / sensitive_internal | remove_public |
| Candidate inference copies, imputed working copy | internal_only | remove_public |
| Knowledge `source-snapshots/` source bytes | internal_only | archive_private |
| Knowledge snapshot `LICENSE` files | approved | keep_public (`PUB-2026-09-16-LICENSE-EVIDENCE`) |
| Generated HTML/PDF/submission copies | internal_only | generate |
| AgentKit `plans/` overlays | internal_only | remove_public |
| G0 contracts snapshot `plans/reports/260913-independent-plans-contracts.md` | approved | keep_public (`PUB-2026-09-17-G0-CONTRACT-SNAPSHOT`) |

The public-text scanner skips `06_implementation/freezes/G0/` and the G0 contracts snapshot. Those freeze bytes may contain historical local paths; do not rewrite them to pass the scanner.

## Gold / labels

`02_datasets/processed/labels/` and `06_implementation/data/private/` stay evaluator-only. They must never be retrieval/index input. A later public release needs a separate release-stage approval.

## Exceptions

Every size, path or rights exception needs scope, artifact owner, approver, decision/ticket id and expiry. Expired exceptions fail validation. Exceptions are not a permanent bypass.

## Validation receipts

`check` / `validate` / `verify` commands are read-only. They must not refresh receipts, manifests or working-tree files. Write/build commands are separate and promote from clean staging only after checks pass.

Public freeze checksums (`04_audit/public-tracked-manifest.tsv`) and release `CHECKSUMS_SHA256.txt` use LF-normalized SHA-256 for text files (no NUL in the first 8 KiB). That lock is internal to this repository's validators; `sha256sum` on a CRLF working copy can differ. Freeze artifacts omit themselves from the path list so the freeze hash stays stable.
