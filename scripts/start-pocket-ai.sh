#!/usr/bin/env bash
# Start Pocket AI: backend (FastAPI) then Electron GUI.
# When you close the GUI, the backend is stopped too.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate venv if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Start backend in background
python app.py &
BACKEND_PID=$!

# Wait for backend to be ready (health check or timeout)
for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null | grep -q 200; then
        break
    fi
    sleep 1
done

# Start Electron GUI (blocks until user closes the window)
cd "$PROJECT_ROOT/chat-gui"
if [ -f "out/main/index.js" ]; then
    npx electron . 2>/dev/null || npm run dev
else
    npm run dev
fi

# When GUI exits, stop the backend
kill $BACKEND_PID 2>/dev/null || true
