# ADR 0002 — SpatiaLite in dev, PostGIS in prod

**Status:** Accepted

**Context.** The spec mandates PostGIS spatial queries with a <200ms SLA. We
also want the project to clone-and-run without provisioning Postgres.

**Decision.** Use GeoDjango with the SpatiaLite backend for local dev/test and
PostGIS in production. GeoDjango abstracts the backend, so model fields and
spatial lookups (`__contains`, `Distance`, `__dwithin`) are identical; switching
is a `DATABASES` engine change.

**Consequences.** Spatial code is verified on SpatiaLite (point-in-polygon
~0.9ms on 500 districts) and ports unchanged to PostGIS. District boundaries in
the seed data are synthetic (placed near real state centroids); production
ingests real shapefiles with no query-code change.
