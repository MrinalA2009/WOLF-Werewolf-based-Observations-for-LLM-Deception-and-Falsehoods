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

This comprehensive system enables detailed analysis of deceptive behavior in multi-agent AI interactions, providing valuable insights for research into AI deception detection and social reasoning.