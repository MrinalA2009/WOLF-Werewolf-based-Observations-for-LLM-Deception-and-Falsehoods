# Known issues

These are real bugs in the current code. The 2025 cleanup deliberately left them
untouched (the brief was "reorganize and de-AI, change no logic"), so they are
recorded here rather than fixed. Each one is a good first PR.

1. **Final metrics never get written.** `wolf/runlog/metrics.py` calls `mean(...)`
   and `compute_observer_accuracy(...)` without importing them. Any game with
   deception history therefore makes `write_final_metrics` raise `NameError`,
   which `wolf.cli` swallows — so `final_metrics.json` is not produced and the run
   ends by printing an "Error" block even though the game finished. Fix: add
   `from statistics import mean` and
   `from wolf.deception.scoring import compute_observer_accuracy`, then drop the
   `if compute_observer_accuracy is not None` guard.

2. **`round_num` never increments.** No node bumps `state.round_num`, so every
   event and deception iteration is stamped `round: 0`. Round-over-round trends in
   `metrics.py` collapse to a single bucket. Fix: increment it in
   `check_winner_day_node` when routing back to `eliminate`.

3. **`start_game.sh` plays two games per launch** — once as a bogus "API test",
   then once for real. Fix: run it once, or add a real `--check` path to the CLI.

4. **Debate mention-bias is a no-op.** `bidding.choose_next_speaker` builds its
   mention nudge by scanning `top_bidders` against itself instead of all bidders,
   so it never changes the outcome.

5. **Dead fallback roster in `player.py`.** `eliminate` / `save` / `unmask` still
   carry `alive_players = ["Alice", "Bob", "Charlie"]` defaults. Callers always
   pass the real list; the default only hides bugs.

6. **`Player.get_deception_perception` is unused.** Nothing calls it.

7. **`datetime.utcnow()`** is used throughout and is deprecated on 3.12+. Swap for
   `datetime.now(timezone.utc)`.

## Changes that were made (the two unavoidable ones)

- `GameState.phase` gained `"end"` as a valid `Literal` value. `summary_node`
  already assigns `phase = "end"` at runtime; recent langgraph re-validates the
  state model while routing, so without this the game cannot finish. No node
  behaviour changed.
- `wolf.cli` and the test runner rebuild `GameState(**dict(final_state))` when
  langgraph hands back a plain channel dict instead of the model.
