FROM node:20-bookworm-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
COPY frontend ./
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=/api/v1
RUN npm run build

FROM python:3.12-slim AS backend-builder
WORKDIR /app/backend
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=/api/v1
ENV PYTHONUNBUFFERED=1

COPY --from=frontend-builder /usr/local/bin/node /usr/local/bin/node
RUN useradd --create-home --shell /bin/bash vira

COPY --from=backend-builder /install /usr/local
COPY backend/app ./backend/app
COPY backend/alembic ./backend/alembic
COPY backend/alembic.ini ./backend/alembic.ini

COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend
COPY --from=frontend-builder /app/frontend/.next/static ./frontend/.next/static
COPY --from=frontend-builder /app/frontend/public ./frontend/public

COPY start.sh ./start.sh
RUN sed -i 's/\r$//' ./start.sh \
    && chmod +x ./start.sh \
    && mkdir -p /app/backend/storage/uploads \
    && chown -R vira:vira /app

USER vira
EXPOSE 10000
CMD ["sh", "./start.sh"]