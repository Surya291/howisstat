#!/usr/bin/env python3
"""
HowisStat Web API Server
Wraps the Python game engine for the web terminal UI.
Run: python api_server.py
"""

import sys
import os
import json
import uuid
import traceback

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, "secrets", ".env"))

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install flask flask-cors")
    sys.exit(1)

from main.game_engine import (
    GameState, RoundResult,
    create_initial_state, resolve_round,
    get_available_franchises, get_available_years, validate_franchise_year
)
from main.deal_cards import deal_player_cards
from main.ai.ai_challenger import get_stat_challenge
from main.ai.ai_defender import get_defense_choice

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ═══════════════════════════════════════════════════════════════
# In-memory session storage
# ═══════════════════════════════════════════════════════════════
sessions = {}

# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

COUNTRY_FLAGS = {
    "IND": "🇮🇳", "AUS": "🇦🇺", "ENG": "🇬🇧", "SA": "🇿🇦", "NZ": "🇳🇿",
    "PAK": "🇵🇰", "SL": "🇱🇰", "BAN": "🇧🇩", "AFG": "🇦🇫", "WI": "🏴‍☠️",
    "ZIM": "🇿🇼", "IRE": "🇮🇪", "SCO": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "NED": "🇳🇱", "UAE": "🇦🇪",
    "USA": "🇺🇸", "CAN": "🇨🇦", "KEN": "🇰🇪", "UKN": "",
    # Full names
    "India": "🇮🇳", "Australia": "🇦🇺", "England": "🇬🇧", "South Africa": "🇿🇦",
    "New Zealand": "🇳🇿", "Pakistan": "🇵🇰", "Sri Lanka": "🇱🇰", "Bangladesh": "🇧🇩",
    "Afghanistan": "🇦🇫", "West Indies": "🏴‍☠️", "Zimbabwe": "🇿🇼", "Ireland": "🇮🇪",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Netherlands": "🇳🇱",
}

DIFFICULTY_NAMES = {"G": "Gully", "D": "Domestic", "S": "Sachin Mode"}
CONFIDENCE_EMOJIS = {"high": "🔥", "medium": "⚡", "low": "🤞"}


def player_to_card(player_info, index):
    """Convert player_info to web-friendly card data."""
    country = player_info.get("country", "")
    return {
        "index": index,
        "name": player_info.get("display_name", "Unknown"),
        "country": country,
        "flag": COUNTRY_FLAGS.get(country, ""),
        "role": player_info.get("role", ""),
        "batting_style": player_info.get("batting_style"),
        "bowling_style": player_info.get("bowling_style"),
    }


def get_user_cards(session):
    """Get user's current cards for display."""
    gs = session["game_state"]
    return [
        player_to_card(gs.player_id2player_info[pid], i)
        for i, pid in enumerate(gs.user_deck, 1)
    ]


def state_summary(session):
    """Get game state summary for frontend status bar."""
    gs = session.get("game_state")
    if not gs:
        return None
    return {
        "round": session.get("round_number", 0),
        "user_cards": len(gs.user_deck),
        "ai_cards": len(gs.ai_deck),
        "role": "challenger" if gs.challenger == "user" else "defender",
        "phase": session["phase"],
    }


def respond(sid, session, messages, prompt):
    """Build standardized API response."""
    return jsonify({
        "session_id": sid,
        "messages": messages,
        "prompt": prompt,
        "game_state": state_summary(session),
    })


# ═══════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════

@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})


@app.route('/api/game', methods=['POST'])
def game_action():
    try:
        data = request.json or {}
        session_id = data.get("session_id")
        user_input = (data.get("input") or "").strip()

        # New game
        if not session_id or session_id not in sessions:
            return init_game()

        session = sessions[session_id]
        phase = session["phase"]

        handlers = {
            "awaiting_self_franchise": handle_self_franchise,
            "awaiting_opponent_franchise": handle_opponent_franchise,
            "awaiting_year": handle_year,
            "awaiting_difficulty": handle_difficulty,
            "round_awaiting_stat": handle_user_stat,
            "round_awaiting_defender": handle_user_defender,
            "round_awaiting_continue": handle_continue,
        }

        handler = handlers.get(phase)
        if not handler:
            return jsonify({"error": f"Unexpected game phase: {phase}"}), 400

        return handler(session_id, session, user_input)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# Phase Handlers
