# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Mrinal Agarwal, Saad Rana, and the WOLF authors
#
# The night/day loop and role set are derived from Google's Werewolf Arena
# (Apache-2.0). WOLF swaps its own LangGraph state machine and deception
# instrumentation in around that shape; see NOTICE and docs/methodology.md.

import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import Literal, Optional

import tqdm
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph

from wolf.deception.analysis import analyze_statement_deception, generate_deception_summary
from wolf.deception.scoring import compute_observer_accuracy
from wolf.game.bidding import choose_next_speaker, get_bid
from wolf.game.state import GameState
from wolf.runlog.console import print_header, print_kv, print_matrix, print_subheader
from wolf.runlog.events import log_event


def _seated(config: RunnableConfig) -> dict:
    """The name -> Player table, threaded through langgraph's configurable slot."""
    return config.get("configurable", {}).get("player_objects", {})


def _compute_current_winner(state: GameState) -> Optional[Literal["Villagers", "Werewolves"]]:
    """Villagers win once no Werewolf is alive; Werewolves win once they reach
    parity with the rest. Anything else means the game is still going."""
    wolves_alive = [p for p in state.werewolves if p in state.alive_players]
    villagers_alive = [p for p in state.alive_players if p not in wolves_alive]

    if not wolves_alive:
        return "Villagers"
    if len(wolves_alive) >= len(villagers_alive):
        return "Werewolves"
    return None


def _as_text(raw_reply) -> str:
    """Player action methods hand back a parsed dict; the *_log state fields want
    a plain string."""
    return str(raw_reply) if isinstance(raw_reply, dict) else raw_reply


# --- Night: the werewolves pick a victim -----------------------------------

def eliminate_node(state: GameState, config: RunnableConfig) -> GameState:
    table = _seated(config)

    immediate_winner = _compute_current_winner(state)
    if immediate_winner:
        state = state.model_copy(update={
            "winner": immediate_winner,
            "phase": "summarize",
            "step": 0
        })
        state = log_event(state, "check_winner_night", "system", {
            "winner": immediate_winner,
            "context": "early_check_in_eliminate"
        })
        return state

    alive_wolves = [name for name in state.werewolves if name in state.alive_players]
    if not alive_wolves:
        state = state.model_copy(update={
            "eliminated": None,
            "eliminate_log": "No werewolves alive; skipping elimination.",
            "phase": "protect"
        })
        state = log_event(state, "eliminate", "system", {
            "target": None,
            "raw_output": {"info": "No werewolves alive; skipped."}
        })
        return state

    acting_wolf = random.choice(alive_wolves)
    victim, raw_reply = table[acting_wolf].eliminate(state.alive_players)

    if not victim:
        raise ValueError(f"{acting_wolf} failed to return a target.")

    tqdm.tqdm.write(f"{acting_wolf} eliminated {victim}")

    # The pack shares the kill so nobody re-litigates it during the day.
    for wolf in alive_wolves:
        table[wolf]._add_observation(
            f"During the night, we decided to eliminate {victim}."
        )

    state = state.model_copy(update={
        "eliminated": victim,
        "eliminate_log": _as_text(raw_reply),
        "phase": "protect"
    })
    state = log_event(state, "eliminate", acting_wolf, {
        "target": victim,
        "raw_output": raw_reply,
    })
    return state


# --- Night: the Doctor shields one player ---------------------------------

def protect_node(state: GameState, config: RunnableConfig) -> GameState:
    """Doctor chooses a player to save during the same night."""
    table = _seated(config)
    doctor_name = state.doctor

    if doctor_name not in state.alive_players:
        return state.model_copy(update={"phase": "unmask"})

    protect_target, raw_reply = table[doctor_name].save(state.alive_players)

    if not protect_target:
        raise ValueError(f"{doctor_name} failed to specify a protection target.")

    tqdm.tqdm.write(f"{doctor_name} protected {protect_target}")

    state = state.model_copy(update={
        "protected": protect_target,
        "protect_log": _as_text(raw_reply),
        "phase": "unmask"
    })
    state = log_event(state, "protect", doctor_name, {
        "target": protect_target,
        "raw_output": raw_reply,
    })
    return state


# --- Night: the Seer learns one role -------------------------------------

def unmask_node(state: GameState, config: RunnableConfig) -> GameState:
    """Seer investigates one player each night."""
    table = _seated(config)
    seer_name = state.seer

    if seer_name not in state.alive_players:
        return state.model_copy(update={"phase": "resolve_night"})

    target, raw_reply = table[seer_name].unmask(state.alive_players)
    if not target:
        raise ValueError(f"{seer_name} failed to return a target.")

    role_revealed = state.roles[target]
    table[seer_name].reveal_and_update(target, role_revealed)

    state = state.model_copy(update={
        "unmasked": target,
        "unmask_log": _as_text(raw_reply),
        "phase": "resolve_night"
    })
    state = log_event(state, "unmask", seer_name, {
        "target": target,
        "revealed_role": state.roles[target],
        "raw_output": raw_reply,
    })
    return state


