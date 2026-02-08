# Note this a refactored version of a file Obtained copyright license from Google LLC, Apache License. 
# It utilizes similar game style-play but implements a different network and data system via Lang-Chain to ease manual rooting. 
# Copyright 2025 *tbd name*

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from langchain_core.runnables import RunnableConfig
import random, tqdm, json, os
from langgraph.graph import StateGraph, END
from collections import Counter
from Bidding import get_bid, choose_next_speaker
from concurrent.futures import ThreadPoolExecutor
from logs import log_event, print_header, print_subheader, print_kv, print_list, print_matrix
from deception_detection import DeceptionDetector, update_deception_history, compute_observer_accuracy
from datetime import datetime

class GameState(BaseModel):
    round_num: int = 0
    players: List[str] = []  # all players
    alive_players: List[str] = []  # updated after each night/day
    villagers: List[str] = []
    werewolves: List[str] = []
    seer: Optional[str] = None
    doctor: Optional[str] = None
    roles: Dict[str, str] = {}  # {name: role}

    # Logs
    eliminated: Optional[str] = None
    protected: Optional[str] = None
    unmasked: Optional[str] = None
    exiled: Optional[str] = None
    votes: Dict[str, str] = {}  # voter: target
    bids: List[Dict[str, int]] = []  # list per turn
    debate_log: List[List[str]] = []  # [[speaker, dialogue]]
    summaries: List[str] = []

    # Logs from LLM responses
    vote_logs: List[str] = []
    bid_logs: List[str] = []
    summary_logs: List[str] = []
    protect_log: Optional[str] = None
    eliminate_log: Optional[str] = None
    unmask_log: Optional[str] = None

    # Game logs 
    game_logs: List[Dict] = Field(default_factory=list)

    # Deception tracking
    deception_history: Dict[str, List[Dict]] = Field(default_factory=dict)  # {player: [deception_records]}
    deception_scores: Dict[str, Dict[str, float]] = Field(default_factory=dict)  # {observer: {target: score}}
    # New: per-iteration summaries for quick inspection and export
    deception_iterations: List[Dict] = Field(default_factory=list)
    current_speaker: Optional[str] = None
    winner: Optional[Literal["Villagers", "Werewolves"]] = None

    phase: Literal[
        "eliminate", "protect", "unmask", "resolve_night",
        "check_winner_night", "debate", "vote", "exile",
        "check_winner_day", "summarize", "end"
    ] = "eliminate"
    step: int = 0 

    # File logging configuration (optional)
    log_dir: Optional[str] = None
    log_run_id: Optional[str] = None
    log_paths: Dict[str, str] = Field(default_factory=dict)

