"""
Flask API for GameMatch Tonight.

Run locally from the project root:
    python3 api/app.py

Example POST:
    curl -X POST http://127.0.0.1:8000/recommend \
      -H "Content-Type: application/json" \
      -d '{"play_vibe":"Chill / Cozy","platform":"PC","play_style":"Solo","session_length":"Short session","top_n":5}'
"""

from pathlib import Path
import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS

# Allow importing src/recommender.py when running api/app.py directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from recommender import (  # noqa: E402
    VALID_PLAY_VIBES,
    VALID_PLATFORMS,
    VALID_PLAY_STYLES,
    VALID_SESSION_LENGTHS,
    load_games,
    recommend_games,
)


app = Flask(__name__)
CORS(app)

DATA_PATH = os.getenv(
    "GAMEMATCH_DATA_PATH",
    str(PROJECT_ROOT / "data" / "processed" / "games_features.csv"),
)

try:
    GAMES_DF = load_games(DATA_PATH)
    LOAD_ERROR = None
except Exception as exc:
    GAMES_DF = None
    LOAD_ERROR = str(exc)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "GameMatch Tonight API is running.",
        "endpoints": ["/health", "/options", "/recommend"],
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok" if GAMES_DF is not None else "error",
        "data_path": DATA_PATH,
        "num_games": 0 if GAMES_DF is None else len(GAMES_DF),
        "load_error": LOAD_ERROR,
    })


@app.route("/options", methods=["GET"])
def options():
    return jsonify({
        "play_vibes": VALID_PLAY_VIBES,
        "platforms": VALID_PLATFORMS,
        "play_styles": VALID_PLAY_STYLES,
        "session_lengths": VALID_SESSION_LENGTHS,
    })


@app.route("/recommend", methods=["POST"])
def recommend():
    if GAMES_DF is None:
        return jsonify({
            "error": "Dataset not loaded. Run python3 src/preprocess.py first.",
            "details": LOAD_ERROR,
        }), 500

    data = request.get_json(silent=True) or {}

    try:
        play_vibe = data["play_vibe"]
        platform = data["platform"]
        play_style = data["play_style"]
        session_length = data["session_length"]
        top_n = int(data.get("top_n", 10))
        min_score = float(data.get("min_score", 50))

        recommendations = recommend_games(
            df=GAMES_DF,
            play_vibe=play_vibe,
            platform=platform,
            play_style=play_style,
            session_length=session_length,
            top_n=top_n,
            min_score=min_score,
        )

        return jsonify({
            "inputs": {
                "play_vibe": play_vibe,
                "platform": platform,
                "play_style": play_style,
                "session_length": session_length,
                "top_n": top_n,
                "min_score": min_score,
            },
            "recommendations": recommendations,
        })

    except KeyError as exc:
        return jsonify({
            "error": f"Missing required input: {exc.args[0]}",
            "required_inputs": [
                "play_vibe",
                "platform",
                "play_style",
                "session_length",
            ],
        }), 400

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
