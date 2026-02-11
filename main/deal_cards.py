import json
import random
import os

from .config import path

position_grp2classes = {
    "BAT": ['Batter', 'Middle-order batter', 'Opening batter', 'Top-order batter'],
    "BOWL": ['Bowler', 'Bowling allrounder'],
    "ALL_ROUNDER": ['Allrounder', 'Batting allrounder'],
    "WK": ['Wicketkeeper', 'Wicketkeeper batter'],
}
# Create the inverse mapping from class (e.g. "Batter") to position group (e.g. "BAT" )
class2position_grp = {}
for position_grp, classes in position_grp2classes.items():
    for cls in classes:
        class2position_grp[cls] = position_grp


def get_player_info(player_id):

    def get_country_name(country_id): 


        country_map = {
            "2": "AUS",
            "25": "BAN",
            "1": "ENG",
            "6": "IND",
            "5": "NZ",
            "7": "PAK",
            "3": "SA",
            "8": "SL",
            "4": "WI",
            "9": "ZIM",
            "40": "AFG",
            "17": "CAN",
            "29": "IRE",
            "26": "KEN",
            "15": "NED",
            "30": "SCO",
            "11": "USA",
        }
        return country_map.get(str(country_id), "UKN")
        # return country_emojis.get(country_map.get(str(country_id), "UKN"), "UKN")

    def get_style(style):
        style_description_map = {
            'Right-hand bat': 'Right-Hand Bat',
            'Left-hand bat': 'Left-Hand Bat',
            'Right-arm medium': 'Right-Arm Medium',
            'Right-arm offbreak': 'Right-Arm Offbreak',
            'Slow left-arm orthodox': 'Slow Left-Arm Orthodox',
            'Right-arm medium-fast': 'Right-Arm Medium-Fast',
            'Legbreak': 'Legbreak',
            'Legbreak googly': 'Legbreak Googly',
            'Right-arm fast': 'Right-Arm Fast',
            'Left-arm medium': 'Left-Arm Medium',
            'Right-arm fast-medium': 'Right-Arm Fast-Medium',
            'Left-arm medium-fast': 'Left-Arm Medium-Fast',
            'Left-arm wrist-spin': 'Left-Arm Wrist-Spin',
            'Left-arm fast-medium': 'Left-Arm Fast-Medium',
            'Right-arm slow-medium': 'Right-Arm Slow-Medium',
            'Left-arm fast': 'Left-Arm Fast',
            'Right-arm bowler': 'Right-Arm Bowler'
        }

        return style_description_map.get(style, "")




    with open(path("data", "player_id2player_info.json"), "r") as f:
        player_id2player_info = json.load(f)

    player_info = player_id2player_info[player_id] 


    style_list = player_info["style"] 
    try: 
        suggestion = player_info["suggestion"]["casual_stat_description"]
    except:
        suggestion = None
    batting_style_list = []
    bowling_style_list = []
    for style in style_list:
        if style["type"] == "batting":
            batting_style_list.append(get_style(style["description"]))
        if style["type"] == "bowling":
            bowling_style_list.append(get_style(style["description"]))

    if batting_style_list:
        batting_style = " / ".join(batting_style_list)
    else:
        batting_style = None
    if bowling_style_list:
        bowling_style = " / ".join(bowling_style_list)
    else:
        bowling_style = None

    headshot_href = player_info["headshot"]["href"]
    headshots_dir = path("web", "public", "headshots")
    headshot_path = os.path.join(headshots_dir, headshot_href.split("/")[-1])
    if not os.path.exists(headshot_path):
        headshot_path = path("web", "public", "headshots", "default-player-logo-500.png")


    filtered_player_info = {
        "display_name": player_info["display_name"],
        "headshot_url": player_info["headshot"]["href"],
        "headshot_path": headshot_path,
        "role": player_info["position"]["name"],
        "country": get_country_name(player_info["country"]),
        "dob": player_info["date_of_birth"], 
        "batting_style": batting_style,
        "bowling_style": bowling_style,
        "suggestion": suggestion,
    }
    return filtered_player_info







def get_role2player_ids(year_list, franchise):

    with open(path("data", "player_id2player_info.json"), "r") as f:
        player_id2player_info = json.load(f)

    with open(path("data", "filtered_team2year2player_ids.json"), "r") as f:
        team2year2player_ids = json.load(f)

    all_franchise_players = []
    franchise_players = team2year2player_ids[franchise]
    for year in year_list:
        all_franchise_players.extend(franchise_players[(year)])

    all_franchise_players = list(set(all_franchise_players))
    print("TOTAL FILTERED PLAYERS: ", len(all_franchise_players))
    player2ipl_matches = {}
    role2player_ids = {} 

    for player_id in all_franchise_players:
        try: 
            player_info = player_id2player_info[player_id]
            # player2ipl_matches[player_id] = player_info["ipl_matches"]
            role = class2position_grp[player_info["position"]["name"]]
            if role not in role2player_ids:
                role2player_ids[role] = []
            role2player_ids[role].append(player_id)
        except: 
            # print("!! player_id not found: ", player_id)
            pass
    return role2player_ids



