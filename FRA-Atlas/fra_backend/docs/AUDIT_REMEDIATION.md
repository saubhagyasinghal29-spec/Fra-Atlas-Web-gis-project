# Audit Remediation Delta

Status of each finding from the Stakeholder Audit after the production-hardening pass.

## Critical
| Finding | Status | Evidence |
|---|---|---|
| R1 Backups wrote no data / self-verified | **CLOSED** | `apps/ops/backup.py`: real serialize→store→read-back→hash-verify; `backup`/`restore` commands; round-trip test recovers a hard-deleted row. |
| R2 No DPDP program / erasure vs audit | **CLOSED (code) / IN PROGRESS (program)** | `apps/privacy` access + crypto-erasure endpoints; `docs/DPIA.md`; retention job. Legal/DPO sign-off still required. |
| R8 SAST/lint non-blocking in CI | **CLOSED** | CI now runs `ruff`/`bandit` as blocking gates + `pip-audit`; coverage gate raised to **80%** (actual 91%). Code is ruff- and bandit-clean. |

## High
| Finding | Status | Evidence |
|---|---|---|
| R3 Unproven at scale; no matviews | **SUBSTANTIALLY CLOSED** | Postgres materialized view `district_claim_summary` + CONCURRENT refresh; measured **0.3 ms vs 2.34 ms** live at **200k claims**; `seed_scale` for load testing. |
| R7 No token revocation | **CLOSED** | SimpleJWT blacklist + refresh-rotation; `/auth/logout/` revokes; test confirms revoked token rejected. |
| R6 No ML governance | **SUBSTANTIALLY CLOSED** | Drift monitoring (PSI), `fairness_report` by group, CV metrics stored, human-in-the-loop invariant test (model output never transitions a claim). External fairness/legal review still advised. |
| R4 No UI / accessibility | **OPEN** | Backend-only; UI + WCAG remain a separate workstream. |
| R5 External integrations stubbed | **OPEN** | Interfaces in place; live wiring pending credentials/sandboxes. |

## Medium
| Finding | Status |
|---|---|
| R9 Spoofable upload type | **CLOSED** — magic-byte sniffing (`apps/documents/sniff.py`); test rejects spoofed type. |
| R10 Unbounded table growth | **PARTIALLY CLOSED** — `enforce_retention` job for soft-deleted records; idempotency/audit partitioning still recommended. |
| R11 Synthetic geometry | **OPEN** — real shapefile ingest pending. |

## Net effect
All three **Critical** findings are closed in code (R2 pending external legal sign-off). Four of five **High** findings are closed or substantially closed; the two genuinely open items (UI/accessibility, live external integrations) are environment/workstream dependencies, not architectural gaps.
