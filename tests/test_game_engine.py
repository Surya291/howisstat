"""
Test game engine core logic.
"""

import os
import sys
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _repo_root)

from main.game_engine import GameState, create_initial_state


def test_initial_state():
    """Test initial state creation."""
    game_config = {
        "year_list": ["2025"],
        "number_of_players": 7,
        "self_franchise": "RCB",
        "opponent_franchise": "CSK"
    }
    
    self_player_ids = ["player1", "player2", "player3"]
    opponent_player_ids = ["player4", "player5", "player6"]
    player_id2player_info = {
        "player1": {"display_name": "P1"},
        "player2": {"display_name": "P2"},
        "player3": {"display_name": "P3"},
        "player4": {"display_name": "P4"},
        "player5": {"display_name": "P5"},
        "player6": {"display_name": "P6"},
    }
    
    state = create_initial_state(
        game_config,
        self_player_ids,
        opponent_player_ids,
        player_id2player_info
    )
    
    assert state.user_deck == self_player_ids
    assert state.ai_deck == opponent_player_ids
    assert state.challenger == "user"
    assert state.defender == "ai"
    assert not state.is_game_over()
    
    print("✓ Initial state test passed")


def test_game_over_detection():
    """Test game over detection."""
    state = GameState(
        user_deck=["player1"],
        ai_deck=[],
        player_id2player_info={},
        challenger="user",
        defender="ai",
        game_config={}
    )
    
    assert state.is_game_over()
    assert state.get_winner() == "user"
    
    print("✓ Game over detection test passed")


def test_deck_accessors():
    """Test challenger/defender deck accessors."""
    state = GameState(
        user_deck=["u1", "u2"],
        ai_deck=["a1", "a2"],
        player_id2player_info={},
        challenger="user",
        defender="ai",
        game_config={}
    )
    
    assert state.get_challenger_deck() == ["u1", "u2"]
    assert state.get_defender_deck() == ["a1", "a2"]
    
    # Switch roles
    state.challenger = "ai"
    state.defender = "user"
    
    assert state.get_challenger_deck() == ["a1", "a2"]
    assert state.get_defender_deck() == ["u1", "u2"]
    
    print("✓ Deck accessors test passed")


if __name__ == "__main__":
    test_initial_state()
    test_game_over_detection()
    test_deck_accessors()
    print("\n✓ All game engine tests passed!")
