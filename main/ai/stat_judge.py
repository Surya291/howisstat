from .llm_agents import GeminiAgent 
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional
import requests
import urllib.parse


import json
from main.config import path
with open(path("data", "player_id2player_info.json"), "r") as f:
    player_id2player_info = json.load(f)

gemini_agent = GeminiAgent("gemini-flash-latest", temperature=0.6)

class Judgement(BaseModel):
    winner: str = Field(description="The winner of the stat battle.")
    loser: str = Field(description="The loser of the stat battle.")
    stat_value: dict = Field(description="The stat value of the challenger and defender.")
    comment: str = Field(description="A single-line, savage, humorous Indian-style roast of the loser. but dont exaggerate it way too much. Make a comment on all the data that is given while keeping in mind the stat.")

def get_player_stat(player_name: str, stat_description: str) -> dict:
    qna_description = f"{player_name}: {stat_description}"
    qna_description_parsed = urllib.parse.quote(qna_description)
    url = f"https://www.espncricinfo.com/ask/_next/data/Y23c3yFF7-wh3NNz_Usz7/cricket-qna/{qna_description_parsed}.json"
    payload = {}
    headers = {
        'accept': '*/*',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36',
    }
    try:
        response = requests.get(url, headers=headers, data=payload, timeout=10)
    except requests.RequestException as e:
        print(f"REQUEST FAILED for {player_name} {stat_description}: {e}")
        return {
            "player_name": player_name,
            "parsed_data": "REQUEST FAILED"
        }

    # Try to parse response JSON
    try:
        resp_json = response.json()
    except Exception as e:
        print(f"FAILED TO PARSE JSON for {player_name} {stat_description}: {e}")
        return {
            "player_name": player_name,
            "parsed_data": "FAILED TO PARSE JSON"
        }

    # Try to get the scrappedData dictionary
    scrappedData = None
    try:
        scrappedData = resp_json["pageProps"]["parsedData"]["scrappedData"]
    except (KeyError, TypeError) as e:
        print(f"DATA NOT FOUND for {player_name} {stat_description}, KeyError: {e}")
        return {
            "player_name": player_name,
            "parsed_data": "DATA NOT FOUND"
        }

    status = scrappedData.get("status", None)
    if status != 200:
        print(f"DATA NOT FOUND or status not 200 for {player_name} {stat_description}, status: {status}")
        return {
            "player_name": player_name,
            "parsed_data": "DATA NOT FOUND"
        }

    interpreted_query = scrappedData.get("filtersData", {})
    # Try to get the actual stat data
    try:
        parsed_data = scrappedData["data"]["cmpData"]["parsedData"]
    except (KeyError, TypeError) as e:
        print(f"PARSING ERROR for {player_name} {stat_description}: {e}")
        return {
            "player_name": player_name,
            "parsed_data": "COULD NOT PARSE DATA"
        }

    if isinstance(parsed_data, list):
        parsed_data = parsed_data[:4]
    search_out = {
        "player_name": player_name,
        # "stat_description": stat_description,
        "parsed_data": parsed_data,
    }
    print(f" {player_name} {stat_description}\n\n <<<<< interpreted_query >>>>> \n", interpreted_query)
    return search_out


# def judge_stat(search_out):

#     class Judgement(BaseModel):
#         winner: str = Field(description="The winner of the stat battle.")
#         loser: str = Field(description="The loser of the stat battle.")
#         stat_value: dict = Field(description="The stat value of the challenger and defender.")
#         comment: str = Field(description="A single-line, savage, humorous Indian-style roast of the loser. but dont exaggerate it way too much. Make a comment on all the data that is given while keeping in mind the stat.")

#     system_instruction = """ROLE:
#             You are the judge of HowIsStat, a head-to-head trump-card game. Each round features a Challenger and a Defender competing on one stat. You judge only this round and decide who wins the stat battle.

#             TASK:
#             You will receive a JSON input containing challenger, defender, stat, and result.

