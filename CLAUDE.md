# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HOW.IS.STAT is a cricket stats trump-card game where a player competes against an AI opponent using real cricket player cards. The game can be played via terminal CLI or web browser (Next.js frontend + Flask API backend).

**Game Mechanics:**
- Players hold 7 cards each (real cricketers from selected IPL franchises/years)
- Challenger declares a stat, Defender picks a card to compete
- Stats are resolved via Cricinfo API + Gemini AI judge
- Winner takes both cards, loser of round becomes next challenger
- First to 0 cards loses

## Development Commands

### Backend (Flask API)

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp secrets/.env.example secrets/.env  # Add GEMINI_API_KEY

# Run API server (port 5050)
python api_server.py

# Run tests
python -m pytest tests/
python -m pytest tests/test_game_engine.py  # Single test file
```

### Frontend (Next.js)

```bash
cd web
npm install
cp .env.example .env.local  # Configure API URL

# Development
npm run dev  # Port 3000

# Production
npm run build
npm run start
```

### Terminal CLI (Standalone)

```bash
source venv/bin/activate
python main/cli.py
```

## Architecture

### Backend Structure

**Core Game Engine** (`main/game_engine.py`)
- Pure state machine, no I/O operations
- `GameState`: Single source of truth for game state (decks, roles, config)
- `RoundResult`: Immutable result object from round resolution
- `resolve_round()`: Orchestrates stat judgment and state transitions
- Handles role switching: defender becomes challenger when they win

**Card Dealing** (`main/deal_cards.py`)
- Loads player data from `data/player_id2player_info.json`
- `deal_player_cards()`: Deals balanced hands based on franchise/year/positions
- Position balancing ensures each hand gets mix of BAT/BOWL/ALL_ROUNDER/WK

**AI Agents** (`main/ai/`)
- `ai_challenger.py`: Generates stat challenges based on player role/info
  - Three difficulty modes: Gully (simple), Domestic (moderate), Sachin (expert)
  - Uses Gemini to create strategic stat declarations
- `ai_defender.py`: Selects best defending card from available hand
  - Analyzes opponent's stat and picks strongest counter-card
- `stat_judge.py`: Resolves stat battles via Cricinfo API + Gemini judgment
  - `ask_cricinfo_api()`: Fetches real stats from ESPN Cricinfo
  - `judge_stat()`: Uses Gemini to determine winner and generate commentary
- `llm_agents.py`: Base `GeminiAgent` wrapper for structured outputs

**API Server** (`api_server.py`)
- Flask + CORS, wraps game engine for web frontend
- In-memory session storage (sessions dict)
- Endpoints: `/api/new-game`, `/api/play-round`, `/api/ai-defend`, etc.
- Optional SarvamAI TTS integration for commentary

**Configuration** (`main/config.py`)
- Centralized path resolution via `path()` helper
- Uses `HOWISSTAT_ROOT` env var or derives from file location

**Data Files** (`data/`)
- `player_id2player_info.json`: Full player database (3.2MB, ~1000+ players)
- `team2year2player_ids.json`: Franchise-year-player mappings
- `filtered_team2year2player_ids.json`: Filtered version for dealing
- `usage_stats.json`: Tracks games/rounds played

### Frontend Structure

**Next.js App** (`web/app/`)
- `page.js`: Landing page
- `game_cli/page.js`: Terminal-style game interface
- `components/`: Reusable React components
- `api/`: Frontend API utilities (fetch wrappers)

**Styling:**
- `globals.css`: Terminal-themed CSS with cricket aesthetics
- Monospace fonts, green terminal colors, retro UI

## Key Patterns

### State Flow
1. User selects franchises/year → `deal_player_cards()` creates initial decks
2. `create_initial_state()` → `GameState` with user as challenger
3. Each round: `resolve_round()` → `RoundResult`
4. Winner takes both cards, role switch if defender wins
5. Game ends when any deck reaches 0 cards

### AI Difficulty Levels
- **Gully (G)**: Simple role-based stats (e.g., "most runs", "most wickets")
- **Domestic (D)**: Adds context filters (e.g., "strike rate in powerplay")
- **Sachin (S)**: Advanced stats with multiple conditions and edge cases

### Stat Resolution Pipeline
```
Challenger stat → ask_cricinfo_api() → Cricinfo JSON data
                                     ↓
                              Gemini judge → winner + commentary
```

### Error Handling
- Stat judge can reject invalid/unsupported stats
- `RoundResult.success = False` with `error_message` on rejection
- Frontend displays error and allows re-declaration

## Environment Variables

| Variable | Location | Purpose |
|----------|----------|---------|
| `GEMINI_API_KEY` | `secrets/.env` | Required: Google Gemini API for AI agents + stat judge |
| `SARVAM_API_KEY` | `secrets/.env` | Optional: SarvamAI TTS for commentary audio |
| `NEXT_PUBLIC_API_URL` | `web/.env.local` | Frontend API base URL (default: `http://localhost:5050`) |
| `HOWISSTAT_ROOT` | Environment | Optional: Override repo root path |

## Important Notes

- **Never commit secrets**: `secrets/.env` is gitignored
- **Player data is static**: Pre-scraped from Cricinfo, no runtime scraping
- **API rate limits**: Cricinfo API calls happen per round (can be slow)
- **Session storage**: API server uses in-memory sessions (lost on restart)
- **Stat language**: Stats must be plain English, Cricinfo API interprets them
- **Position codes**: BAT, BOWL, ALL_ROUNDER, WK (see `deal_cards.py`)