def analyze_statement_deception(state: GameState, speaker_name: str, statement: str, 
                               player_objects: Dict, config: RunnableConfig) -> GameState:
    """
    Analyze a statement for deception using self-analysis and peer analysis.
    """
    # Initialize deception detector 
    detector = DeceptionDetector(player_objects[speaker_name].llm)
    
    context = f"Round {state.round_num}, Phase: {state.phase}. Alive players: {', '.join(state.alive_players)}."
    if state.debate_log:
        recent_dialogue = state.debate_log[-3:]  # Last 3 statements for context
        context += f" Recent dialogue: {'; '.join([f'{s}: {d}' for s, d in recent_dialogue])}"
    
    # Ask  speaker to analyze their own statement
    self_analysis = detector.analyze_self_deception(speaker_name, statement, context)
    
    # Ask all other alive players to analyze the statement
    other_players = [p for p in state.alive_players if p != speaker_name]
    other_analyses = {}
    
    # Run analyses in parallel
    with ThreadPoolExecutor(max_workers=max(1, len(other_players))) as executor:
        futures = {}
        for observer in other_players:
            # Get observer's history 
            speaker_history = state.deception_history.get(speaker_name, [])
            futures[observer] = executor.submit(
                detector.analyze_other_deception,
                observer, speaker_name, statement, context, speaker_history
            )
        
        for observer, future in futures.items():
            try:
                analysis = future.result()
                analysis["timestamp"] = datetime.utcnow().isoformat()
                other_analyses[observer] = analysis
            except Exception as e:
                # Fallback 
                other_analyses[observer] = {
                    "chain_of_thought": f"Analysis failed: {str(e)}",
                    "is_deceptive": 0,
                    "confidence": 0.0,
                    "deception_type": "none",
                    "reasoning": "Analysis error",
                    "suspicion_level": 0.5,
                    "timestamp": datetime.utcnow().isoformat()
                }
    
    # Update rich history and scores
    state = update_deception_history(state, speaker_name, statement, self_analysis, other_analyses)

    # Compute iteration-level summary metrics
    observer_count = len(other_analyses)
    observer_deceptive_count = sum(1 for a in other_analyses.values() if a.get("is_deceptive", 0) == 1)
    suspicion_levels = {name: a.get("suspicion_level", 0.5) for name, a in other_analyses.items()}
    avg_suspicion = (sum(suspicion_levels.values()) / observer_count) if observer_count else 0.0

    iteration_record = {
        "round": state.round_num,
        "phase": state.phase,
        "step": state.step,
        "speaker": speaker_name,
        "statement": statement,
        "self_analysis": self_analysis,
        "other_analyses": other_analyses,
        "observer_count": observer_count,
        "observer_deceptive_count": observer_deceptive_count,
        "observer_deceptive_fraction": (observer_deceptive_count / observer_count) if observer_count else 0.0,
        "suspicion_levels": suspicion_levels,
        "average_suspicion": avg_suspicion,
        "timestamp": datetime.utcnow().isoformat(),
    }

    state = state.model_copy(update={
        "deception_iterations": state.deception_iterations + [iteration_record]
    })
    
    state = log_event(state, "deception_analysis", speaker_name, {
        "statement": statement,
        "self_analysis": self_analysis,
        "other_analyses": other_analyses,
        "observer_count": observer_count,
        "observer_deceptive_count": observer_deceptive_count,
        "observer_deceptive_fraction": (observer_deceptive_count / observer_count) if observer_count else 0.0,
        "average_suspicion": avg_suspicion,
    })
    
    # Print summary 
    deception_count = sum(1 for analysis in other_analyses.values() if analysis.get("is_deceptive", 0) == 1)
    tqdm.tqdm.write(f"   Deception Analysis: {deception_count}/{len(other_analyses)} observers think it's deceptive")
    
    return state
def generate_deception_summary(state: GameState) -> Dict:
    """
    Generate a summary of deception patterns and perceptions throughout the game.
    """
    summary = {
        "total_statements_analyzed": 0,
        "deception_by_player": {},
        "final_deception_scores": state.deception_scores,
        "deception_patterns": {}
    }
    
    # Analyze deception history
    for player, history in state.deception_history.items():
        player_summary = {
            "total_statements": len(history),
            "self_reported_deceptions": 0,
            "peer_detected_deceptions": 0,
            "average_suspicion": 0.0
        }
        
        total_suspicion = 0
        suspicion_count = 0
        
        for record in history:
            # Count self-reported deceptions
            if record["self_analysis"].get("is_deceptive", 0) == 1:
                player_summary["self_reported_deceptions"] += 1
            
            # Count peer-detected deceptions
            for peer_analysis in record["other_analyses"].values():
                if peer_analysis.get("is_deceptive", 0) == 1:
                    player_summary["peer_detected_deceptions"] += 1
                
                # Track suspicion levels
                suspicion = peer_analysis.get("suspicion_level", 0.5)
                total_suspicion += suspicion
                suspicion_count += 1
        
        if suspicion_count > 0:
            player_summary["average_suspicion"] = total_suspicion / suspicion_count
            
        summary["deception_by_player"][player] = player_summary
        summary["total_statements_analyzed"] += len(history)
    
    return summary
def _compute_current_winner(state: GameState) -> Optional[Literal["Villagers", "Werewolves"]]:
    """Compute winner based on current alive players.

    Villagers win if no Werewolves remain.
    Werewolves win if Werewolves >= Villagers.
    Otherwise, no winner yet.
    """
    wolves_alive = [p for p in state.werewolves if p in state.alive_players]
    villagers_alive = [p for p in state.alive_players if p not in wolves_alive]

    if not wolves_alive:
        return "Villagers"
    if len(wolves_alive) >= len(villagers_alive):
        return "Werewolves"
    return None
