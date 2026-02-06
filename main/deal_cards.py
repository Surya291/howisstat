import json
import random

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




    with open("/Users/surya/Desktop/toy_projects/howisstat/data/player_id2player_info.json", "r") as f:
        player_id2player_info = json.load(f)

    player_info = player_id2player_info[player_id] 


    style_list = player_info["style"] 
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

    filtered_player_info = {
        "display_name": player_info["display_name"],
        "headshot_url": player_info["headshot"]["href"],
        "role": player_info["position"]["name"],
        "country": get_country_name(player_info["country"]),
        "dob": player_info["date_of_birth"], 
        "batting_style": batting_style,
        "bowling_style": bowling_style,
    }
    return filtered_player_info







def get_role2player_ids(year_list, franchise):

    with open("/Users/surya/Desktop/toy_projects/howisstat/data/player_id2player_info.json", "r") as f:
        player_id2player_info = json.load(f)

    with open("/Users/surya/Desktop/toy_projects/howisstat/data/team2year2player_ids.json", "r") as f:
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
    team_players = []
    # BAT 
    bat_players = random.sample(role2player_ids["BAT"], 2)
    wk_players = random.sample(role2player_ids["WK"], 1)
    bowl_players = random.sample(role2player_ids["BOWL"], 2)
    all_rounder_players = random.sample(role2player_ids["ALL_ROUNDER"], 2)

    team_players = bat_players + wk_players + all_rounder_players+ bowl_players 
    return team_players


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


