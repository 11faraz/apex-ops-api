# Failure investigation: service up but not ready

> Re-run these steps yourself and replace the output blocks with your own captures
> (save screenshots in `evidence/`). The commands and expected results are below.

## Reproduce
```bash
docker compose down
# Start the API with a database path that does not exist
docker compose run --rm -d -e DB_PATH=/nonexistent/ops.db -p 8000:8000 api
```
(Alternative that leaves the failure in place for you to investigate: `FAULT_INJECTION=not_ready docker compose up -d`.)

## Symptom
In another terminal:
```bash
curl -i localhost:8000/health   # 200 {"status":"ok"}        -> the process is alive
curl -i localhost:8000/ready    # 503 {"status":"not_ready","reason":"database unavailable"}
```
`docker compose ps` shows the container as `unhealthy` after a few checks.

## Investigation
1. Liveness is fine and readiness fails, so the app runs but cannot reach a dependency.
2. Logs: `docker compose logs api | grep ERROR` shows `database init failed` at startup and `readiness failed` with the reason "unable to open database file".
3. Metrics: `curl localhost:8000/metrics | grep 503` shows the 503 counter on `/ready` rising.
4. Configuration: `docker compose config | grep DB_PATH` shows the wrong path.

## Root cause
`DB_PATH` pointed to a directory that does not exist or is not writable, so SQLite could not open the file.

## Fix and prevention
- Correct `DB_PATH` to `/data/ops.db`, which is the mounted volume, and restart.
- Verify: `/ready` returns 200 and `/operations` still lists the earlier data.
- Prevention: the readiness check and the Compose healthcheck stop a bad release from being marked healthy, and `deploy.sh` rolls back automatically when readiness never passes.
