# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Mrinal Agarwal, Saad Rana, and the WOLF authors

import os
import random

from langchain_openai import ChatOpenAI

# Bidding runs its own client keyed off MODEL_NAME (set by wolf.cli.get_llm)
# rather than taking the game's llm object. Built once, on first bid.
_llm = None


def get_llm():
    global _llm
    if _llm is None:
        model_name = os.environ.get("MODEL_NAME", "gpt-4o")
        _llm = ChatOpenAI(model=model_name, temperature=0.7)
    return _llm

def get_bid(player_name: str, dialogue_history: str):
    """
    Calls gpt to get a bid (0-10) from a player based on the debate so far.

    Returns:
        (int, str): (numeric bid value, raw model output)
    """
    prompt = f"""
You are a player in a competitive game of Werewolf. Your name is {player_name}.
Here is the current conversation between players:

{dialogue_history}

How strongly do you want to speak next? Return a single number from 0 to 10.
0 means you have no desire to speak. 10 means you are extremely eager to speak.
Only respond with the number. Do not explain.
"""

    response = get_llm().invoke(prompt).content.strip()
    try:
        bid = int(response)
        bid = max(0, min(10, bid))
    except ValueError:
        # A non-numeric reply means "I have nothing to add."
        bid = 0

    return bid, response


def get_max_bids(bid_dict):
    max_value = max(bid_dict.values())
    return [name for name, bid in bid_dict.items() if bid == max_value]


def choose_next_speaker(bid_dict, previous_dialogue=None):
    """Pick who speaks next: highest bidders, nudged toward anyone recently
    named, then a coin flip among what's left."""
    top_bidders = get_max_bids(bid_dict)

    # NOTE: this scans top_bidders against itself, so the mention nudge is a
    # no-op today. Behaviour preserved on purpose — see KNOWN_ISSUES.md #4.
    if previous_dialogue:
        top_bidders += [name for name in top_bidders if name in previous_dialogue]

    random.shuffle(top_bidders)
    return random.choice(top_bidders)
