#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "Error: Python 3 not found. Please install Python 3.9+."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    "$PYTHON" -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
python -m src.app
