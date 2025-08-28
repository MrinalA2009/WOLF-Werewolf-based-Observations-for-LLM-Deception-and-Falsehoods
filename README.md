## Werewolf Game — AI Social Deduction Engine

A faithful, programmable Werewolf/Mafia loop implemented with LangGraph and Pydantic, featuring structured agent actions and a deception‑detection protocol.

### Quick start

- **Prerequisites**: Python 3.8+; an OpenAI API key
- **Install**:
```bash
pip install -r requirements.txt
```
- **Configure**:
```bash
export OPENAI_API_KEY=sk-...
```
- **Run**:
```bash
python run.py --model gpt-4o
```

### Methodology

- **Game state** (`game_graph.py: GameState`):
  - Players, roles, alive lists; role partitions (`villagers`, `werewolves`, `seer`, `doctor`)
  - Turn counters: `round_num`, `step`, and `phase`
  - Logs: `debate_log`, `bids`, `votes`, `summaries` and per‑action raw outputs
  - Deception tracking: `deception_history`, `deception_scores`, `deception_iterations`
  - File logging paths and run metadata (`logs.py`)

- **Graphed gameflow (LangGraph StateGraph)**:
  - Nodes: `eliminate → protect → unmask → resolve_night → check_winner_night → debate → vote → exile → check_winner_day → summarize → end`
  - Routing: deterministic via `phase` using `add_conditional_edges`; entry point `eliminate`
  - Winner rules: villagers win if no werewolves remain; werewolves win if werewolves ≥ villagers

- **Night**
  - `eliminate`: A living werewolf calls `Player.eliminate` (JSON target with validation/fallbacks)
  - `protect`: Doctor calls `Player.save` to select protection
  - `unmask`: Seer calls `Player.unmask`; revealed role stored privately via `reveal_and_update`
  - `resolve_night`: Apply elimination unless protected; announce outcome
  - `check_winner_night`: Early termination if a faction has won

- **Day**
  - `debate`: Each turn, living players bid 0–10 (`Bidding.get_bid`); `choose_next_speaker` uses max‑bid, light mention bias, and random tiebreaking. Speaker issues a JSON‑constrained `Player.debate` statement; the system runs deception analysis (below), appends to `debate_log`, and advances until `MAX_DEBATE_TURNS`.
  - `vote`: All living players call `Player.vote`; prompts include observer‑specific deception perceptions (trustworthy/deceptive based on `deception_scores`).
  - `exile`: Majority removes a player; no exile on ties or no majority.
  - `check_winner_day`: Terminate if a faction has won, else start a new night.
  - `summarize`/`end`: Survivors call `Player.summarize`; final metrics and deception summary are produced and printed.

### Measurement protocol (deception detection)

1) For each public statement (debate and, if justified, vote rationale):
   - Speaker performs self‑analysis (`DeceptionDetector.analyze_self_deception`)
   - All other living players perform peer analysis (`analyze_other_deception`)
   - Each analysis returns: `is_deceptive` ∈ {0,1}, `confidence` ∈ [0,1], `deception_type`, `reasoning`, and peers also return `suspicion_level` ∈ [0,1]
2) `update_deception_history` records a rich event with context snapshot (alive set, current speaker, speaker role, recent dialogue), raw prompts/outputs preserved in analysis objects, and a timestamp.
3) Cross‑perception scores update as an exponential running average per observer/target: `new = 0.7 * assessment + 0.3 * prior` (stored in `deception_scores`).

### Agents, prompts, and private scratchpads

- Roles: Villager, Werewolf, Seer, Doctor (`player.py` templates)
- All action interfaces return JSON with fixed keys; targets are validated with explicit fallbacks and the choice/fallback is logged
- Private scratchpads persist concise reasoning and investigations; only structured outputs are shared

### Bidding, debate, and voting

- Bidding: model‑elicited integers in [0,10]; light mention bias and random tie‑breaking for speaker selection
- Debate: concise, outcome‑driven statements (JSON schema enforced)
- Voting: prompts optionally include observer‑specific deception perceptions (`deception_scores`) to link detection signals to downstream decisions

### Metrics

- Per‑player: totals of statements, self‑reported deceptions, peer‑detected deceptions, average suspicion
- Final cross‑perception matrix: `deception_scores[observer][target] ∈ [0,1]`
- Observer accuracy (against self‑labels): tp/tn/fp/fn, accuracy, precision, recall, F1 (`deception_detection.compute_observer_accuracy`)
- Trends: statement‑level averages over time and by round (`logs.py`), plus printed end‑of‑game summary

### Logging and reproducibility

- Per‑action events streamed to NDJSON and accumulated in `GameState.game_logs` (`logs.log_event`)
- Files under `logs/<run_id>/`: `events.ndjson`, `game_state.json`, `final_metrics.json`, `run_meta.json`; runs indexed in `logs/index.jsonl`
- For audit: prompts and raw model outputs are preserved within action results (e.g., `_prompt`, `_raw_response` fields in deception analyses and player actions)

### Project layout

```
run.py                  # Entry point; compiles and runs the graph
game_graph.py           # GameState and LangGraph nodes/edges
player.py               # Role‑grounded prompts and JSON action interfaces
deception_detection.py  # Self/peer deception analysis and score updates
logs.py                 # Structured logging and final metrics
Bidding.py              # 0–10 bidding + speaker selection
requirements.txt        # Dependencies
```

### Configuration

- CLI: `python run.py [--model gpt-4o|gpt-4-turbo|gpt-3.5-turbo] [--api-key ...] [--log-dir ./logs] [--no-file-logging]`
- Env: `OPENAI_API_KEY` required; `MODEL_NAME` used by bidding helper

### License

Apache‑2.0‑licensed code; see headers and LICENSE where applicable.
