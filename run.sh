#!/usr/bin/env bash
# StudyVault Launcher Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "=========================================================="
echo "  🎓 StudyVault is starting at http://localhost:8000"
echo "  📚 API Docs available at http://localhost:8000/docs"
echo "  Press Ctrl+C to stop the server"
echo "=========================================================="

python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
