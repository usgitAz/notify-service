# syntax=docker/dockerfile:1.10

# Stage 1: builder — install uv, resolve & sync dependencies
FROM python:3.13-slim-bookworm AS builder

# Copy the `uv` binary from the official distroless image.
# Pinning the minor version keeps builds reproducible.
COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/

# uv tuning:
#   UV_COMPILE_BYTECODE — precompile .pyc for faster cold starts
#   UV_LINK_MODE=copy   — required when using cache mounts
#   UV_PROJECT_ENVIRONMENT — put the venv at a predictable path
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# --- Layer 1: dependencies only
# This layer is only invalidated when pyproject.toml or uv.lock changes.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# --- Layer 2: project source
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev


# Stage 2: development — builder + dev dependencies
FROM builder AS development

# Install development dependencies (pytest, ruff, mypy, ...)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --dev


# Stage 3: runtime — minimal image with venv + app code
FROM python:3.13-slim-bookworm AS runtime

# Create a non-root user/group with fixed UID/GID for portability.
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup \
    --create-home --shell /bin/false appuser

# Install runtime-only OS deps (curl is for HEALTHCHECK).
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy the prebuilt virtualenv from the builder stage.
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

WORKDIR /app

# Copy the app source
COPY --chown=appuser:appgroup . .

# Make the venv the default Python environment.
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

# Container-level healthcheck (used by Docker / Compose / orchestrators).
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Production command: no --reload, multiple workers.
# Overridden in docker-compose.dev.yml for local dev.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
