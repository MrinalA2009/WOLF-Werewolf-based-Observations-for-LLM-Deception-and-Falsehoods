from game_graph import graph, GameState  
from player import Player             
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import argparse

def get_llm(model_name="gemini-pro", api_key=None):
    """Initialize the language model with configurable parameters."""
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    elif not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable not set and no API key provided")
    
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.7
    )

def run_werewolf_game(model_name="gemini-pro", api_key=None):
    """Run a werewolf game with the specified model."""
    print(f"🎮 Starting Werewolf Game with model: {model_name}")
    
    # Initialize the language model
    llm = get_llm(model_name, api_key)
    
    # Game setup
    players = ["Alice", "Bob", "Charlie"]
    roles = {
        "Alice": "Doctor",
        "Bob": "Werewolf", 
        "Charlie": "Seer"
    }

    seer = next((p for p in players if roles[p] == "Seer"), None)
    doctor = next((p for p in players if roles[p] == "Doctor"), None)
    werewolves = [p for p in players if roles[p] == "Werewolf"]

    player_objects = {
        name: Player(name=name, role=roles[name], llm=llm)
        for name in players
    }

    initial_state = GameState(
        round_num=0,
        players=players,
        alive_players=players.copy(),
        roles=roles,
        werewolves=werewolves,
        seer=seer,
        doctor=doctor,
        phase="eliminate",
        game_logs=[],
        deception_history={},
        deception_scores={}
    )

    # Run the game
    print("🚀 Compiling and running the game graph...")
    runnable = graph.compile()
    final_state = runnable.invoke(initial_state, config={
        "configurable": {
            "player_objects": player_objects,
            "MAX_DEBATE_TURNS": 6
        }
    })
    
    print("✅ Game completed successfully!")
    return final_state

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Werewolf Game with AI players")
    parser.add_argument(
        "--model", 
        default="gemini-pro",
        help="Model to use (default: gemini-pro). Options: gemini-pro, gemini-1.5-pro, gemini-1.5-flash"
    )
    parser.add_argument(
        "--api-key",
        help="Google API key (alternatively set GOOGLE_API_KEY environment variable)"
    )
    
    args = parser.parse_args()
    
    try:
        # If no API key provided via args, try to use the existing one from the file (temporarily)
        if not args.api_key and not os.environ.get("GOOGLE_API_KEY"):
            # Temporarily use the key from your original file for testing
            args.api_key = "AIzaSyAwjHr_8ucLsNTutTvTm64JRnJCj5b_ngs"
            print("⚠️  Using embedded API key for testing. Please set GOOGLE_API_KEY environment variable for production use.")
        
        final_state = run_werewolf_game(args.model, args.api_key)
        
        print("\n🎯 Game Results:")
        print(f"Final alive players: {final_state.alive_players}")
        if hasattr(final_state, 'winner'):
            print(f"Winner: {final_state.winner}")
        
    except Exception as e:
        print(f"❌ Error running game: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Make sure your Google API key is valid")
        print("2. Check that all dependencies are installed: pip install -r requirements.txt")
        print("3. Try running with a different model: python run.py --model gemini-pro")