def deal_team_players(role2player_ids, number_of_players):
    import random

    # Team role requirements
    ROLE_ORDER = ["BAT", "ALL_ROUNDER", "WK", "BOWL"]
    role_counts = {"BAT": 2, "ALL_ROUNDER": 2, "WK": 1, "BOWL": 2}

    # Helper for safe sampling
    def safe_sample(role_key, n, exclude=None):
        arr = role2player_ids.get(role_key, [])
        if exclude:
            arr = [pid for pid in arr if pid not in exclude]
        if not arr or n <= 0:
            return []
        return random.sample(arr, min(len(arr), n))

    selected = {role: [] for role in ROLE_ORDER}
    total_selected = 0

    # 1. Try to fill BAT, WK, BOWL from their own pools
    for role in ["BAT", "WK", "BOWL"]:
        picked = safe_sample(role, role_counts[role])
        selected[role].extend(picked)
        total_selected += len(picked)

    # 2. If any of the above roles have shortfall, try to fill from ALL_ROUNDER
    used_players = set(pid for plist in selected.values() for pid in plist)
    all_rounder_pool = role2player_ids.get("ALL_ROUNDER", [])
    all_rounder_pool = [pid for pid in all_rounder_pool if pid not in used_players]
    all_rounder_to_assign = role_counts["ALL_ROUNDER"]

    for role in ["BAT", "WK", "BOWL"]:
        needed = role_counts[role] - len(selected[role])
        if needed > 0 and all_rounder_pool:
            can_give = min(needed, len(all_rounder_pool))
            additional = random.sample(all_rounder_pool, can_give)
            selected[role].extend(additional)
            # Remove from pool, decrease all_rounder_to_assign accordingly
            all_rounder_pool = [pid for pid in all_rounder_pool if pid not in additional]
            all_rounder_to_assign -= len(additional)
            total_selected += len(additional)

    # 3. Fill ALL_ROUNDER role (with what remains from ALL_ROUNDER pool)
    if all_rounder_to_assign > 0 and all_rounder_pool:
        picked = safe_sample("ALL_ROUNDER", all_rounder_to_assign, exclude=used_players)
        selected["ALL_ROUNDER"].extend(picked)
        total_selected += len(picked)
        used_players.update(picked)

    # 4. If still not enough, fill with any leftover ALL_ROUNDER first, then any role
    # At the end, we want to return a list in strict order: BAT, ALL_ROUNDER, WK, BOWL
    flat_selected = []
    for role in ROLE_ORDER:
        flat_selected.extend(selected[role])
    used_players = set(flat_selected)

    if len(flat_selected) < number_of_players:
        # Prefer remaining ALL_ROUNDERs
        more_all_rounders = [pid for pid in role2player_ids.get("ALL_ROUNDER", []) if pid not in used_players]
        to_add = min(number_of_players - len(flat_selected), len(more_all_rounders))
        if to_add > 0:
            flat_selected.extend(random.sample(more_all_rounders, to_add))
            used_players.update(flat_selected)
        # If still short, pad with anyone from any role (not already picked)
        if len(flat_selected) < number_of_players:
            remaining = []
            for ids in role2player_ids.values():
                for pid in ids:
                    if pid not in used_players:
                        remaining.append(pid)
            n_needed = number_of_players - len(flat_selected)
            flat_selected.extend(random.sample(remaining, min(n_needed, len(remaining))))
            used_players.update(flat_selected)

    # Truncate if needed
    flat_selected = flat_selected[:number_of_players]

    # Now, sort flat_selected by role in required order (BAT, ALL_ROUNDER, WK, BOWL)
    role_priority = {role: i for i, role in enumerate(ROLE_ORDER)}

    # Build reverse mapping from player_id to their role
    pid2role = {}
    for role in ROLE_ORDER:
        for pid in role2player_ids.get(role, []):
            if pid not in pid2role:
                pid2role[pid] = role

    # Get sort key
    def sort_key(pid):
        return role_priority.get(pid2role.get(pid, ""), 99)

    # Stable sort by priority: preserve deal order within same role
    flat_selected_sorted = sorted(flat_selected, key=sort_key)
    return flat_selected_sorted


def deal_player_cards(game_config):
    """ 
    Game config:
    - year list: ["2025", "2024", "2023", "2022", "2021", "2020"]
    - number of players: 7 
    - self franchise: ['RCB', 'CSK', 'DECCAN', 'DC/DD', 'PBKS/KXIP', 'KKR', 'MI', 'RR', 'KTK', 'PWI', 'SRH', 'DC', 'GT', 'LSG', 'GL', 'RPS']
    - opponent franchise : same 
    """ 

    year_list = game_config["year_list"]
    number_of_players = game_config["number_of_players"]
    self_franchise = game_config["self_franchise"]
    opponent_franchise = game_config["opponent_franchise"]

    # get all the players from the self_franchise
    self_role2player_ids = get_role2player_ids(year_list, self_franchise)
    opponent_role2player_ids = get_role2player_ids(year_list, opponent_franchise)

    # deal the cards
    self_cards = deal_team_players(self_role2player_ids, number_of_players)
    opponent_cards = deal_team_players(opponent_role2player_ids, number_of_players)

    player_id2player_info = {}

    for player_id in self_cards:
        player_id2player_info[player_id] = get_player_info(player_id)
        player_id2player_info[player_id]["franchise"] = self_franchise


    for player_id in opponent_cards:
        player_id2player_info[player_id] = get_player_info(player_id) 
        player_id2player_info[player_id]["franchise"] = opponent_franchise

    game_info = {
        "self_player_ids": self_cards,
        "opponent_player_ids": opponent_cards,
        "player_id2player_info": player_id2player_info,
    }

    return game_info