# ═══════════════════════════════════════════════════════════════

def init_game():
    """Create new game session, return welcome screen."""
    sid = str(uuid.uuid4())
    franchises = get_available_franchises()

    sessions[sid] = {
        "phase": "awaiting_self_franchise",
        "config": {},
        "game_state": None,
        "round_number": 0,
        "pending_stat": None,
    }

    messages = [
        {"type": "banner"},
        {"type": "text", "content": "Trump Cards Reimagined", "style": "gold"},
        {"type": "separator", "style": "double"},
        {"type": "heading", "content": "GAME SETUP"},
        {"type": "text", "content": "Select your franchise:", "style": "accent"},
        {"type": "franchise_list", "franchises": franchises},
    ]

    prompt = {
        "type": "text",
        "label": "Enter your franchise",
        "placeholder": "e.g., CSK, MI, RCB...",
    }

    return respond(sid, sessions[sid], messages, prompt)


def handle_self_franchise(sid, session, inp):
    franchises = get_available_franchises()
    if inp not in franchises:
        return respond(sid, session,
            [{"type": "error", "content": f"Invalid franchise '{inp}'. Choose from the list above."}],
            {"type": "text", "label": "Enter your franchise", "placeholder": "e.g., CSK, MI, RCB..."})

    session["config"]["self_franchise"] = inp
    session["phase"] = "awaiting_opponent_franchise"

    return respond(sid, session, [
        {"type": "text", "content": f"Your franchise: {inp}", "style": "success"},
        {"type": "separator"},
        {"type": "text", "content": "Select opponent franchise:", "style": "accent"},
        {"type": "franchise_list", "franchises": franchises},
    ], {"type": "text", "label": "Enter opponent franchise", "placeholder": "e.g., CSK, MI, RCB..."})


def handle_opponent_franchise(sid, session, inp):
    franchises = get_available_franchises()
    if inp not in franchises:
        return respond(sid, session,
            [{"type": "error", "content": f"Invalid franchise '{inp}'. Choose from the list above."}],
            {"type": "text", "label": "Enter opponent franchise", "placeholder": "e.g., CSK, MI, RCB..."})

    session["config"]["opponent_franchise"] = inp
    session["phase"] = "awaiting_year"

    self_f = session["config"]["self_franchise"]
    years = get_available_years(self_f)

    return respond(sid, session, [
        {"type": "text", "content": f"Opponent franchise: {inp}", "style": "success"},
        {"type": "separator"},
        {"type": "text", "content": f"Select year(s) for {self_f}:", "style": "accent"},
        {"type": "text", "content": ", ".join(years), "style": "muted"},
        {"type": "text", "content": "You can enter multiple years separated by commas", "style": "hint"},
    ], {"type": "text", "label": "Enter year(s)", "placeholder": "e.g., 2023 or 2022,2023"})


