# ADR 0001 — Django over Flask

**Status:** Accepted

**Context.** The system needs an ORM with migrations, a battle-tested auth/RBAC
layer, an admin, GeoDjango spatial support, and DRF for a large versioned API —
all for a government welfare system that must be maintainable across staff
turnover.

**Decision.** Use Django + Django REST Framework. GeoDjango gives first-class
PostGIS support; DRF gives serializers, throttling, and OpenAPI; Django's auth
and migrations reduce bespoke code in a system that values auditability over
novelty.

**Consequences.** Heavier than Flask, but the batteries-included surface (admin,
migrations, GIS, auth) directly maps to the spec's requirements. Async compute
is offloaded to Celery rather than Django's request cycle.
