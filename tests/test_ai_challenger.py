

import os,sys 
from dotenv import load_dotenv
load_dotenv("/Users/surya/Desktop/toy_projects/cricinfo-mcp/secrets/.env")


sys.path.append("/Users/surya/Desktop/toy_projects/howisstat")

from main.ai.ai_challenger import get_stat_challenge
player_info = {'display_name': 'Shreyas Gopal', 'headshot_url': 'https://a.espncdn.com/i/headshots/cricket/players/full/344580.png', 'role': 'Allrounder', 'country': 'IND', 'dob': '1993-09-04T00:00Z', 'batting_style': 'Right-Hand Bat', 'bowling_style': 'Legbreak', 'franchise': 'CSK'}

challenge = get_stat_challenge(player_info)

print("\n" + "="*60)
print("CHALLENGE RESULT:")
print("="*60)
print(f"Stat Description: {challenge['stat_description']}")
print(f"Reason: {challenge['reason']}")
print("="*60)

