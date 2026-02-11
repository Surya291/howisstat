import os
import sys
from dotenv import load_dotenv

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _repo_root)
load_dotenv(os.path.join(_repo_root, "secrets", ".env"))
from main.ai.stat_judge import get_judgement


attacker_player_id = "abhishek-sharma-1070183"
defender_player_id = "virat-kohli-253802"


attacker_player_id = "yuzvendra-chahal-430246" 
defender_player_id = "rashid-khan-793463"

# stat = "batting strike rate in t20is"
# stat = "no of boundaries hit in t20is"
# stat = "bowling average in t20is"
stat = "most wickets in IPL"

judgement_dict = get_judgement(attacker_player_id, defender_player_id, stat)
print("\n", "****"*5, "\n")
for key, value in judgement_dict.items():
    if value == "challenger":
        value = attacker_player_id
    elif value == "defender":
        value = defender_player_id

    print(f"*{key}*: {value}")

print("\n", "****"*5, "\n")

