# 🎮 Werewolf AI Game - Setup Fixed & Ready!

## 🔥 Main Issue Fixed

**The Original Problem:** You were running `bash run.py` instead of `python run.py`

- ❌ **Wrong:** `bash run.py` → This tries to execute Python code as bash commands
- ✅ **Fixed:** `python run.py` → This properly runs the Python script

## 🛠️ What Was Fixed

### 1. **Execution Method**
- Fixed command execution from bash to python
- Created virtual environment for dependency management
- Added proper startup script (`start_game.sh`)

### 2. **Python Code Issues**
- Fixed Pydantic model annotations (`ClassVar` for class variables)
- Fixed GameState import order in `game_graph.py`
- Fixed LangGraph config access pattern
- Corrected Google Generative AI model naming

### 3. **Model Configuration**
- Updated to working model names (`gemini-1.5-flash`, `gemini-pro`, etc.)
- Added model switching capability
- Created configuration system for easy model changes

### 4. **API Key Management**
- Added environment variable support
- Created API key testing functionality
- Added command-line API key option

## 🚀 How to Run the Game Now

### Option 1: Using the Startup Script (Recommended)
```bash
# With API key as argument
./start_game.sh --api-key YOUR_API_KEY_HERE

# With environment variable
export GOOGLE_API_KEY="your_api_key_here"
./start_game.sh

# With different model
./start_game.sh --model gemini-pro --api-key YOUR_API_KEY
```

### Option 2: Manual Python Execution
```bash
# Activate virtual environment
source venv/bin/activate

# Run with API key
python run.py --api-key YOUR_API_KEY_HERE

# Run with environment variable
export GOOGLE_API_KEY="your_api_key_here"
python run.py

# Run with different model
python run.py --model gemini-1.5-pro
```

### Option 3: Test API First
```bash
# Test your API key before running the game
source venv/bin/activate
python test_api.py --api-key YOUR_API_KEY_HERE
```

## 🎯 Available Models

The following models are confirmed to work:
- `gemini-1.5-flash` (default - fast and efficient)
- `gemini-pro` (balanced performance)
- `gemini-1.5-pro` (enhanced reasoning)

## 📋 Quick Start Checklist

1. ✅ **Virtual Environment:** Already created in `venv/`
2. ✅ **Dependencies:** Already installed via `requirements.txt`
3. ✅ **Code Fixes:** All Python issues resolved
4. ✅ **Startup Script:** `start_game.sh` ready to use
5. 🔑 **API Key:** You need to provide your Google API key

## 🆘 Troubleshooting

### "API Test Failed"
- Check if your Google API key is valid
- Ensure the API key has Google Generative AI access enabled
- Try a different model name

### "command not found"
- Make sure you're running `python run.py` not `bash run.py`
- Ensure the virtual environment is activated: `source venv/bin/activate`

### "Module not found"
- Run: `source venv/bin/activate && pip install -r requirements.txt`

## 🎉 You're Ready!

Your Werewolf AI game is now properly configured and ready to run. Just add your Google API key and enjoy the game!

**Remember:** Always use `python run.py` or `./start_game.sh`, never `bash run.py`!