# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Mrinal Agarwal, Saad Rana, and the WOLF authors

import argparse
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from wolf.agents.player import Player
from wolf.game.graph import graph
from wolf.game.state import GameState
from wolf.runlog.console import print_header, print_kv, print_subheader
from wolf.runlog.events import init_logging_state, write_final_state
from wolf.runlog.metrics import write_final_metrics

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")


def get_llm(model_name="gpt-4o", api_key=None):
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    elif not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable not set and no API key provided")
    # bidding.py reads MODEL_NAME to build its own client; keep them in sync here.
    os.environ["MODEL_NAME"] = model_name

    return ChatOpenAI(model=model_name, temperature=0.7)


def run_werewolf_game(model_name="gpt-4o", api_key=None, log_dir: str = "./logs", enable_file_logging: bool = True):
    """Run a werewolf game with the specified model."""
    print_header("Starting Werewolf Game")
    print_kv("Model", model_name)

    llm = get_llm(model_name, api_key)

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

    table = {name: Player(name=name, role=roles[name], llm=llm) for name in players}

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

    initial_state = init_logging_state(initial_state, log_dir=log_dir, enable_file_logging=enable_file_logging)

    print_subheader("Execute")
    print_kv("Action", "Compiling and running the game graph...")
    runnable = graph.compile()
    final_state = runnable.invoke(initial_state, config={
        # One node per phase; a multi-round game is ~150 hops, well under this.
        "recursion_limit": 1000,
        "configurable": {
            "player_objects": table,
            "MAX_DEBATE_TURNS": 6
        }
    })

    # Recent langgraph returns the raw channel dict rather than the pydantic
    # model; rebuild it so the persistence layer has a GameState. See KNOWN_ISSUES.
    if not isinstance(final_state, GameState):
        final_state = GameState(**dict(final_state))

    write_final_state(final_state)
    write_final_metrics(final_state)

    print_subheader("Status")
    print_kv("Result", "Game completed successfully!")

    paths = getattr(final_state, "log_paths", {})
    if paths:
        print_subheader("Log Files")
        print_kv("Events (NDJSON)", paths.get('events'), indent=2)
        print_kv("Final State JSON", paths.get('state'), indent=2)
        print_kv("Final Metrics JSON", paths.get('metrics'), indent=2)
        print_kv("Run Metadata", paths.get('meta'), indent=2)
    return final_state


def main():
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
        final_state = run_werewolf_game(args.model, args.api_key, log_dir=args.log_dir, enable_file_logging=(not args.no_file_logging))

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


if __name__ == "__main__":
    main()