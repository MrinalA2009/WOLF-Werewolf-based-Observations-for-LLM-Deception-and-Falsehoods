"""Deterministic, network-free test doubles and a full-game runner.

Everything here exists so the suite can exercise the real graph without an API
key. The runner mirrors run.py / wolf.cli step for step; if the two drift, the
parity test is the thing that will scream.
"""

from __future__ import annotations

import json
import random
import re

# Import paths are tried package-first, then flat-layout, so the same file works
# before and after the reorg.
try:
    from wolf.game.graph import graph
    from wolf.game.state import GameState
    from wolf.agents.player import Player
    from wolf.game import bidding
    from wolf.runlog.events import init_logging_state, write_final_state
    from wolf.runlog.metrics import write_final_metrics
except ModuleNotFoundError:  # flat pre-refactor layout
    from game_graph import graph, GameState
    from player import Player
    import Bidding as bidding
    from logs import init_logging_state, write_final_state, write_final_metrics


ROSTER = ["Alice", "Bob", "Selena", "Raj", "Frank", "Joy", "Cyrus", "Emma"]
ROLES = {
    "Alice": "Doctor",
    "Bob": "Werewolf",
    "Selena": "Seer",
    "Raj": "Villager",
    "Frank": "Villager",
    "Joy": "Werewolf",
    "Cyrus": "Villager",
    "Emma": "Villager",
}

_SPEAKER = re.compile(r"You are (\w+)")


class _Reply:
    __slots__ = ("content",)

    def __init__(self, content: str):
        self.content = content


class ScriptedLLM:
    """Stands in for ChatOpenAI. Answers each prompt shape with fixed JSON so a
    whole game plays out identically every run."""

    def __init__(self, roster=ROSTER):
        self.roster = list(roster)

    def _pick_target(self, prompt: str) -> str:
        speaker = _SPEAKER.search(prompt)
        speaker_name = speaker.group(1) if speaker else ""
        options = [n for n in self.roster if n in prompt and n != speaker_name]
        return options[0] if options else self.roster[0]

    def invoke(self, prompt: str, **_kwargs) -> _Reply:
        if "single number from 0 to 10" in prompt:
            return _Reply("7")

        if '"suspicion_level"' in prompt:  # peer deception read
            return _Reply(json.dumps({
                "chain_of_thought": "Weighing their claim against the round so far.",
                "is_deceptive": 0,
                "confidence": 0.5,
                "deception_type": "none",
                "reasoning": "Nothing contradicts what they said earlier.",
                "suspicion_level": 0.5,
            }))

        if '"chain_of_thought"' in prompt:  # self deception read
            return _Reply(json.dumps({
                "chain_of_thought": "Recapping my own intent behind that line.",
                "is_deceptive": 0,
                "confidence": 0.5,
                "deception_type": "none",
                "reasoning": "I said what I actually believe.",
            }))

        if '"statement"' in prompt:  # debate turn
            return _Reply(json.dumps({
                "statement": "I want the quiet players to explain themselves.",
                "is_deceptive": False,
                "analysis": "Keep pressure broad until someone slips.",
            }))

        if '"vote"' in prompt:  # exile vote
            return _Reply(json.dumps({
                "vote": self._pick_target(prompt),
                "is_deceptive": False,
                "analysis": "Front-runner is the safe pick.",
                "reasoning": "They dodged every direct question.",
            }))

        if '"summary"' in prompt:  # end-of-game recap
            return _Reply(json.dumps({
                "summary": "Factions traded losses until one side ran out of numbers.",
                "is_deceptive": False,
                "analysis": "Voting bloc discipline decided it.",
            }))

        # eliminate / save / unmask all ask for a "target"
        return _Reply(json.dumps({
            "target": self._pick_target(prompt),
            "is_deceptive": False,
            "analysis": "Highest-value removal available.",
        }))


def play_game(*, seed: int = 0, log_dir: str | None = None,
              enable_file_logging: bool = False) -> GameState:
    """Run one full game against ScriptedLLM. Mirrors run.run_werewolf_game."""
    random.seed(seed)
    llm = ScriptedLLM()
    bidding._llm = llm  # short-circuit the module-global lazy init

    seer = next((p for p in ROSTER if ROLES[p] == "Seer"), None)
    doctor = next((p for p in ROSTER if ROLES[p] == "Doctor"), None)
    werewolves = [p for p in ROSTER if ROLES[p] == "Werewolf"]
    villagers = [p for p in ROSTER if ROLES[p] == "Villager"]

    # model_construct skips validation of the llm field so the double slots in.
    agents = {name: Player.model_construct(name=name, role=ROLES[name], llm=llm)
              for name in ROSTER}

    state = GameState(
        round_num=0,
        players=ROSTER,
        alive_players=ROSTER.copy(),
        roles=ROLES,
        villagers=villagers,
        werewolves=werewolves,
        seer=seer,
        doctor=doctor,
        phase="eliminate",
        game_logs=[],
        deception_history={},
        deception_scores={},
    )
    state = init_logging_state(state, log_dir=log_dir, enable_file_logging=enable_file_logging)

    runnable = graph.compile()
    final_state = runnable.invoke(state, config={
        "recursion_limit": 1000,
        "configurable": {"player_objects": agents, "MAX_DEBATE_TURNS": 6},
    })
    # Recent langgraph hands back the raw channel dict rather than the pydantic
    # model; rebuild it so the rest of the pipeline has a GameState. (Same shim
    # lives in wolf.cli — see KNOWN_ISSUES.md.)
    if not isinstance(final_state, GameState):
        final_state = GameState(**dict(final_state))

    write_final_state(final_state)
    try:
        write_final_metrics(final_state)
    except Exception:
        # Known issue: metrics path raises NameError today. See KNOWN_ISSUES.md.
        pass
    return final_state


_ISO = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)?")


def normalize(blob):
    """Recursively replace timestamps and run ids so two runs compare equal."""
    if isinstance(blob, dict):
        return {k: ("<ts>" if k in {"timestamp", "created_at_utc"} else normalize(v))
                for k, v in blob.items()}
    if isinstance(blob, list):
        return [normalize(v) for v in blob]
    if isinstance(blob, str):
        s = _ISO.sub("<ts>", blob)
        s = re.sub(r"\d{8}-\d{6}-\d{6}", "<run>", s)
        return s
    return blob
