"""
Feature engineering for Video Game Recommender.

This script reads data/processed/games_clean.csv and creates:
- play_vibe
- play_style
- session_length
- platform_group

Run from the project root:
    python3 src/preprocess.py
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "games_clean.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "games_features.csv"


def clean_text(value) -> str:
    """Convert missing values to empty strings and lowercase text."""
    if pd.isna(value):
        return ""
    return str(value).lower()


def assign_play_vibes(row):
    """
    Assign ONE primary play vibe instead of multiple vibes.

    This avoids inflated match scores where one game matches too many
    play vibe options at the same time.
    """
    text = clean_text(row.get("genres", "")) + " " + clean_text(row.get("tags", ""))

    vibe_keywords = {
        "Chill / Cozy": [
            "cozy", "relaxing", "farming", "life sim", "cute",
            "peaceful", "family friendly", "wholesome"
        ],
        "Competitive / Intense": [
            "shooter", "fighting", "pvp", "competitive", "difficult",
            "combat", "battle royale", "souls-like", "fps", "hack and slash"
        ],
        "Story-Driven": [
            "story rich", "narrative", "choices matter", "visual novel",
            "rpg", "jrpg", "cinematic", "atmospheric"
        ],
        "Puzzle / Strategy": [
            "puzzle", "strategy", "tactical", "turn-based", "logic",
            "management", "card game", "board game"
        ],
        "Creative / Exploration": [
            "open world", "exploration", "sandbox", "building",
            "creative", "crafting", "survival"
        ],
    }

    # Tie-breaking priority. This helps avoid broad games being labeled randomly.
    vibe_priority = [
        "Story-Driven",
        "Puzzle / Strategy",
        "Chill / Cozy",
        "Competitive / Intense",
        "Creative / Exploration",
    ]

    scores = {}

    for vibe, keywords in vibe_keywords.items():
        scores[vibe] = sum(1 for word in keywords if word in text)

    best_score = max(scores.values())

    if best_score == 0:
        return "Other"

    # If multiple vibes tie, choose based on the priority list.
    for vibe in vibe_priority:
        if scores[vibe] == best_score:
            return vibe

    return "Other"


def assign_play_style(row):
    """
    Infer play style from RAWG tags/genres.

    A game can support both Solo and Multiplayer / Co-op.
    For example, Minecraft can be played solo or multiplayer.
    """
    text = clean_text(row.get("tags", "")) + " " + clean_text(row.get("genres", ""))

    play_styles = []

    solo_words = [
        "singleplayer", "single-player",
        "story rich", "narrative", "choices matter",
        "rpg", "jrpg", "adventure", "visual novel",
        "sandbox", "open world", "exploration",
        "building", "crafting", "survival",
        "simulation", "puzzle", "strategy",
        "platformer", "casual"
    ]

    multiplayer_words = [
        "multiplayer", "co-op", "online co-op", "local co-op",
        "pvp", "party", "massively multiplayer", "team-based",
        "split screen", "shared screen", "online multiplayer"
    ]

    if any(word in text for word in solo_words):
        play_styles.append("Solo")

    if any(word in text for word in multiplayer_words):
        play_styles.append("Multiplayer / Co-op")

    if not play_styles:
        play_styles.append("Unknown")

    return ", ".join(play_styles)


def assign_session_length(row):
    """
    Infer broad session length.

    Short Session: 1 hour or less
    Medium Session: 1–3 hours
    Long Session: 3+ hours

    RAWG playtime is measured in hours, but many games have playtime = 0.
    Because of that, tags/genres are used first, and playtime is only used
    when it is positive.
    """
    text = clean_text(row.get("genres", "")) + " " + clean_text(row.get("tags", ""))
    playtime = row.get("playtime", 0)

    short_words = [
        "arcade", "casual", "platformer", "puzzle", "roguelike",
        "roguelite", "runner", "party"
    ]

    long_words = [
        "rpg", "open world", "strategy", "mmorpg", "grand strategy",
        "story rich", "simulation", "management"
    ]

    # Use tags/genres first because many RAWG playtime values are 0 or unknown.
    if any(word in text for word in short_words):
        return "Short session"

    if any(word in text for word in long_words):
        return "Long session"

    # Use RAWG playtime only if it is available and greater than 0.
    if pd.notna(playtime) and playtime > 0:
        if playtime <= 1:
            return "Short session"
        elif playtime <= 3:
            return "Medium session"
        else:
            return "Long session"

    # Default when session length is unclear.
    return "Medium session"


def simplify_platforms(row: pd.Series) -> str:
    """Group RAWG platforms into user-friendly platform choices."""
    text = clean_text(row.get("platforms", ""))
    platforms = []

    if "pc" in text:
        platforms.append("PC")
    if "playstation" in text:
        platforms.append("PlayStation")
    if "xbox" in text:
        platforms.append("Xbox")
    if "nintendo switch" in text:
        platforms.append("Nintendo Switch")

    if not platforms:
        platforms.append("Other")

    return ", ".join(platforms)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create feature columns used by the recommender."""
    df = df.copy()

    required_columns = ["name", "genres", "tags", "platforms", "playtime"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["play_vibe"] = df.apply(assign_play_vibes, axis=1)
    df["play_style"] = df.apply(assign_play_style, axis=1)
    df["session_length"] = df.apply(assign_session_length, axis=1)
    df["platform_group"] = df.apply(simplify_platforms, axis=1)

    return df


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_PATH}. Run src/collect_data.py first."
        )

    df = pd.read_csv(INPUT_PATH)
    features = build_features(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved feature dataset to {OUTPUT_PATH}")
    print(features[["name", "play_vibe", "platform_group", "play_style", "session_length"]].head())


if __name__ == "__main__":
    main()
