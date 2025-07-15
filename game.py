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
import random
import tqdm
from langgraph.graph import StateGraph, END

class GameState(BaseModel):
    round_num: int = 0
    players: List[str] = []  # all players
    alive_players: List[str] = []  # updated after each night/day
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

    current_speaker: Optional[str] = None
    winner: Optional[Literal["Villagers", "Werewolves"]] = None

    phase: Literal[
        "eliminate", "protect", "unmask", "resolve_night",
        "check_winner_night", "debate", "vote", "exile",
        "check_winner_day", "summarize"
    ] = "eliminate"
    step: int = 0 

def eliminate_node(state: GameState, config: RunnableConfig) -> GameState:
    player_objects = config["player_objects"]

    alive_wolves = [
        name for name in state.werewolves if name in state.alive_players
    ]
    if not alive_wolves:
        raise ValueError("No werewolves left to eliminate.")

    acting_wolf = random.choice(alive_wolves)
    eliminated, log = player_objects[acting_wolf].eliminate()

    if not eliminated:
        raise ValueError(f"{acting_wolf} failed to return a target.")

    tqdm.tqdm.write(f"{acting_wolf} eliminated {eliminated}")

   # temp for sharing who was eliminated during the night
    for wolf in alive_wolves:
        player_objects[wolf]._add_observation(
            f"During the night, we decided to eliminate {eliminated}."
        )

    return state.model_copy(update={
        "eliminated": eliminated,
        "eliminate_log": log,
        "phase": "protect"
    })
def protect_node(state: GameState, config: RunnableConfig) -> GameState:
    """Doctor chooses a player to save during the same night."""
    player_objects = config["player_objects"]
    doctor_name = state.doctor

    # check if doctor was killed 
    if doctor_name not in state.alive_players:
        return state.model_copy(update={"phase": "unmask"})

    protect_target, log = player_objects[doctor_name].save()

    if not protect_target:
        raise ValueError(f"{doctor_name} failed to specify a protection target.")

    tqdm.tqdm.write(f"{doctor_name} protected {protect_target}")

    return state.model_copy(update={
        "protected": protect_target,
        "protect_log": log,
        "phase": "unmask"
    })
def unmask_node(state: GameState, config: RunnableConfig) -> GameState:
    """Seer investigates one player each night."""
    player_objects = config["player_objects"]
    seer_name = state.seer

    # check if seer is dead
    if seer_name not in state.alive_players:
        return state.model_copy(update={"phase": "resolve_night"})

    target, log = player_objects[seer_name].unmask()
    if not target:
        raise ValueError(f"{seer_name} failed to return a target.")

    # reveal to seer 
    role_revealed = state.roles[target]
    player_objects[seer_name].reveal_and_update(target, role_revealed)

    return state.model_copy(update={
        "unmasked": target,
        "unmask_log": log,
        "phase": "resolve_night"
    })
def night_node(state: GameState, _: RunnableConfig) -> GameState:
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

    return state.model_copy(update={
        "alive_players": new_alive,
        "phase": "check_winner_night"
    })
def checkwinner_node(state: GameState, _: RunnableConfig) -> GameState:
    """Return to day phase or finish game if a faction wins."""
    wolves_alive = [p for p in state.werewolves if p in state.alive_players]
    villagers_alive = [p for p in state.alive_players if p not in wolves_alive]

    if not wolves_alive:
        winner = "Villagers"
    elif len(wolves_alive) >= len(villagers_alive):
        winner = "Werewolves"
    else:
        winner = None

    next_phase = "debate" if not winner else "summarize"  # ends/explains  if completed

    return state.model_copy(update={
        "winner": winner,
        "phase": next_phase,
        "step": 0        
    })
#game state LangChain graph

graph = StateGraph(GameState)

graph.add_node("eliminate", eliminate_node)
graph.add_node("protect", protect_node)
graph.add_node("unmask", unmask_node)
graph.add_node("resolve_night", resolve_night_node)
graph.add_node("check_winner_night", check_winner_node)
graph.add_node("debate", debate_node)
graph.add_node("vote", vote_node)
graph.add_node("exile", exile_node)
graph.add_node("check_winner_day", check_winner_node)
graph.add_node("summarize", summarize_node)
graph.add_node("end", end_node)

# Entry point
graph.set_entry_point("eliminate")

# Routing 
graph.add_conditional_edges("eliminate", lambda s: s.phase)
graph.add_conditional_edges("protect", lambda s: s.phase)
graph.add_conditional_edges("unmask", lambda s: s.phase)
graph.add_conditional_edges("resolve_night", lambda s: s.phase)
graph.add_conditional_edges("check_winner_night", lambda s: s.phase)
graph.add_conditional_edges("debate", lambda s: "vote" if s.step >= MAX_DEBATE_TURNS else "debate")
graph.add_conditional_edges("vote", lambda s: "exile")
graph.add_conditional_edges("exile", lambda s: "check_winner_day")
graph.add_conditional_edges("check_winner_day", lambda s: "summarize" if s.winner else "eliminate")
graph.add_conditional_edges("summarize", lambda s: "end")
graph.add_edge("end", END)




