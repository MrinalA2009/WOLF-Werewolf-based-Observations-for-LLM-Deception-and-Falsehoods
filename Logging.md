### Logging and Data Access

This project streams all game events to disk and writes a final full-state JSON snapshot for every run.

- Events (NDJSON): `logs/<run_id>/events.ndjson`
  - One JSON object per line, in chronological order
  - Contains: timestamp, round, step, phase, event type, actor, and `details`
  - `details` may include raw model prompts and responses under `_prompt` and `_raw_response`
- Final State JSON: `logs/<run_id>/game_state.json`
  - Full Pydantic-serialized `GameState` including `game_logs`, deception history, scores, etc.
- Final Metrics JSON: `logs/<run_id>/final_metrics.json`
  - Clean research-ready metrics only (no raw prompts/responses)
  - Includes: per-player deception totals and average suspicion, cross-perception score matrix, per-observer detection accuracy (accuracy/precision/recall/f1), and time/round trends of average suspicion and fraction of observers flagging deception
- Run Metadata: `logs/<run_id>/run_meta.json`
  - Players, roles, model name, timestamps, and convenience pointers
- Runs Index: `logs/index.jsonl`
  - One-line JSON index of all past runs with paths

#### Configure where logs are saved

- CLI flag: `--log-dir ./logs` (default is `./logs`)
- Disable file logging entirely: `--no-file-logging`
- Environment variable alternative: `LOG_DIR=/custom/path python run.py`

#### Quick examples with jq

- Tail events while the game runs:
```bash
jq -c . logs/<run_id>/events.ndjson | sed -u 's/.*/&/'
```

- Filter only debate events:
```bash
jq -c 'select(.event=="debate")' logs/<run_id>/events.ndjson
```

- Extract all raw model responses for auditing:
```bash
jq -r 'select(.details._raw_response) | .details._raw_response' logs/<run_id>/events.ndjson
```

- Get final winner and survivors from the snapshot:
```bash
jq '.winner, .alive_players' logs/<run_id>/game_state.json
```

- List your most recent runs:
```bash
tail -n 20 logs/index.jsonl | jq -c .
```

#### What gets logged

- Night actions: eliminate, protect, unmask (includes model prompts and raw responses)
- Day actions: debate turns, bids, votes, exile
- Deception analyses: self and peer analyses for every statement
- Phase transitions and win checks

All raw model responses and the exact prompts are preserved for reproducibility under `_raw_response` and `_prompt` when available.