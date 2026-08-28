# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Build stage: install the project (runtime deps only) into a self-contained
# virtualenv that the final stage can copy wholesale.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /src

# Copy only what the build backend (hatchling) needs to produce the wheel.
COPY pyproject.toml ./
COPY app ./app

# Install the app and its runtime dependencies (no dev extras, no pip cache).
RUN pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Final stage: minimal runtime image, non-root, migrations run on start.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS final

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000

# Unprivileged user to run the service.
RUN groupadd --system app && useradd --system --gid app --create-home --home-dir /app app

WORKDIR /app

# Runtime virtualenv from the build stage (contains the installed app package).
COPY --from=builder /opt/venv /opt/venv

# Alembic lives outside the wheel, so copy it explicitly for `alembic upgrade`.
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini ./

USER app

# Render sets $PORT; default to 8000 for `docker run` without it.
EXPOSE 8000

# Apply pending migrations, then hand off (exec) to uvicorn as PID 1.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
