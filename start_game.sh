#!/bin/bash

# Werewolf Game Startup Script
echo "Werewolf AI Game Launcher"
echo "============================"

# Load environment variables from .env if present
if [ -f ".env" ]; then
    echo "Loading environment from .env"
    set -a
    while IFS= read -r line; do
        if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
            export "$line"
        fi
    done < .env
    set +a
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Setting up..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if Python dependencies are installed
echo "Checking dependencies..."
if ! python -c "import langchain_openai" &> /dev/null; then
    echo "Installing missing dependencies..."
    pip install -r requirements.txt
fi

echo "Starting game..."
echo ""
python run.py "$@"
echo ""
echo "Game session ended."