# --- Night resolves: protection can cancel the kill ----------------------

def night_node(state: GameState, config: RunnableConfig) -> GameState:
    """Apply elimination/protection outcome and broadcast announcement."""
    if state.eliminated and state.eliminated != state.protected:
        new_alive = [p for p in state.alive_players if p != state.eliminated]
        announcement = (
            f"The Werewolves removed {state.eliminated} from the game during the night."
        )
    else:
        new_alive = state.alive_players
        announcement = "No one was removed from the game during the night."

    tqdm.tqdm.write(announcement)

    state = state.model_copy(update={
        "alive_players": new_alive,
        "phase": "check_winner_night"
    })
    state = log_event(state, "resolve_night", "system", {"announcement": announcement})
    return state


def checkwinner_node(state: GameState, config: RunnableConfig) -> GameState:
    """Back to the day phase, or straight to the wrap-up if a faction has won."""
    winner = _compute_current_winner(state)

    state = state.model_copy(update={
        "winner": winner,
        "phase": "debate" if not winner else "summarize",
        "step": 0
    })
    state = log_event(state, "check_winner_night", "system", {"winner": winner})
    return state


# --- Day: bid-ordered debate, one line per visit ------------------------

def debate_node(state: GameState, config: RunnableConfig) -> GameState:
    table = _seated(config)
    MAX_DEBATE_TURNS = config.get("configurable", {}).get("MAX_DEBATE_TURNS", 6)

    dialogue_history = "\n".join([f"{s}: {t}" for s, t in state.debate_log])
    last_speaker = state.debate_log[-1][0] if state.debate_log else None

    contenders = [p for p in state.alive_players if p != last_speaker]
    bid_logs = []
    bid_dict = {}

    with ThreadPoolExecutor(max_workers=len(contenders)) as executor:
        futures = {name: executor.submit(get_bid, name, dialogue_history) for name in contenders}
        for name, future in futures.items():
            bid, raw_output = future.result()
            bid_dict[name] = bid
            bid_logs.append(f"{name} bid {bid} – {raw_output}")

    next_speaker = choose_next_speaker(bid_dict, dialogue_history)
    dialogue, raw_reply = table[next_speaker].debate(state.debate_log)
    if not dialogue:
        raise ValueError(f"{next_speaker} failed to produce a debate line.")

    tqdm.tqdm.write(f"{next_speaker}: {dialogue}")

    state = analyze_statement_deception(state, next_speaker, dialogue, table, config)

    state = state.model_copy(update={
        "debate_log": state.debate_log + [[next_speaker, dialogue]],
        "bid_logs": state.bid_logs + bid_logs,
        "current_speaker": next_speaker,
        "step": state.step + 1,
        "phase": "vote" if state.step + 1 >= MAX_DEBATE_TURNS else "debate"
    })
    state = log_event(state, "debate", next_speaker, {
        "dialogue": dialogue,
        "bids": bid_dict,
        "raw_output": raw_reply,
    })
    return state


# --- Day: everyone votes, majority exiles -------------------------------

def vote_node(state: GameState, config: RunnableConfig) -> GameState:
    table = _seated(config)
    votes = {}
    vote_lines = []

    for voter in state.alive_players:
        choice, raw_reply = table[voter].vote(state.deception_scores)
        votes[voter] = choice
        vote_lines.append(f"{voter} voted for {choice} – {raw_reply}")

        # A bare vote isn't worth analysing; a vote *with* stated reasoning is.
        vote_statement = f"I vote for {choice}"
        if "reasoning" in raw_reply and raw_reply.get("reasoning"):
            vote_statement += f" because {raw_reply.get('reasoning', '')}"
            state = analyze_statement_deception(state, voter, vote_statement, table, config)

    state = state.model_copy(update={
        "votes": votes,
        "vote_logs": vote_lines,
        "phase": "exile"
    })
    state = log_event(state, "vote", "system", {"votes": votes})
    return state


