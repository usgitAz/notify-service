# Changelog

All notable changes to this project will be documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned
- Push notifications (FCM)
- SMS channel
- Rate limiting

## [0.3.0] - 2026-10-10

### Added
- Multi-tenant API key authentication (HMAC-SHA256 + pepper)
- User management: create, get, soft-delete
- Device management: register, list, update
- Email notifications via SMTP (async, retries, backoff)
- Idempotency keys via Redis
- Health probes: liveness + readiness (DB + Redis)
- Docker multi-stage build (dev + prod compose)
- CI: ruff, mypy, pytest with 100% coverage

### Security
- API keys hashed; pepper not stored in DB
- Sensitive headers redacted in logs
