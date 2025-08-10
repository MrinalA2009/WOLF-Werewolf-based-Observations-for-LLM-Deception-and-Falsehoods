import random
from langchain_openai import ChatOpenAI
import os

# ChatGpt model setup - initialize lazily
_llm = None


def get_llm():
    global _llm
    if _llm is None:
        model_name = os.environ.get("MODEL_NAME", "gpt-4o")
        _llm = ChatOpenAI(model=model_name, temperature=0.7)
    return _llm


def get_bid(player_name: str, dialogue_history: str):
    """
    Calls the model to get a bid (0-10) from a player based on the debate so far.

    Returns:
        (int, str): (numeric bid value, raw model output)
    """
    prompt = f"""
You are a player in a competitive game of Werewolf. Your name is {player_name}.
Here is the current conversation between players:

{dialogue_history}

How strongly do you want to speak next? Return a SINGLE INTEGER from 0 to 10.
- 0: no desire to speak; 10: extremely eager to speak.
Output ONLY the integer. No extra text, no markdown, no explanations.
"""

    response = get_llm().invoke(prompt).content.strip()
    try:
        bid = int(response)
        bid = max(0, min(10, bid))
    except ValueError:
        bid = 0  # Safe fallback

    return bid, response


def get_max_bids(bid_dict):
    max_value = max(bid_dict.values())
    return [name for name, bid in bid_dict.items() if bid == max_value]


def choose_next_speaker(bid_dict, previous_dialogue=None):
    """
    Given a dictionary of player bids, returns the chosen speaker using:
    - Max bid
    - Mention bias from previous dialogue
    - Random tiebreaking
    """
    top_bidders = get_max_bids(bid_dict)

    if previous_dialogue:
        top_bidders += [name for name in top_bidders if name in previous_dialogue]

    random.shuffle(top_bidders)
    return random.choice(top_bidders)