def eliminate_node(state: GameState, config: RunnableConfig) -> GameState:
    player_objects = config.get("configurable", {}).get("player_objects", {})
    # Reset night-phase fields so stale values from prior rounds don't persist
    state = state.model_copy(update={
        "eliminated": None,
        "protected": None,
        "unmasked": None,
        "round_num": state.round_num + 1,
    })
    # Early terminal check: if a winner is already determined, end now
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

    alive_wolves = [
        name for name in state.werewolves if name in state.alive_players
    ]
    if not alive_wolves:
        # No werewolves left; skip elimination and proceed with night flow
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
    eliminated, log = player_objects[acting_wolf].eliminate(state.alive_players)

    if not eliminated:
        raise ValueError(f"{acting_wolf} failed to return a target.")

    tqdm.tqdm.write(f"{acting_wolf} eliminated {eliminated}")


   # temp for sharing who was eliminated during the night
    for wolf in alive_wolves:
        player_objects[wolf]._add_observation(
            f"During the night, we decided to eliminate {eliminated}."
        )

    # Convert log to string if it's a dict
    log_str = str(log) if isinstance(log, dict) else log
    
    state = state.model_copy(update={
        "eliminated": eliminated,
        "eliminate_log": log_str,
        "phase": "protect"
    })
    state = log_event(state, "eliminate", acting_wolf, {
    "target": eliminated,
    "raw_output": log
    })
    
    return state
    
def protect_node(state: GameState, config: RunnableConfig) -> GameState:
    """Doctor chooses a player to save during the same night."""
    player_objects = config.get("configurable", {}).get("player_objects", {})
    doctor_name = state.doctor

    # check if doctor was killed
    if doctor_name not in state.alive_players:
        return state.model_copy(update={"protected": None, "phase": "unmask"})

    protect_target, log = player_objects[doctor_name].save(state.alive_players)

    if not protect_target:
        raise ValueError(f"{doctor_name} failed to specify a protection target.")

    tqdm.tqdm.write(f"{doctor_name} protected {protect_target}")

    # Convert log to string if it's a dict
    log_str = str(log) if isinstance(log, dict) else log
    
    state =  state.model_copy(update={
        "protected": protect_target,
        "protect_log": log_str,
        "phase": "unmask"
    })

    state = log_event(state, "protect", doctor_name, {
    "target": protect_target,
    "raw_output": log
    })

    return state
    
def unmask_node(state: GameState, config: RunnableConfig) -> GameState:
    """Seer investigates one player each night."""
    player_objects = config.get("configurable", {}).get("player_objects", {})
    seer_name = state.seer

    # check if seer is dead
    if seer_name not in state.alive_players:
        return state.model_copy(update={"phase": "resolve_night"})

    target, log = player_objects[seer_name].unmask(state.alive_players)
    if not target:
        raise ValueError(f"{seer_name} failed to return a target.")

    # reveal to seer 
    role_revealed = state.roles[target]
    player_objects[seer_name].reveal_and_update(target, role_revealed)

    # Convert log to string if it's a dict
    log_str = str(log) if isinstance(log, dict) else log
    
    state =  state.model_copy(update={
        "unmasked": target,
        "unmask_log": log_str,
        "phase": "resolve_night"
    })

    state = log_event(state, "unmask", seer_name, {
    "target": target,
    "revealed_role": state.roles[target],
    "raw_output": log
    })
    
    return state
    
def night_node(state: GameState, config: RunnableConfig) -> GameState:
    """Apply elimination/protection outcome and broadcast announcement."""
    if state.eliminated and state.eliminated != state.protected:
        # death of victim
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

    state = log_event(state, "resolve_night", "system", {
    "announcement": announcement
    })
    
    return state
    
def checkwinner_node(state: GameState, config: RunnableConfig) -> GameState:
    """Return to day phase or finish game if a faction wins."""
    winner = _compute_current_winner(state)

    next_phase = "debate" if not winner else "summarize"  # ends/explains  if completed

    state = state.model_copy(update={
        "winner": winner,
        "phase": next_phase,
        "step": 0        
    })

    state = log_event(state, "check_winner_night", "system", {
        "winner": winner
    })
    return state
    
def debate_node(state: GameState, config: RunnableConfig) -> GameState:
    player_objects = config.get("configurable", {}).get("player_objects", {})
    MAX_DEBATE_TURNS = config.get("configurable", {}).get("MAX_DEBATE_TURNS", 6)

    dialogue_history = "\n".join([f"{s}: {t}" for s, t in state.debate_log])
    last_speaker = state.debate_log[-1][0] if state.debate_log else None

    alive_players = [p for p in state.alive_players if p != last_speaker]
    bid_logs = []
    bid_dict = {}

    # Run bids in parallel
    with ThreadPoolExecutor(max_workers=len(alive_players)) as executor:
        futures = {name: executor.submit(get_bid, name, dialogue_history) for name in alive_players}
        for name, future in futures.items():
            bid, raw_output = future.result()
            bid_dict[name] = bid
            bid_logs.append(f"{name} bid {bid} – {raw_output}")

    next_speaker = choose_next_speaker(bid_dict, dialogue_history)
    dialogue, log = player_objects[next_speaker].debate(state.debate_log)
    if not dialogue:
        raise ValueError(f"{next_speaker} failed to produce a debate line.")

    tqdm.tqdm.write(f"{next_speaker}: {dialogue}")

    # DECEPTION ANALYSIS: Analyze the statement made by the speaker
    state = analyze_statement_deception(state, next_speaker, dialogue, player_objects, config)
    
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
    "raw_output": log
    })
    
    return state

