## given a player id, and a stat, return the player's performance in that stat


from .llm_agents import GeminiAgent 
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional
import requests
import urllib.parse


import json
with open("/Users/surya/Desktop/toy_projects/howisstat/data/player_id2player_info.json", "r") as f:
    player_id2player_info = json.load(f)

gemini_agent = GeminiAgent("gemini-flash-latest")

class Judgement(BaseModel):
    winner: str = Field(description="The winner of the stat battle.")
    loser: str = Field(description="The loser of the stat battle.")
    stat_value: dict = Field(description="The stat value of the challenger and defender.")
    comment: str = Field(description="A single-line, savage, humorous Indian-style roast of the loser. but dont exaggerate it way too much. Make a comment on all the data that is given while keeping in mind the stat.")


def ask_cricinfo_api(challenger_player_name, defender_player_name, stat_description):
    qna_description = f'{challenger_player_name} and {defender_player_name} : {stat_description}'
    tournament_id = "allintls" #"menst20i" # "ipl", "allintls", "odi"
    qna_description_parsed = urllib.parse.quote(qna_description)

    url = f"https://www.espncricinfo.com/ask/_next/data/Y23c3yFF7-wh3NNz_Usz7/cricket-qna/{qna_description_parsed}%26tournament%3D{tournament_id}.json"
    payload = {}
    headers = {
        'accept': '*/*',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36',
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    out = response.json()["pageProps"]["parsedData"]["scrappedData"]
    status = out["status"]
    interpreted_query = out["filtersData"]  
    parsed_data = out["data"]["cmpData"]

    assert status == 200, "ask info failed, status: " + str(status)
    search_out = {
        "challenger": challenger_player_name,
        "defender": defender_player_name,
        "stat": stat_description,
        "result": parsed_data
    }
    print("\n\n <<<<< interpreted_query >>>>> \n", interpreted_query)
    return search_out


def judge_stat(search_out):

    class Judgement(BaseModel):
        winner: str = Field(description="The winner of the stat battle.")
        loser: str = Field(description="The loser of the stat battle.")
        stat_value: dict = Field(description="The stat value of the challenger and defender.")
        comment: str = Field(description="A single-line, savage, humorous Indian-style roast of the loser. but dont exaggerate it way too much. Make a comment on all the data that is given while keeping in mind the stat.")

    system_instruction = """ROLE:
            You are the judge of HowIsStat, a head-to-head trump-card game. Each round features a Challenger and a Defender competing on one stat. You judge only this round and decide who wins the stat battle.

            TASK:
            You will receive a JSON input containing challenger, defender, stat, and result.

            Using only the result data:
                1.	Determine the winner and loser.
                2.	Assess the margin of victory (close, clear, or dominant) based on the comparison.
                3.	Return a JSON response with:
                •	winner: \"challenger\" or \"defender\"
                •	loser: \"challenger\" or \"defender\"
                •	stat_value:
            { \"challenger_value\": \"<value>\", \"defender_value\": \"<value>\" }
                •	comment: a single-line, savage, humorous Indian-style roast of the loser. but dont exaggerate it way too much. Make a comment on all the data that is given while keeping in mind the stat. 

            Comment tone rules (must scale with margin):
                •	Close win: sarcastic, “almost had it” energy
                •	Clear win: confident, dismissive roast
                •	Dominant win: brutal, meme-worthy humiliation

            Global comment constraints:
                •	One sentence only
                •	No numbers
                •	No explanations
                •	Max 20 words

            Return only valid JSON. No extra text."""

    out = gemini_agent.get_structured_output(system_instruction, json.dumps(search_out), Judgement)
    return out
    


def get_judgement(challenger_player_id, defender_player_id, stat_description):
    challenger_player_name = player_id2player_info[challenger_player_id]["name"]
    defender_player_name = player_id2player_info[defender_player_id]["name"]
    search_out = ask_cricinfo_api(challenger_player_name, defender_player_name, stat_description)

    judgement = judge_stat(search_out)
    return judgement




