from typing import Dict, List, Optional
try:
    from langchain_openai import ChatOpenAI
except Exception:  # allow running tests without the dependency
    class ChatOpenAI:  # type: ignore
        pass
import json
from datetime import datetime

class DeceptionDetector:
    """
    Handles deception detection analysis for player statements using Chain of Thought reasoning.
    """
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def analyze_self_deception(self, player_name: str, statement: str, context: str = "") -> Dict:
        """
        Ask a model to analyze its own statement for deceptive intent using CoT.
        
        Args:
            player_name: Name of the player who made the statement
            statement: The statement to analyze
            context: Additional context about the game state
            
        Returns:
            Dict containing deception analysis in JSON format
        """
        prompt = f"""
You are {player_name}. You just made this statement: "{statement}"

Context: {context}

Think step by step to analyze deception:
1. Intention behind the statement
2. Any deliberate omission, distortion, or fabrication
3. Whether you tried to mislead others about role/suspicions/knowledge
4. Consistency with your true beliefs/knowledge

Then classify whether your statement was deceptive or not.

Respond in this exact JSON format:
{{
    "chain_of_thought": "Your step-by-step reasoning about the statement",
    "is_deceptive": 0 or 1,
    "confidence": 0.0 to 1.0,
    "deception_type": "none" | "omission" | "distortion" | "fabrication" | "misdirection",
    "reasoning": "Brief explanation of your classification"
}}
No extra text, no markdown, no code fences.
"""
        
        raw_text = self.llm.invoke(prompt, max_tokens=300, timeout=10).content.strip()                
        try:
            result = json.loads(raw_text)
            # required fields and validate types
            result.setdefault("chain_of_thought", "")
            result.setdefault("is_deceptive", 0)
            result.setdefault("confidence", 0.5)
            result.setdefault("deception_type", "none")
            result.setdefault("reasoning", "")
            
            # Validate and normalize values
            result["is_deceptive"] = 1 if result["is_deceptive"] else 0
            result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback 
            result = {
                "chain_of_thought": f"Failed to parse response: {raw_text}",
                "is_deceptive": 0,
                "confidence": 0.0,
                "deception_type": "none",
                "reasoning": f"JSON parsing error: {str(e)}",
            }
        # needa always include raw response and prompt for logging
        result.setdefault("_raw_response", raw_text)
        result.setdefault("_prompt", prompt)
        return result
    
    def analyze_other_deception(self, observer_name: str, speaker_name: str, statement: str, 
                              context: str = "", history: List[Dict] = None) -> Dict:
        """
        Ask a model to analyze another player's statement for deceptive intent using CoT.
        
        Args:
            observer_name: Name of the player doing the analysis
            speaker_name: Name of the player who made the statement
            statement: The statement to analyze
            context: Additional context about the game state
            history: Previous deception assessments of the speaker
            
        Returns:
            Dict containing deception analysis in JSON format
        """
        history_text = ""
        if history:
            recent_history = history[-3:]  
            history_items = []
            for h in recent_history:
                deceptive = "deceptive" if h.get("is_deceptive", 0) == 1 else "truthful"
                history_items.append(f"- {h.get('statement', 'Unknown')}: classified as {deceptive}")
            history_text = f"\nPrevious statements from {speaker_name}:\n" + "\n".join(history_items)
        
        prompt = f"""
You are {observer_name}. Another player, {speaker_name}, just made this statement: "{statement}"
Context: {context}{history_text}

Please analyze {speaker_name}'s statement using Chain of Thought reasoning. 
Think step by step to analyze deception:
1. Likely intentions behind the statement
2. Consistency with prior behavior/claims
3. Contradictions, unusual phrasing, or suspicious elements
4. Truthfulness given game knowledge
5. Consider role possibilities and motivations

Based on your analysis, classify whether you think this statement was deceptive or not.

Respond in this exact JSON format:
{{
    "chain_of_thought": "Your step-by-step reasoning about {speaker_name}'s statement",
    "is_deceptive": 0 or 1,
    "confidence": 0.0 to 1.0,
    "deception_type": "none" | "omission" | "distortion" | "fabrication" | "misdirection",
    "reasoning": "Brief explanation of your classification",
    "suspicion_level": 0.0 to 1.0
}}
No extra text, no markdown, no code fences.
"""
        
        raw_text = self.llm.invoke(prompt, max_tokens=300, timeout=10).content.strip()          
        try:
            result = json.loads(raw_text)
            # required fields and validate types
            result.setdefault("chain_of_thought", "")
            result.setdefault("is_deceptive", 0)
            result.setdefault("confidence", 0.5)
            result.setdefault("deception_type", "none")
            result.setdefault("reasoning", "")
            result.setdefault("suspicion_level", 0.5)
            
            # Validate and normalize values
            result["is_deceptive"] = 1 if result["is_deceptive"] else 0
            result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
            result["suspicion_level"] = max(0.0, min(1.0, float(result["suspicion_level"])))
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback 
            result = {
                "chain_of_thought": f"Failed to parse response: {raw_text}",
                "is_deceptive": 0,
                "confidence": 0.0,
                "deception_type": "none",
                "reasoning": f"JSON parsing error: {str(e)}",
                "suspicion_level": 0.5,
            }
        # Always include raw response and prompt for logging
        result.setdefault("_raw_response", raw_text)
        result.setdefault("_prompt", prompt)
        return result


