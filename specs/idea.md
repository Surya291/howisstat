howisstat — Product Specification (V1, Role-Based)

1. Intention of the Game

howisstat is a turn-based, asymmetric judgment game built around challenging and defending claims using real-world cricket statistics under uncertainty.

The core tension of the game is:

Can you name a stat that favors your forced card, without knowing what the defender will counter with?

The game tests:
	•	Judgment
	•	Risk appetite
	•	Intuition about statistics
	•	Comfort with uncertainty

This is not a memory game, trivia game, or pure stats browser.

⸻

2. Roles (Critical)

There are two roles, not two fixed players:
	•	Challenger
	•	Defender

At game start:
	•	User = Challenger
	•	AI = Defender

After that:
	•	Roles switch whenever the challenger loses a round

The role, not the identity, defines who does what.

⸻

3. Game Setup
	•	Two players: User and AI
	•	Each starts with 7 cards
	•	Each card represents a cricket player
	•	Each player has an ordered deck

Visibility
	•	Challenger sees:
	•	Only the name of their top card
	•	Deck sizes of both players
	•	Defender sees:
	•	All their own cards (names only unless needed for resolution)
	•	Neither side sees:
	•	The opponent’s card before reveal
	•	Any precomputed stats

⸻

4. Card Model

Each card contains:
	•	Player name (string)
	•	Identifier(s) usable for online/stat search

No stats are stored locally or canonically.

Stats are not preloaded or normalized.

⸻

5. Round Flow (Role-Based)

Each round proceeds as follows:

⸻

Step 1: Challenger Card (Forced)
	•	Challenger must play the top card of their deck
	•	No choice, no discard, no swap

⸻

Step 2: Stat Declaration (Challenger)
	•	Challenger declares a stat in natural language
	•	Example:
	•	“Most test centuries”
	•	“Better batting average”
	•	“More wickets in ODIs”

This is a commitment without knowing the defender’s card.

⸻

Step 3: Defender Card Selection
	•	Defender:
	•	Knows the declared stat
	•	Does not know the challenger’s player
	•	Defender may choose any card from their deck to defend the stat

This is a best-guess defense, not perfect information.

⸻

Step 4: Resolution (System)
	•	System performs runtime stat resolution:
	•	Searches online / queries external sources
	•	Determines:
	•	Challenger stat value
	•	Defender stat value
	•	Only a binary outcome is required:
	•	Challenger wins
	•	Defender wins

Exact numeric values do not need to be shown.

⸻

Step 5: Reveal
	•	Both player names are revealed
	•	The stat outcome is revealed (optionally with values if available)

⸻

6. Outcome Rules
	•	If challenger wins:
	•	Challenger remains challenger
	•	If challenger loses:
	•	Roles switch
	•	Defender becomes challenger
	•	Challenger becomes defender

Tie Rule
	•	Defender wins ties
	•	Therefore:
	•	Tie ⇒ challenger loses ⇒ roles switch

⸻

7. Card Movement Rules
	•	Winner of the round takes both cards
	•	Both cards are placed at the back of the winner’s deck
	•	No discards
	•	No reshuffling

Deck order always matters.

⸻

8. Win Condition
	•	Game ends immediately when:
	•	One player has 0 cards
	•	That player loses
	•	The other player wins

⸻

9. AI Behavior (V1)

AI is Role-Agnostic

The AI can be:
	•	Challenger or
	•	Defender

It follows role rules exactly like the user.

AI Strategy
	•	As Defender:
	•	Choose the card that best defends against the declared stat, given uncertainty
	•	As Challenger:
	•	Forced top card
	•	Declares a stat using heuristics or templates

No memory.
No learning.
No adaptation across rounds.

Each round is independent.

⸻

10. Stat Resolution Philosophy
	•	There is no fixed stat list
	•	There are no canonical stats
	•	There is no pre-validation

The system:
	•	Accepts stat input as-is
	•	Attempts to resolve it via:
	•	Online search
	•	Structured queries
	•	LLM-based reasoning if needed
	•	Produces:
	•	Challenger wins / Defender wins

If resolution fails:
	•	Reject the stat
	•	Ask challenger to rephrase

⸻

11. UX Principles
	•	Minimal UI
	•	No dashboards
	•	No stat explanations
	•	No coaching

The game should feel:
	•	Slightly uncomfortable
	•	Slightly risky
	•	Judgment-heavy

⸻

12. Explicit Non-Goals (Do NOT Build in V1)
	•	Precomputed stat databases
	•	Canonical stat ontologies
	•	Multiplayer
	•	Difficulty levels
	•	AI personalities
	•	Match history
	•	Replays
	•	Rewards / XP / badges
	•	Tutorials

⸻

13. Why This Design Works
	•	Roles can reverse → momentum swings
	•	Defender advantage creates tension
	•	Forced cards prevent min-maxing
	•	Runtime stats keep the game alive and surprising

The player is not proving knowledge —
they are testing instinct.

⸻

If you want next, I can:
	•	Convert this into a state machine
	•	Write role-based pseudocode
	•	Or draft prompt templates for the stat resolution/search layer

But as a V1 coding-agent spec, this is now aligned with your true intent.