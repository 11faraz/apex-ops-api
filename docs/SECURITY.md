# Security and configuration

## Secrets handling
- No secret is stored in the repository or the image. `.env` holds the `API_KEY`, is listed in `.gitignore` and `.dockerignore`, and only `.env.example` (placeholder value) is committed.
- The API key is read from the environment at run time and compared with `hmac.compare_digest`. It is never written to logs.
- CI generates a throwaway key for each run. Real deployments would use GitHub Actions secrets and, in the cloud, a secrets manager.
- If a key leaks: rotate it in `.env`, restart the service, and treat anything it protected as exposed.

## Least privilege
- The container runs as a non-root user (UID 10001).
- Root filesystem is read-only; only `/data` (volume) and `/tmp` (tmpfs) are writable.
- All Linux capabilities are dropped and `no-new-privileges` is set.
- The CI workflow has `contents: read` permission only.
- Only port 8000 is published.

## Dependency and image scanning
- `pip-audit` checks Python dependencies on every CI run.
- Trivy scans the built image and fails the build on fixable CRITICAL findings.
- Dependencies are pinned in `requirements.txt`. Next step: Dependabot for automatic update PRs and pinning the base image by digest.

## Cost-aware path to the cloud
1. **Start tiny:** one small VM (or a free-tier container service), the same Compose file, a daily snapshot of the data volume.
2. **Move the database** to a small managed PostgreSQL only when one instance is no longer enough or backups become a worry.
3. **Container registry:** GitHub Container Registry is free for this scale.
4. **Monitoring:** begin with logs and the alert rules in `OBSERVABILITY.md`; add a hosted Prometheus/Grafana free tier later.
5. **Guard the bill:** set a budget alert on day one, use a single region, scale down or stop non-production environments outside working hours.
