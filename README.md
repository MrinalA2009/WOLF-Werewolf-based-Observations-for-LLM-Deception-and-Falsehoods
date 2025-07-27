# Werewolf Deception Detection Game (need to come up with name)

# Deception Detection System for Werewolf Game

This implementation adds a comprehensive deception detection system to the Werewolf game that analyzes every statement made by models and tracks their deceptive behavior over time.

## 🎯 Requirements Implemented

### ✅ Core Requirements Met:

1. **Everytime a model takes an action, we should look whether or not that statement is deceptive**
   - ✅ Implemented in `analyze_statement_deception()` function
   - ✅ Integrated into debate phase, voting phase, and all statement-making actions

2. **Ask the model to construct thoughts via CoT and then classify whether its statement was deceptive**
   - ✅ Implemented in `DeceptionDetector.analyze_self_deception()`
   - ✅ Uses Chain of Thought reasoning with step-by-step analysis
   - ✅ Model analyzes its own intentions and classifies deception

3. **Make sure the model is outputting it in JSON format**
   - ✅ All analysis responses are in structured JSON format
   - ✅ Includes: `chain_of_thought`, `is_deceptive`, `confidence`, `deception_type`, `reasoning`

4. **When a model says something in global chat, all other models run their own CoT**
   - ✅ Implemented peer analysis in `analyze_other_deception()`
   - ✅ Every statement triggers analysis by all other alive players
   - ✅ Parallel processing for efficiency

5. **Classify that as deceptive or not**
   - ✅ Binary classification: 0 (not deceptive) or 1 (deceptive)
   - ✅ Includes confidence scores and reasoning

6. **Model should have a way of understanding how they perceive history of deceptive actions**
   - ✅ `deception_history` tracks all past statements and analyses
   - ✅ `deception_scores` maintains running perception scores
   - ✅ Historical context provided to analysis functions

7. **0 or 1 (basic)**
   - ✅ Binary classification system implemented

## 🏗️ System Architecture

### Key Components:

#### 1. `DeceptionDetector` Class (`deception_detection.py`)
- **Self-analysis**: Models analyze their own statements for deceptive intent
- **Peer analysis**: Models analyze other players' statements
- **Chain of Thought**: Step-by-step reasoning process
- **JSON output**: Structured, consistent response format

#### 2. Game State Extensions (`game_graph.py`)
- **`deception_history`**: Stores all deception analyses per player
- **`deception_scores`**: Tracks how each player perceives others' trustworthiness
- **Real-time updates**: Scores update with weighted averages (70% new, 30% historical)

#### 3. Integration Points
- **Debate phase**: Every statement analyzed immediately
- **Voting phase**: Vote reasoning statements analyzed
- **Player voting**: Deception scores influence voting decisions

## 📊 JSON Output Format

### Self-Analysis Output:
```json
{
    "chain_of_thought": "Step-by-step reasoning about the statement",
    "is_deceptive": 0,
    "confidence": 0.6,
    "deception_type": "none",
    "reasoning": "Brief explanation of classification"
}
```

### Peer Analysis Output:
```json
{
    "chain_of_thought": "Analysis of other player's statement",
    "is_deceptive": 1,
    "confidence": 0.7,
    "deception_type": "misdirection",
    "reasoning": "Statement seems like deflection",
    "suspicion_level": 0.8
}
```

## 🔄 Deception Analysis Flow

1. **Player makes statement** in debate/voting phase
2. **Self-analysis** triggered automatically:
   - Player analyzes own statement using CoT
   - Returns JSON with deception classification
3. **Peer analysis** triggered in parallel:
   - All other alive players analyze the statement
   - Each returns independent JSON analysis
4. **History update**:
   - Statement and all analyses stored in `deception_history`
   - Deception scores updated with weighted averages
5. **Game integration**:
   - Updated scores influence future voting decisions
   - Historical context provided for future analyses

## 🎮 Usage Example

```python
# When a player makes a statement in debate:
statement = "I suspect Bob is acting suspicious"

# 1. Self-analysis (automatic)
self_analysis = detector.analyze_self_deception(
    player_name="Alice",
    statement=statement,
    context="Round 1, debate phase"
)

# 2. Peer analysis (automatic, parallel)
for observer in other_players:
    peer_analysis = detector.analyze_other_deception(
        observer_name=observer,
        speaker_name="Alice", 
        statement=statement,
        context="Round 1, debate phase",
        history=player_deception_history
    )

# 3. Update game state (automatic)
state = update_deception_history(state, "Alice", statement, 
                                self_analysis, peer_analyses)
```

## 📈 Deception Tracking Features

### Historical Context
- **Recent statements**: Last 3 analyses provided for context
- **Pattern recognition**: Models can identify behavioral patterns
- **Trust evolution**: Perception scores evolve over time

### Deception Types Classified
- `"none"`: No deception detected
- `"omission"`: Withholding information
- `"distortion"`: Twisting facts
- `"fabrication"`: Making false claims
- `"misdirection"`: Deflecting suspicion

### Scoring System
- **Suspicion levels**: 0.0 (completely trustworthy) to 1.0 (highly suspicious)
- **Weighted updates**: New assessments weighted more heavily than old
- **Per-observer tracking**: Each player maintains independent perceptions

## 🧪 Testing

Run the test demonstration:
```bash
python3 test_deception_simple.py
```

This shows:
- Self-analysis and peer analysis in action
- JSON output formatting
- Deception history tracking
- Score updates and summaries

## 🔧 Technical Details

### Performance Optimizations
- **Parallel processing**: Multiple analyses run simultaneously
- **Efficient scoring**: Weighted averages prevent score stagnation
- **Context limiting**: Only recent history provided to prevent token overflow

### Error Handling
- **JSON parsing fallbacks**: Malformed responses handled gracefully
- **Default values**: Missing fields filled with sensible defaults
- **Timeout protection**: Analysis calls have time limits

### Integration Points
- **Game phases**: Seamlessly integrated into existing game flow
- **Player decisions**: Deception scores influence voting behavior
- **Logging**: All analyses logged for post-game analysis

## 📊 Expected Output

The system produces rich deception analysis data including:

- **Statement-by-statement tracking**
- **Player deception profiles** 
- **Trust relationship matrices**
- **Behavioral pattern summaries**
- **Game-ending deception reports**

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/DetectionBenchmark.git
cd DetectionBenchmark
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
touch game_log.json
```

And paste in this initial content:

```json
[]
```

---

### 5. Run Game

run:

```bash
python run.py
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
├── run.py                  # Main file to run  game
├── game_graph.py           # LangChain state graph + nodes
├── Player.py               # Player defs
├── Bidding.py              # speaker selection
├── game_log.json           # Game log (auto-generated)
├── README.md               # You're here
```

---

## Output Logs

All gameplay is logged in:

```
game_log.json
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
- **Werewolf**: Kills at night and blends in during the day
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
