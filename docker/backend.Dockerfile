# Build context is the repo root (see docker-compose.yml) — backend/ depends
# on postura-scanner and postura-ai-engine as local packages (see
# backend/pyproject.toml), so all three directories need to be in the build
# context together; a context scoped to backend/ alone couldn't see them.
FROM python:3.12-slim

WORKDIR /app

# build-essential/libffi-dev: argon2-cffi and cryptography both use cffi,
# which occasionally needs to compile against a wheel-less manylinux target.
# Cheap up front, avoids a confusing build failure later.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copied and installed in dependency order: scanner has no local deps,
# ai-engine depends on scanner, backend depends on both.
COPY scanner/ ./scanner/
COPY ai-engine/ ./ai-engine/
COPY backend/ ./backend/

RUN pip install --no-cache-dir ./scanner ./ai-engine ./backend

WORKDIR /app/backend

EXPOSE 8000

# Migrate then serve — one container, simplest thing that works at MVP
# scale (a separate migrate-then-serve init step is v2, once there's more
# than one backend replica and a startup race becomes possible).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
