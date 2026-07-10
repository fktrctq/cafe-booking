# ============================================
# Базовый слой
# ============================================
FROM python:3.12-slim AS base

SHELL ["/bin/sh", "-exc"]

RUN apt-get update \
    && apt-get install --quiet --no-install-recommends --assume-yes netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY --link --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv

ARG UID=1000
ARG GID=1000

RUN groupadd -g ${GID} cafeuser \
    && useradd -u ${UID} -g cafeuser -m -s /bin/bash cafeuser \
    && mkdir -p /app/logs /app/media && chown -R ${UID}:${GID} /app

USER cafeuser

ENV UV_PYTHON="python3.12" \
  UV_PYTHON_DOWNLOADS=never \
  UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  PYTHONOPTIMIZE=1

WORKDIR /app

COPY --chown=$UID:$GID pyproject.toml uv.lock /app/

RUN uv sync --no-dev --no-install-project --frozen

ENV PATH=/app/.venv/bin:$PATH \
  PYTHONOPTIMIZE=1 \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1

# ============================================
# FastAPI приложение
# ============================================
FROM base AS backend

COPY --exclude=src/fixtures/ --chown=$UID:$GID src .

EXPOSE 8000/tcp

# ============================================
# Celery образ (общий для worker и beat)
# ============================================
FROM base AS celery

COPY --parents --chown=$UID:$GID \
    src/./celery_app.py \
    src/./celery_core/ \
    src/./core/ \
    src/./models/ \
    ./

ENV PYTHONPATH=/app