def handle_year(sid, session, inp):
    self_f = session["config"]["self_franchise"]
    opp_f = session["config"]["opponent_franchise"]
    self_years = get_available_years(self_f)
    opp_years = get_available_years(opp_f)

    selected = [y.strip() for y in inp.split(",") if y.strip()]

    if not selected:
        return respond(sid, session,
            [{"type": "error", "content": "Please enter at least one year."}],
            {"type": "text", "label": "Enter year(s)", "placeholder": "e.g., 2023 or 2022,2023"})

    invalid_self = [y for y in selected if y not in self_years]
    if invalid_self:
        return respond(sid, session, [
            {"type": "error", "content": f"Invalid year(s) for {self_f}: {', '.join(invalid_self)}"},
            {"type": "text", "content": f"Available: {', '.join(self_years)}", "style": "muted"},
        ], {"type": "text", "label": "Enter year(s)", "placeholder": "e.g., 2023 or 2022,2023"})

    invalid_opp = [y for y in selected if y not in opp_years]
    if invalid_opp:
        return respond(sid, session, [
            {"type": "error", "content": f"Year(s) {', '.join(invalid_opp)} not available for {opp_f}."},
            {"type": "text", "content": f"Available for {opp_f}: {', '.join(opp_years)}", "style": "muted"},
            {"type": "text", "content": "All years must be valid for both franchises.", "style": "hint"},
        ], {"type": "text", "label": "Enter year(s)", "placeholder": "e.g., 2023 or 2022,2023"})

    session["config"]["year_list"] = selected
    session["phase"] = "awaiting_difficulty"

    return respond(sid, session, [
        {"type": "text", "content": f"Year(s): {', '.join(selected)}", "style": "success"},
        {"type": "separator"},
        {"type": "heading", "content": "SELECT DIFFICULTY"},
        {"type": "difficulty_options"},
    ], {"type": "text", "label": "Enter difficulty (G/D/S)", "placeholder": "G = Gully, D = Domestic, S = Sachin Mode"})


def handle_difficulty(sid, session, inp):
    d = inp.upper()
    if d not in ["G", "D", "S"]:
        return respond(sid, session,
            [{"type": "error", "content": "Invalid choice. Please enter G, D, or S."}],
            {"type": "text", "label": "Enter difficulty (G/D/S)", "placeholder": "G = Gully, D = Domestic, S = Sachin Mode"})

    session["config"]["difficulty"] = d
    session["config"]["number_of_players"] = 7

    # Deal cards
    try:
        game_info = deal_player_cards(session["config"])
    except Exception as e:
        return respond(sid, session,
            [{"type": "error", "content": f"Failed to deal cards: {str(e)}"}],
            {"type": "text", "label": "Enter difficulty (G/D/S)", "placeholder": "G = Gully, D = Domestic, S = Sachin Mode"})

    state = create_initial_state(
        session["config"],
        game_info["self_player_ids"],
        game_info["opponent_player_ids"],
        game_info["player_id2player_info"]
    )

    session["game_state"] = state
    session["round_number"] = 1
    user_cards = get_user_cards(session)
    cfg = session["config"]

    messages = [
        {"type": "text", "content": f"Difficulty: {DIFFICULTY_NAMES[d]}", "style": "success"},
        {"type": "separator", "style": "wave"},
        {"type": "text", "content": "Dealing cards...", "style": "accent"},
        {"type": "separator"},
        {"type": "text", "content": "Cards dealt!", "style": "success"},
        {"type": "setup_summary", "data": {
            "self_franchise": cfg["self_franchise"],
            "opponent_franchise": cfg["opponent_franchise"],
            "years": ", ".join(cfg["year_list"]),
            "difficulty": DIFFICULTY_NAMES[d],
            "cards_each": 7,
        }},
        {"type": "cards", "title": "YOUR CARDS", "cards": user_cards},
        {"type": "separator", "style": "double"},
        {"type": "heading", "content": "GAME START"},
        {"type": "text", "content": "You are the CHALLENGER. AI is the DEFENDER.", "style": "body"},
        {"type": "text", "content": "Your forced card will be revealed each round.", "style": "muted"},
    ]

    # Start first round
    round_msgs, prompt = start_round(session)
    messages.extend(round_msgs)

    return respond(sid, session, messages, prompt)