#             Using only the result data:
#                 1.	Determine the winner and loser.
#                 2.	Assess the margin of victory (close, clear, or dominant) based on the comparison.
#                 3.	Return a JSON response with:
#                 •	winner: \"challenger\" or \"defender\"
#                 •	loser: \"challenger\" or \"defender\"
#                 •	stat_value:
#             { \"challenger_value\": \"<value>\", \"defender_value\": \"<value>\" }
#                 •	comment: a single-line, savage, humorous Indian-style roast of the loser. but dont exaggerate it way too much. Make a comment on all the data that is given while keeping in mind the stat. 

#             Comment tone rules (must scale with margin):
#                 •	Close win: sarcastic, “almost had it” energy
#                 •	Clear win: confident, dismissive roast
#                 •	Dominant win: brutal, meme-worthy humiliation

#             Global comment constraints:
#                 •	One sentence only
#                 •	No numbers
#                 •	No explanations
#                 •	Max 20 words

#             Return only valid JSON. No extra text."""

#     out = gemini_agent.get_structured_output(system_instruction, json.dumps(search_out), Judgement)
#     return out
    
# def get_judgement(challenger_player_id, defender_player_id, stat_description):
#     challenger_player_name = player_id2player_info[challenger_player_id]["name"]
#     defender_player_name = player_id2player_info[defender_player_id]["name"]
#     search_out = ask_cricinfo_api(challenger_player_name, defender_player_name, stat_description)

#     judgement = judge_stat(search_out)
#     return judgement

def judge_stat(search_out):

    class Judgement(BaseModel):
        winner: str = Field(description="The winner of the stat battle.")
        loser: str = Field(description="The loser of the stat battle.")
        stat_value: dict = Field(description="The stat value of the challenger and defender.")
        margin: str = Field(description="The margin of victory (narrow, moderate, massive).")
        comment: str = Field(description="A single-line, savage, humorous Indian-style roast of the loser. but dont exaggerate it way too much. Make a comment on all the data that is given while keeping in mind the stat.")


    system_instruction = """
        ROLE:
        You are the "Master Judge" of How.IS.STAT. You are a seasoned cricket analyst with a sharp tongue and a deep love for the game's nuances. Your job is to compare two stats and roast the loser using authentic cricket terminology.

        TASK:
        1. Extract the primary number from the challenger_data and defender_data.
        2. Determine the winner.
        3. Apply the "Cricketer's Margin Scale" for the comment:

        | Margin Type | Criteria | Tone | Cricket Vibe |
        | :--- | :--- | :--- | :--- |
        | NARROW | < 10% diff | Respectful Sledge | Focus on "fine margins," "dropped catches," or "falling short at the crease." |
        | MODERATE | 10% - 40% diff | Technical Roast | Focus on "wrong line and length," "playing across the line," or "missing the gap." |
        | MASSIVE | > 50% diff | Brutal Declaration | Focus on "follow-ons," "associates vs legends," or "sending them back to the nets." |

        CONSTRAINTS:
        - Use actual cricket metaphors (e.g., "outside edge," "stumped," "wrong 'un").
        - Exactly one sentence, max 10-15 words, no numbers.
        - Tone:  Cheeky, witty, authentic Indian cricket banter—deliver one-line roasts based on the stats, keeping it light, realistic, and funny.

        OUTPUT FORMAT (JSON ONLY):
        {
        "winner": "challenger/defender",
        "loser": "challenger/defender",
        "stat_value": { "challenger": <num>, "defender": <num> },
        "margin": "narrow/moderate/massive",
        "comment": "<The Cricket-Themed Sass>"
        }

        - If one of the player's data is not found, return the following -- give it to the one which has the metric ; say could not find data. 

    """
    out = gemini_agent.get_structured_output(system_instruction, json.dumps(search_out), Judgement)
    return out
    
def get_judgement(challenger_player_name, defender_player_name, stat_description):
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_challenger = executor.submit(get_player_stat, challenger_player_name, stat_description)
        future_defender = executor.submit(get_player_stat, defender_player_name, stat_description)
        challenger_search_out = future_challenger.result()
        defender_search_out = future_defender.result()
    search_out = {
        "stat_description": stat_description,
        "challenger": challenger_search_out,
        "defender": defender_search_out,
    }
    judgement = judge_stat(search_out)
    return judgement


