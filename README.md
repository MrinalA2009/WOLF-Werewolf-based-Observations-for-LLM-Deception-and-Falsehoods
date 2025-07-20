# Werewolf LLM Game (LangChain Edition)

A fully automated, LLM-driven version of the classic **Werewolf social deduction game**, powered by Gemini and structured with LangChain’s state-graph architecture.  
No setup or scripting needed, just install dependencies and run!

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/werewolf-llm-game.git
cd werewolf-llm-game
```

### 2. Set Your Gemini API Key

Create a `.env` file in the root:

```env
GOOGLE_API_KEY=your-google-api-key-here
```

Or export it in your shell:

```bash
export GOOGLE_API_KEY="your-google-api-key-here"
```

---

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install langchain langgraph langchain-core langchain-google-genai tqdm pydantic
```

---

### 4. Initialize the Log File

Make sure this file exists in the project root:

```bash
touch werewolf_game_log.json
```

And paste in this initial content:

```json
[]
```

---

### 5. ▶️ Run the Game

run:

```bash
python run_game.py
```

The game will:
- Assign roles
- Simulate night actions (kill, protect, reveal)
- Allow players to debate based on LLM bidding
- Vote and exile players
- Log the entire flow to a structured JSON file

---

## File Structure

```bash
.
├── run_game.py              # Main file to launch the game
├── werewolf_graph.py       # LangChain state graph + nodes
├── Player.py               # Role-based player behavior
├── Bidding.py              # LLM bidding logic for speaker selection
├── werewolf_game_log.json  # Game log (auto-generated)
├── README.md               # You're here
```

---

## Output Logs

All gameplay is logged in:

```
werewolf_game_log.json
```

Each log entry is JSON-formatted with timestamps, actor, action, and raw LLM responses. Example:
```json
{
  "timestamp": "2025-07-20T01:22:00Z",
  "event": "protect",
  "actor": "Alice",
  "details": {
    "target": "Charlie",
    "raw_output": "Alice chose to protect Charlie..."
  },
  "round": 1,
  "phase": "protect"
}
```

You can use this log for auditing, visualization, or game summaries.

---

## Roles 

- **Villager**: Votes and debates honestly
- **Werewolf**: Kills at night and lies during the day
- **Seer**: Can reveal one player's role per night
- **Doctor**: Can protect one player per night

Roles and logic are preconfigured, no setup needed.

---

## Powered By

- [Gemini 2.0 (Flash)](https://ai.google.dev/)
- [LangChain](https://www.langchain.com/)
- [LangGraph](https://github.com/langchain-ai/langgraph)

---

## License

This project is licensed under the [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0).


Werewolf paper for reference: 
https://arxiv.org/pdf/2407.13943
Github link: https://github.com/google/werewolf_arena
