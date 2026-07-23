# backend/Dockerfile
#
# Why this file exists:
#   Multi-stage build: the `builder` stage installs dependencies (needs
#   build tools for faiss-cpu/numpy compilation on some platforms), the
#   final stage copies only the installed packages + app code, keeping the
#   shipped image lean and free of compiler toolchains.

FROM python:3.12-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --break-system-packages --prefix=/install .

FROM python:3.12-slim AS runtime

# Non-root user: never run the app as root in production.
RUN useradd --create-home --shell /bin/bash vira
WORKDIR /app

COPY --from=builder /install /usr/local
COPY app ./app

RUN mkdir -p /app/storage/uploads && chown -R vira:vira /app
USER vira

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
