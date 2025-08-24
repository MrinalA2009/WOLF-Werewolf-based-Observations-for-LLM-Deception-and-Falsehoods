import os
import json
import threading
from datetime import datetime
from typing import Dict, Optional

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
                fidx.write(json.dumps({"run_id": run_id, "meta_path": paths["meta"], "events_path": paths["events"], "state_path": paths["state"]}) + "\n")
        except FileNotFoundError:
            # Ensure parent exists and retry
            _ensure_dirs(os.path.dirname(paths["index"]))
            with open(paths["index"], "a", encoding="utf-8") as fidx:
                fidx.write(json.dumps({"run_id": run_id, "meta_path": paths["meta"], "events_path": paths["events"], "state_path": paths["state"]}) + "\n")

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


# ---------------------------
# Console formatting helpers
# ---------------------------

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