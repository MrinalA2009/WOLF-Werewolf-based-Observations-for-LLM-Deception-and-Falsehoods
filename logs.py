from datetime import datetime
from typing import Dict, Optional

def log_event(state, event_type: str, actor: Optional[str], content: Dict):
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
