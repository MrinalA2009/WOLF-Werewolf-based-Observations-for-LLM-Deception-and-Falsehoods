from game_graph import graph, GameState  
from player import Player             
from langchain_openai import ChatOpenAI
import os
import argparse
from dotenv import load_dotenv
from logs import init_logging_state, write_final_state, print_header, print_subheader, print_kv, write_final_metrics

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")


def get_llm(model_name="gpt-4o", api_key=None, base_url=None):
    """Initialize the language model with configurable parameters."""
    os.environ["MODEL_NAME"] = model_name

    if base_url:
        os.environ["VLLM_BASE_URL"] = base_url
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = "EMPTY"
        return ChatOpenAI(
            model=model_name,
            temperature=0.7,
            base_url=base_url,
        )

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    elif not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable not set and no API key provided")

    return ChatOpenAI(
        model=model_name,
        temperature=0.7
    )


def run_werewolf_game(model_name="gpt-4o", api_key=None, base_url=None, log_dir: str = "./logs", enable_file_logging: bool = True):
    """Run a werewolf game with the specified model."""
    print_header("Starting Werewolf Game")
    print_kv("Model", model_name)
    if base_url:
        print_kv("Base URL", base_url)

    # Initialize the language model
    llm = get_llm(model_name, api_key, base_url=base_url)
    
    # Game setup
    players = ["Alice", "Bob", "Selena", "Raj", "Frank", "Joy", "Cyrus", "Emma"]
    roles = {
        "Alice": "Doctor",
        "Bob": "Werewolf", 
        "Selena": "Seer", 
        "Raj": "Villager", 
        "Frank": "Villager", 
        "Joy": "Werewolf", 
        "Cyrus": "Villager", 
        "Emma": "Villager"
    }

    seer = next((p for p in players if roles[p] == "Seer"), None)
    doctor = next((p for p in players if roles[p] == "Doctor"), None)
    werewolves = [p for p in players if roles[p] == "Werewolf"]
    villagers = [p for p in players if roles[p] == "Villager"]

    player_objects = {
        name: Player(name=name, role=roles[name], llm=llm)
        for name in players
    }

    initial_state = GameState(
        round_num=0,
        players=players,
        alive_players=players.copy(),
        roles=roles,
        villagers=villagers,
        werewolves=werewolves,
        seer=seer,
        doctor=doctor,
        phase="eliminate",
        game_logs=[],
        deception_history={},
        deception_scores={}
    )

    # Initialize file logging on the state
    initial_state = init_logging_state(initial_state, log_dir=log_dir, enable_file_logging=enable_file_logging)

    # Run the game
    print_subheader("Execute")
    print_kv("Action", "Compiling and running the game graph...")
    runnable = graph.compile()
    final_state = runnable.invoke(initial_state, config={
        "recursion_limit": 1000,
        "configurable": {
            "player_objects": player_objects,
            "MAX_DEBATE_TURNS": 6
        }
    })
    
    # Persist the final state to disk if logging is enabled
    write_final_state(final_state)
    # Persist organized final metrics (no raw prompts/outputs)
    write_final_metrics(final_state)

    print_subheader("Status")
    print_kv("Result", "Game completed successfully!")

    # Print helpful info for locating logs
    paths = getattr(final_state, "log_paths", {})
    if paths:
        print_subheader("Log Files")
        print_kv("Events (NDJSON)", paths.get('events'), indent=2)
        print_kv("Final State JSON", paths.get('state'), indent=2)
        print_kv("Final Metrics JSON", paths.get('metrics'), indent=2)
        print_kv("Run Metadata", paths.get('meta'), indent=2)
    return final_state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Werewolf Game with AI players")
    parser.add_argument(
        "--model", 
        default="gpt-4o",
        help="Model to use (default: gpt-4o). Options: gpt-4o, gpt-4-turbo, gpt-3.5-turbo"
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (alternatively set OPENAI_API_KEY environment variable)"
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL for OpenAI-compatible API (e.g. http://localhost:8000/v1 for vLLM)"
    )
    parser.add_argument(
        "--log-dir",
        default="./logs",
        help="Directory to store run logs (events NDJSON + final JSON). Default: ./logs"
    )
    parser.add_argument(
        "--no-file-logging",
        action="store_true",
        help="Disable writing logs to disk (events and final state)"
    )
    
    args = parser.parse_args()
    
    try:
        # If no API key provided via args, rely on environment variables loaded from .env
        final_state = run_werewolf_game(args.model, args.api_key, base_url=args.base_url, log_dir=args.log_dir, enable_file_logging=(not args.no_file_logging))

        print_subheader("Game Results")
        print_kv("Final alive players", final_state.alive_players, indent=2)
        if hasattr(final_state, 'winner'):
            print_kv("Winner", final_state.winner, indent=2)
        
    except Exception as e:
        print_subheader("Error")
        print_kv("Message", f"{e}")
        print_subheader("Troubleshooting")
        print_kv("1", "Make sure your OPENAI API key is valid", indent=2)
        print_kv("2", "Install dependencies: pip install -r requirements.txt", indent=2)
        print_kv("3", "Try a different model: python run.py --model gpt-4o-mini", indent=2)