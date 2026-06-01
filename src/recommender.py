"""
Recommendation model for Video Game Recommender.

The model creates a match score based on:
1. Primary play vibe
2. Solo or multiplayer preference
3. Session length
4. RAWG rating
5. Rating count confidence

Important design choices:
- Each game has ONE primary play vibe.
- Platform is used as a hard filter, not a scoring feature.
- Match scores are not capped manually.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import math

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "games_features.csv"


VALID_PLAY_VIBES = [
    "Chill / Cozy",
    "Competitive / Intense",
    "Story-Driven",
    "Puzzle / Strategy",
    "Creative / Exploration",
]

VALID_PLATFORMS = [
    "PC",
    "PlayStation",
    "Xbox",
    "Nintendo Switch",
]

VALID_PLAY_STYLES = [
    "Solo",
    "Multiplayer / Co-op",
]

VALID_SESSION_LENGTHS = [
    "Short session",
    "Medium session",
    "Long session",
]


# Platform is NOT included because it is a hard filter.
WEIGHTS = {
    "play_vibe": 0.45,
    "play_style": 0.20,
    "session_length": 0.15,
    "rating": 0.15,
    "confidence": 0.05,
}


def _split_values(cell_value: Any) -> List[str]:
    """Split a comma-separated cell into clean lowercase values."""
    if pd.isna(cell_value):
        return []

    return [
        value.strip().lower()
        for value in str(cell_value).split(",")
        if value.strip()
    ]


def _contains_value(cell_value: Any, target: str) -> bool:
    """Check if target appears in a comma-separated cell."""
    values = _split_values(cell_value)
    return target.strip().lower() in values


def validate_inputs(
    play_vibe: str,
    platform: str,
    play_style: str,
    session_length: str,
) -> None:
    """Validate user inputs from the app/API."""
    errors = []

    if play_vibe not in VALID_PLAY_VIBES:
        errors.append(f"play_vibe must be one of {VALID_PLAY_VIBES}")

    if platform not in VALID_PLATFORMS:
        errors.append(f"platform must be one of {VALID_PLATFORMS}")

    if play_style not in VALID_PLAY_STYLES:
        errors.append(f"play_style must be one of {VALID_PLAY_STYLES}")

    if session_length not in VALID_SESSION_LENGTHS:
        errors.append(f"session_length must be one of {VALID_SESSION_LENGTHS}")

    if errors:
        raise ValueError("; ".join(errors))


def get_vibe_score(row: pd.Series, selected_vibe: str) -> float:
    """
    Score primary play vibe.

    Since each game now has one primary play vibe, this is an exact match.
    This prevents one game from matching many vibes at once.
    """
    game_vibe = str(row.get("play_vibe", "")).strip().lower()
    selected_vibe = selected_vibe.strip().lower()

    if game_vibe == selected_vibe:
        return 1.0

    return 0.0


def get_play_style_score(row: pd.Series, selected_style: str) -> float:
    """
    Score solo/multiplayer preference.

    A game can have multiple play styles, such as:
    "Solo, Multiplayer / Co-op"

    Exact inclusion gets full credit.
    Unknown gets partial credit because the data may be incomplete.
    """
    game_styles = _split_values(row.get("play_style", ""))
    selected_style = selected_style.strip().lower()

    if selected_style in game_styles:
        return 1.0

    if "unknown" in game_styles:
        return 0.35

    return 0.0


def get_session_score(row: pd.Series, selected_session: str) -> float:
    """
    Score session length.

    Exact match gets full credit.
    Medium is treated as flexible and can partially match short or long.
    """
    game_session = str(row.get("session_length", "")).strip().lower()
    selected_session = selected_session.strip().lower()

    if game_session == selected_session:
        return 1.0

    if "medium" in game_session or "medium" in selected_session:
        return 0.50

    return 0.0


def get_rating_score(row: pd.Series) -> float:
    """
    Normalize RAWG rating to a 0–1 score.

    RAWG rating is usually on a 0–5 scale.
    """
    rating = row.get("rating", 0)

    if pd.isna(rating):
        return 0.0

    try:
        rating_value = float(rating)
    except (TypeError, ValueError):
        return 0.0

    rating_value = max(0.0, min(rating_value, 5.0))
    return rating_value / 5.0


def get_confidence_score(row: pd.Series) -> float:
    """
    Use ratings_count as a small confidence score.

    This gives a small boost to games with more user ratings.
    Log scaling prevents very popular games from dominating too much.
    """
    ratings_count = row.get("ratings_count", 0)

    if pd.isna(ratings_count):
        return 0.0

    try:
        count = float(ratings_count)
    except (TypeError, ValueError):
        return 0.0

    if count <= 0:
        return 0.0

    return min(math.log1p(count) / math.log1p(5000), 1.0)


def score_game(
    row: pd.Series,
    play_vibe: str,
    platform: str,
    play_style: str,
    session_length: str,
) -> Dict[str, Any]:
    """
    Score one game based on user preferences.

    Platform is checked here, but it does not add points.
    """
    platform_match = _contains_value(row.get("platform_group", ""), platform)

    vibe_score = get_vibe_score(row, play_vibe)
    play_style_score = get_play_style_score(row, play_style)
    session_score = get_session_score(row, session_length)
    rating_score = get_rating_score(row)
    confidence_score = get_confidence_score(row)

    total_score = (
        vibe_score * WEIGHTS["play_vibe"]
        + play_style_score * WEIGHTS["play_style"]
        + session_score * WEIGHTS["session_length"]
        + rating_score * WEIGHTS["rating"]
        + confidence_score * WEIGHTS["confidence"]
    )

    return {
        "match_score": round(total_score * 100, 1),
        "platform_match": platform_match,
        "vibe_score": round(vibe_score, 2),
        "play_style_score": round(play_style_score, 2),
        "session_score": round(session_score, 2),
        "rating_score": round(rating_score, 2),
        "confidence_score": round(confidence_score, 2),
    }


def load_games(data_path: Optional[str] = None) -> pd.DataFrame:
    """Load the feature-engineered game dataset."""
    path = Path(data_path) if data_path else DEFAULT_DATA_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path}. Run python3 src/preprocess.py first."
        )

    df = pd.read_csv(path)

    required_columns = [
        "name",
        "play_vibe",
        "platform_group",
        "play_style",
        "session_length",
        "rating",
        "ratings_count",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(
            f"Missing columns {missing_columns}. Run python3 src/preprocess.py first."
        )

    return df


def recommend_games(
    df: pd.DataFrame,
    play_vibe: str,
    platform: str,
    play_style: str,
    session_length: str,
    top_n: int = 10,
    min_score: float = 40.0,
) -> List[Dict[str, Any]]:
    """Return ranked game recommendations."""
    validate_inputs(
        play_vibe=play_vibe,
        platform=platform,
        play_style=play_style,
        session_length=session_length,
    )

    scored_games = []

    for _, row in df.iterrows():
        score_parts = score_game(
            row=row,
            play_vibe=play_vibe,
            platform=platform,
            play_style=play_style,
            session_length=session_length,
        )

        # Platform is required. Do not recommend games unavailable on the selected platform.
        if not score_parts["platform_match"]:
            continue

        rating = row.get("rating")
        ratings_count = row.get("ratings_count")
        playtime = row.get("playtime")

        result = {
            "name": row.get("name"),
            "match_score": score_parts["match_score"],
            "play_vibe": row.get("play_vibe"),
            "platforms": row.get("platform_group"),
            "play_style": row.get("play_style"),
            "session_length": row.get("session_length"),
            "rating": None if pd.isna(rating) else rating,
            "ratings_count": None if pd.isna(ratings_count) else ratings_count,
            "playtime": None if pd.isna(playtime) else playtime,
            "background_image": row.get("background_image"),
            "vibe_score": score_parts["vibe_score"],
            "play_style_score": score_parts["play_style_score"],
            "session_score": score_parts["session_score"],
            "rating_score": score_parts["rating_score"],
            "confidence_score": score_parts["confidence_score"],
        }

        scored_games.append(result)

    ranked_games = sorted(
        scored_games,
        key=lambda game: (
            game["match_score"],
            game["rating"] if game["rating"] is not None else 0,
            game["ratings_count"] if game["ratings_count"] is not None else 0,
        ),
        reverse=True,
    )

    filtered_games = [
        game for game in ranked_games
        if game["match_score"] >= min_score
    ]

    if len(filtered_games) >= top_n:
        return filtered_games[:top_n]

    # If there are not enough games above min_score, fill with the best platform-compatible games.
    seen_names = {game["name"] for game in filtered_games}

    for game in ranked_games:
        if game["name"] not in seen_names:
            filtered_games.append(game)
            seen_names.add(game["name"])

        if len(filtered_games) >= top_n:
            break

    return filtered_games[:top_n]


def recommend_from_file(
    play_vibe: str,
    platform: str,
    play_style: str,
    session_length: str,
    top_n: int = 10,
    min_score: float = 40.0,
    data_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Load data from CSV and return recommendations."""
    df = load_games(data_path)

    return recommend_games(
        df=df,
        play_vibe=play_vibe,
        platform=platform,
        play_style=play_style,
        session_length=session_length,
        top_n=top_n,
        min_score=min_score,
    )


if __name__ == "__main__":
    games = load_games()

    recs = recommend_games(
        df=games,
        play_vibe="Competitive / Intense",
        platform="Xbox",
        play_style="Multiplayer / Co-op",
        session_length="Long session",
        top_n=10,
        min_score=40,
    )

    for rec in recs:
        print(
            f"{rec['match_score']}% - {rec['name']} | "
            f"Vibe: {rec['play_vibe']} | "
            f"Style: {rec['play_style']} | "
            f"Session: {rec['session_length']} | "
            f"Rating: {rec['rating']}"
        )