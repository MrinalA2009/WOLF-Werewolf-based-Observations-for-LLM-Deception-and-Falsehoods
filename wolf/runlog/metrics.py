# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Mrinal Agarwal, Saad Rana, and the WOLF authors

import json
from datetime import datetime
from typing import Dict, List, Optional

from wolf.runlog.events import _FILE_LOCK

# NOTE: `mean` and `compute_observer_accuracy` are referenced below but deliberately
# NOT imported. That is a real, pre-existing bug (write_final_metrics raises
# NameError whenever a game has any deception history) preserved verbatim per the
# cleanup's no-logic-change rule. See KNOWN_ISSUES.md, item 1.


def _summarize_deception_by_player(state) -> Dict[str, Dict[str, float]]:
    """Aggregate per-player deception counts and average suspicion from state.deception_history.

    Returns a mapping of player name to summary dict with keys:
    total_statements, self_reported_deceptions, peer_detected_deceptions, average_suspicion
    """
    summary: Dict[str, Dict[str, float]] = {}
    history: Dict[str, List[Dict]] = getattr(state, "deception_history", {}) or {}

    for player, records in history.items():
        total_statements = len(records)
        self_deceptions = 0
        peer_detected = 0
        suspicion_values: List[float] = []

        for rec in records:
            if (rec.get("self_analysis", {}) or {}).get("is_deceptive", 0) == 1:
                self_deceptions += 1
            for peer in (rec.get("other_analyses", {}) or {}).values():
                if peer.get("is_deceptive", 0) == 1:
                    peer_detected += 1
                susp = float(peer.get("suspicion_level", 0.5))
                suspicion_values.append(susp)

        avg_susp = mean(suspicion_values) if suspicion_values else 0.0  # noqa: F821
        summary[player] = {
            "total_statements": total_statements,
            "self_reported_deceptions": self_deceptions,
            "peer_detected_deceptions": peer_detected,
            "average_suspicion": avg_susp,
        }

    return summary


def _compute_trends(state) -> Dict:
    """Compute suspicion and deception-flagging trends over time and by round from state.deception_iterations."""
    iterations: List[Dict] = getattr(state, "deception_iterations", []) or []
    timepoints: List[Dict] = []
    by_round: Dict[str, Dict[str, float]] = {}

    for idx, it in enumerate(iterations):
        round_num = int(it.get("round", 0))
        avg_susp = float(it.get("average_suspicion", 0.0))
        frac_flag = float(it.get("observer_deceptive_fraction", 0.0))
        timepoints.append({
            "t": idx,
            "round": round_num,
            "phase": it.get("phase"),
            "speaker": it.get("speaker"),
            "average_suspicion": avg_susp,
            "observer_deceptive_fraction": frac_flag,
        })

        key = str(round_num)
        r = by_round.setdefault(key, {"avg_suspicion_sum": 0.0, "avg_flag_sum": 0.0, "n": 0})
        r["avg_suspicion_sum"] += avg_susp
        r["avg_flag_sum"] += frac_flag
        r["n"] += 1

    by_round_final: Dict[str, Dict[str, float]] = {}
    for rnd, agg in by_round.items():
        n = agg.get("n", 0)
        by_round_final[rnd] = {
            "num_statements": n,
            "avg_suspicion": (agg["avg_suspicion_sum"] / n) if n else 0.0,
            "avg_observer_deceptive_fraction": (agg["avg_flag_sum"] / n) if n else 0.0,
        }

    overall = {
        "num_timepoints": len(timepoints),
        "global_avg_suspicion": (mean([tp["average_suspicion"] for tp in timepoints]) if timepoints else 0.0),  # noqa: F821
        "global_avg_observer_deceptive_fraction": (mean([tp["observer_deceptive_fraction"] for tp in timepoints]) if timepoints else 0.0),  # noqa: F821
    }

    return {
        "timepoints": timepoints,
        "by_round": by_round_final,
        "overall": overall,
    }


def compute_final_metrics(state) -> Dict:
    """Compute organized final metrics for the run without raw prompts or model outputs."""
    run_id = getattr(state, "log_run_id", None)
    roles = getattr(state, "roles", {}) or {}
    players = getattr(state, "players", []) or []
    created_at = datetime.utcnow().isoformat()

    deception_by_player = _summarize_deception_by_player(state)
    trends = _compute_trends(state)

    # Cross-perception scores as of the end
    deception_scores = getattr(state, "deception_scores", {}) or {}

    # Accuracy by observer (if available)
    accuracy_by_observer: Dict = {}
    try:
        if compute_observer_accuracy is not None:  # noqa: F821
            accuracy_by_observer = compute_observer_accuracy(state)  # noqa: F821
    except Exception:
        accuracy_by_observer = {}

    total_statements = sum(p["total_statements"] for p in deception_by_player.values()) if deception_by_player else 0

    metrics = {
        "schema_version": 1,
        "run": {
            "run_id": run_id,
            "created_at_utc": created_at,
            "num_players": len(players),
            "num_alive_end": len(getattr(state, "alive_players", []) or []),
            "winner": getattr(state, "winner", None),
        },
        "roster": {
            "players": players,
            "roles": roles,
        },
        "summary": {
            "total_statements_analyzed": total_statements,
        },
        "deception": {
            "per_player": deception_by_player,
            "cross_perception_scores": deception_scores,
            "accuracy_by_observer": accuracy_by_observer,
            "trends": trends,
        },
    }

    return metrics


def write_final_metrics(state) -> Optional[str]:
    """Write a clean, organized final-metrics JSON file. Returns path if written."""
    paths = getattr(state, "log_paths", None)
    if not paths or not paths.get("metrics"):
        return None

    metrics = compute_final_metrics(state)
    with _FILE_LOCK:
        with open(paths["metrics"], "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
    return paths["metrics"]
