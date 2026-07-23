#!/bin/sh
set -eu

export PORT="${PORT:-10000}"
export FRONTEND_URL="${FRONTEND_URL:-https://${RENDER_EXTERNAL_HOSTNAME:-localhost}}"

cd /app/backend
if [ -n "${DATABASE_URL:-}" ]; then
  alembic upgrade head
fi
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

cd /app/frontend
HOSTNAME=0.0.0.0 PORT="$PORT" node server.js &
FRONTEND_PID=$!

shutdown() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap shutdown INT TERM

while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 5
done

shutdown
wait "$BACKEND_PID" 2>/dev/null || true
wait "$FRONTEND_PID" 2>/dev/null || true
exit 1