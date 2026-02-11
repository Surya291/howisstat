import os
import sys
from dotenv import load_dotenv

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _repo_root)
load_dotenv(os.path.join(_repo_root, "secrets", ".env"))

from main.deal_cards import deal_player_cards
game_config = {
    "year_list": ["2025"],
    "number_of_players": 7,
    "self_franchise": "RCB",
    "opponent_franchise": "CSK",
}
# player_cards, opponent_cards = deal_player_cards(game_config)
# print("\n\n")
# print("--------------------------------")
# print("player_cards: \n", player_cards)
# print("opponent_cards: \n", opponent_cards)
# print("--------------------------------")

game_info = deal_player_cards(game_config)
# Print self team and opponent team with neat numbering and a brief description for each

# print(game_info)

print("\n===== Self Team ({}) =====".format(game_config["self_franchise"]))
for idx, player_id in enumerate(game_info["self_player_ids"], 1):
    player = game_info["player_id2player_info"][player_id]
    name = player.get("display_name") 
    country = player.get("country")
    role = player.get("role")
    desc = "{} [{}] | {}".format(name, country, role)
    print(f"#{idx}: {desc}")

print("\n===== Opponent Team ({}) =====".format(game_config["opponent_franchise"]))
for idx, player_id in enumerate(game_info["opponent_player_ids"], 1):
    player = game_info["player_id2player_info"][player_id]
    # print(player)
    name = player.get("display_name") 
    country = player.get("country")
    role = player.get("role")
    desc = "{} [{}] | {}".format(name, country, role)
    print(f"#{idx}: {desc}")
