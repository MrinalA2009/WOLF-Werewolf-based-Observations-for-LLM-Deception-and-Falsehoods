"""A scripted game reaches a terminal state and writes the expected log files."""

import json

from tests.support import ROSTER, play_game


def test_game_reaches_a_winner():
    final = play_game(seed=0)
    assert final.phase == "end"
    assert final.winner in {"Villagers", "Werewolves"}
    assert 0 < len(final.alive_players) < len(ROSTER)
    assert final.game_logs[-1]["event"] == "summarize"


def test_file_logging_writes_the_run_artifacts(tmp_path):
    final = play_game(seed=0, log_dir=str(tmp_path), enable_file_logging=True)
    run_dir = tmp_path / final.log_run_id

    events = (run_dir / "events.ndjson").read_text().splitlines()
    assert events and all(json.loads(line)["event"] for line in events)

    state_blob = json.loads((run_dir / "game_state.json").read_text())
    assert state_blob["winner"] == final.winner
    assert (run_dir / "run_meta.json").exists()
