<div align="center">

# Notify Service

**Notification as a Service (NaaS)** — a scalable, multi-tenant, multi-channel notification platform built with FastAPI.

[![CI Tests](https://github.com/usgitAz/notify-service/actions/workflows/tests.yml/badge.svg)](https://github.com/usgitAz/notify-service/actions/workflows/tests.yml)
[![Lint](https://github.com/usgitAz/notify-service/actions/workflows/lint.yml/badge.svg)](https://github.com/usgitAz/notify-service/actions/workflows/lint.yml)
[![Type Check](https://github.com/usgitAz/notify-service/actions/workflows/type-check.yml/badge.svg)](https://github.com/usgitAz/notify-service/actions/workflows/type-check.yml)
[![codecov](https://codecov.io/gh/usgitAz/notify-service/branch/main/graph/badge.svg)](https://codecov.io/gh/usgitAz/notify-service)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#features) ·
[Architecture](#architecture) ·
[Quick Start](#quick-start) ·
[API](#api-overview) ·
[Development](#development) ·
[Docker](#docker) ·
[Testing](#testing--ci) ·
[Configuration](#configuration)

</div>

---

## Overview

Notify Service is an MVP **Notification as a Service** platform. Tenants authenticate with API keys, manage end-users and devices, and send notifications across channels. Delivery is asynchronous, idempotent, and tracked with full status history.

| Channel | Status |
|---------|--------|
| **Email** (SMTP) | Implemented |
| **Push** (FCM / devices) | **Future** |
| **SMS** | **Future** |

**Stack highlights:** Python 3.13 · FastAPI · SQLAlchemy 2 · PostgreSQL · Redis · Docker multi-stage ·

---

## Features

- **Multi-tenant isolation** — every resource is scoped by tenant via `X-API-Key`
- **Secure API keys** — format `sk_<env>_<random>`, stored as HMAC-SHA256 + server pepper; prefix indexed for O(1) lookup; constant-time verify
- **Users & devices** — external IDs unique per tenant; soft-delete; device registration (push delivery is future)
- **Email notifications** — async create (`202 Accepted`), background delivery, retries with exponential backoff
- **Idempotency** — optional `Idempotency-Key` header backed by Redis (24h TTL by default)
- **Cross-channel notification model** — shared table + JSONB `payload` for channel-specific fields
- **Health probes** — liveness (`/health`) and readiness (`/health/ready` with DB check)
- **Structured logging** — request ID middleware, fapilog, redacted sensitive headers
- **Clean architecture** — API → services → repositories → models; domain exceptions mapped in the API layer
- **Production Docker** — multi-stage (builder / development / runtime), non-root user, healthcheck
- **Dev ergonomics** — hot-reload, MailHog, compose overrides, dedicated test DB profile
- **CI** — Ruff, Mypy, full pytest suite + coverage (Codecov)

---

## Architecture

```text
                    ┌─────────────────────────────────────────┐
                    │              Clients / Tenants           │
                    └───────────────────┬─────────────────────┘
                                        │  X-API-Key
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  FastAPI (app.main)                                                       │
│  Middleware: RequestID · Logging · Exception handlers                     │
│  Routes: /health · /api/v1/users · /devices · /notifications              │
└───────────────┬─────────────────────────────┬─────────────────────────────┘
                │                             │
                ▼                             ▼
        ┌───────────────┐             ┌───────────────┐
        │   Services    │             │ BackgroundTasks│
        │  user/device  │             │  send_notification
        │  notification │             │  → SMTP / retry │
        └───────┬───────┘             └───────────────┘
                │
                ▼
        ┌───────────────┐     ┌─────────────┐
        │ Repositories  │────▶│ PostgreSQL  │
        └───────────────┘     └─────────────┘
                │
                ▼
        ┌───────────────┐
        │ Redis         │  idempotency cache
        └───────────────┘
```

### Layering

| Layer | Responsibility |
|-------|----------------|
| `app/api` | HTTP routes, deps (`get_db`, `get_current_tenant`), response envelope, exception → HTTP |
| `app/services` | Business rules, orchestration |
| `app/repositories` | Persistence queries |
| `app/infrastructure` | DB models/session, SMTP client, Redis |
| `app/core` | Settings, security, idempotency, domain exceptions |
| `app/schemas` | Pydantic request/response models |

---

## Project structure

<details>
<summary><strong>Expand directory map</strong></summary>

```text
notify-service/
├── .github/workflows/          # CI: lint, type-check, tests + Codecov
├── alembic/                    # Migrations
│   └── versions/
├── app/
│   ├── api/
│   │   ├── deps.py             # DB session, tenant auth, idempotency, Redis
│   │   ├── exception_handlers.py
│   │   ├── responses.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── health.py
│   │           ├── users.py
│   │           ├── devices.py
│   │           └── notifications/
│   │               ├── common.py   # list / get (all channels)
│   │               └── email.py    # POST /notifications/email
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py         # API key generate / hash / verify
│   │   ├── idempotency.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── models/         # Tenant, User, Device, Notification
│   │   └── clients/
│   │       └── email_client.py # aiosmtplib
│   ├── middleware/
│   │   └── request_id.py
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   │   ├── user_service.py
│   │   ├── device_service.py
│   │   ├── notification_service.py
│   │   ├── notification_email_service.py
│   │   ├── sender.py           # background delivery + retries
│   │   └── tenant_service.py
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py             # async fixtures, TEST_DATABASE_URL
├── docker-compose.yml          # base: Postgres + Redis
├── docker-compose.dev.yml      # API hot-reload, MailHog, ports, db-test profile
├── docker-compose.prod.yml
├── Dockerfile                  # builder → development → runtime
├── pyproject.toml              # deps, ruff, mypy, pytest, coverage
├── uv.lock
├── .env.example
└── README.md
```

</details>

---

## Quick start

### Prerequisites

- Docker & Docker Compose **or**
- Python **3.13+**, [uv](https://docs.astral.sh/uv/), PostgreSQL 17, Redis 7

### Option A — Docker (recommended)

```bash
# 1. Env
cp .env.example .env.dev
# Edit .env.dev: POSTGRES_*, API_KEY_PEPPER (≥48 chars), SMTP_* for MailHog

# 2. Start stack
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# 3. Migrations
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head

# 4. API
open http://localhost:8000/docs
```

| Service | URL |
|---------|-----|
| API / OpenAPI | http://localhost:8000/docs |
| MailHog UI | http://localhost:8025 |
| Postgres (host) | `localhost:5432` |
| Redis (host) | `localhost:6379` |

Stop everything:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

### Option B — Local (uv)

```bash
uv sync --all-groups
cp .env.example .env
# Point POSTGRES_HOST / REDIS_URL at your local services

alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API overview

Base path: **`/api/v1`**
Auth header: **`X-API-Key: sk_live_...`** (or `sk_test_...`)

Success envelope:

```json
{
  "success": true,
  "data": { },
  "meta": {
    "timestamp": "2026-10-06T19:06:50.539390Z",
    "request_id": "f0468f6b-cd9f-46bb-b87d-3cefdc1c0be6"
  }
}
```

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness |
| `GET` | `/health/ready` | Readiness (includes DB) |

### Users

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/users` | Create user (`external_id` unique per tenant) |
| `GET` | `/api/v1/users/{external_id}` | Get user |
| `PATCH` | `/api/v1/users/{external_id}` | Update email / soft-delete (`is_active`) |

### Devices

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/users/{external_id}/device/register` | Register push device |
| `GET` | `/api/v1/users/{external_id}/devices` | List active devices |
| `GET` | `/api/v1/devices/{device_id}` | Get device |
| `PATCH` | `/api/v1/devices/{device_id}` | Update name / deactivate |

### Notifications

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/notifications/email` | Create email notification (`202`) |
| `GET` | `/api/v1/notifications/` | List (filters: `status`, `channel`, pagination) |
| `GET` | `/api/v1/notifications/{id}` | Get by ID |

Optional header on email create:

```http
Idempotency-Key: <client-uuid>
```

Retries with the same key return the original `202` response body (Redis-backed).

### Example: send email

```bash
curl -s -X POST http://localhost:8000/api/v1/notifications/email \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_test_YOUR_KEY" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "user_id": "user-1",
    "subject": "Welcome!",
    "body": "Thanks for signing up.",
    "from_email": "noreply@example.com"
  }'
```

With MailHog in dev (`SMTP_HOST=mailhog`, `SMTP_PORT=1025`, `SMTP_USE_TLS=false`, `SMTP_ENABLED=true`), open http://localhost:8025 to inspect the message.

### Create a tenant (API key)

```bash
# Local (uv / venv) — requires DB env vars loaded
python -m app.scripts.create_tenant "New Tenant"

# Optional: test-environment key prefix (sk_test_...)
python -m app.scripts.create_tenant "New Tenant" --env test

# Inside Docker API container
docker compose -f docker-compose.yml -f docker-compose.dev.yml \
  exec api python -m app.scripts.create_tenant "New Tenant"
```

The command prints the tenant id, key prefix, and the **full API key once**. Store it securely; it is not shown again.

---

## Domain model (summary)

| Entity | Notes |
|--------|--------|
| **Tenant** | API key owner; `api_key_hash` + `api_key_prefix`; soft-delete |
| **User** | `(tenant_id, external_id)` unique; optional email; soft-delete |
| **Device** | Push token (unique), platform, provider (FCM), soft-delete |
| **Notification** | Channel enum, status (`pending` / `delivered` / `failed`), attempts, `payload` JSONB; **not** soft-deleted (audit trail) |

Delivery (email): background task loads notification → SMTP via `aiosmtplib` → up to 3 attempts with backoff on transient errors; permanent errors mark `failed`.

---

## Configuration

Copy `.env.example`. Important variables:

| Variable | Purpose |
|----------|---------|
| `POSTGRES_USER` / `PASSWORD` / `DB` / `HOST` / `PORT` | Database (in Docker use host `db`) |
| `API_KEY_PEPPER` | Secret ≥ 48 chars for key hashing |
| `REDIS_URL` | e.g. `redis://redis:6379/0` in Docker |
| `SMTP_ENABLED` | `true` to send for real (else mock log) |
| `SMTP_HOST` / `PORT` / `USE_TLS` | MailHog: `mailhog`, `1025`, `false` |
| `IDEMPOTENCY_TTL_SECONDS` | Default `86400` |

Inside Docker Compose, service hostnames are **`db`**, **`redis`**, **`mailhog`** — not `localhost`.

---

## Docker

### Stages (`Dockerfile`)

1. **builder** — uv sync production deps into `/opt/venv`
2. **development** — builder + `--dev` deps (for compose `target: development`)
3. **runtime** — slim image, non-root `appuser` (UID 1001), healthcheck on `/health`

Production image only copies the venv from **builder** (no dev packages).

### Compose files

```bash
# Development
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production-style
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Test database** (profile `test`, port **5433** — matches `tests/conftest.py`):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile test up -d db-test
```

Always use the same `-f` pair for `down` as for `up`.

---

## Development

```bash
# Install (incl. dev tools)
uv sync --all-groups

# Lint & format
uv run ruff check .
uv run ruff format .

# Types
uv run mypy app/

# Pre-commit (optional)
pre-commit install
```

Migrations:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

---

## Testing & CI

### Local

```bash
# Needs Postgres on 5433 (db-test) or override TEST_DATABASE_URL
export TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/notif_test
export API_KEY_PEPPER=test-pepper-with-at-least-48-characters-for-ci-only-xyz
export POSTGRES_USER=user POSTGRES_PASSWORD=pass POSTGRES_DB=notif_test

uv run pytest tests/ -v --cov=app --cov-report=term-missing
```

- **Unit** (`tests/unit`) — no real DB; mocks
- **Integration** (`tests/integration`) — real Postgres; Redis via **fakeredis**
- Background email send is mocked in the HTTP client fixture to avoid event-loop issues

### GitHub Actions

| Workflow | Role |
|----------|------|
| `lint.yml` | Ruff check + format |
| `type-check.yml` | Mypy |
| `tests.yml` | Full pytest + coverage → Codecov |

Path filters can skip docs-only changes via `paths-ignore` (e.g. `**.md`) on each workflow.

---

## Security notes

- API keys never stored in plaintext; pepper stays only on the server
- Failed auth always returns the same generic message (no oracle)
- Soft-delete preferred over hard-delete for tenants/users/devices
- Notifications retained for audit; FKs use `RESTRICT`
- Sensitive headers redacted in access logs

---

## Roadmap (indicative)

- [ ] **Push** delivery (FCM) using registered devices
- [ ] **SMS** channel
- [ ] Rate limiting
- [ ] Outbox / queue worker instead of in-process `BackgroundTasks` for multi-replica
- [ ] OpenAPI examples & public changelog

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

**[OpenAPI docs](http://localhost:8000/docs)** when running locally ·
Built with FastAPI & uv

</div>
