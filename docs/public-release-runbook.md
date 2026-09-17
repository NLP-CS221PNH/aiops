# Public release and history-rewrite runbook

Technical procedure only. It does not authorize a force-push by itself.

## Current history decision

`HIST-2026-09-16-NO-REWRITE`: do not rewrite public Git history. After untracking, forbidden blobs may still be reachable from old commits, tags, pull-request refs and forks. Do not claim that artifacts were revoked from every clone.

## Archive reconstruction

1. Read the acquisition manifest for the artifact class (`02_datasets/acquired/labels/acquisition-manifest.jsonl` for RCAEval; `03_collection_plan/knowledge-corpus*/source-manifest.jsonl` for knowledge sources).
2. Download the recorded URL at the recorded revision.
3. Verify byte size and SHA-256 before parse.
4. Place bytes in the original path, which is gitignored.
5. Run the heavy reproducibility workflow, not the PR workflow.

No GitHub Release or object-storage mirror is configured. If offline reproduction is required later, an owner must name the store, retention and grant scope first (`ARCH-2026-09-16-UPSTREAM-PIN`).

## PR versus heavy gates

- PR CI is offline with respect to raw Parquet and full text. It uses tracked public files plus synthetic fixtures, installs `pytest`, `pyyaml`, `numpy`, `pydantic` and `tokenizers==0.21.4` from PyPI, and must not download raw data or model weights.
- Heavy CI runs only on an approved private/self-hosted runner with pinned inputs in an ephemeral workspace. Do not upload raw/full text/private bytes to `actions/cache`, workflow artifacts or logs.

## Remote-surface inventory (owner-controlled)

Before any future purge, inventory and record:

- branches and tags
- pull-request refs
- GitHub Releases and assets
- Actions artifacts and caches
- GitHub Pages and Packages
- alternate remotes
- known forks/mirrors (notify only; cannot delete)

Public freeze checksums use LF-normalized SHA-256 for text files. The freeze TSV and receipt omit themselves from the path list so those hashes stay stable across regeneration.

## History rewrite protocol (do not run under --auto)

Required before a rewrite:

1. Written owner approval, scope, expiry and maintenance window.
2. Mirror backup under owner control.
3. Freeze pushes and notify collaborators to stop committing.
4. Exact path globs and object IDs.
5. `git filter-repo` in a disposable clone.
6. Verify forbidden objects are absent with `git rev-list --objects --all`.
7. Coordinated force-push.
8. Collaborators reclone; invalidate Releases, Pages, Packages and Actions caches in scope.
9. Fresh clone verification of CI, size and public-artifact scan.
10. Audit record of before/after counts, commit map, surface checklist and approvals.

Rollback is restore-from-mirror before pushes reopen. Third-party forks are out of scope.
