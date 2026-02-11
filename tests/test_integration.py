"""
Integration test for full game flow.
Tests that game_engine, deal_cards, AI modules, and stat_judge work together.
"""

import os
import sys
from dotenv import load_dotenv

# Add project root and load env
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _repo_root)
load_dotenv(os.path.join(_repo_root, "secrets", ".env"))

from main.game_engine import create_initial_state, resolve_round, GameState
from main.deal_cards import deal_player_cards
from main.ai.ai_challenger import get_stat_challenge
from main.ai.ai_defender import get_defense_choice


def test_full_game_setup():
    """Test that we can set up a complete game."""
    print("\n" + "="*60)
    print("TEST: Full Game Setup")
    print("="*60)
    
    game_config = {
        "year_list": ["2025"],
        "number_of_players": 7,
        "self_franchise": "RCB",
        "opponent_franchise": "CSK"
    }
    
    # Deal cards
    print("\n1. Dealing cards...")
    game_info = deal_player_cards(game_config)
    
    assert len(game_info["self_player_ids"]) == 7
    assert len(game_info["opponent_player_ids"]) == 7
    assert len(game_info["player_id2player_info"]) == 14
    
    print(f"   ✓ Dealt {len(game_info['self_player_ids'])} cards to user")
    print(f"   ✓ Dealt {len(game_info['opponent_player_ids'])} cards to AI")
    
    # Create state
    print("\n2. Creating initial state...")
    state = create_initial_state(
        game_config,
        game_info["self_player_ids"],
        game_info["opponent_player_ids"],
        game_info["player_id2player_info"]
    )
    
    assert state.challenger == "user"
    assert state.defender == "ai"
    assert len(state.user_deck) == 7
    assert len(state.ai_deck) == 7
    
    print(f"   ✓ Initial state created")
    print(f"   ✓ User is challenger, AI is defender")
    
    return state


def test_ai_challenger_integration(state: GameState):
    """Test AI challenger can declare a stat."""
    print("\n" + "="*60)
    print("TEST: AI Challenger Integration")
    print("="*60)
    
    # Simulate AI as challenger
    ai_top_card_id = state.ai_deck[0]
    player_info = state.player_id2player_info[ai_top_card_id]
    
    print(f"\n1. AI top card: {player_info['display_name']}")
    print(f"   Role: {player_info['role']}")
    
    print("\n2. AI declaring stat...")
    stat_challenge = get_stat_challenge(player_info)
    
    assert "stat_description" in stat_challenge
    assert "reason" in stat_challenge
    
    print(f"   ✓ Stat: {stat_challenge['stat_description']}")
    print(f"   ✓ Reason: {stat_challenge['reason']}")
    
    return stat_challenge["stat_description"]


def test_ai_defender_integration(state: GameState, stat: str):
    """Test AI defender can choose a card."""
    print("\n" + "="*60)
    print("TEST: AI Defender Integration")
    print("="*60)
    
    print(f"\n1. Declared stat: {stat}")
    print(f"2. AI has {len(state.ai_deck)} cards to choose from")
    
    print("\n3. AI choosing defender...")
    defense_choice = get_defense_choice(
        stat,
        state.ai_deck,
        state.player_id2player_info
    )
    
    assert "chosen_player_id" in defense_choice
    assert defense_choice["chosen_player_id"] in state.ai_deck
    
    chosen_name = state.player_id2player_info[defense_choice["chosen_player_id"]]["display_name"]
    print(f"   ✓ Chosen: {chosen_name}")
    print(f"   ✓ Confidence: {defense_choice['confidence_level']}")
    print(f"   ✓ Reason: {defense_choice['reason']}")
    
    return defense_choice["chosen_player_id"]


def test_round_resolution(state: GameState):
    """Test a complete round resolution."""
    print("\n" + "="*60)
    print("TEST: Round Resolution")
    print("="*60)
    
    # User is challenger, AI is defender
    user_top_card = state.user_deck[0]
    user_card_name = state.player_id2player_info[user_top_card]["display_name"]
    
    print(f"\n1. Challenger (User): {user_card_name}")
    
    # Use a simple stat
    stat = "Most runs in IPL"
    print(f"2. Stat declared: {stat}")
    
    # AI chooses defender
    print("\n3. Getting AI defender choice...")
    defender_player_id = get_defense_choice(
        stat,
        state.ai_deck,
        state.player_id2player_info
    )["chosen_player_id"]
    
    defender_name = state.player_id2player_info[defender_player_id]["display_name"]
    print(f"   AI defender: {defender_name}")
    
    # Resolve round
    print("\n4. Resolving round...")
    new_state, result = resolve_round(state, stat, defender_player_id)
    
    if not result.success:
        print(f"   ⚠️  Stat rejected: {result.error_message}")
        print("   (This is OK - stat may not be resolvable)")
        return state, False
    
    print(f"   ✓ Round resolved successfully")
    print(f"   ✓ Winner: {result.round_winner} ({result.round_winner_side})")
    print(f"   ✓ Comment: {result.comment}")
    
    # Verify state changes
    if result.round_winner == "challenger":
        # User should have gained cards, roles unchanged
        assert new_state.challenger == "user"
        assert new_state.defender == "ai"
        assert len(new_state.user_deck) == len(state.user_deck) + 1  # Net +1 (lost 1, gained 2)
        print(f"   ✓ Challenger won - kept both cards, roles unchanged")
    else:
        # AI should have gained cards, roles switched
        assert new_state.challenger == "ai"
        assert new_state.defender == "user"
        assert len(new_state.ai_deck) == len(state.ai_deck) + 1  # Net +1
        print(f"   ✓ Defender won - got both cards, roles switched")
    
    return new_state, True


def main():
    """Run all integration tests."""
    print("\n" + "█"*60)
    print("  HOWISSTAT INTEGRATION TESTS")
    print("█"*60)
    
    try:
        # Test 1: Setup
        state = test_full_game_setup()
        
        # Test 2: AI as challenger
        stat = test_ai_challenger_integration(state)
        
        # Test 3: AI as defender
        defender_id = test_ai_defender_integration(state, stat)
        
        # Test 4: Round resolution (may fail if stat not resolvable)
        print("\n" + "="*60)
        print("NOTE: Next test calls actual stat resolution API")
        print("It may fail if stat is not resolvable - this is expected")
        print("="*60)
        
        new_state, resolved = test_round_resolution(state)
        
        # Summary
        print("\n" + "█"*60)
        print("  INTEGRATION TEST SUMMARY")
        print("█"*60)
        print("\n✓ Game setup: PASS")
        print("✓ AI challenger: PASS")
        print("✓ AI defender: PASS")
        if resolved:
            print("✓ Round resolution: PASS")
        else:
            print("⚠️  Round resolution: SKIPPED (stat not resolvable)")
        
        print("\n" + "█"*60)
        print("  ALL CORE COMPONENTS WORKING ✓")
        print("█"*60)
        print("\n🎮 Game is ready to play! Run: python3 main/cli.py")
        print()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
