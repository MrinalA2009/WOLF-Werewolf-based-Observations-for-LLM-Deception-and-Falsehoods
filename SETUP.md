# 🎮 Werewolf AI Game Setup Guide

## Quick Start

The easiest way to run the game is using the startup script:

```bash
# Make the script executable (first time only)
chmod +x start_game.sh

# Run the game
./start_game.sh
```

## Manual Setup

If you prefer to set up manually:

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set API Key (Recommended)
```bash
export GOOGLE_API_KEY="your_api_key_here"
```

### 4. Run the Game
```bash
python run.py
```

## Running Options

### Basic Usage
```bash
python run.py                    # Use default settings
python run.py --model gemini-pro # Use different model
python run.py --api-key YOUR_KEY # Provide API key directly
```

### Using the Startup Script
```bash
./start_game.sh                    # Default settings
./start_game.sh --model gemini-pro # Different model
```

### Available Models
- `gemini-2.0-flash` (default) - Latest and fastest
- `gemini-pro` - Balanced performance  
- `gemini-1.5-pro` - Enhanced reasoning

## Troubleshooting

### Error: "bash: run.py: command not found"
**Problem:** You're trying to run Python code with bash.
**Solution:** Use `python run.py` instead of `bash run.py`

### Error: "GOOGLE_API_KEY environment variable not set"
**Problem:** Missing API key.
**Solutions:**
1. Set environment variable: `export GOOGLE_API_KEY="your_key"`
2. Pass directly: `python run.py --api-key "your_key"`

### Error: "ModuleNotFoundError"
**Problem:** Missing dependencies.
**Solution:** 
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Virtual Environment Issues
**Problem:** Can't activate virtual environment.
**Solution:**
```bash
# Linux/Mac
source venv/bin/activate

# Windows Command Prompt
venv\Scripts\activate.bat

# Windows PowerShell
venv\Scripts\Activate.ps1
```

## Security Notes

- Keep your API key secure
- Don't commit API keys to version control
- Use environment variables for production
- The embedded API key in the code is for testing only

## Game Features

- AI-powered werewolf gameplay
- Multiple AI models supported
- Configurable game settings
- Detailed game logging
- Player deception detection

## Next Steps

Once everything is working:
1. Try different models to see how they play
2. Modify player roles in `config.py`
3. Adjust game settings like debate turns
4. Check out the game logs for detailed analysis

Happy gaming! 🐺🎭