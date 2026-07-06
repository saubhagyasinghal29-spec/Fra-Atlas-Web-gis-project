# ADR 0003 — HMAC-chained immutable audit log

**Status:** Accepted

**Context.** Every data mutation in a welfare system affecting 100M+ people must
be forensically auditable and tamper-evident.

**Decision.** Each AuditLog row is HMAC-SHA512 signed over
`(previous_row_signature + canonical_content)`, forming a hash chain. Rows reject
updates/deletes at the application layer; production adds Postgres rules and a
non-empty `reason_text` CHECK. A daily Celery job recomputes the chain and flags
breaks.

**Consequences.** Altering any historical row invalidates every signature after
it, which `verify_chain()` detects. Signing key rotates quarterly; old keys are
retained to verify historical rows.
