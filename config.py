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

    # --- Google Models ---
    "gemini-pro": {
        "name": "gemini-pro", 
        "description": "Gemini Pro - balanced performance",
        "temperature": 0.7,
        "max_tokens": None,
        "provider": "google"
    },
    "gemini-1.5-pro": {
        "name": "gemini-1.5-pro",
        "description": "Gemini 1.5 Pro - enhanced reasoning",
        "temperature": 0.7,
        "max_tokens": None,
        "provider": "google"
    },
    "gemini-1.5-flash": {
        "name": "gemini-1.5-flash",
        "description": "Gemini 1.5 Flash - fast and efficient",
        "temperature": 0.7,
        "max_tokens": None,
        "provider": "google"
    },

    # --- Local Models (served via vLLM) ---
    "meta-llama/Meta-Llama-3-8B-Instruct": {
        "name": "meta-llama/Meta-Llama-3-8B-Instruct",
        "description": "Meta Llama 3 8B Instruct - local via vLLM",
        "temperature": 0.7,
        "max_tokens": None,
        "provider": "local-vllm",
        "base_url": "http://localhost:8000/v1"
    }
}

# Default model (you can change to "gpt-4o" if you want OpenAI by default)
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
    "google_api_key_env": "GOOGLE_API_KEY",  # For Gemini models
    "openai_api_key_env": "OPENAI_API_KEY",  # For OpenAI models
    "debug_mode": False,
    "log_level": "INFO"
}
