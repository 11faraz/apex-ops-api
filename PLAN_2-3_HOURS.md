# Finish-in-3-hours plan

| Time | Do this | Done when |
|---|---|---|
| 0:00-0:15 | Unzip, `git init`, create a GitHub repo, `make setup`, `make test` | 11 tests pass |
| 0:15-0:45 | `docker compose up -d --build`, `scripts/smoke.sh`, check `id` in the container, restart to prove persistence | Evidence 2-5 captured |
| 0:45-1:15 | Push to `main`; wait for green CI. Then run the workflow with `demo_fail` ticked | Evidence 6, 7, 13 captured |
| 1:15-1:50 | `scripts/deploy.sh 1.0.0`, then `1.1.0`, then the `FAULT_INJECTION=not_ready` deploy, then `scripts/rollback.sh` | Evidence 8-10 captured |
| 1:50-2:20 | Follow `docs/FAILURE_INVESTIGATION.md`; capture logs | Evidence 11, 12 captured |
| 2:20-2:45 | Fix anything that broke; edit `docs/AI_DISCLOSURE.md` honestly; delete files you don't want to submit (this plan, the cheat sheet) | Docs match what you ran |
| 2:45-3:00 | Fresh clone, follow README once, zip, submit | Checklist in the assessment ticked |

If something breaks, fix it before adding anything new. A smaller solution that runs beats a bigger one that doesn't.
