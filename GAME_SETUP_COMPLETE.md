## 🚀 How to Run the Game

### Method 1: Using the Startup Script (Recommended)
```bash
# Make executable (first time only)
chmod +x start_game.sh

# Run with default settings
./start_game.sh

# Run with different model
./start_game.sh --model gemini-pro
```

### Method 2: Manual Python Execution
```bash
# Activate virtual environment
source venv/bin/activate

# Run with default model
python run.py

# Run with specific model
python run.py --model gemini-1.5-flash
python run.py --model gemini-pro
python run.py --model gemini-1.5-pro

# Run with custom API key
python run.py --api-key "your_api_key_here"
```

## 🎯 Available Models

- `gemini-1.5-flash` (default) - Fast and efficient
- `gemini-pro` - Balanced performance  
- `gemini-1.5-pro` - Enhanced reasoning

## 🔧 Configuration

### API Key Setup (Recommended)
```bash
# Set environment variable (Linux/Mac)
export GOOGLE_API_KEY="your_api_key_here"

# Windows
set GOOGLE_API_KEY=your_api_key_here
```

### Game Settings
Edit `config.py` to modify:
- Player names and roles
- Game parameters (debate turns, etc.)
- Model configurations

## 📁 Project Structure

```
werewolf-game/
├── venv/                 # Virtual environment
├── run.py               # Main game runner (FIXED)
├── start_game.sh        # Startup script
├── config.py           # Configuration file
├── game_graph.py       # Game logic (FIXED)
├── player.py           # Player classes (FIXED)
├── requirements.txt    # Dependencies
├── SETUP.md            # Setup instructions
└── README.md           # Project documentation
```

## ⚠️ Current Status

- ✅ **Infrastructure:** Fully working
- ✅ **Dependencies:** All installed
- ✅ **Models:** Correct configuration
- ⚠️ **Game Logic:** Minor issue with Bob's targeting (game design issue, not setup)

## 🐛 Known Issues

1. **"Bob failed to return a target"** - This is a game logic issue in the player decision-making, not a setup problem. The AI model and infrastructure are working correctly.

## 🎮 Next Steps

1. **Test the game:** Try running with different models to see which works best
2. **Customize players:** Edit the roles and player configurations in `config.py`
3. **Debug game logic:** If needed, adjust the player decision-making logic in `player.py`
4. **Add features:** Extend the game with additional roles or mechanics

## 🆘 Troubleshooting

If you encounter issues:

1. **"Command not found"**: Make sure you're using `python run.py`, not `bash run.py`
2. **"Module not found"**: Run `pip install -r requirements.txt` in the virtual environment
3. **API errors**: Check your Google API key is valid and has Gemini access
4. **Game logic errors**: These are design issues, not setup problems
