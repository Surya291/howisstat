"""
HowisStat Game Engine - State and Round Logic

This module handles the core game state and round resolution.
No I/O operations - pure state transitions.
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, field
import json


@dataclass
class GameState:
    """
    Single source of truth for game state.
    
    Attributes:
        user_deck: List of player IDs (ordered, user's cards)
        ai_deck: List of player IDs (ordered, AI's cards)
        player_id2player_info: Dict mapping player_id -> player info
        challenger: Current challenger role ("user" or "ai")
        defender: Current defender role ("user" or "ai")
        game_config: Game configuration (franchises, year, etc.)
    """
    user_deck: List[str]
    ai_deck: List[str]
    player_id2player_info: Dict[str, dict]
    challenger: Literal["user", "ai"]
    defender: Literal["user", "ai"]
    game_config: Dict[str, any]
    
    def is_game_over(self) -> bool:
        """Check if game is over (any deck is empty)."""
        return len(self.user_deck) == 0 or len(self.ai_deck) == 0
    
    def get_winner(self) -> Optional[str]:
        """Return winner if game is over, None otherwise."""
        if not self.is_game_over():
            return None
        return "ai" if len(self.user_deck) == 0 else "user"
    
    def get_challenger_deck(self) -> List[str]:
        """Get the current challenger's deck."""
        return self.user_deck if self.challenger == "user" else self.ai_deck
    
    def get_defender_deck(self) -> List[str]:
        """Get the current defender's deck."""
        return self.user_deck if self.defender == "user" else self.ai_deck


@dataclass
class RoundResult:
    """
    Result of a round resolution.
    
    Attributes:
        success: True if round completed successfully, False if stat rejected
        challenger_player_id: Challenger's player ID
        challenger_name: Challenger's display name
        defender_player_id: Defender's player ID (None if stat rejected)
        defender_name: Defender's display name (None if stat rejected)
        stat_description: The stat that was declared
        round_winner: "challenger" or "defender" (None if stat rejected)
        round_winner_side: "user" or "ai" (None if stat rejected)
        stat_value: Stat values dict (None if stat rejected)
        comment: Judge's comment (None if stat rejected)
        error_message: Error message if stat rejected (None if success)
    """
    success: bool
    challenger_player_id: str
    challenger_name: str
    defender_player_id: Optional[str] = None
    defender_name: Optional[str] = None
    stat_description: Optional[str] = None
    round_winner: Optional[Literal["challenger", "defender"]] = None
    round_winner_side: Optional[Literal["user", "ai"]] = None
    stat_value: Optional[dict] = None
    comment: Optional[str] = None
    error_message: Optional[str] = None


def create_initial_state(
    game_config: dict,
    self_player_ids: List[str],
    opponent_player_ids: List[str],
    player_id2player_info: Dict[str, dict]
) -> GameState:
    """
    Create initial game state from deal results.
    
    Args:
        game_config: Game configuration
        self_player_ids: User's dealt cards (player IDs)
        opponent_player_ids: AI's dealt cards (player IDs)
        player_id2player_info: Player info lookup
        
    Returns:
        Initial GameState with user as challenger, ai as defender
    """
    return GameState(
        user_deck=self_player_ids.copy(),
        ai_deck=opponent_player_ids.copy(),
        player_id2player_info=player_id2player_info,
        challenger="user",
        defender="ai",
        game_config=game_config
    )


def resolve_round(
    state: GameState,
    stat_description: str,
    defender_player_id: str
) -> tuple[GameState, RoundResult]:
    """
    Resolve a round: judgment, card movement, role switch.
    
    Args:
        state: Current game state
        stat_description: The stat declared by challenger
        defender_player_id: The player ID chosen by defender
        
    Returns:
        Tuple of (new_state, round_result)
    """
    from main.ai.stat_judge import get_judgement
    
    # Get challenger's top card (forced)
    challenger_deck = state.get_challenger_deck()
    challenger_player_id = challenger_deck[0]
    
    # Validate defender card is in their deck
    defender_deck = state.get_defender_deck()
    if defender_player_id not in defender_deck:
        raise ValueError(f"Defender player {defender_player_id} not in defender's deck")
    
    # Get display names
    challenger_name = state.player_id2player_info[challenger_player_id]["display_name"]
    defender_name = state.player_id2player_info[defender_player_id]["display_name"]
    
    # Try to get judgment
    try:
        judgment = get_judgement(challenger_player_id, defender_player_id, stat_description)
    except Exception as e:
        # Stat resolution failed - return reject result without changing state
        return state, RoundResult(
            success=False,
            challenger_player_id=challenger_player_id,
            challenger_name=challenger_name,
            stat_description=stat_description,
            error_message=f"Stat resolution failed: {str(e)}"
        )
    
    # Interpret winner
    round_winner = judgment["winner"]  # "challenger" or "defender"
    
    # Create new state with updated decks and roles
    new_state = GameState(
        user_deck=state.user_deck.copy(),
        ai_deck=state.ai_deck.copy(),
        player_id2player_info=state.player_id2player_info,
        challenger=state.challenger,
        defender=state.defender,
        game_config=state.game_config
    )
    
    # Remove played cards from their decks
    if state.challenger == "user":
        new_state.user_deck.pop(0)  # Remove challenger's top card
        # Remove defender's card
        defender_idx = new_state.ai_deck.index(defender_player_id)
        new_state.ai_deck.pop(defender_idx)
    else:
        new_state.ai_deck.pop(0)  # Remove challenger's top card
        # Remove defender's card
        defender_idx = new_state.user_deck.index(defender_player_id)
        new_state.user_deck.pop(defender_idx)
    
    # Determine which side won and add cards to back of winner's deck
    if round_winner == "challenger":
        # Challenger wins - keeps both cards, roles unchanged
        round_winner_side = state.challenger
        if state.challenger == "user":
            new_state.user_deck.extend([challenger_player_id, defender_player_id])
        else:
            new_state.ai_deck.extend([challenger_player_id, defender_player_id])
    else:
        # Defender wins (or tie) - defender gets both cards, roles switch
        round_winner_side = state.defender
        if state.defender == "user":
            new_state.user_deck.extend([challenger_player_id, defender_player_id])
        else:
            new_state.ai_deck.extend([challenger_player_id, defender_player_id])
        
        # Switch roles
        new_state.challenger, new_state.defender = new_state.defender, new_state.challenger
    
    # Build result
    result = RoundResult(
        success=True,
        challenger_player_id=challenger_player_id,
        challenger_name=challenger_name,
        defender_player_id=defender_player_id,
        defender_name=defender_name,
        stat_description=stat_description,
        round_winner=round_winner,
        round_winner_side=round_winner_side,
        stat_value=judgment.get("stat_value"),
        comment=judgment.get("comment")
    )
    
    return new_state, result


def load_franchise_data() -> Dict[str, Dict[str, List[str]]]:
    """Load franchise-year-players data for validation."""
    with open("/Users/surya/Desktop/toy_projects/howisstat/data/team2year2player_ids.json", "r") as f:
        return json.load(f)


def get_available_franchises() -> List[str]:
    """Get list of all available franchises."""
    data = load_franchise_data()
    return sorted(data.keys())


def get_available_years(franchise: str) -> List[str]:
    """Get list of available years for a franchise."""
    data = load_franchise_data()
    if franchise not in data:
        return []
    return sorted(data[franchise].keys())


def validate_franchise_year(franchise: str, year: str) -> bool:
    """Check if franchise and year combination is valid."""
    data = load_franchise_data()
    return franchise in data and year in data.get(franchise, {})
