# AGENTS.md

## Project

**wp-cron-scheduler** — a Docker-based solution that spreads out WordPress cron (`wp-cron.php`) executions over time. Instead of a fixed crontab, a Python scheduler container applies a per-site interval plus smart jitter. Configuration is a single JSON file.

## Language convention

- The repo is public and meant for a worldwide audience: everything (code comments, log messages, README, config examples) is written in **English**. Keep it that way when modifying code.
- Code identifiers and config keys use English.

## Architecture

Single-file Python app (`cron_scheduler.py`) with three parts:

1. **Health server** — `HTTPServer` on port `8080`, serves `GET /health` → `200 OK`. Used by the Docker healthcheck.
2. **Site workers** — one daemon thread per site; each loops: call the URL, log the result, sleep for `interval + jitter`.
3. **Config loader** — reads a JSON array from `CONFIG_PATH` (default `/config/sites.json`).

`main()` starts the health server thread, starts one worker thread per site, then joins the worker threads (they are daemons, so `join()` keeps the process alive).

## Config format

`/config/sites.json` is a JSON array. Template: `sites.example.json`.

```json
[
  { "url": "https://example.com/wp-cron.php?doing_wp_cron", "interval": 900 }
]
```

Each entry requires `url` and `interval` (seconds). Entries missing either are skipped with a warning.

## Scheduling behavior (don't change casually)

- **Start offset**: `int(md5(url).hexdigest(), 16) % interval` — evenly spreads initial start times across sites.
- **Jitter**: `max_jitter = min(240, interval * 0.4)`; sleep `= max(1, interval + uniform(-max_jitter, max_jitter))` — never negative.
- `REQUEST_TIMEOUT = 30` seconds per HTTP call.

## Docker

- Build/run: `docker compose up -d --build`; logs: `docker compose logs -f`.
- Runs as non-root user `scheduler` (uid 1000).
- Real config is mounted read-only from the host: `/opt/wp-cron-scheduler/sites.json:/config/sites.json:ro`.
- Healthcheck curls `http://localhost:8080/health` (interval 150s).
- `Dockerfile` uses `python:3-slim` and installs `curl` (needed by the healthcheck).

## Pitfalls

- `CONFIG_PATH` is hardcoded to `/config/sites.json`. Running `cron_scheduler.py` directly outside Docker fails unless that file exists — there is no CLI/config-file argument.
- Python dependency: only `requests` (see `requirements.txt`).
- No test suite exists. Validate config JSON with: `python -c "import json; json.load(open('sites.example.json'))"`.
- Log levels: INFO for normal runs, WARNING for non-200 status, ERROR for exceptions, DEBUG for sleep timing.
