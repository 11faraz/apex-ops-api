# Decision memo

## Assumptions
- This is a local, reproducible demonstration. No paid cloud and no real data are used.
- One host is enough; high availability is out of scope for 48 hours.

## Decisions and trade-offs

| Decision | Why | Trade-off / what I would change |
|---|---|---|
| Flask + gunicorn | Small, well understood, easy to read in a review | Not async; fine for this load |
| SQLite on a named volume | Zero extra services, persistent, fully reproducible | Single writer, single instance. For real use I would move to PostgreSQL as a second Compose service, then a managed database |
| One gunicorn worker, four threads | Keeps in-process metrics counters correct | Less CPU parallelism. With more workers I would use a metrics library with multiprocess support |
| Separate `/health` and `/ready` | Restart on dead process, stop traffic on broken dependency | Readiness touches the database, so a slow database can flap readiness |
| Image tag = version, never `latest` | You can say exactly what runs and roll back with one command | Needs a registry in real use; locally images live on the host |
| Compose healthcheck uses `/ready` | Deploy script and Compose agree on what "healthy" means | |
| Rollback by redeploying the previous tag | Simple, fast, data volume untouched | Does not handle database schema changes; those would need backward-compatible migrations |
| Non-root user, read-only filesystem, all capabilities dropped | Limits damage if the app is compromised | Writes only work in `/data` and `/tmp` |
| CI stages: test, then build and scan, then deploy | Cheapest checks first; a failing test stops everything | Trivy scan adds time; set to CRITICAL only so one noisy base-image CVE does not block every build |
| `FAULT_INJECTION` demo flag | Lets me prove automatic rollback on demand | A debug switch in the code; off by default and documented. I would remove it from a production build |
| API key header for writes | Shows secret handling without building a user system | Shared key, no per-user audit. Real use would need proper auth |

## What I would do with more time
1. Add PostgreSQL and a migration tool.
2. Push images to a registry (GitHub Container Registry) with signed tags.
3. Run Prometheus and Grafana in Compose with the alert rules from `OBSERVABILITY.md`.
4. Add integration tests that run against the Compose stack in CI.
5. Pin the base image by digest and enable Dependabot.
