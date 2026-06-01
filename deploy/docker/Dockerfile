# syntax=docker/dockerfile:1
# Nexu Cinema HTTP server — build from nexu repo root.
# Build contexts: --build-context repatch=../repatch --build-context intract=../intract

FROM python:3.12-slim-bookworm AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build/nexu

COPY . .
COPY --from=repatch . /build/repatch/
COPY --from=intract . /build/intract/

RUN sed -i 's|repatch\[web\] @ file://[^"]*|repatch[web]|' pyproject.toml \
    && pip install --no-cache-dir --upgrade pip \
    && if [ -f /build/repatch/pyproject.toml ]; then pip install --no-cache-dir "/build/repatch[web]"; fi \
    && if [ -f /build/intract/pyproject.toml ]; then pip install --no-cache-dir /build/intract; fi \
    && pip install --no-cache-dir . \
    && pip install --no-cache-dir litellm

FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin nexu

WORKDIR /workspace

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /build/nexu/deploy/docker/cinema_serve.py /usr/local/bin/cinema_serve.py
COPY --from=builder /build/nexu/project /workspace/project

RUN chown -R nexu:nexu /workspace

USER nexu

ENV NEXU_WORKSPACE=/workspace \
    NEXU_CAPSULE=nexu \
    CINEMA_PORT=8080 \
    CINEMA_BIND_HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${CINEMA_PORT}/cinema_player.html" >/dev/null || exit 1

CMD ["python", "/usr/local/bin/cinema_serve.py"]
