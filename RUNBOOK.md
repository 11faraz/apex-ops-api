# Runbook

Everything below runs from the repository root. The service listens on `http://localhost:8000`.

## 1. Deploy

1. `cp .env.example .env` and set `API_KEY` (first time only).
2. `scripts/deploy.sh <version>` (for example `1.1.0`).
3. Confirm: `curl localhost:8000/version` shows the new version and `curl localhost:8000/ready` returns `ready`.
4. Run `scripts/smoke.sh`.

If the new version does not become ready within 45 seconds the script rolls back by itself and exits non-zero.

## 2. Roll back

Use this when a release passed the health check but behaves badly later.

1. `scripts/rollback.sh` (goes back to the version in `.release/previous`), or `scripts/rollback.sh 1.0.0` for a specific version.
2. Confirm with `curl localhost:8000/version` and `curl localhost:8000/ready`.
3. Data is untouched: the `ops-data` volume is not recreated. Check with `curl localhost:8000/operations`.

Rollback only works if the older image still exists locally (`docker images apex-ops-api`). Do not prune old tags until a release has proved stable.

## 3. Incident response

1. **Detect.** An alert fires, or `/ready` returns 503, or users report errors.
2. **Assess.** `docker compose ps` (is it up and healthy?), then `curl localhost:8000/ready` for the reason.
3. **Stabilise first.** If the problem started with a release, roll back (section 2) before investigating. Restoring service comes before finding root cause.
4. **Investigate.** Read logs (section 4), check metrics at `/metrics`.
5. **Communicate.** Say what is affected, what you did, and when the next update is.
6. **Follow up.** Write down the cause, the fix and one change that stops it recurring. `docs/FAILURE_INVESTIGATION.md` is an example.

## 4. Troubleshooting

| Symptom | Check | Likely cause and fix |
|---|---|---|
| `docker compose up` fails with "env file not found" | `ls .env` | Run `cp .env.example .env` |
| Container restarts repeatedly | `docker compose logs api --tail 50` | Read the last JSON log line for the error |
| `/ready` returns 503, `/health` is OK | Logs show `readiness failed` and a reason | Database path wrong or volume not writable; check `DB_PATH` and volume mount |
| `POST /operations` returns 401 | Header `X-API-Key` | Key must match `API_KEY` in `.env`; restart after changing it |
| `POST /operations` returns 503 "API key is not configured" | `.env` | `API_KEY` is empty |
| Port 8000 already in use | `docker ps`, `lsof -i :8000` | Stop the other process or change the port mapping |
| Deploy script says image does not exist | `docker images apex-ops-api` | Build the version first with `scripts/deploy.sh` |

Useful commands:

```bash
docker compose ps
docker compose logs -f api
docker compose logs api | grep '"level": "ERROR"'
docker exec apex-ops-api-1 id          # confirms the container user is not root
curl localhost:8000/metrics
```
