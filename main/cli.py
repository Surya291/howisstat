#!/usr/bin/env python3
"""
HowisStat Terminal CLI - V1 Game Driver

Terminal-based game loop for HowisStat.
Handles setup, input/output, and coordinates game engine with AI modules.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add project root to path (before imports)
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _repo_root)
load_dotenv(os.path.join(_repo_root, "secrets", ".env"))


from main.game_engine import (
    GameState, 
    RoundResult,
    create_initial_state,
    resolve_round,
    get_available_franchises,
    get_available_years,
    validate_franchise_year
)
from main.deal_cards import deal_player_cards
from main.ai.ai_challenger import get_stat_challenge
from main.ai.ai_defender import get_defense_choice


# ============================================================================
# COLORS AND FORMATTING UTILITIES
# ============================================================================

class Colors:
    """Hermes-inspired color palette for premium terminal experience."""
    # Primary Hermes colors
    HERMES_ORANGE = '\033[38;5;208m'  # Signature orange - main highlights
    BURNT_ORANGE = '\033[38;5;166m'   # Darker orange - errors, warnings
    
    # Warm earth tones
    TAN = '\033[38;5;180m'            # Warm tan - user content, success
    CREAM = '\033[38;5;223m'          # Light cream - metadata, info
    BROWN = '\033[38;5;130m'          # Rich brown - AI content
    GOLD = '\033[38;5;220m'           # Gold accent - special emphasis
    
    # Neutrals
    BOLD = '\033[1m'
    RESET = '\033[0m'


def get_country_flag_emoji(country_name: str) -> str:
    """
    Map country name to flag emoji.
    
    Args:
        country_name: Country name
        
    Returns:
        Flag emoji or empty string
    """
    flag_map = {
        "India": "🇮🇳",
        "Australia": "🇦🇺",
        "England": "🇬🇧",
        "South Africa": "🇿🇦",
        "New Zealand": "🇳🇿",
        "Pakistan": "🇵🇰",
        "Sri Lanka": "🇱🇰",
        "Bangladesh": "🇧🇩",
        "Afghanistan": "🇦🇫",
        "West Indies": "🇼🇮",
        "Zimbabwe": "🇿🇼",
        "Ireland": "🇮🇪",
        "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
        "Netherlands": "🇳🇱",
        "UAE": "🇦🇪",
    }
    return flag_map.get(country_name, "")


def format_player_card(player_info: dict, index: int) -> str:
    """
    Format player card with role, styles, and country flag.
    
    Format: #N PlayerName 🏳️ • Role • [Batting Style <> Bowling Style]
    
    Args:
        player_info: Player information dict
        index: Card number (1-based)
        
    Returns:
        Formatted player card string
    """
    name = player_info["display_name"]
    country = player_info.get("country", "")
    flag = get_country_flag_emoji(country)
    role = player_info["role"]
    batting_style = player_info.get("batting_style")
    bowling_style = player_info.get("bowling_style")
    
    # Build the card string
    card = f"#{index} {name}"
    if flag:
        card += f" {flag}"
    card += f" • {role}"
    
    # Add styles if present
    styles = []
    if batting_style:
        styles.append(batting_style)
    if bowling_style:
        styles.append(bowling_style)
    
    if styles:
        card += " • [" + " <> ".join(styles) + "]"
    
    return card


def wrap_text(text: str, width: int) -> list:
    """
    Wrap text to fit within specified width.
    
    Args:
        text: Text to wrap
        width: Maximum width
        
    Returns:
        List of wrapped lines
    """
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines if lines else [""]


def create_dialogue_box(title: str, message: str, reasoning: str = None, width: int = 60) -> str:
    """
    Create a clean dialogue box for AI messages and judge comments.
    
    Args:
        title: Box title
        message: Main message
        reasoning: Optional reasoning text
        width: Box width
        
    Returns:
        Multi-line formatted box string
    """
    lines = []
    
    # Top border
    lines.append("┌" + "─" * (width - 2) + "┐")
    
    # Title
    title_padded = f" {title} ".ljust(width - 2)
    lines.append("│" + title_padded + "│")
    
    # Separator
    lines.append("├" + "─" * (width - 2) + "┤")
    
    # Message (wrapped)
    message_lines = wrap_text(message, width - 4)
    for line in message_lines:
        padded = f" {line} ".ljust(width - 2)
        lines.append("│" + padded + "│")
    
    # Reasoning if provided
    if reasoning:
        lines.append("│" + " " * (width - 2) + "│")
        reasoning_label = f" Reasoning: {reasoning}"
        reasoning_lines = wrap_text(reasoning_label, width - 4)
        for line in reasoning_lines:
            padded = f" {line} ".ljust(width - 2)
            lines.append("│" + padded + "│")
    
    # Bottom border
    lines.append("└" + "─" * (width - 2) + "┘")
    
    return "\n".join(lines)


def create_comment_box(comment: str, width: int = 50) -> str:
    """
    Create a simple comment box.
    
    Args:
        comment: Comment text
        width: Box width
        
    Returns:
        Multi-line formatted box string
    """
    lines = []
    
    # Top border
    lines.append("┌" + "─" * (width - 2) + "┐")
    
    # Comment (wrapped)
    comment_lines = wrap_text(comment, width - 4)
    for line in comment_lines:
        padded = f" {line} ".ljust(width - 2)
        lines.append("│" + padded + "│")
    
    # Bottom border
    lines.append("└" + "─" * (width - 2) + "┘")
    
    return "\n".join(lines)


# ============================================================================
# GAME FUNCTIONS
# ============================================================================

def print_separator(char="=", length=60):
    """Print a separator line."""
    print(char * length)


def print_header(text):
    """Print a header with separators."""
    print()
    print_separator("=", 80)
    print(f"{Colors.HERMES_ORANGE}{Colors.BOLD}  {text}{Colors.RESET}")
    print_separator("=", 80)
    print()


def prompt_franchise(prompt_text: str) -> str:
    """
    Prompt user to select a franchise with validation.
    
    Args:
        prompt_text: Text to display for prompt
        
    Returns:
        Valid franchise name
    """
    franchises = get_available_franchises()
    
    print(f"\n{Colors.HERMES_ORANGE}{Colors.BOLD}{prompt_text}{Colors.RESET}")
    print(f"\n{Colors.CREAM}Available franchises:{Colors.RESET}")
    for i, franchise in enumerate(franchises, 1):
        # Display in 3 columns
        if i % 3 == 1:
            print(f"  {franchise:15}", end="")
        elif i % 3 == 2:
            print(f"{franchise:15}", end="")
        else:
            print(f"{franchise}")
    if len(franchises) % 3 != 0:
        print()  # End line if needed
    
    while True:
        franchise = input(f"\n{Colors.TAN}Enter franchise: {Colors.RESET}").strip()
        if franchise in franchises:
            return franchise
        print(f"{Colors.BURNT_ORANGE}Invalid franchise '{franchise}'. Please choose from the list above.{Colors.RESET}")


def prompt_year(franchise: str) -> list:
    """
    Prompt user to select year(s) for the franchise with validation.
    
    Args:
        franchise: The franchise to get years for
        
    Returns:
        List of valid year strings (can be single or multiple)
    """
    years = get_available_years(franchise)
    
    print(f"\n{Colors.CREAM}Available years for {Colors.BOLD}{franchise}{Colors.RESET}{Colors.CREAM}:{Colors.RESET}")
    print(f"  {Colors.CREAM}" + ", ".join(years) + f"{Colors.RESET}")
    print(f"  {Colors.HERMES_ORANGE}(Enter at least 3 years, separated by commas){Colors.RESET}")
    
    while True:
        year_input = input(f"\n{Colors.TAN}Enter year(s): {Colors.RESET}").strip()
        
        # Parse comma-separated years
        selected_years = [y.strip() for y in year_input.split(",")]
        
        if len(selected_years) < 3:
            print(f"{Colors.BURNT_ORANGE}Please enter at least 3 years (e.g., 2022, 2023, 2024).{Colors.RESET}")
            continue
        
        # Validate all years
        invalid_years = [y for y in selected_years if y not in years]
        if invalid_years:
            print(f"{Colors.BURNT_ORANGE}Invalid year(s): {', '.join(invalid_years)}.{Colors.RESET}")
            print(f"{Colors.HERMES_ORANGE}Please choose from: {', '.join(years)}{Colors.RESET}")
            continue
        
        return selected_years


def prompt_difficulty() -> str:
    """
    Prompt user to select difficulty level.
    
    Returns:
        "G", "D", or "S"
    """
    print(f"\n{Colors.HERMES_ORANGE}{Colors.BOLD}SELECT DIFFICULTY LEVEL{Colors.RESET}")
    print(f"\n{Colors.CREAM}Available difficulties:{Colors.RESET}")
    print(f"  {Colors.TAN}G - Gully{Colors.RESET}        (Beginner: Simple stats, 50-50 chance)")
    print(f"  {Colors.HERMES_ORANGE}D - Domestic{Colors.RESET}     (Intermediate: Broad stats, balanced)")
    print(f"  {Colors.GOLD}S - Sachin Mode{Colors.RESET}  (Expert: Deep stats, maximum difficulty)")
    
    while True:
        difficulty = input(f"\n{Colors.TAN}Enter difficulty (G/D/S): {Colors.RESET}").strip().upper()
        if difficulty in ["G", "D", "S"]:
            return difficulty
        print(f"{Colors.BURNT_ORANGE}Invalid choice. Please enter G, D, or S.{Colors.RESET}")


def difficulty_name(code: str) -> str:
    """Convert difficulty code to display name."""
    return {"G": "Gully", "D": "Domestic", "S": "Sachin Mode"}[code]


def confidence_emoji(level: str) -> str:
    """Convert confidence level to emoji."""
    return {"high": "🔥", "medium": "⚡", "low": "🤞"}[level]


def setup_game() -> GameState:
    """
    Handle game setup: franchise/year selection and card dealing.
    
    Returns:
        Initial GameState
    """
    print_header("HOWISSTAT - Setup")
    
    # Prompt for franchises
    self_franchise = prompt_franchise("SELECT YOUR FRANCHISE")
    opponent_franchise = prompt_franchise("\nSELECT OPPONENT FRANCHISE")
    
    # Prompt for years (now returns a list, validate ALL for both franchises)
    while True:
        year_list = prompt_year(self_franchise)
        
        # Check if ALL years are valid for opponent too
        invalid_for_opponent = []
        opponent_years = get_available_years(opponent_franchise)
        
        for year in year_list:
            if not validate_franchise_year(opponent_franchise, year):
                invalid_for_opponent.append(year)
        
        if invalid_for_opponent:
            print(f"\n{Colors.BURNT_ORANGE}Year(s) {', '.join(invalid_for_opponent)} not available for {opponent_franchise}.{Colors.RESET}")
            print(f"{Colors.CREAM}Available years for {opponent_franchise}: {', '.join(opponent_years)}{Colors.RESET}")
            print(f"{Colors.HERMES_ORANGE}All years must be valid for both franchises.{Colors.RESET}")
            continue
        
        break
    
    # Prompt for difficulty
    difficulty = prompt_difficulty()
    
    # Build game config
    game_config = {
        "year_list": year_list,
        "number_of_players": 7,
        "self_franchise": self_franchise,
        "opponent_franchise": opponent_franchise,
        "difficulty": difficulty
    }
    
    # Deal cards
    print(f"\n{Colors.CREAM}" + "~" * 80 + f"{Colors.RESET}")
    print(f"{Colors.HERMES_ORANGE}{Colors.BOLD}  Dealing cards...{Colors.RESET}")
    print(f"{Colors.CREAM}" + "~" * 80 + f"{Colors.RESET}")
    time.sleep(1)  # Drum roll effect
    
    game_info = deal_player_cards(game_config)
    
    # Create initial state
    state = create_initial_state(
        game_config,
        game_info["self_player_ids"],
        game_info["opponent_player_ids"],
        game_info["player_id2player_info"]
    )
    
    print(f"\n{Colors.TAN}✓ Cards dealt!{Colors.RESET}")
    print(f"  {Colors.CREAM}Your team: {Colors.BOLD}{self_franchise}{Colors.RESET}")
    print(f"  {Colors.CREAM}Opponent: {Colors.BOLD}{opponent_franchise}{Colors.RESET}")
    years_display = ", ".join(year_list)
    print(f"  {Colors.CREAM}Year(s): {Colors.BOLD}{years_display}{Colors.RESET}")
    print(f"  {Colors.CREAM}Difficulty: {Colors.BOLD}{difficulty_name(difficulty)}{Colors.RESET}")
    print(f"  {Colors.CREAM}Cards each: {Colors.BOLD}7{Colors.RESET}")
    
    # Show user's cards
    print(f"\n{Colors.HERMES_ORANGE}{Colors.BOLD}YOUR CARDS:{Colors.RESET}")
    print("┌" + "─" * 78 + "┐")
    for i, player_id in enumerate(state.user_deck, 1):
        player_info = state.player_id2player_info[player_id]
        card_display = format_player_card(player_info, i)
        card_line = f" {card_display}".ljust(78)
        print(f"│{card_line}│")
    print("└" + "─" * 78 + "┘")
    
    return state


def show_visibility(state: GameState):
    """
    Show cards based on current role visibility rules.
    
    Challenger sees: only top card name + deck sizes
    Defender sees: all their cards (names, numbered) + deck sizes
    """
    print()
    print("┌" + "─" * 78 + "┐")
    
    if state.challenger == "user":
        # User is challenger - show only top card
        top_card_id = state.user_deck[0]
        player_info = state.player_id2player_info[top_card_id]
        card_display = format_player_card(player_info, 1)
        
        role_text = f"{Colors.TAN}{Colors.BOLD}YOUR ROLE: Challenger{Colors.RESET}".ljust(94)
        print(f"│ {role_text} │")
        print("├" + "─" * 78 + "┤")
        print(f"│ {Colors.HERMES_ORANGE}Your card (forced):{Colors.RESET}                                                    │")
        card_line = f"  {card_display}".ljust(78)
        print(f"│ {card_line} │")
    else:
        # User is defender - show all cards
        role_text = f"{Colors.TAN}{Colors.BOLD}YOUR ROLE: Defender{Colors.RESET}".ljust(93)
        print(f"│ {role_text} │")
        print("├" + "─" * 78 + "┤")
        print(f"│ {Colors.HERMES_ORANGE}Your cards:{Colors.RESET}                                                              │")
        for i, player_id in enumerate(state.user_deck, 1):
            player_info = state.player_id2player_info[player_id]
            card_display = format_player_card(player_info, i)
            card_line = f"  {card_display}".ljust(78)
            print(f"│ {card_line} │")
    
    print("├" + "─" * 78 + "┤")
    deck_info = f"{Colors.CREAM}Deck sizes: You={len(state.user_deck)} | AI={len(state.ai_deck)}{Colors.RESET}".ljust(94)
    print(f"│ {deck_info} │")
    print("└" + "─" * 78 + "┘")
    print()


def get_user_stat_input() -> str:
    """Prompt user to declare a stat."""
    print(f"\n{Colors.HERMES_ORANGE}{Colors.BOLD}Declare your stat:{Colors.RESET}")
    stat = input(f"{Colors.TAN}> {Colors.RESET}").strip()
    return stat


def get_user_defender_choice(state: GameState) -> str:
    """
    Prompt user to choose a defender card (1-based).
    
    Args:
        state: Current game state
        
    Returns:
        Player ID of chosen card
    """
    num_cards = len(state.user_deck)
    
    while True:
        try:
            choice = input(f"\n{Colors.HERMES_ORANGE}Choose your defender card (1-{num_cards}): {Colors.RESET}").strip()
            idx = int(choice)
            if 1 <= idx <= num_cards:
                # Convert 1-based to 0-based and return player_id
                return state.user_deck[idx - 1]
            else:
                print(f"{Colors.BURNT_ORANGE}Please enter a number between 1 and {num_cards}.{Colors.RESET}")
        except ValueError:
            print(f"{Colors.BURNT_ORANGE}Please enter a valid number between 1 and {num_cards}.{Colors.RESET}")


def get_ai_stat(state: GameState) -> dict:
    """
    Get AI's stat declaration when AI is challenger.
    
    Args:
        state: Current game state
        
    Returns:
        Dict with stat_description and reason
    """
    ai_top_card_id = state.ai_deck[0]
    player_info = state.player_id2player_info[ai_top_card_id]
    difficulty = state.game_config.get("difficulty", "S")  # Default to Sachin if not set
    
    print(f"\n{Colors.BROWN}AI is thinking...{Colors.RESET}")
    stat_challenge = get_stat_challenge(player_info, difficulty)
    return stat_challenge


def get_ai_defender_choice(state: GameState, stat_description: str) -> dict:
    """
    Get AI's defender card choice.
    
    Args:
        state: Current game state
        stat_description: The declared stat
        
    Returns:
        Defense choice dict with chosen_player_id, confidence_level, and reason
    """
    ai_deck = state.ai_deck
    
    print(f"\n{Colors.BROWN}AI is choosing defender...{Colors.RESET}")
    defense_choice = get_defense_choice(
        stat_description,
        ai_deck,
        state.player_id2player_info
    )
    return defense_choice


def show_round_reveal(result: RoundResult, state: GameState):
    """
    Display round result reveal.
    
    Args:
        result: Round result
        state: Current state (after round resolution)
    """
    print()
    
    # Top border
    print("╔" + "═" * 78 + "╗")
    
    # Header
    header = f"{Colors.BOLD}ROUND REVEAL{Colors.RESET}".ljust(89)
    print(f"║{header}║")
    
    # Section: Battle
    print("╠" + "═" * 78 + "╣")
    battle_header = f"{Colors.HERMES_ORANGE}BATTLE{Colors.RESET}".ljust(100)
    print(f"║ {battle_header}║")
    
    # Get player info for better display
    challenger_info = state.player_id2player_info[result.challenger_player_id]
    defender_info = state.player_id2player_info[result.defender_player_id]
    
    challenger_line = f"  Challenger: {challenger_info['display_name']} {get_country_flag_emoji(challenger_info.get('country', ''))} [{challenger_info['role']}]".ljust(78)
    defender_line = f"  Defender:   {defender_info['display_name']} {get_country_flag_emoji(defender_info.get('country', ''))} [{defender_info['role']}]".ljust(78)
    
    print(f"║ {challenger_line} ║")
    print(f"║ {defender_line} ║")
    
    # Stat description (wrapped if needed)
    stat_text = f'  Stat: "{result.stat_description}"'
    stat_lines = wrap_text(stat_text, 76)
    for line in stat_lines:
        padded_line = line.ljust(78)
        print(f"║ {padded_line} ║")
    
    # Section: Stat Values
    if result.stat_value:
        print("╠" + "═" * 78 + "╣")
        values_header = f"{Colors.HERMES_ORANGE}STAT VALUES{Colors.RESET}".ljust(106)
        print(f"║ {values_header}║")
        for key, value in result.stat_value.items():
            value_line = f"  {key}: {value}".ljust(78)
            print(f"║ {value_line} ║")
    
    # Section: Winner
    print("╠" + "═" * 78 + "╣")
    
    if result.round_winner_side == "user":
        winner_text = f"{Colors.TAN}{Colors.BOLD}WINNER: {result.round_winner.upper()} (YOU){Colors.RESET}"
        winner_line = winner_text.ljust(98)
    else:
        winner_text = f"{Colors.BROWN}{Colors.BOLD}WINNER: {result.round_winner.upper()} (AI){Colors.RESET}"
        winner_line = winner_text.ljust(99)
    
    print(f"║ {winner_line}║")
    
    # Judge's Comment
    if result.comment:
        print("╠" + "═" * 78 + "╣")
        comment_header = " COMMENTARY".ljust(78)
        print(f"║{comment_header}║")
        
        # Create comment box
        comment_box = create_comment_box(result.comment, width=74)
        for line in comment_box.split('\n'):
            padded = f"  {line}".ljust(78)
            print(f"║ {padded} ║")
    
    # Role switch notification
    if result.round_winner == "defender":
        print("╠" + "═" * 78 + "╣")
        switch_text = f"{Colors.HERMES_ORANGE}Roles have switched!{Colors.RESET}".ljust(108)
        print(f"║ {switch_text}║")
    
    # Bottom border
    print("╚" + "═" * 78 + "╝")
    print()


def play_round(state: GameState) -> tuple[GameState, bool]:
    """
    Play one round of the game.
    
    Args:
        state: Current game state
        
    Returns:
        Tuple of (new_state, continue_game)
    """
    # Show visibility
    show_visibility(state)
    
    # Step 1: Get stat declaration
    if state.challenger == "user":
        stat_description = get_user_stat_input()
    else:
        stat_challenge = get_ai_stat(state)
        stat_description = stat_challenge["stat_description"]
        
        print()
        title = f"{Colors.BROWN}AI CHALLENGER{Colors.RESET}"
        dialogue = create_dialogue_box(
            title,
            f'"{stat_description}"',
            stat_challenge['reason'],
            width=70
        )
        print(dialogue)
    
    # Step 2: Get defender choice
    if state.defender == "user":
        defender_player_id = get_user_defender_choice(state)
    else:
        defense_choice = get_ai_defender_choice(state, stat_description)
        defender_player_id = defense_choice["chosen_player_id"]
        defender_info = state.player_id2player_info[defender_player_id]
        
        print()
        title = f"{Colors.BROWN}AI DEFENDER CHOICE{Colors.RESET}"
        message = f"Chosen: {format_player_card(defender_info, 1)}"
        conf_emoji = confidence_emoji(defense_choice['confidence_level'])
        reasoning = f"{conf_emoji} {defense_choice['reason']}"
        dialogue = create_dialogue_box(title, message, reasoning, width=70)
        print(dialogue)
    
    # Step 3: Resolve round
    print(f"\n{Colors.CREAM}Resolving stat...{Colors.RESET}")
    new_state, result = resolve_round(state, stat_description, defender_player_id)
    
    if not result.success:
        # Stat failed - show error and retry
        print(f"\n{Colors.BURNT_ORANGE}{Colors.BOLD}✗ {result.error_message}{Colors.RESET}")
        print(f"{Colors.HERMES_ORANGE}Please try a different stat.{Colors.RESET}\n")
        return state, True  # Keep same state, continue game
    
    # Step 4: Show reveal
    show_round_reveal(result, new_state)
    
    return new_state, True


def main():
    """Main game loop."""
    # Load environment
    from main.config import path
    load_dotenv(path("secrets", ".env"))
    
    # Banner
    print()
    print_separator("=", 80)
    print(f"{Colors.HERMES_ORANGE}{Colors.BOLD}")
    print("  ██╗  ██╗ ██████╗ ██╗    ██╗   ██╗███████╗   ███████╗████████╗ █████╗ ████████╗")
    print("  ██║  ██║██╔═══██╗██║    ██║   ██║██╔════╝   ██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝")
    print("  ███████║██║   ██║██║ █╗ ██║   ██║███████╗   ███████╗   ██║   ███████║   ██║")
    print("  ██╔══██║██║   ██║██║███╗██║   ██║╚════██║   ╚════██║   ██║   ██╔══██║   ██║")
    print("  ██║  ██║╚██████╔╝╚███╔███╔╝██╗██║███████║██╗███████║   ██║   ██║  ██║   ██║")
    print("  ╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝ ╚═╝╚═╝╚══════╝╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝")
    print(f"{Colors.RESET}")
    print_separator("=", 80)
    print(f"{Colors.GOLD}                    Trump Cards Reimagined{Colors.RESET}")
    print_separator("=", 80)
    
    # Setup
    state = setup_game()
    
    # Game loop
    print()
    print("═" * 80)
    print(f"{Colors.HERMES_ORANGE}{Colors.BOLD}                              GAME START{Colors.RESET}")
    print("═" * 80)
    print(f"{Colors.TAN}You are the CHALLENGER.{Colors.RESET} {Colors.BROWN}AI is the DEFENDER.{Colors.RESET}")
    print(f"{Colors.CREAM}Your forced card will be revealed each round.{Colors.RESET}")
    print()
    
    round_number = 1
    
    while not state.is_game_over():
        print(f"\n{Colors.CREAM}{'▬' * 80}{Colors.RESET}")
        print(f"{Colors.HERMES_ORANGE}{Colors.BOLD}                                ROUND {round_number}{Colors.RESET}")
        print(f"{Colors.CREAM}{'▬' * 80}{Colors.RESET}")
        
        state, continue_game = play_round(state)
        
        if not continue_game:
            break
        
        # Check if game over after round
        if state.is_game_over():
            break
        
        round_number += 1
        
        # Pause before next round
        input(f"\n{Colors.CREAM}Press Enter to continue to next round...{Colors.RESET}")
    
    # Game over
    print()
    print("╔" + "═" * 78 + "╗")
    header = f"{Colors.BOLD}GAME OVER{Colors.RESET}".ljust(89)
    print(f"║{header}║")
    print("╠" + "═" * 78 + "╣")
    
    winner = state.get_winner()
    
    if winner == "user":
        victory_text = f"{Colors.GOLD}{Colors.BOLD}CONGRATULATIONS! YOU WIN!{Colors.RESET}".ljust(105)
        print(f"║{victory_text}║")
        print("╠" + "═" * 78 + "╣")
        score_text = f"{Colors.CREAM}Final score: You={len(state.user_deck)} | AI=0{Colors.RESET}".ljust(94)
        print(f"║ {score_text}║")
    else:
        defeat_text = f"{Colors.BROWN}{Colors.BOLD}DEFEAT! AI WINS!{Colors.RESET}".ljust(98)
        print(f"║{defeat_text}║")
        print("╠" + "═" * 78 + "╣")
        score_text = f"{Colors.CREAM}Final score: You=0 | AI={len(state.ai_deck)}{Colors.RESET}".ljust(94)
        print(f"║ {score_text}║")
    
    print("╚" + "═" * 78 + "╝")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Thanks for playing!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
