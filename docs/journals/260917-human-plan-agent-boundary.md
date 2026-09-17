---
title: Human remaining-work and AgentKit plan boundary
date: 2026-09-17
summary: Public remaining-work lives in 00_plan; AgentKit plans are gitignored except the G0 contracts snapshot.
---

# Human remaining-work and AgentKit plan boundary

Public Git now points humans at `00_plan/remaining-work.md`. Timestamped AgentKit plans stay on disk and are untracked. The only tracked `plans/` file is `plans/reports/260913-independent-plans-contracts.md`, because G0 hashes it. That snapshot contains a local workspace path, so the public-text scanner skips it rather than rewriting freeze bytes.

Ledger rule order: G0 snapshot `keep_public`, then `plans/**` `remove_public`. History was not rewritten. Headline IR stays `NOT_RUN` until human G2.

Verification: public-artifact `--tracked-only` pass; freeze `--check` pass; research-pack PR 58/58; pytest 363 passed.

> Historical work record — not durable authority. Prefer 00_plan/remaining-work.md for current leftover gates.
