from datetime import datetime

def log_event(state: GameState, event_type: str, actor: Optional[str], content: Dict) -> GameState:
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "round": state.round_num,
        "step": state.step,
        "phase": state.phase,
        "event": event_type,
        "actor": actor,
        "details": content
    }
    return state.model_copy(update={
        "game_logs": state.game_logs + [entry]
    })