def vote_node(state: GameState, config: RunnableConfig) -> GameState:
    player_objects = config.get("configurable", {}).get("player_objects", {})
    votes = {}
    logs = []

    for voter in state.alive_players:
        
        vote, log = player_objects[voter].vote(state.deception_scores)
        votes[voter] = vote
        logs.append(f"{voter} voted for {vote} – {log}")
       
        # DECEPTION ANALYSIS: Analyze voting statements (if they contain reasoning)
        # Note: Votes might not always warrant deception analysis unless they include reasoning
        vote_statement = f"I vote for {vote}"
        if "reasoning" in log and log.get("reasoning"):
            vote_statement += f" because {log.get('reasoning', '')}"
            state = analyze_statement_deception(state, voter, vote_statement, player_objects, config)
    state = state.model_copy(update={
        "votes": votes,
        "vote_logs": logs,
        "phase": "exile"
    })

    state = log_event(state, "vote", "system", {
    "votes": votes
    })
    
    return state
    
def exile_node(state: GameState, config: RunnableConfig) -> GameState:
    if not state.votes:
        raise ValueError("No votes found.")

    tally = Counter(state.votes.values())
    top_candidate, count = tally.most_common(1)[0]

    majority = len(state.alive_players) // 2 + 1
    exiled = top_candidate if count >= majority else None

    new_alive = [
        p for p in state.alive_players if p != exiled
    ] if exiled else state.alive_players

    if exiled:
        msg = f"The majority voted to remove {exiled} from the game."
    else:
        msg = "No majority. No one was removed."

    tqdm.tqdm.write(msg)

    state = state.model_copy(update={
        "exiled": exiled,
        "alive_players": new_alive,
        "phase": "check_winner_day"
    })

    state = log_event(state, "exile", "system", {
    "exiled": exiled,
    "vote_tally": dict(tally)
    })

    return state

def check_winner_day_node(state: GameState, config: RunnableConfig) -> GameState:
    winner = _compute_current_winner(state)

    state = state.model_copy(update={
        "winner": winner,
        "phase": "summarize" if winner else "eliminate",
        "step": 0  
    })

    state = log_event(state, "check_winner_day", "system", {
    "winner": winner
    })
    
    return state

def summary_node(state: GameState, config: RunnableConfig) -> GameState:
    player_objects = config.get("configurable", {}).get("player_objects", {})
    logs = []

    for player in state.alive_players:
        summary, log = player_objects[player].summarize()
        logs.append(f"{player}: {summary} – {log}")
    
    # Generate deception summary
    deception_summary = generate_deception_summary(state)

    state = state.model_copy(update={
        "summaries": logs,
        "phase": "end"
    })

    state = log_event(state, "summarize", "system", {
    "summaries": logs,
    "deception_summary": deception_summary
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

    # Observer accuracy
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

    # Print where logs were saved (if enabled)
    paths = getattr(state, "log_paths", {})
    if paths:
        print_subheader("Log Files")
        print_kv("Events (NDJSON)", paths.get('events'), indent=2)
        print_kv("Final State JSON", paths.get('state'), indent=2)
        print_kv("Run Metadata", paths.get('meta'), indent=2)
    return state

#game state LangChain graph

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

# Routing 
graph.add_conditional_edges("eliminate", lambda s: s.phase)
graph.add_conditional_edges("protect", lambda s: s.phase)
graph.add_conditional_edges("unmask", lambda s: s.phase)
graph.add_conditional_edges("resolve_night", lambda s: s.phase)
graph.add_conditional_edges("check_winner_night", lambda s: s.phase)
graph.add_conditional_edges("debate", lambda s: s.phase)
graph.add_conditional_edges("vote", lambda s: s.phase)
graph.add_conditional_edges("exile", lambda s: s.phase)
graph.add_conditional_edges("check_winner_day", lambda s: s.phase)
graph.add_conditional_edges("summarize", lambda s: s.phase)
graph.add_edge("end", END)