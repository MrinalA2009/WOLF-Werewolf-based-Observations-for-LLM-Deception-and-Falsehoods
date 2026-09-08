"""Guard rail for the 2025 reorg: a scripted full game must serialize to exactly
the snapshot captured before any files were moved. Regenerate the golden only
when you *intend* to change observable output:

    python -m tests.regen_golden
"""

from pathlib import Path

from tests.support import canonical, play_game

GOLDEN = Path(__file__).parent / "golden" / "game_state.json"


def test_full_game_matches_golden():
    assert canonical(play_game(seed=0)) == GOLDEN.read_text()


def test_game_is_deterministic():
    assert canonical(play_game(seed=0)) == canonical(play_game(seed=0))
