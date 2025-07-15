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