def start_round(session):
    """Prepare a new round. Returns (messages, prompt)."""
    gs = session["game_state"]
    rn = session["round_number"]

    messages = [
        {"type": "separator", "style": "heavy"},
        {"type": "round_header", "round": rn},
    ]

    if gs.challenger == "user":
        # User is challenger — show top card, prompt for stat
        top_pid = gs.user_deck[0]
        top_info = gs.player_id2player_info[top_pid]
        top_card = player_to_card(top_info, 1)

        messages.append({
            "type": "visibility", "role": "challenger", "top_card": top_card,
            "deck_sizes": {"user": len(gs.user_deck), "ai": len(gs.ai_deck)}
        })

        session["phase"] = "round_awaiting_stat"
        prompt = {"type": "text", "label": "Declare your stat", "placeholder": "e.g., Most runs in IPL by a batter..."}

    else:
        # AI is challenger — run AI, then prompt user for defender
        ai_top_pid = gs.ai_deck[0]
        ai_info = gs.player_id2player_info[ai_top_pid]
        difficulty = gs.game_config.get("difficulty", "S")

        messages.append({"type": "text", "content": "AI is thinking...", "style": "ai_thinking"})

        try:
            stat_challenge = get_stat_challenge(ai_info, difficulty)
        except Exception as e:
            messages.append({"type": "error", "content": f"AI challenger failed: {str(e)}"})
            session["phase"] = "round_awaiting_continue"
            return messages, {"type": "continue", "label": "Press Enter to retry..."}

        session["pending_stat"] = stat_challenge["stat_description"]

        messages.append({
            "type": "dialogue", "title": "AI CHALLENGER",
            "message": f'"{stat_challenge["stat_description"]}"',
            "reasoning": stat_challenge.get("reason", ""),
            "style": "challenger"
        })

        user_cards = get_user_cards(session)
        messages.append({
            "type": "visibility", "role": "defender", "cards": user_cards,
            "deck_sizes": {"user": len(gs.user_deck), "ai": len(gs.ai_deck)}
        })

        session["phase"] = "round_awaiting_defender"
        prompt = {"type": "text", "label": f"Choose your defender card (1-{len(gs.user_deck)})", "placeholder": "Enter card number..."}

    return messages, prompt


def handle_user_stat(sid, session, inp):
    """User declared a stat (user is challenger)."""
    if not inp:
        return respond(sid, session,
            [{"type": "error", "content": "Please enter a stat description."}],
            {"type": "text", "label": "Declare your stat", "placeholder": "e.g., Most runs in IPL by a batter..."})

    gs = session["game_state"]

    messages = [{"type": "text", "content": f'Your stat: "{inp}"', "style": "accent"}]
    messages.append({"type": "text", "content": "AI is choosing defender...", "style": "ai_thinking"})

    # AI defends
    try:
        defense_choice = get_defense_choice(inp, gs.ai_deck, gs.player_id2player_info)
    except Exception as e:
        messages.append({"type": "error", "content": f"AI defender failed: {str(e)}"})
        return respond(sid, session, messages,
            {"type": "text", "label": "Declare your stat (retry)", "placeholder": "Try a different stat..."})

    defender_pid = defense_choice["chosen_player_id"]
    defender_info = gs.player_id2player_info[defender_pid]
    defender_card = player_to_card(defender_info, 1)

    conf = defense_choice.get("confidence_level", "medium")
    emoji = CONFIDENCE_EMOJIS.get(conf, "")

    card_display = f"{defender_card['name']} {defender_card['flag']} • {defender_card['role']}"
    messages.append({
        "type": "dialogue", "title": "AI DEFENDER",
        "message": f"Chosen: {card_display}",
        "reasoning": f"{emoji} {defense_choice.get('reason', '')}",
        "style": "defender"
    })

    # Resolve
    messages.append({"type": "text", "content": "Resolving stat...", "style": "muted"})

    try:
        new_state, result = resolve_round(gs, inp, defender_pid)
    except Exception as e:
        messages.append({"type": "error", "content": f"Resolution failed: {str(e)}. Try a different stat."})
        return respond(sid, session, messages,
            {"type": "text", "label": "Declare your stat (retry)", "placeholder": "Try a different stat..."})

    if not result.success:
        messages.append({"type": "error", "content": result.error_message})
        messages.append({"type": "text", "content": "Please try a different stat.", "style": "hint"})
        return respond(sid, session, messages,
            {"type": "text", "label": "Declare your stat (retry)", "placeholder": "Try a different stat..."})

    session["game_state"] = new_state
    messages.append({"type": "result", "data": build_result_data(result, new_state)})

    if new_state.is_game_over():
        winner = new_state.get_winner()
        messages.append({"type": "game_over", "winner": winner,
                         "user_cards": len(new_state.user_deck), "ai_cards": len(new_state.ai_deck)})
        session["phase"] = "game_over"
        return respond(sid, session, messages, None)

    session["phase"] = "round_awaiting_continue"
    session["round_number"] += 1
    return respond(sid, session, messages, {"type": "continue", "label": "Press Enter for next round..."})