def exile_node(state: GameState, config: RunnableConfig) -> GameState:
    if not state.votes:
        raise ValueError("No votes found.")

    tally = Counter(state.votes.values())
    front_runner, front_runner_votes = tally.most_common(1)[0]

    majority = len(state.alive_players) // 2 + 1
    exiled = front_runner if front_runner_votes >= majority else None

    new_alive = [
        p for p in state.alive_players if p != exiled
    ] if exiled else state.alive_players

    if exiled:
        verdict = f"The majority voted to remove {exiled} from the game."
    else:
        verdict = "No majority. No one was removed."

    tqdm.tqdm.write(verdict)

    state = state.model_copy(update={
        "exiled": exiled,
        "alive_players": new_alive,
        "phase": "check_winner_day"
    })
    state = log_event(state, "exile", "system", {
        "exiled": exiled,
        "vote_tally": dict(tally),
    })
    return state


def check_winner_day_node(state: GameState, config: RunnableConfig) -> GameState:
    winner = _compute_current_winner(state)

    state = state.model_copy(update={
        "winner": winner,
        "phase": "summarize" if winner else "eliminate",
        "step": 0
    })
    state = log_event(state, "check_winner_day", "system", {"winner": winner})
    return state


# --- Wrap-up ----------------------------------------------------------

def summary_node(state: GameState, config: RunnableConfig) -> GameState:
    table = _seated(config)
    recap_lines = []

    for player in state.alive_players:
        summary, raw_reply = table[player].summarize()
        recap_lines.append(f"{player}: {summary} – {raw_reply}")

    deception_summary = generate_deception_summary(state)

    state = state.model_copy(update={
        "summaries": recap_lines,
        "phase": "end"
    })
    state = log_event(state, "summarize", "system", {
        "summaries": recap_lines,
        "deception_summary": deception_summary,
    })
    return state


def end_node(state: GameState, config: RunnableConfig) -> GameState:
    print_header("GAME OVER")
    print_kv("Winner", state.winner)
    print_kv("Final alive players", state.alive_players)
    print_kv("Eliminated", state.eliminated)
    print_kv("Exiled", state.exiled)

    print_subheader("Debate Log")
    for turn in state.debate_log:
        print_kv(turn[0], turn[1], indent=2)

    deception_summary = generate_deception_summary(state)
    print_subheader("Deception Analysis Summary")
    print_kv("Total statements analyzed", deception_summary['total_statements_analyzed'])

    for player, stats in deception_summary['deception_by_player'].items():
        print_subheader(f"{player} ({state.roles.get(player, 'Unknown')})")
        print_kv("Statements made", stats['total_statements'], indent=2)
        print_kv("Self-reported deceptions", stats['self_reported_deceptions'], indent=2)
        print_kv("Peer-detected deceptions", stats['peer_detected_deceptions'], indent=2)
        print_kv("Average suspicion level", f"{stats['average_suspicion']:.2f}", indent=2)

    print_matrix("Final deception scores (observer -> target perception)", state.deception_scores, indent=2)

    observer_metrics = compute_observer_accuracy(state)
    print_subheader("Observer Accuracy by Player")
    for observer, stat in observer_metrics.items():
        print_kv(observer, "", indent=0)
        print_kv("Total", stat.get("total", 0), indent=2)
        print_kv("TP/TN/FP/FN", f"{stat.get('tp',0)}/{stat.get('tn',0)}/{stat.get('fp',0)}/{stat.get('fn',0)}", indent=2)
        print_kv("Accuracy", f"{stat.get('accuracy',0.0):.2f}", indent=2)
        print_kv("Precision", f"{stat.get('precision',0.0):.2f}", indent=2)
        print_kv("Recall", f"{stat.get('recall',0.0):.2f}", indent=2)
        print_kv("F1", f"{stat.get('f1',0.0):.2f}", indent=2)

    paths = getattr(state, "log_paths", {})
    if paths:
        print_subheader("Log Files")
        print_kv("Events (NDJSON)", paths.get('events'), indent=2)
        print_kv("Final State JSON", paths.get('state'), indent=2)
        print_kv("Run Metadata", paths.get('meta'), indent=2)
    return state


graph = StateGraph(GameState)

graph.add_node("eliminate", eliminate_node)
graph.add_node("protect", protect_node)
graph.add_node("unmask", unmask_node)
graph.add_node("resolve_night", night_node)
graph.add_node("check_winner_night", checkwinner_node)
graph.add_node("debate", debate_node)
graph.add_node("vote", vote_node)
graph.add_node("exile", exile_node)
graph.add_node("check_winner_day", check_winner_day_node)
graph.add_node("summarize", summary_node)
graph.add_node("end", end_node)

graph.set_entry_point("eliminate")

# Every node parks the name of the next phase in state.phase; routing is just
# "go wherever the node said to go".
for _phase in ("eliminate", "protect", "unmask", "resolve_night", "check_winner_night",
               "debate", "vote", "exile", "check_winner_day", "summarize"):
    graph.add_conditional_edges(_phase, lambda s: s.phase)
graph.add_edge("end", END)
