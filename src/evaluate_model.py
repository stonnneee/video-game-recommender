"""
Simple evaluation for the video game recommender.

Because this project does not have real user-click labels, evaluation focuses on:
- recommendation coverage
- average match score
- percent of returned games that satisfy each requested constraint

Run:
    python3 src/evaluate_model.py
"""

from itertools import product
from pathlib import Path
import pandas as pd

from recommender import (
    VALID_PLAY_VIBES,
    VALID_PLATFORMS,
    VALID_PLAY_STYLES,
    VALID_SESSION_LENGTHS,
    load_games,
    recommend_games,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "reports" / "evaluation_results.csv"


def evaluate_all_profiles(top_n: int = 5) -> pd.DataFrame:
    games = load_games()
    rows = []

    for play_vibe, platform, play_style, session_length in product(
        VALID_PLAY_VIBES,
        VALID_PLATFORMS,
        VALID_PLAY_STYLES,
        VALID_SESSION_LENGTHS,
    ):
        recs = recommend_games(
            games,
            play_vibe=play_vibe,
            platform=platform,
            play_style=play_style,
            session_length=session_length,
            top_n=top_n,
            min_score=0,
        )

        if not recs:
            rows.append({
                "play_vibe": play_vibe,
                "platform": platform,
                "play_style": play_style,
                "session_length": session_length,
                "num_recommendations": 0,
                "avg_match_score": 0,
                "platform_match_rate": 0,
                "play_style_match_rate": 0,
                "session_length_match_rate": 0,
            })
            continue

        rec_df = pd.DataFrame(recs)

        rows.append({
            "play_vibe": play_vibe,
            "platform": platform,
            "play_style": play_style,
            "session_length": session_length,
            "num_recommendations": len(recs),
            "avg_match_score": rec_df["match_score"].mean(),
            "platform_match_rate": rec_df["platforms"].astype(str).str.contains(platform, regex=False).mean(),
            "play_style_match_rate": (rec_df["play_style"] == play_style).mean(),
            "session_length_match_rate": (rec_df["session_length"] == session_length).mean(),
        })

    return pd.DataFrame(rows)


def main() -> None:
    results = evaluate_all_profiles(top_n=5)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUTPUT_PATH, index=False)

    print("Saved evaluation results to", OUTPUT_PATH)
    print("\nSummary:")
    print(results[[
        "num_recommendations",
        "avg_match_score",
        "platform_match_rate",
        "play_style_match_rate",
        "session_length_match_rate",
    ]].mean(numeric_only=True).round(3))


if __name__ == "__main__":
    main()
