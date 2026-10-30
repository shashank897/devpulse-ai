# DevPulse AI

**Understand your code. Inspect the evidence. Engineer with confidence.**

A working engineering-intelligence preview built with Next.js, React, TypeScript, FastAPI, and SQLAlchemy. The frontend follows the supplied **Deep Sea** design system and feature-based architecture.

## What works

- Responsive landing page with an interactive, explicitly labeled SQL-injection example.
- Browser-session workspace with code snippets and public GitHub repository scans.
- Python AST rules; selected JavaScript/TypeScript and C/C++ patterns.
- Commit-pinned GitHub snapshots with bounded file, byte, and request limits.
- Source evidence, remediation, severity filters, triage, file metrics, and scan history.
- JSON and SARIF report exports; session-owned data deletion.
- Opt-in, server-side OpenRouter free-model explanations with rule-guidance fallback.
- Trainable TF-IDF/logistic-regression baseline with project-disjoint evaluation.
- Docker, local PostgreSQL Compose configuration, and GitHub Actions verification.

## Run locally

Use Node 22+ and Python 3.12+.

```sh
npm ci
npm run build
python -m venv .venv
# Activate the virtual environment for your operating system.
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://localhost:8000. FastAPI serves the static frontend and API from one origin. `npm run dev` is useful for visual development, but scans require the built frontend served by FastAPI. Run `docker compose up --build` for a local PostgreSQL-backed environment.

## Verify

```sh
npm run build
npm run typecheck
python -m pytest tests -q
```

## Configuration

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection; defaults to local SQLite |
| `ENVIRONMENT=production` | Secure session cookies for HTTPS |
| `OPENROUTER_API_KEY` | Optional server-only API key |
| `OPENROUTER_MODEL` | `openrouter/free` or a `:free` model only |
| `MODEL_PATH` | Trusted baseline artifact; requires ML dependencies |
| `PORT` | Container HTTP port; defaults to 10000 |

Never commit `.env`, credentials, downloaded datasets, or model artifacts. The GitHub connection used to publish this repository is **not** an application credential and is not embedded in the app.

## Render

Deploy this repository as a Docker web service using `Dockerfile`, with `ENVIRONMENT=production`. The frontend and API run in one container. The free preview uses ephemeral SQLite: history disappears on restart/redeploy/sleep. Supply a managed PostgreSQL `DATABASE_URL` for durable data. The container listens on `$PORT` and exposes `/api/v1/health`.

## Honest scope

This is not the complete enterprise platform described in the long-form brief. Private GitHub App installations/OAuth, webhooks and check runs, distributed Celery workers, dependency advisory scanning, transformer fine-tuning, and advanced commit comparison are not implemented. The UI explicitly labels unavailable capabilities. No model accuracy, test coverage, scan metrics, or successful integrations are fabricated.

See [ARCHITECTURE.md](ARCHITECTURE.md), [SECURITY.md](SECURITY.md), [ML_REPORT.md](ML_REPORT.md), [TEST_REPORT.md](TEST_REPORT.md), and [ml/README.md](ml/README.md).
