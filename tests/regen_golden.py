"""Rewrite tests/golden/game_state.json from the current code. Only run this when
you deliberately change observable game output."""

from pathlib import Path

from tests.support import canonical, play_game

if __name__ == "__main__":
    out = Path(__file__).parent / "golden" / "game_state.json"
    out.write_text(canonical(play_game(seed=0)))
    print(f"wrote {out}")
