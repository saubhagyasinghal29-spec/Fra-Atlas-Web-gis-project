# Data Protection Impact Assessment (DPIA) — FRA Atlas

**Regime:** Digital Personal Data Protection Act, 2023 (India). GDPR treated as analogue.

## Personal data processed
| Data | Sensitivity | Basis | Control |
|---|---|---|---|
| Officer account (name, email, phone) | Personal | Employment/role | Phone & MFA secret encrypted at rest (versioned Fernet); RBAC; audit. |
| Tribal claimant / community references | Personal, vulnerable group | Statutory welfare administration | Access scoped by jurisdiction; soft-delete; audit chain. |
| Claim records (area, status, geography) | Personal + locational | Statutory record-keeping | Immutable audit trail; retained per statute. |

## Data-subject rights (implemented)
- **Access / portability:** `GET /api/v1/privacy/my-data/` exports the subject's data.
- **Erasure:** `POST /api/v1/privacy/erase/` crypto-erases account PII (overwrites encrypted fields, pseudonymizes username, deactivates) and records the *event* in the audit log. Claim records are **retained** under the statutory record-keeping carve-out; the personal link is pseudonymized.

## Erasure vs. immutable audit — resolution
The audit chain stores **event metadata, never PII content**. Erasure destroys PII plaintext (encrypted columns overwritten) and pseudonymizes identifiers, while the tamper-evident chain remains intact. This satisfies the right to erasure without weakening auditability.

## Retention
`RETENTION_YEARS` (default 7) governs hard-deletion of soft-deleted, non-audit records via the annual `enforce_retention` job. The audit log is never purged.

## Residual risks / actions
- Re-identification via claim geography — mitigate with aggregation thresholds before any public disclosure.
- Cross-border transfer / data localisation — host in an Indian government cloud (deployment-time control).
- A full legal review and Data Protection Officer sign-off are required before production processing of real citizen data.
