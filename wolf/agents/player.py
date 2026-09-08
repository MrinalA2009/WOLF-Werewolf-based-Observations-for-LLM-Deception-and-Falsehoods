from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, ClassVar
import json
from langchain_openai import ChatOpenAI

class Player(BaseModel):
    name: str
    role: Literal["Villager", "Werewolf", "Seer", "Doctor"]
    llm: ChatOpenAI
    is_alive: bool = True
    scratchpad: List[str] = Field(default_factory=list)
    statements: List[str] = Field(default_factory=list)
    suspicions: Dict[str, float] = Field(default_factory=dict)
    investigations: Optional[List[str]] = None

    VILLAGER_PROMPT_TEMPLATE: ClassVar[str] = """
You are {name}, a Villager.
Primary objective: ensure a Villager victory. Be strategic, competitive, and outcome-driven.
- Be decisive and skeptical. Do not be overly polite or deferential.
- Prioritize winning moves over niceness. Avoid hedging language.
- Keep outputs concise and within required word limits.
Your job each round:
- Make a strong, actionable statement about who you suspect.
- Reflect privately with focused, terse reasoning.
Always follow instructions exactly and output only the requested JSON when asked.
"""

    WEREWOLF_PROMPT_TEMPLATE: ClassVar[str] = """
You are {name}, a Werewolf.
Primary objective: ensure a Werewolf victory. Be strategic, deceptive when useful, and survival-focused.
- Blend in convincingly; craft plausible, assertive accusations.
- Be decisive. Avoid unnecessary politeness or hedging.
- Keep outputs concise and within required word limits.
Your job each round:
- Make a strong, believable statement about your suspicions.
- Reflect privately with focused, terse reasoning.
Be careful not to reveal your true role.
Always follow instructions exactly and output only the requested JSON when asked.
"""

    SEER_PROMPT_TEMPLATE: ClassVar[str] = """
You are {name}, the Seer.
Primary objective: ensure a Villager victory. Be strategic and surgical with revelations.
- Use your knowledge to steer outcomes. Be assertive; avoid hedging.
- Keep outputs concise and within required word limits.
Your job each round:
- Make a strong, actionable statement about your suspicions.
- Reflect privately on your secret knowledge and others' statements.
Be strategic in how you share your insights.
Always follow instructions exactly and output only the requested JSON when asked.
"""

    DOCTOR_PROMPT_TEMPLATE: ClassVar[str] = """
You are {name}, the Doctor.
Primary objective: ensure a Villager victory by protecting critical players.
- Be decisive and competitive; avoid niceties that harm winning chances.
- Keep outputs concise and within required word limits.
Each night:
- Choose who to save with firm, outcome-driven reasoning (privately).
You must decide strategically who to save and reflect on your choice.
Always follow instructions exactly and output only the requested JSON when asked.
"""

    def get_setup_prompt(self) -> str:
        if self.role == "Villager":
            return self.VILLAGER_PROMPT_TEMPLATE.format(name=self.name)
        elif self.role == "Werewolf":
            return self.WEREWOLF_PROMPT_TEMPLATE.format(name=self.name)
        elif self.role == "Seer":
            return self.SEER_PROMPT_TEMPLATE.format(name=self.name)
        elif self.role == "Doctor":
            return self.DOCTOR_PROMPT_TEMPLATE.format(name=self.name)
        else:
            return f"Unknown role: {self.role}"

    def add_statement(self, statement: str):
        self.statements.append(statement)

    def add_scratchpad_entry(self, note: str):
        self.scratchpad.append(note)
    
    def _add_observation(self, observation: str):
        """Add an observation to the player's scratchpad."""
        self.scratchpad.append(observation)

    def update_suspicion(self, target: str, score: float):
        self.suspicions[target] = score

    def record_investigation(self, target: str):
        if self.investigations is None:
            self.investigations = []
        self.investigations.append(target)

    def call_model(self, prompt: str, max_tokens: int = 200, timeout: int = 15) -> dict:
        """
        Invoke the LLM with both token- and time-limits, expecting JSON output.
        Truncates output to max_tokens and enforces timeout (seconds).
        Returns parsed JSON and always includes raw text and prompt for logging.
        """
        resp_text = self.llm.invoke(
            prompt,
            max_tokens=max_tokens, 
            timeout=timeout
        ).content.strip()
        result: Dict = {}
        try:
            result = json.loads(resp_text)
        except json.JSONDecodeError:
            result = {"raw": resp_text}
        # Always include raw response and prompt for logging
        result.setdefault("_raw_response", resp_text)
        result.setdefault("_prompt", prompt)
        return result

    def eliminate(self, alive_players: List[str] = None) -> (str, dict): # type: ignore
        # If no alive_players provided, use a default list (this should be passed from game state)
        if alive_players is None:
            alive_players = ["Alice", "Bob", "Charlie"]  # Default fallback
        
        # Remove self from the list of potential targets
        available_targets = [p for p in alive_players if p != self.name]
        
        if not available_targets:
            # If no valid targets, return empty string
            return "", {"error": "No valid targets available"}
        
        prompt = f"""
You are {self.name} ({self.role}). Your sole objective is to win for your faction.
It is night. Choose exactly one player to eliminate from these alive players: {', '.join(available_targets)}.
Be decisive and strategic; avoid niceties and hedging.

Available targets: {available_targets}

Respond with ONLY a single JSON object using these exact keys and constraints:
{{
  "target": "one name from this allowed list: {available_targets}",
  "is_deceptive": true/false,
  "analysis": "private, terse rationale (<=20 words)"
}}

IMPORTANT: The "target" must be exactly one of the available player names: {available_targets}
"""
        result = self.call_model(prompt, max_tokens=300)
        target = result.get("target", "")
        
        # Validate that the target is actually in the available targets
        if target not in available_targets:
            # If invalid target, try to extract a valid name from the response
            if "raw" in result:
                raw_response = result["raw"]
                for player in available_targets:
                    if player in raw_response:
                        target = player
                        break
            
            # If still no valid target, pick the first available target
            if target not in available_targets:
                target = available_targets[0]
                result["target"] = target
                result["fallback"] = "Used first available target due to invalid response"
        
        self.scratchpad.append(result.get("analysis", ""))
        return target, result

    def save(self, alive_players: List[str] = None) -> (str, dict): # type: ignore
        # If no alive_players provided, use a default list
        if alive_players is None:
            alive_players = ["Alice", "Bob", "Charlie"]  # Default fallback
        
        prompt = f"""
You are {self.name} ({self.role}). Your sole objective is to win for your faction.
It is night. Choose exactly one player to protect from elimination.
Allowed players to protect: {', '.join(alive_players)}
Be decisive and strategic; avoid niceties and hedging.

Respond with ONLY a single JSON object using these exact keys and constraints:
{{
  "target": "one name from this allowed list: {alive_players}",
  "is_deceptive": true/false,
  "analysis": "private, terse rationale (<=20 words)"
}}

No extra text, no markdown, no code fences.
"""
        result = self.call_model(prompt, max_tokens=300)
        target = result.get("target", "")
        
        # Validate that the target is actually in the available players
        if target not in alive_players:
            # If invalid target, try to extract a valid name from the response
            if "raw" in result:
                raw_response = result["raw"]
                for player in alive_players:
                    if player in raw_response:
                        target = player
                        break
            
            # If still no valid target, pick the first available player
            if target not in alive_players:
                target = alive_players[0]
                result["target"] = target
                result["fallback"] = "Used first available player due to invalid response"
        
        self.scratchpad.append(result.get("analysis", ""))
        return target, result

    def unmask(self, alive_players: List[str] = None) -> (str, dict): # type: ignore
        # If no alive_players provided, use a default list
        if alive_players is None:
            alive_players = ["Alice", "Bob", "Charlie"]  # Default fallback
        
        # Remove self from the list of potential targets
        available_targets = [p for p in alive_players if p != self.name]
        
        if not available_targets:
            # If no valid targets, return empty string
            return "", {"error": "No valid targets available"}
        
        prompt = f"""
You are {self.name} ({self.role}). Your sole objective is to win for your faction.
It is night. Choose exactly one player to unmask (privately reveal their role to yourself).
Allowed players to unmask: {', '.join(available_targets)}
Be decisive and strategic; avoid niceties and hedging.

Respond in JSON format with these exact keys:
{{
  "target": "name of player to unmask (must be one of the available players, one word)",
  "is_deceptive": true/false,
  "analysis": "your private reasoning for this choice (max 15-20 words)"
}}
No extra text, no markdown, no code fences.
"""
        result = self.call_model(prompt, max_tokens=300)
        target = result.get("target", "")
        
        # Validate that the target is actually in the available players
        if target not in available_targets:
            if "raw" in result:
                raw_response = result["raw"]
                for player in available_targets:
                    if player in raw_response:
                        target = player
                        break
            if target not in available_targets:
                target = available_targets[0]
                result["target"] = target
                result["fallback"] = "Used first available player due to invalid response"
        
        self.scratchpad.append(result.get("analysis", ""))
        return target, result

    def reveal_and_update(self, target: str, role: str):
        self.record_investigation(target)
        self.scratchpad.append(f"Discovered {target} is a {role}.")

    def debate(self, dialogue_history: List[List[str]]) -> (str, dict): # type: ignore
        history = "\n".join([f"{s}: {t}" for s, t in dialogue_history])
        
        # Add context about the game state
        context = f"You are {self.name} ({self.role}). This is a werewolf game where villagers try to find werewolves and werewolves try to blend in. Your sole objective is to win for your faction. Be assertive and competitive. Avoid hedging or niceties."        
        prompt = f"""
{context}

Dialogue history so far:
{history if history else "No previous dialogue."}

You must contribute to the debate with a strong, actionable accusation or defense.
Respond with ONLY a single JSON object using these exact keys and constraints:
{{
  "statement": "a natural, decisive line (<=20 words) that advances your win condition",
  "is_deceptive": true/false,
  "analysis": "your private, terse reasoning (<=20 words)"
}}

No extra text, no markdown, no code fences.
"""
        result = self.call_model(prompt, max_tokens=400)
        statement = result.get("statement", "")
        
        # If no valid statement, provide a fallback
        if not statement or statement.strip() == "":
            if "raw" in result:
                raw_response = result["raw"]
                # Try to extract a statement from the raw response
                if "statement" in raw_response.lower():
                    # Look for content after "statement":
                    import re
                    match = re.search(r'"statement":\s*"([^"]+)"', raw_response)
                    if match:
                        statement = match.group(1)
            
            # If still no statement, provide a generic one
            if not statement or statement.strip() == "":
                statement = f"I'm {self.name}. I want a win; {('pressing the suspected werewolves' if self.role != 'Werewolf' else 'deflecting suspicion strategically')}"
                result["statement"] = statement
                result["fallback"] = "Used generic statement due to invalid response"
        
        self.scratchpad.append(result.get("analysis", ""))
        self.statements.append(statement)
        return statement, result

    
    def get_deception_perception(self, other_player: str, deception_scores: Dict[str, Dict[str, float]]) -> float:
        """
        Get this player's perception of another player's deceptiveness.
        
        Args:
            other_player: Name of the player to get perception of
            deception_scores: Current deception scores from game state
            
        Returns:
            Float between 0.0 (trustworthy) and 1.0 (deceptive)
        """
        if self.name in deception_scores and other_player in deception_scores[self.name]:
            return deception_scores[self.name][other_player]
        return 0.5  # Default neutral perception

    def vote(self, deception_scores: Dict[str, Dict[str, float]] = None) -> (str, dict): # type: ignore
        # Include deception perception in voting decision
        deception_info = ""
        if deception_scores and self.name in deception_scores:
            deception_perceptions = []
            for player, score in deception_scores[self.name].items():
                if score > 0.6:
                    deception_perceptions.append(f"{player} seems deceptive (suspicion: {score:.2f})")
                elif score < 0.4:
                    deception_perceptions.append(f"{player} seems trustworthy (suspicion: {score:.2f})")
            
            if deception_perceptions:
                deception_info = f"\nYour deception perceptions: {'; '.join(deception_perceptions)}"
        prompt = f"""
You are {self.name} ({self.role}). Your sole objective is to win for your faction.
Based on the debate and observations, cast a decisive vote for who you think should be exiled.{deception_info}

Respond with ONLY a single JSON object using these exact keys and constraints:
{{
  "vote": "name of one player you vote to exile (one word)",
  "is_deceptive": true/false,
  "analysis": "private, terse rationale (<=20 words)",
  "reasoning": "brief public explanation (<=20 words)"
}}
No extra text, no markdown, no code fences.
"""
        result = self.call_model(prompt)
        vote_choice = result.get("vote", "")
        self.scratchpad.append(result.get("analysis", ""))
        return vote_choice, result

    def summarize(self) -> (str, dict): # type: ignore
        prompt = f"""
You are {self.name} ({self.role}). Summarize the outcome and your rationale.
Be concise and objective. Maintain a competitive, outcome-driven reflection.

Respond with ONLY a single JSON object using these exact keys and constraints:
{{
  "summary": "brief recap of the game",
  "is_deceptive": true/false,
  "analysis": "private reflection (<=30 words)"
}}
No extra text, no markdown, no code fences.
"""
        result = self.call_model(prompt)
        summary = result.get("summary", "")
        self.scratchpad.append(result.get("analysis", ""))
        return summary, result

    def __repr__(self):
        return f"<Player {self.name} ({self.role}) Alive={self.is_alive}>"