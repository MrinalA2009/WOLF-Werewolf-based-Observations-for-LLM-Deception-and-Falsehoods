# WOLF — Werewolf-based Observations for LLM Deception and Falsehoods

WOLF runs games of Werewolf where every player is an LLM agent, and instruments
every statement so you can measure two things separately:

- **deception production** — how often, and in what form, a player lies
- **deception detection** — how well the other players catch it

Each debate line gets a self-honesty label from the speaker and a suspicion
judgment from every other living player, categorised as *omission*, *distortion*,
*fabrication*, or *misdirection*. Suspicion is smoothed across the game so you can
watch trust move round to round. Full prompts, raw model output, and state
transitions are written to disk for every run.

The engine is a LangGraph state machine with strict night/day cycles, bid-ordered
debate, and majority-vote exile. It is derived from Google's
[Werewolf Arena](https://github.com/google/werewolf_arena) (Apache-2.0); see
`NOTICE`.

## Layout

```
wolf/
  cli.py            entry point (also exposed as the `wolf` command)
  config.py         model list and defaults
  game/
    state.py        GameState — the single source of truth
    graph.py        phase nodes + the StateGraph wiring
    bidding.py      debate turn order
  agents/
    player.py       role prompts + per-action LLM calls
  deception/
    detector.py     self / peer chain-of-thought reads
    scoring.py      suspicion smoothing, observer accuracy
    analysis.py     orchestrates a full statement analysis
  runlog/
    events.py       per-run log setup + NDJSON event stream
    metrics.py      research-ready metrics JSON
    console.py      terminal report helpers
docs/               methodology.md, logging.md
tests/              scripted-LLM suite (no API key needed)
```

## Setup

Needs Python 3.9+ and an OpenAI API key.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
export OPENAI_API_KEY=sk-...        # or put it in a .env file
```

## Run

```bash
python run.py                       # or: wolf
python run.py --model gpt-4o-mini
python run.py --log-dir ./runs
python run.py --no-file-logging
```

The roster (8 players: 2 Werewolves, 1 Seer, 1 Doctor, 4 Villagers) and the
6-turn debate cap are set in `wolf/cli.py`.

## Output

Each run writes `logs/<run_id>/`:

| file | contents |
|---|---|
| `events.ndjson` | one JSON event per line, in order, with `_prompt` / `_raw_response` |
| `game_state.json` | the full final `GameState` |
| `run_meta.json` | roster, roles, model, timestamps |
| `final_metrics.json` | research metrics, no raw prompts — **but see KNOWN_ISSUES.md #1** |

`docs/logging.md` has `jq` recipes for slicing these.

## Development

```bash
pip install -e ".[dev]"
pytest        # scripted games + scoring unit tests, no network
ruff check .
```

`tests/test_refactor_parity.py` pins a scripted full game to a byte-exact golden
snapshot; regenerate it with `python -m tests.regen_golden` only when you mean to
change game output.

## Status

The code works but has several known, deliberately-unfixed bugs (final-metrics
crash, `round_num` never incrementing, others) — see `KNOWN_ISSUES.md`.
`docs/methodology.md` explains the engine end to end.
