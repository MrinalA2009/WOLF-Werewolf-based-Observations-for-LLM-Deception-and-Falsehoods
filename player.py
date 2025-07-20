from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from langchain_core.language_models.chat_models import BaseChatModel

class Player(BaseModel):
    name: str
    role: Literal["Villager", "Werewolf", "Seer", "Doctor"]
    is_alive: bool = True
    scratchpad: List[str] = Field(default_factory=list)
    statements: List[str] = Field(default_factory=list)
    suspicions: Dict[str, float] = Field(default_factory=dict)
    investigations: Optional[List[str]] = None
    llm: Optional[BaseChatModel] = None  # <- Injected LLM

    # Role prompts
    VILLAGER_PROMPT_TEMPLATE = """
You are {name}, a Villager.
Your goal is to find and eliminate the Werewolves.
You must speak honestly about your suspicions.
Each round, you will:
- Make a statement about who you suspect.
- Reflect privately on what others have said.
Stay consistent and truthful.
"""

    WEREWOLF_PROMPT_TEMPLATE = """
You are {name}, a Werewolf.
Your goal is to survive and eliminate the Villagers without being caught.
You must blend in and pretend to be a Villager.
Each round, you will:
- Make a statement about who you suspect.
- Reflect privately on whether others suspect you.
Be careful not to reveal your true role.
"""

    SEER_PROMPT_TEMPLATE = """
You are {name}, the Seer.
Each night, you secretly learn the role of one player.
You must help the Villagers without revealing your power too obviously.
Each round, you will:
- Make a statement about who you suspect.
- Reflect privately on your knowledge and others' statements.
Be strategic in how you share your insights.
"""

    DOCTOR_PROMPT_TEMPLATE = """
You are {name}, the Doctor.
Each night, you can choose one player to protect.
Try to keep the most valuable players alive.
Each round, observe the discussion and decide who is most at risk.
"""

    def _run_prompt(self, prompt: str) -> str:
        if not self.llm:
            raise ValueError("LLM not set for player.")
        return self.llm.invoke(prompt).content.strip()

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

    def update_suspicion(self, target: str, score: float):
        self.suspicions[target] = score

    def record_investigation(self, target: str):
        if self.investigations is None:
            self.investigations = []
        self.investigations.append(target)

    def eliminate(self):
        prompt = f"""
You are {self.name}, a Werewolf. Pick one living player to eliminate tonight.
Only reply with a name. No explanation.
"""
        response = self._run_prompt(prompt)
        return response, prompt

    def save(self):
        prompt = f"""
You are {self.name}, the Doctor. Choose one player to protect tonight.
Only reply with a name. No explanation.
"""
        response = self._run_prompt(prompt)
        return response, prompt

    def unmask(self):
        prompt = f"""
You are {self.name}, the Seer. Choose one player to investigate tonight.
Only reply with a name. No explanation.
"""
        response = self._run_prompt(prompt)
        return response, prompt

    def debate(self):
        prompt = f"""
You are {self.name}. The discussion is ongoing. Make your next statement (1-2 sentences).
Be persuasive and stay in character.
"""
        response = self._run_prompt(prompt)
        return response, prompt

    def vote(self):
        prompt = f"""
You are {self.name}. Based on the debate, vote for who you think is the Werewolf.
Only reply with a name. No explanation.
"""
        response = self._run_prompt(prompt)
        return response, prompt

    def summarize(self):
        prompt = f"""
You are {self.name}. Summarize today's discussion and reflect on your suspicions.
Keep it brief (1-2 sentences).
"""
        response = self._run_prompt(prompt)
        return response, prompt

    def _add_observation(self, message: str):
        self.scratchpad.append(message)

    def reveal_and_update(self, target: str, role: str):
        self.scratchpad.append(f"{target} was revealed to be a {role}.")

    def __repr__(self):
        return f"<Player {self.name} ({self.role}) Alive={self.is_alive}>"
