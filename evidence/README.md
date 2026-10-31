# Evidence checklist

Capture these yourself from your own runs and save them in this folder. The assessment penalises claims without evidence, so only keep what you actually ran.

| # | What to capture | Command or place | File name suggestion |
|---|---|---|---|
| 1 | Tests passing locally | `make test` | `01-tests-pass.png` |
| 2 | Stack running and healthy | `docker compose up -d --build` then `docker compose ps` | `02-compose-ps.png` |
| 3 | Non-root user | `docker exec apex-ops-api-1 id` (should show uid 10001) | `03-nonroot.png` |
| 4 | Health, ready, smoke test | `scripts/smoke.sh` | `04-smoke.png` |
| 5 | Persistence | create an operation, `docker compose down`, `docker compose up -d`, list again | `05-persistence.png` |
| 6 | Green CI run | GitHub > Actions > CI (all three jobs green) | `06-ci-green.png` |
| 7 | Red CI run that blocks the release | Run workflow with `demo_fail` ticked; build and deploy are skipped | `07-ci-red-blocked.png` |
| 8 | Release 1.0.0 then 1.1.0 | `scripts/deploy.sh 1.0.0`, `scripts/deploy.sh 1.1.0`, `curl localhost:8000/version` | `08-releases.png` |
| 9 | Bad release rolls back automatically | `FAULT_INJECTION=not_ready scripts/deploy.sh 1.2.0` | `09-auto-rollback.png` |
| 10 | Manual rollback | `scripts/rollback.sh` then `curl localhost:8000/version` | `10-manual-rollback.png` |
| 11 | Structured logs | `docker compose logs api --tail 20` | `11-logs.png` |
| 12 | Failure investigation | steps in `docs/FAILURE_INVESTIGATION.md` | `12-investigation.png` |
| 13 | Image scan result | the Trivy step in the CI run | `13-trivy.png` |
