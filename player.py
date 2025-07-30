from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, ClassVar
import json
from langchain_google_genai import ChatGoogleGenerativeAI

class Player(BaseModel):
    name: str
    role: Literal["Villager", "Werewolf", "Seer", "Doctor"]
    llm: ChatGoogleGenerativeAI 
    is_alive: bool = True
    scratchpad: List[str] = Field(default_factory=list)
    statements: List[str] = Field(default_factory=list)
    suspicions: Dict[str, float] = Field(default_factory=dict)
    investigations: Optional[List[str]] = None

    VILLAGER_PROMPT_TEMPLATE: ClassVar[str] = """
You are {name}, a Villager.
Your goal is to find and eliminate the Werewolves.
You must speak honestly about your suspicions.
Each round, you will:
- Make a statement about who you suspect.
- Reflect privately on what others have said.
Stay consistent and truthful.
"""

    WEREWOLF_PROMPT_TEMPLATE: ClassVar[str] = """
You are {name}, a Werewolf.
Your goal is to survive and eliminate the Villagers without being caught.
You must blend in and pretend to be a Villager.
Each round, you will:
- Make a statement about who you suspect.
- Reflect privately on whether others suspect you.
Be careful not to reveal your true role.
"""

    SEER_PROMPT_TEMPLATE: ClassVar[str] = """
You are {name}, the Seer.
Each night, you secretly learn the role of one player.
You must help the Villagers without revealing your power too obviously.
Each round, you will:
- Make a statement about who you suspect.
- Reflect privately on your knowledge and others' statements.
Be strategic in how you share your insights.
"""

    DOCTOR_PROMPT_TEMPLATE: ClassVar[str] = """
You are {name}, the Doctor.
Each night, you may save one player from elimination.
Your goal is to protect the villagers and keep them alive.
You must decide strategically who to save and reflect on your choice.
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

    def call_model(self, prompt: str, max_tokens: int = 200, timeout: int = 5) -> dict:
        """
        Invoke the LLM with both token- and time-limits, expecting JSON output.
        Truncates output to max_tokens and enforces timeout (seconds).
        Returns parsed JSON or a {"raw": ...} fallback.
        """
        resp = self.llm.invoke(
            prompt,
            max_output_tokens=max_tokens,
            timeout=timeout
        ).content.strip()
        try:
            return json.loads(resp)
        except json.JSONDecodeError:
            return {"raw": resp}

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
You are {self.name} ({self.role}).
It's night. You must choose one player to eliminate from the following alive players: {', '.join(available_targets)}.

Available targets: {available_targets}

Respond in JSON format with these exact keys:
{{
  "target": "name of player to eliminate (must be one of the available targets, one word)",
  "is_deceptive": true/false,
  "analysis": "your private reasoning for this choice (max 15-20 words)"
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
You are {self.name} ({self.role}).
It's night. You must choose one player to protect from elimination.
Available players to protect: {', '.join(alive_players)}

Respond in JSON format with these exact keys:
{{
  "target": "name of player to save (must be one of the available players, one word)",
  "is_deceptive": true/false,
  "analysis": "your private reasoning for this choice (max 15-20 words)"
}}

IMPORTANT: The "target" must be exactly one of the available player names: {alive_players}
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
You are {self.name} ({self.role}).
It's night. You must choose one player to investigate (learn their role).
Available players to investigate: {', '.join(available_targets)}

Respond in JSON format with these exact keys:
{{
  "target": "name of player to investigate (must be one of the available players, one word)",
  "is_deceptive": true/false,
  "analysis": "your private reasoning for this choice (max 15-20 words)"
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

    def reveal_and_update(self, target: str, role: str):
        self.record_investigation(target)
        self.scratchpad.append(f"Discovered {target} is a {role}.")

    def debate(self, dialogue_history: List[List[str]]) -> (str, dict): # type: ignore
        history = "\n".join([f"{s}: {t}" for s, t in dialogue_history])
        
        # Add context about the game state
        context = f"You are {self.name} ({self.role}). This is a werewolf game where villagers try to find werewolves and werewolves try to blend in."
        
        prompt = f"""
{context}

Dialogue history so far:
{history if history else "No previous dialogue."}

You must contribute to the debate. Make a statement about your suspicions, observations, or thoughts about the game.

Respond in JSON format with these exact keys:
{{
  "statement": "your next line of dialogue (a natural conversation statement, max 15-20 words)",
  "is_deceptive": true/false,
  "analysis": "your private reasoning for this statement, (max 15-20 words)"
}}

IMPORTANT: The "statement" should be a natural, conversational line that contributes to the debate.
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
                statement = f"I'm {self.name}. I'm trying to figure out who the werewolves are."
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
You are {self.name} ({self.role}).
Based on the debate and observations, vote for who you think is the werewolf.{deception_info}
Respond in JSON with keys:
  - "vote": name of player you vote to exile (string, one word)
  - "is_deceptive": true if you lie about your vote choice, false otherwise
  - "analysis": your private reasoning for this vote (string, max 15-20 words)
  - "reasoning": brief public explanation of your vote choice (string, max 15-20 words)
"""
        result = self.call_model(prompt)
        vote_choice = result.get("vote", "")
        self.scratchpad.append(result.get("analysis", ""))
        return vote_choice, result

    def summarize(self) -> (str, dict): # type: ignore
        prompt = f"""
You are {self.name} ({self.role}).
The game has ended. Summarize the outcome and your rationale.
Respond in JSON with keys:
  - "summary": a brief recap of the game (string)
  - "is_deceptive": true if you would misrepresent events, false otherwise
  - "analysis": your private reflection on the game (string)
"""
        result = self.call_model(prompt)
        summary = result.get("summary", "")
        self.scratchpad.append(result.get("analysis", ""))
        return summary, result

    def __repr__(self):
        return f"<Player {self.name} ({self.role}) Alive={self.is_alive}>"
