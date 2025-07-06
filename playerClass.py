class Player(BaseModel):
    name: str
    role: Literal["Villager", "Werewolf", "Seer"]
    is_alive: bool = True
    scratchpad: List[str] = Field(default_factory=list)
    statements: List[str] = Field(default_factory=list)
    suspicions: Dict[str, float] = Field(default_factory=dict)
    investigations: Optional[List[str]] = None

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

    def get_setup_prompt(self) -> str:
        if self.role == "Villager":
            return self.VILLAGER_PROMPT_TEMPLATE.format(name=self.name)
        elif self.role == "Werewolf":
            return self.WEREWOLF_PROMPT_TEMPLATE.format(name=self.name)
        elif self.role == "Seer":
            return self.SEER_PROMPT_TEMPLATE.format(name=self.name)
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

    def __repr__(self):
        return f"<Player {self.name} ({self.role}) Alive={self.is_alive}>"
