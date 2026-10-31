# Interview cheat sheet (do not submit this file; keep it for yourself)

## Your 5-minute walkthrough
1. **The goal (20 s):** "I packaged a small operations API so it can go from commit to release safely, and I can show it running, failing and rolling back."
2. **Architecture (40 s):** Flask API in a non-root container, SQLite on a volume, Compose for local deploy, GitHub Actions for CI.
3. **Live demo (3 min):** `docker compose up`, `scripts/smoke.sh`, deploy 1.1.0, show `/version`, deploy a bad release and watch it roll back.
4. **CI (40 s):** show a green run and the red run where the build is skipped.
5. **Close (20 s):** "With more time I would add PostgreSQL, a registry, and Prometheus with the alert rules I proposed."

## Questions you will probably get, in plain words
- **Why non-root?** If the app is compromised, the attacker is not root inside the container.
- **Health vs ready?** Health: is the process alive. Ready: can it do real work, meaning the database answers.
- **Why not `latest`?** It changes without warning, so you can't say what is running or go back to a known version.
- **How does rollback work?** The previous version's image is still on the host. `rollback.sh` starts it, waits for `/ready`, checks `/version`, and leaves the data volume untouched.
- **What stops a broken build from deploying?** The `build` job `needs: test`, and `deploy-local` `needs: build`. If tests fail, the later jobs never start.
- **Where are the secrets?** In `.env` (git-ignored) locally, and generated per run in CI. Never in the repo, image or logs.
- **Why SQLite?** It keeps the demo reproducible with no extra services. The trade-off is one instance; the next step is PostgreSQL.
- **Why one gunicorn worker?** Metrics counters live in memory, so more workers would split the counts.
- **What does `FAULT_INJECTION` do?** A demo-only switch that makes readiness fail so I can prove automatic rollback. It is off by default and I would remove it in production.
- **What if a release changes the database schema?** Rollback gets harder. I'd use backward-compatible migrations (add before remove).
- **What would you monitor first?** Error rate, latency, restarts, disk on the data volume.
- **Cost-aware cloud path?** One small VM or free-tier container service, same Compose file, backups of the volume, budget alert from day one.

## If you are asked to troubleshoot live
Say what you expect, then: `docker compose ps` -> `docker compose logs api --tail 50` -> `curl /ready` -> check config -> change one thing at a time. Think out loud.

## If you don't know something
"I haven't used that yet. Here is how I'd work it out..." is a good answer. Bluffing is the only bad one.

## AI disclosure answer (be truthful)
"I used an AI assistant to draft the first version of the code and docs. I then ran everything myself, captured the evidence from my own runs, and I'm happy to walk through any file." Only say this if it matches what you actually did, and make sure it does by reading every file once.
