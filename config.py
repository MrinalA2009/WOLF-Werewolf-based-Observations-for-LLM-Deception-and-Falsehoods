# Werewolf Game Configuration

# Available models and their configurations
AVAILABLE_MODELS = {
    "gemini-pro": {
        "name": "gemini-pro", 
        "description": "Gemini Pro - balanced performance",
        "temperature": 0.7,
        "max_tokens": None
    },
    "gemini-1.5-pro": {
        "name": "gemini-1.5-pro",
        "description": "Gemini 1.5 Pro - enhanced reasoning",
        "temperature": 0.7,
        "max_tokens": None
    },
    "gemini-1.5-flash": {
        "name": "gemini-1.5-flash",
        "description": "Gemini 1.5 Flash - fast and efficient",
        "temperature": 0.7,
        "max_tokens": None
    }
}

# Default model
DEFAULT_MODEL = "gemini-pro"

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
    "google_api_key_env": "GOOGLE_API_KEY",
    "debug_mode": False,
    "log_level": "INFO"
}