import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from recommender import recommend_games, score_game


def test_score_game_full_match():
    row = pd.Series({
        "name": "Test Game",
        "play_vibe": "Chill / Cozy",
        "platform_group": "PC, PlayStation",
        "play_style": "Solo",
        "session_length": "Short session",
        "rating": 4.5,
    })

    score = score_game(
        row,
        play_vibe="Chill / Cozy",
        platform="PC",
        play_style="Solo",
        session_length="Short session",
    )

    assert score["match_score"] >= 95
    assert score["play_vibe_match"] is True
    assert score["platform_match"] is True
    assert score["play_style_match"] is True
    assert score["session_length_match"] is True


def test_recommend_games_returns_platform_compatible_results():
    df = pd.DataFrame([
        {
            "name": "PC Cozy Game",
            "play_vibe": "Chill / Cozy",
            "platform_group": "PC",
            "play_style": "Solo",
            "session_length": "Short session",
            "rating": 4.0,
            "ratings_count": 100,
            "playtime": 1,
            "background_image": "",
        },
        {
            "name": "Xbox Cozy Game",
            "play_vibe": "Chill / Cozy",
            "platform_group": "Xbox",
            "play_style": "Solo",
            "session_length": "Short session",
            "rating": 5.0,
            "ratings_count": 500,
            "playtime": 1,
            "background_image": "",
        },
    ])

    recs = recommend_games(
        df,
        play_vibe="Chill / Cozy",
        platform="PC",
        play_style="Solo",
        session_length="Short session",
        top_n=1,
    )

    assert len(recs) == 1
    assert recs[0]["name"] == "PC Cozy Game"
