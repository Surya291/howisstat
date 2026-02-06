# HowisStat - How to Play (V1)

## Quick Start

Run the game from the terminal:

```bash
cd /Users/surya/Desktop/toy_projects/howisstat
python3 main/cli.py
```

## Game Setup

1. **Select your franchise** (e.g., RCB, CSK, MI, KKR, etc.)
2. **Select opponent franchise** (can be same or different)
3. **Choose a year** (must be valid for both franchises)
4. Cards are dealt automatically (7 cards each)

## How to Play

### Roles
- **Challenger**: Plays forced top card, declares a stat
- **Defender**: Chooses best card from their hand to compete

You start as **Challenger**, AI starts as **Defender**.

### Each Round

**When you're Challenger:**
1. You'll see your top card (forced)
2. Declare a stat (e.g., "Most runs in IPL", "Best bowling average in T20Is")
3. AI chooses their defender card
4. Stats are resolved, winner announced

**When you're Defender:**
1. You'll see all your cards
2. AI declares a stat with their forced card
3. Choose which card (1-7) you want to defend with
4. Stats are resolved, winner announced

### Winning & Losing Rounds

- **Challenger wins**: Keeps both cards, remains challenger
- **Defender wins** (or tie): Gets both cards, **becomes new challenger**
- Roles switch when defender wins!

### Win Condition

Game ends when one player has **0 cards**.  
The other player wins!

## Example Stats

Good stats to declare:
- "Most runs in IPL"
- "Best bowling average in Test cricket"
- "Most sixes in T20 internationals"
- "Highest strike rate in powerplay in IPL"
- "Most wickets in ODIs"
- "Best economy rate in death overs"

## Tips

- Think about your card's strengths when declaring stats
- As defender, pick the card most likely to compete well
- AI will try to pick smart stats and defender cards
- Stat resolution may take a few seconds (API call)

## Controls

- Type your stat declaration when prompted
- Enter card number (1-7) when choosing defender
- Press Enter to continue between rounds
- Press Ctrl+C to quit anytime

---

**Focus**: This V1 is about testing game logic and state flow. UI/UX will be enhanced for web version.
