from game_graph import graph, GameState  
from player import Player             
from langchain_google_genai import ChatGoogleGenerativeAI
import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyAwjHr_8ucLsNTutTvTm64JRnJCj5b_ngs"
llm = ChatGoogleGenerativeAI(
    model="google_genai:gemini-2.0-flash",
    temperature=0.7
)

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

runnable = graph.compile()
final_state = runnable.invoke(initial_state, config={
    "player_objects": player_objects,
    "MAX_DEBATE_TURNS": 6
})
