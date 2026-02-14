
from .llm_agents import GeminiAgent 
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional
import json


gemini_agent = GeminiAgent("gemini-flash-latest", temperature=0.6)


class StatChallenge(BaseModel):
    stat_description: str = Field(description="A broad cricket stat description that gives the player the best chance of winning.")
    reason: str = Field(description="Short, snarky 5-10 word overconfident commentary on why this stat wins.")

def get_gully_prompt() -> str:
    print("test2")
    return """You are the Challenger in a cricket trump-card game called HOW.IS.STAT (BEGINNER MODE).

    GAME LOGIC:
    - Your output will be used to query AskCricinfo: "[] [stat_description] does [Player Name] have?"
    - A "Stat Judge" compares the results. 
    - NOTE: AskCricinfo does NOT support percentages (e.g., "dot ball %"). Use raw values only.
    - Make sure to mix up the stat formats—alternate between IPL, ODI, T20I, and Test. Don’t limit yourself to a single format.

    STAT SELECTION RULES (CRITICAL):
    1. KEYWORD INTEGRATION: To help the engine, you MUST use the keywords "batter", "bowler", "fielder", "wicketkeeper" and the specific format.
    2. FORMAT: Use the structure: "{Role} with {Metric} in {Format}"
    3. NO SUPERLATIVES: Never use "Most". 
    - For career totals: Use "No. of [Metric]" (e.g., "Batter with No. of sixes in IPL").
    - For peak records: Use "Highest [Metric] in an innings" (e.g., "Batter with Highest score in an innings in ODIs").
    4. RATE-BASED STATS: For Strike Rate or Economy, you must include a minimum threshold and the specific role.
    - Format: "Batter with strike rate in IPL (min 500 runs)"
    - Format: "Bowler with economy rate in T20Is (min 20 overs)"
    - Format: "Fielder with most catches in a single IPL innings"

    5. SUPPORTED TOURNAMENTS: TEST, ODI, T20I, IPL 

    STRATEGY:
    - If your player is a legendary batter, pick a counting stat like "No. of sixes" or "No. of centuries".
    - If they are a clinical bowler, pick "No. of wickets" or "No. of five-wicket hauls".

    REASONING PERSONA:
    - Keep the reason to 5-10 words MAXIMUM.
    - Tone: Snarky, overconfident, elite commentator. Make it feel like an insult to the opponent.

    OUTPUT FORMAT (JSON ONLY):
    {
    "stat_description": "<Role> with <Metric> in <Format>",
    "reason": "<5-10 word snarky reason>"
    }

    EXAMPLES:
    - { "stat_description": "Batter with No. of sixes in IPL", "reason": "He clears the ropes while your guy is still grounding his bat." }
    - { "stat_description": "Bowler with No. of wickets in Tests", "reason": "A wicket-taking machine. Your batter should just stay in the pavilion." }
    - { "stat_description": "Batter with Highest score in an innings in ODIs", "reason": "This knock alone is more than your player's career total." }
    - { "stat_description": "Bowler with economy rate in T20Is (min 30 overs)", "reason": "He’s stingier than a billionaire at a charity auction.
    - { "stat_description": "total score in a ODI world cup edition", "reason": "He’s stingier than a billionaire at a charity auction.

    " }
        """
    

def get_stat_challenge(player_info: dict, difficulty: str = "S") -> dict:
    """
    Given player info, return a cricket stat declaration that gives them the best chance of winning.
    
    Args:
        player_info: The player's info dictionary
        {'display_name': 'Ruturaj Gaikwad', 'headshot_url': 'https://a.espncdn.com/i/headshots/cricket/players/full/1060380.png', 'role': 'Batter', 'country': 'IND', 'dob': '1997-01-31T00:00Z', 'batting_style': 'Right-Hand Bat', 'bowling_style': 'Right-Arm Offbreak', 'franchise': 'CSK'}
        difficulty: "G" (Gully), "D" (Domestic), or "S" (Sachin). Default: "S"
        
    Returns:
        dict with 'stat_description' and 'reason'
    """
    if not player_info:
        raise ValueError(f"Player info not provided or invalid")
    

    player_card = f""" 
    Name: {player_info['display_name']}
    Role: {player_info['role']}
    Country: {player_info['country']}
    Batting Style: {player_info['batting_style']}
    Bowling Style: {player_info['bowling_style']}
    Franchise: {player_info['franchise']}
    """ 

    # Select prompt based on difficulty
    # if difficulty == "G":
    #     system_instruction = get_gully_prompt()
    # elif difficulty == "D":
    #     system_instruction = get_domestic_prompt()
    # else:  # "S" or default
    #     system_instruction = get_sachin_prompt()

    system_instruction = get_gully_prompt()

    input_text = f"Player Card: {player_card}"
    
    out = gemini_agent.get_structured_output(system_instruction, input_text, StatChallenge)
    return out

