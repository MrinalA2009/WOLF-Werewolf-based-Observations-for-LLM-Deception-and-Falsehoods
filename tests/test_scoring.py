"""Locks in the current numbers coming out of the deception scorer. Ported from
the old detection_test.py demo, which had prints but no assertions."""

from wolf.deception.scoring import compute_observer_accuracy, update_deception_history
from wolf.game.state import GameState


def _state():
    return GameState(
        round_num=1,
        players=["Alice", "Bob", "Charlie"],
        alive_players=["Alice", "Bob", "Charlie"],
        roles={"Alice": "Villager", "Bob": "Werewolf", "Charlie": "Seer"},
        phase="debate",
    )


def test_suspicion_is_recency_weighted_0_7_0_3():
    state = _state()
    liar = {"is_deceptive": 1, "suspicion_level": 1.0}
    # first read: 0.7 * 1.0 + 0.3 * 0.5 (neutral prior)
    state = update_deception_history(state, "Alice", "s1", {"is_deceptive": 0}, {"Bob": dict(liar)})
    assert state.deception_scores["Bob"]["Alice"] == 0.85
    # second read compounds on the running score
    state = update_deception_history(state, "Alice", "s2", {"is_deceptive": 0}, {"Bob": dict(liar)})
    assert round(state.deception_scores["Bob"]["Alice"], 4) == round(0.7 * 1.0 + 0.3 * 0.85, 4)


def test_observer_accuracy_scores_against_self_report():
    state = _state()
    # Alice admits deception; Bob catches it, Charlie misses it.
    state = update_deception_history(
        state, "Alice", "I'm totally a villager", {"is_deceptive": 1},
        {"Bob": {"is_deceptive": 1, "suspicion_level": 0.9},
         "Charlie": {"is_deceptive": 0, "suspicion_level": 0.4}},
    )
    metrics = compute_observer_accuracy(state)

    assert metrics["Bob"] == {"tp": 1, "tn": 0, "fp": 0, "fn": 0, "total": 1,
                              "accuracy": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0}
    assert metrics["Charlie"]["fn"] == 1
    assert metrics["Charlie"]["recall"] == 0.0
    assert metrics["Charlie"]["accuracy"] == 0.0


def test_history_and_iteration_records_accumulate():
    state = _state()
    state = update_deception_history(state, "Bob", "trust me", {"is_deceptive": 1},
                                    {"Alice": {"is_deceptive": 1, "suspicion_level": 0.8}})
    (record,) = state.deception_history["Bob"]
    assert record["statement"] == "trust me"
    assert record["observers_flagging"] == ["Alice"]
    assert record["self_reported_deceptive"] == 1
