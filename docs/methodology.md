### Methodology: Werewolf Game Engine

This document explains how the game works end‑to‑end, including phases, AI behavior, deception analysis, bidding, voting, and logging.

#### Core Data Model

- `GameState` (see `game_graph.py`): single source of truth containing:
  - Players, roles, alive lists, special roles (Seer, Doctor, Werewolves, Villagers)
  - Turn/round counters: `round_num`, `step`, and `phase`
  - Action logs and summaries: bids, votes, debate log, summaries
  - Deception tracking: `deception_history` and `deception_scores`
  - `game_logs`: append‑only list of structured events (also streamed to disk)

#### Phases per Round

1) Night
- eliminate: Werewolves choose a target
- protect: Doctor chooses a target to save
- unmask: Seer reveals (to self) the role of one player
- resolve_night: Announce outcome considering protection
- check_winner_night: Early win condition check

2) Day
- debate: Players speak in sequence; bidding determines order and turn length
- vote: Everyone votes to exile one player
- exile: Resolve votes and remove a player
- check_winner_day: Win condition after exile
- summarize: Summaries and deception statistics

Each phase is a node in a LangGraph `StateGraph`. Transitions are deterministic based on game rules and the evolving `GameState`.

#### AI Players (`player.py`)

- Each player is a `Player` with `role`, `scratchpad`, and a shared `llm`.
- Action methods: `eliminate`, `save`, `unmask` construct a role‑aware JSON prompt and call `call_model`.
- `call_model` returns parsed JSON and also includes the exact `_prompt` and `_raw_response` for auditability.
- Post‑validation ensures targets are valid; fallbacks are applied when the model returns invalid data, and this is recorded in logs.

#### Deception Detection (`deception_detection.py`)

- `DeceptionDetector` asks the active speaker to self‑assess deception and asks all peers to analyze the statement.
- Peer analyses run concurrently via a thread pool.
- Results are normalized and stored in `deception_history` and aggregated into `deception_scores` via a weighted update.
- A per‑round deception summary is produced at the end of the game.

#### Bidding and Debate (`Bidding.py` and `game_graph.py`)

- Players bid for speaking order/priority using `get_bid`.
- `choose_next_speaker` resolves the next speaker.
- `debate_log` preserves the dialogue as `[speaker, text]` pairs.

#### Voting and Resolution

- `vote` collects each alive player's vote. Ties break via deterministic rules.
- `exile` removes the selected player from `alive_players` and updates role‑specific lists.
- Night protection can cancel a werewolf elimination.
- Win conditions: 
  - Werewolves eliminated => Villagers win
  - Werewolves >= Villagers => Werewolves win

#### Logging (`logs.py`)

- Every state transition or action appends a structured event via `log_event`.
- Events are streamed to `logs/<run_id>/events.ndjson` with concurrency safety.
- A final full `game_state.json` snapshot is written upon completion.
- Metadata for each run is written to `run_meta.json` and indexed in `logs/index.jsonl`.

#### Reproducibility and Auditing

- Prompts and raw model outputs are preserved in event details (`_prompt`, `_raw_response`).
- Validation/fallbacks are explicitly logged (e.g., when an invalid target is corrected).
- Deception analyses retain chain‑of‑thought fields in raw form for offline study (note: treat with care).

#### Extending the System

- Add new phases by extending `GameState.phase` literals and adding nodes to `StateGraph`.
- Use `log_event` for any new actions; include both `inputs` and `outputs` fields.
- Register additional per‑run artifacts by updating `init_logging_state` in `logs.py`.