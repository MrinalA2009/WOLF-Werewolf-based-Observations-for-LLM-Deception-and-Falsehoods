from tests.support import ScriptedLLM
from wolf.game import bidding


def test_get_bid_clamps_to_0_10(monkeypatch):
    monkeypatch.setattr(bidding, "_llm", ScriptedLLM())
    bid, raw = bidding.get_bid("Raj", "some debate text")
    assert 0 <= bid <= 10
    assert raw == "7"


def test_get_bid_non_numeric_reply_is_zero(monkeypatch):
    class Mumbler:
        def invoke(self, *_a, **_k):
            return type("R", (), {"content": "hmm, hard to say"})()

    monkeypatch.setattr(bidding, "_llm", Mumbler())
    bid, _ = bidding.get_bid("Raj", "text")
    assert bid == 0


def test_choose_next_speaker_returns_a_top_bidder():
    picked = bidding.choose_next_speaker({"Raj": 8, "Bob": 8, "Emma": 2}, "Raj and Bob talked")
    assert picked in {"Raj", "Bob"}


def test_choose_next_speaker_single_leader_is_deterministic():
    assert bidding.choose_next_speaker({"Raj": 9, "Bob": 1}) == "Raj"
