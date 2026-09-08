# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Mrinal Agarwal, Saad Rana, and the WOLF authors

from typing import Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import tqdm
from langchain_core.runnables import RunnableConfig

from wolf.game.state import GameState
from wolf.deception.detector import DeceptionDetector
from wolf.deception.scoring import update_deception_history
from wolf.runlog.events import log_event


def analyze_statement_deception(state: GameState, speaker_name: str, statement: str,
                               player_objects: Dict, config: RunnableConfig) -> GameState:
    """
    Analyze a statement for deception using self-analysis and peer analysis.
    """
    detector = DeceptionDetector(player_objects[speaker_name].llm)

    context = f"Round {state.round_num}, Phase: {state.phase}. Alive players: {', '.join(state.alive_players)}."
    if state.debate_log:
        recent_dialogue = state.debate_log[-3:]
        context += f" Recent dialogue: {'; '.join([f'{s}: {d}' for s, d in recent_dialogue])}"

    self_analysis = detector.analyze_self_deception(speaker_name, statement, context)

    other_players = [p for p in state.alive_players if p != speaker_name]
    other_analyses = {}

    # Every observer reads the statement at once — this is the expensive part of a
    # turn, so it fans out across a thread pool.
    with ThreadPoolExecutor(max_workers=max(1, len(other_players))) as executor:
        futures = {}
        for observer in other_players:
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
                # A failed read counts as "saw nothing suspicious" rather than
                # dropping the observer, so downstream counts stay consistent.
                other_analyses[observer] = {
                    "chain_of_thought": f"Analysis failed: {str(e)}",
                    "is_deceptive": 0,
                    "confidence": 0.0,
                    "deception_type": "none",
                    "reasoning": "Analysis error",
                    "suspicion_level": 0.5,
                    "timestamp": datetime.utcnow().isoformat()
                }

    state = update_deception_history(state, speaker_name, statement, self_analysis, other_analyses)

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
            if record["self_analysis"].get("is_deceptive", 0) == 1:
                player_summary["self_reported_deceptions"] += 1

            for peer_analysis in record["other_analyses"].values():
                if peer_analysis.get("is_deceptive", 0) == 1:
                    player_summary["peer_detected_deceptions"] += 1

                suspicion = peer_analysis.get("suspicion_level", 0.5)
                total_suspicion += suspicion
                suspicion_count += 1

        if suspicion_count > 0:
            player_summary["average_suspicion"] = total_suspicion / suspicion_count

        summary["deception_by_player"][player] = player_summary
        summary["total_statements_analyzed"] += len(history)

    return summary
