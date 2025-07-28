#!/bin/bash

# Werewolf Game Startup Script
echo "🎮 Werewolf AI Game Launcher"
echo "============================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Setting up..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
fi

# Check if Python dependencies are installed
echo "📦 Checking dependencies..."
if ! python -c "import langchain_google_genai" &> /dev/null; then
    echo "📥 Installing missing dependencies..."
    pip install -r requirements.txt
fi

echo "🔑 Testing API key..."
if python test_api.py "$@"; then
    echo "🚀 Starting game..."
    echo ""
    
    # Run the game with any arguments passed to this script
    python run.py "$@"
    
    echo ""
    echo "🎯 Game session ended."
else
    echo "❌ API test failed. Please check your API key and try again."
    echo ""
    echo "💡 Usage examples:"
    echo "  ./start_game.sh --api-key YOUR_API_KEY_HERE"
    echo "  export GOOGLE_API_KEY='your_key' && ./start_game.sh"
    exit 1
fi