# Werewolf Game

A fully functional AI-powered Werewolf game where AI players engage in strategic deception, investigation, and social deduction. The game features advanced deception detection, dynamic dialogue, and realistic player behavior.

## 🎯 Game Overview

This is a multiplayer social deduction game where:
- **Villagers** try to identify and eliminate the Werewolves
- **Werewolves** try to blend in and eliminate Villagers  
- **Seer** can investigate one player each night to learn their role
- **Doctor** can protect one player each night from elimination

The game includes sophisticated deception detection that analyzes player statements and voting patterns to determine trustworthiness.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Gemini API key

### Installation

1. **Clone and setup the environment:**
```bash
git clone <repository-url>
cd ai-werewolf-game
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Set up your API key:**
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

3. **Run the game:**
```bash
python run.py
```

### 🎮 Game Features

- **Dynamic AI Players**: Each player has their own personality and strategy
- **Advanced Deception Detection**: Real-time analysis of player statements for deception
- **Sophisticated Dialogue**: Natural conversation flow with context awareness
- **Role-Based Actions**: Seer investigation, Doctor protection, Werewolf elimination
- **Voting System**: Democratic exile voting with deception analysis
- **Game State Tracking**: Comprehensive logging of all game events

## 📁 Project Structure

```
ai-werewolf-game/
├── run.py                 # Main game entry point
├── game_graph.py          # Game logic and state machine
├── player.py              # Player class with AI behavior
├── deception_detection.py # Deception analysis system
├── Bidding.py            # Bidding mechanics
├── config.py             # Game configuration
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🎲 How to Play

### Game Flow

1. **Night Phase**:
   - Werewolves choose a player to eliminate
   - Doctor chooses a player to protect
   - Seer investigates a player's role

2. **Day Phase**:
   - Players debate and discuss suspicions
   - Deception detection analyzes statements
   - Players vote to exile someone
   - Winner is determined

### Player Roles

- **Villager**: Basic role, tries to identify werewolves
- **Werewolf**: Tries to eliminate villagers without being caught
- **Seer**: Can investigate one player per night to learn their role
- **Doctor**: Can protect one player per night from elimination

## 🔍 Deception Detection

The game includes a sophisticated deception detection system that:

- **Self-Analysis**: Players analyze their own statements for deceptive intent
- **Peer Analysis**: Other players analyze each statement for deception
- **Historical Tracking**: Maintains deception history for each player
- **Confidence Scoring**: Provides confidence levels for deception assessments

## ⚙️ Configuration

Edit `config.py` to customize:
- Number of players
- Role distribution
- Game parameters
- Debug settings

## 🐛 Troubleshooting

### Common Issues

1. **API Rate Limits (429 Error)**
   - **Cause**: Free tier Gemini API has rate limits
   - **Solution**: Wait a few minutes or upgrade to paid tier
   - **Workaround**: Use `--model gemini-pro` for different rate limits

2. **Missing API Key**
   - **Solution**: Set `GOOGLE_API_KEY` environment variable
   - **Alternative**: Use embedded test key (limited functionality)

3. **Import Errors**
   - **Solution**: Ensure all dependencies are installed: `pip install -r requirements.txt`
   - **Check**: Verify Python version is 3.8+

### Debug Mode

Enable debug mode in `config.py`:
```python
"debug_mode": True
```

## 📊 Game Logs

The game generates comprehensive logs:
- `game_log.json`: Complete game state history
- Console output: Real-time game events
- Deception analysis: Detailed deception assessments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is open source. See LICENSE file for details.

## 🙏 Acknowledgments

- Built with LangChain and LangGraph
- Powered by Google Gemini AI
- Inspired by the classic Werewolf/Mafia party game

---

**Note**: This game requires an active internet connection and a valid Google Gemini API key to function properly.
