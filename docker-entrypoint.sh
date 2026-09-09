#!/bin/sh
set -e

echo "[entrypoint] Starting UGC Video Generator services..."

# Start FastAPI backend (Port 8000)
cd /app/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "[entrypoint] FastAPI backend started (PID $BACKEND_PID) on port 8000."

# Start Next.js frontend (Port 3000)
cd /app/frontend
PORT=3000 npm start &
FRONTEND_PID=$!
echo "[entrypoint] Next.js frontend started (PID $FRONTEND_PID) on port 3000."

# Forward termination signals
trap "kill -TERM $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# Wait for any process to exit
wait -n $BACKEND_PID $FRONTEND_PID