def handle_user_defender(sid, session, inp):
    """User chose a defender card (user is defender)."""
    gs = session["game_state"]
    num_cards = len(gs.user_deck)

    try:
        idx = int(inp)
        if idx < 1 or idx > num_cards:
            raise ValueError()
    except (ValueError, TypeError):
        return respond(sid, session,
            [{"type": "error", "content": f"Please enter a number between 1 and {num_cards}."}],
            {"type": "text", "label": f"Choose your defender card (1-{num_cards})", "placeholder": "Enter card number..."})

    defender_pid = gs.user_deck[idx - 1]
    defender_info = gs.player_id2player_info[defender_pid]
    stat_description = session.get("pending_stat", "")

    messages = [
        {"type": "text", "content": f"Your choice: #{idx} {defender_info['display_name']}", "style": "success"},
        {"type": "text", "content": "Resolving stat...", "style": "muted"},
    ]

    try:
        new_state, result = resolve_round(gs, stat_description, defender_pid)
    except Exception as e:
        messages.append({"type": "error", "content": f"Resolution failed: {str(e)}"})
        session["phase"] = "round_awaiting_continue"
        return respond(sid, session, messages, {"type": "continue", "label": "Press Enter to continue..."})

    if not result.success:
        messages.append({"type": "error", "content": result.error_message})
        session["phase"] = "round_awaiting_continue"
        return respond(sid, session, messages, {"type": "continue", "label": "Press Enter to continue..."})

    session["game_state"] = new_state
    messages.append({"type": "result", "data": build_result_data(result, new_state)})

    if new_state.is_game_over():
        winner = new_state.get_winner()
        messages.append({"type": "game_over", "winner": winner,
                         "user_cards": len(new_state.user_deck), "ai_cards": len(new_state.ai_deck)})
        session["phase"] = "game_over"
        return respond(sid, session, messages, None)

    session["phase"] = "round_awaiting_continue"
    session["round_number"] += 1
    return respond(sid, session, messages, {"type": "continue", "label": "Press Enter for next round..."})


def handle_continue(sid, session, inp):
    """Continue to next round."""
    gs = session["game_state"]
    if gs.is_game_over():
        winner = gs.get_winner()
        return respond(sid, session, [
            {"type": "game_over", "winner": winner,
             "user_cards": len(gs.user_deck), "ai_cards": len(gs.ai_deck)},
        ], None)

    round_msgs, prompt = start_round(session)
    return respond(sid, session, round_msgs, prompt)


def build_result_data(result, new_state):
    """Build result data for frontend rendering."""
    c_info = new_state.player_id2player_info.get(result.challenger_player_id, {})
    d_info = new_state.player_id2player_info.get(result.defender_player_id, {})

    return {
        "challenger": {
            "name": result.challenger_name,
            "country": c_info.get("country", ""),
            "flag": COUNTRY_FLAGS.get(c_info.get("country", ""), ""),
            "role": c_info.get("role", ""),
        },
        "defender": {
            "name": result.defender_name,
            "country": d_info.get("country", ""),
            "flag": COUNTRY_FLAGS.get(d_info.get("country", ""), ""),
            "role": d_info.get("role", ""),
        },
        "stat": result.stat_description,
        "stat_values": result.stat_value,
        "winner": result.round_winner,
        "winner_side": result.round_winner_side,
        "comment": result.comment,
        "roles_switched": result.round_winner == "defender",
    }


# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 60)
    print("  HowisStat API Server")
    print("  http://localhost:5050/api/game")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5050, debug=True)
