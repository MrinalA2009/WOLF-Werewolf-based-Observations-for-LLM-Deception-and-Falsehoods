# Werewolf Game Configuration

# Available models and their configurations
AVAILABLE_MODELS = {
    # --- OpenAI Models ---
    "gpt-4o": {
        "name": "gpt-4o",
        "description": "OpenAI GPT-4o - latest flagship reasoning model",
        "temperature": 0.7,
        "max_tokens": None,
        "provider": "openai"
    },
    "gpt-4o-mini": {
        "name": "gpt-4o-mini",
        "description": "OpenAI GPT-4o Mini - faster, cheaper, lower latency",
        "temperature": 0.7,
        "max_tokens": None,
        "provider": "openai"
    },
}

DEFAULT_MODEL = "gpt-4o"

# Game settings
GAME_CONFIG = {
    "max_debate_turns": 6,
    "player_names": ["Alice", "Bob", "Charlie"],
    "default_roles": {
        "Alice": "Doctor",
        "Bob": "Werewolf",
        "Charlie": "Seer"
    }
}

# Environment settings
ENV_CONFIG = {
    "openai_api_key_env": "OPENAI_API_KEY",
    "debug_mode": False,
    "log_level": "INFO"
}
