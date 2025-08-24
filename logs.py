import os
import json
import threading
from datetime import datetime
from typing import Dict, Optional, List
from statistics import mean

# Avoid circular imports: `deception_detection` does not import this module
try:
    from deception_detection import compute_observer_accuracy
except Exception:
    compute_observer_accuracy = None  # type: ignore

# global lock to ensure concurrent threads don't corrupt log files
_FILE_LOCK = threading.Lock()


def _ensure_dirs(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _default_run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")


def init_logging_state(state, log_dir: Optional[str] = None, enable_file_logging: bool = True):
    """
    Initialize per-run logging paths on the game state. Returns a new updated state.

    - Creates `log_dir` if provided (defaults to ./logs) and generates a unique run_id
    - Prepares three files:
      - events_path: NDJSON stream of event entries (one per line)
      - state_path: full-game-state JSON snapshot (written at end, can be updated incrementally)
      - meta_path: run metadata (players, roles, model, timestamps)
    """
    if not enable_file_logging:
        return state

    base_dir = log_dir or os.getenv("LOG_DIR", "./logs")
    _ensure_dirs(base_dir)

    run_id = _default_run_id()
    folder = os.path.join(base_dir, run_id)
    _ensure_dirs(folder)

    paths = {
        "folder": folder,
        "events": os.path.join(folder, "events.ndjson"),
        "state": os.path.join(folder, "game_state.json"),
        "meta": os.path.join(folder, "run_meta.json"),
        "metrics": os.path.join(folder, "final_metrics.json"),
        "index": os.path.join(base_dir, "index.jsonl"),  # global index of runs
    }

    # Write meta and append to index
    meta = {
        "run_id": run_id,
        "created_at_utc": datetime.utcnow().isoformat(),
        "players": getattr(state, "players", []),
        "roles": getattr(state, "roles", {}),
        "model": os.getenv("MODEL_NAME", None),
        "config": {
            "max_debate_turns": getattr(state, "step", None),
        },
    }
    with _FILE_LOCK:
        with open(paths["meta"], "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        # Append an index record for easy discovery
        try:
            with open(paths["index"], "a", encoding="utf-8") as fidx:
                fidx.write(json.dumps({
                    "run_id": run_id,
                    "meta_path": paths["meta"],
                    "events_path": paths["events"],
                    "state_path": paths["state"],
                    "metrics_path": paths["metrics"],
                }) + "\n")
        except FileNotFoundError:
            # Ensure parent exists and retry
            _ensure_dirs(os.path.dirname(paths["index"]))
            with open(paths["index"], "a", encoding="utf-8") as fidx:
                fidx.write(json.dumps({
                    "run_id": run_id,
                    "meta_path": paths["meta"],
                    "events_path": paths["events"],
                    "state_path": paths["state"],
                    "metrics_path": paths["metrics"],
                }) + "\n")

    return state.model_copy(update={
        "log_dir": base_dir,
        "log_run_id": run_id,
        "log_paths": paths,
    })


def _persist_event(entry: Dict, events_path: str) -> None:
    line = json.dumps(entry, ensure_ascii=False)
    with _FILE_LOCK:
        with open(events_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def _persist_full_state(state, state_path: str) -> None:
    serializable = json.loads(state.model_dump_json())  # pydantic safe dump
    with _FILE_LOCK:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)


def write_final_state(state) -> None:
    """Write the final game state JSON snapshot if logging is configured."""
    paths = getattr(state, "log_paths", None)
    if not paths or not paths.get("state"):
        return
    _persist_full_state(state, paths["state"])


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

        avg_susp = mean(suspicion_values) if suspicion_values else 0.0
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
        "global_avg_suspicion": (mean([tp["average_suspicion"] for tp in timepoints]) if timepoints else 0.0),
        "global_avg_observer_deceptive_fraction": (mean([tp["observer_deceptive_fraction"] for tp in timepoints]) if timepoints else 0.0),
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
        if compute_observer_accuracy is not None:
            accuracy_by_observer = compute_observer_accuracy(state)
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


def log_event(state, event_type: str, actor: Optional[str], content: Dict):
    """
    Create an event entry, append into state.game_logs, and if configured, stream to NDJSON.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "round": state.round_num,
        "step": state.step,
        "phase": state.phase,
        "event": event_type,
        "actor": actor,
        "details": content,
    }

    # Stream to NDJSON if configured
    paths = getattr(state, "log_paths", None)
    if paths and paths.get("events"):
        try:
            _persist_event(entry, paths["events"])
        except Exception:
            # Do not break the game on logging errors
            pass

    # Optionally, we could persist incremental full-state snapshots. Keep lightweight by default.
    return state.model_copy(update={
        "game_logs": state.game_logs + [entry]
    })

# Formatting
def _line(char: str = "-", width: int = 60) -> str:
    return char * width


def print_header(title: str) -> None:
    print()
    print(_line("="))
    print(title)
    print(_line("="))


def print_subheader(title: str) -> None:
    print()
    print(title)
    print(_line("-"))


def print_kv(label: str, value, indent: int = 0) -> None:
    prefix = " " * indent
    print(f"{prefix}{label}: {value}")


def print_list(items, indent: int = 2) -> None:
    prefix = " " * indent
    for item in items:
        print(f"{prefix}- {item}")


def print_matrix(title: str, matrix: Dict[str, Dict[str, float]], indent: int = 2) -> None:
    print_subheader(title)
    for row_key, cols in matrix.items():
        parts = [f"{col}={val:.2f}" for col, val in cols.items()]
        print_kv(row_key, ", ".join(parts), indent)