from game_graph import graph, GameState  
from player import Player             
from langchain_openai import ChatOpenAI
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

def get_llm(model_name="gpt-4o", api_key=None):
    """Initialize the language model with configurable parameters."""
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    elif not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable not set and no API key provided")
    
    return ChatOpenAI(
        model=model_name,
        temperature=0.7
    )

def run_werewolf_game(model_name="gpt-4o", api_key=None):
    """Run a werewolf game with the specified model."""
    print(f"Starting Werewolf Game with model: {model_name}")
    
    # Initialize the language model
    llm = get_llm(model_name, api_key)
    
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
        villagers = villagers,
        werewolves=werewolves,
        seer=seer,
        doctor=doctor,
        phase="eliminate",
        game_logs=[],
        deception_history={},
        deception_scores={}
    )

    # Run the game
    print("Compiling and running the game graph...")
    runnable = graph.compile()
    final_state = runnable.invoke(initial_state, config={
        "recursion_limit": 1000,
        "configurable": {
            "player_objects": player_objects,
            "MAX_DEBATE_TURNS": 6
        }
    })
    
    print("Game completed successfully!")
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
    
    args = parser.parse_args()
    
    try:
        # If no API key provided via args, rely on environment variables loaded from .env
        final_state = run_werewolf_game(args.model, args.api_key)
        
        print("\n Game Results:")
        print(f"Final alive players: {final_state.alive_players}")
        if hasattr(final_state, 'winner'):
            print(f"Winner: {final_state.winner}")
        
    except Exception as e:
        print(f" Error running game: {e}")
        print("\n Troubleshooting:")
        print("1. Make sure your OPENAI API key is valid")
        print("2. Check that all dependencies are installed: pip install -r requirements.txt")
        print("3. Try running with a different model: python run.py --model gemini-pro")
