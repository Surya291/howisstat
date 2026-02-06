## given a stat description and a list of available players, choose the best player to compete

from .llm_agents import GeminiAgent 
from google import genai
from pydantic import BaseModel, Field
from typing import List, Dict
import json


gemini_agent = GeminiAgent("gemini-flash-latest")


class DefenseChoice(BaseModel):
    chosen_player_id: str = Field(description="The player ID chosen to defend against the stat.")
    confidence_level: str = Field(description="Confidence level: high, medium, or low.")
    reason: str = Field(description="Short, snarky 5-10 word overconfident commentary on why this player will win.")


def get_defense_choice(challenger_stat_description: str, available_player_id_list: list, player_id2player_info: Dict) -> dict:
    """
    Given a challenger's stat description and a list of available player IDs,
    choose the best player to compete on that stat.

    Args:
        challenger_stat_description: The stat declared by the challenger
        available_player_id_list: List of player IDs (strings)
        player_id2player_info: Dictionary of player IDs and player info

    Returns:
        dict with 'chosen_player_id', 'confidence_level', and 'reason'
    """
    if not available_player_id_list:
        raise ValueError("No available player IDs provided")

    # Build enriched player info list from player_id2player_info
    enriched_players = []
    for player_id in available_player_id_list:
        player_info = player_id2player_info.get(player_id)
        enriched_players.append({
            "player_id": player_id,
            "player_name": player_info["display_name"],
            "player_description": f'ROLE: {player_info["role"]} || Batting Style: {player_info["batting_style"]} || Bowling Style: {player_info["bowling_style"]}',
        })

    system_instruction = """You are the Defender in a cricket trump-card game.

Game context:
- Each round, the Challenger declares a cricket stat in plain language.
- That stat is applied uniformly across players.
- The Defender must choose the best possible player card to compete on that stat.
- Actual values will be resolved externally.

Your role:
- You are the Defender.
- Given the declared stat and your available players, choose the player most likely to beat or closely challenge the stat.

Decision rules:
- Interpret the stat exactly as stated.
- Choose a player with strong historical association with that stat.
- If no player clearly beats it, choose the closest competitor.
- Do not redefine or narrow the stat.
- Consider the player's format specialization (Test, ODI, T20, IPL).
- Think about career achievements, records, and playing style.

Confidence levels:
- high: This player is historically dominant in this exact stat or very similar stats
- medium: This player is strong in this stat but may not be the absolute best
- low: This is the best available option but may not compete well

CRITICAL REASONING FORMAT:
- Keep reason to 5-10 words MAXIMUM
- Be snarky and overconfident like a sports commentator
- Act like this player will definitely beat the challenger
- Examples: "Nobody beats this legend here", "Challenge accepted, easy counter", "Challenger picked the wrong stat"

Output format (JSON only):
{
  "chosen_player_id": "<player_id>",
  "confidence_level": "<high | medium | low>",
  "reason": "<5-10 word snarky overconfident reason>"
}"""

    input_text = f"""Declared stat: {challenger_stat_description}

Available defender cards:
{json.dumps(enriched_players, indent=2)}"""
    
    out = gemini_agent.get_structured_output(system_instruction, input_text, DefenseChoice)
    return out
    