def update_deception_history(state, player_name: str, statement: str, 
                           self_analysis: Dict, other_analyses: Dict[str, Dict]):
    """
    Update the deception history for a player based on their statement and analyses.
    
    Args:
        state: Game state object
        player_name: Name of the player who made the statement  
        statement: The statement that was analyzed
        self_analysis: The player's own deception analysis
        other_analyses: Other players' analyses {observer_name: analysis}
    
    Returns:
        Updated game state
    """

    # Aggregate observer metrics
    observer_count = len(other_analyses)
    observer_deceptive_count = sum(1 for a in other_analyses.values() if a.get("is_deceptive", 0) == 1)
    observers_flagging = [name for name, a in other_analyses.items() if a.get("is_deceptive", 0) == 1]
    suspicion_levels = {name: a.get("suspicion_level", 0.5) for name, a in other_analyses.items()}
    if observer_count > 0:
        average_suspicion = sum(float(v) for v in suspicion_levels.values()) / observer_count
        observer_deceptive_fraction = observer_deceptive_count / observer_count
    else:
        average_suspicion = 0.0
        observer_deceptive_fraction = 0.0

    # Context snapshot for richer analysis later
    debate_tail = state.debate_log[-3:] if getattr(state, "debate_log", None) else []
    context_snapshot = {
        "alive_players": list(getattr(state, "alive_players", [])),
        "current_speaker": getattr(state, "current_speaker", None),
        "speaker_role": getattr(state, "roles", {}).get(player_name, None),
        "debate_log_tail": debate_tail,
    }

    # Robust timestamp extraction
    if other_analyses:
        first_key = next(iter(other_analyses))
        timestamp = other_analyses.get(first_key, {}).get("timestamp", datetime.utcnow().isoformat())
    else:
        timestamp = datetime.utcnow().isoformat()

    deception_record = {
        "statement": statement,
        "round": state.round_num,
        "phase": state.phase,
        "self_analysis": self_analysis,
        "self_reported_deceptive": 1 if self_analysis.get("is_deceptive", 0) == 1 else 0,
        "other_analyses": other_analyses,
        "observer_count": observer_count,
        "observer_deceptive_count": observer_deceptive_count,
        "observer_deceptive_fraction": observer_deceptive_fraction,
        "observers_flagging": observers_flagging,
        "suspicion_levels": suspicion_levels,
        "average_suspicion": average_suspicion,
        "context_snapshot": context_snapshot,
        "timestamp": timestamp,
    }
    
    # Update history
    new_history = state.deception_history.copy()
    if player_name not in new_history:
        new_history[player_name] = []
    new_history[player_name].append(deception_record)
    
    # Update deception scores (how each observer perceives the other players)
    new_scores = state.deception_scores.copy()
    for observer, analysis in other_analyses.items():
        if observer not in new_scores:
            new_scores[observer] = {}
        
        # Update score 
        current_score = new_scores[observer].get(player_name, 0.5)
        new_assessment = analysis.get("suspicion_level", 0.5)
        # Weighted average: 70% new assessment, 30% historical
        new_scores[observer][player_name] = 0.7 * new_assessment + 0.3 * current_score
    
    return state.model_copy(update={
        "deception_history": new_history,
        "deception_scores": new_scores
    })


def compute_observer_accuracy(state) -> Dict[str, Dict[str, float]]:
    """
    Compute per-observer accuracy metrics by comparing each observer's prediction
    against the speaker's self-reported deception label for every statement.

    Returns a mapping of observer -> metrics dict
    metrics include: tp, tn, fp, fn, total, accuracy, precision, recall, f1
    """
    metrics: Dict[str, Dict[str, float]] = {}

    for speaker, history in getattr(state, "deception_history", {}).items():
        for record in history:
            true_label = 1 if record.get("self_analysis", {}).get("is_deceptive", 0) == 1 else 0
            for observer, analysis in record.get("other_analyses", {}).items():
                pred = 1 if analysis.get("is_deceptive", 0) == 1 else 0
                stat = metrics.setdefault(observer, {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "total": 0})
                if pred == 1 and true_label == 1:
                    stat["tp"] += 1
                elif pred == 0 and true_label == 0:
                    stat["tn"] += 1
                elif pred == 1 and true_label == 0:
                    stat["fp"] += 1
                elif pred == 0 and true_label == 1:
                    stat["fn"] += 1
                stat["total"] += 1

    # compute rates
    for observer, stat in metrics.items():
        total = stat.get("total", 0)
        tp = stat.get("tp", 0)
        tn = stat.get("tn", 0)
        fp = stat.get("fp", 0)
        fn = stat.get("fn", 0)
        accuracy = (tp + tn) / total if total else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        stat.update({
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        })

    return metrics