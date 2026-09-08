# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Mrinal Agarwal, Saad Rana, and the WOLF authors
# The game loop is derived from Google's Werewolf Arena (Apache-2.0); see NOTICE.

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


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
