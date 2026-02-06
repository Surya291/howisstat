import os,sys 
from dotenv import load_dotenv
load_dotenv("/Users/surya/Desktop/toy_projects/cricinfo-mcp/secrets/.env")


sys.path.append("/Users/surya/Desktop/toy_projects/howisstat")
from main.ai.stat_judge import get_judgement


attacker_player_id = "abhishek-sharma-1070183"
defender_player_id = "virat-kohli-253802"
# stat = "batting strike rate in t20is"
stat = "no of boundaries hit in t20is"

judgement_dict = get_judgement(attacker_player_id, defender_player_id, stat)
print("\n", "****"*5, "\n")
for key, value in judgement_dict.items():
    if value == "challenger":
        value = attacker_player_id
    elif value == "defender":
        value = defender_player_id

    print(f"*{key}*: {value}")

print("\n", "****"*5, "\n")

