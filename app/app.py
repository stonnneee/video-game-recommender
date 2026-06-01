"""
Shiny for Python app for Video Game Recommender.

Run locally:
    GAMEMATCH_API_URL=http://127.0.0.1:8000 shiny run --reload --port 8001 app/app.py
"""

import os
import requests
from shiny import App, reactive, render, ui


API_URL = os.getenv("GAMEMATCH_API_URL", "http://127.0.0.1:8000").rstrip("/")

PLAY_VIBES = [
    "Chill / Cozy",
    "Competitive / Intense",
    "Story-Driven",
    "Puzzle / Strategy",
    "Creative / Exploration",
]

PLATFORMS = [
    "PC",
    "PlayStation",
    "Xbox",
    "Nintendo Switch",
]

PLAY_STYLES = [
    "Solo",
    "Multiplayer / Co-op",
]

SESSION_LABEL_TO_VALUE = {
    "Short Session (≤ 1 Hour)": "Short session",
    "Medium Session (1–3 Hours)": "Medium session",
    "Long Session (3+ Hours)": "Long session",
}

SESSION_LENGTHS = list(SESSION_LABEL_TO_VALUE.keys())

SESSION_VALUE_TO_LABEL = {
    value: label for label, value in SESSION_LABEL_TO_VALUE.items()
}


app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style(
            """
            body {
                background-color: #f6f7fb;
                font-size: 13px;
                color: #222;
            }

            .title-box {
                padding: 18px 24px;
                border-radius: 0 0 18px 18px;
                background: white;
                margin-bottom: 16px;
                box-shadow: 0 3px 12px rgba(0, 0, 0, 0.05);
            }

            .main-title {
                font-size: 30px;
                font-weight: 600;
                letter-spacing: 1px;
                margin-bottom: 5px;
            }

            .subtitle {
                font-size: 14px;
                color: #555;
                margin-bottom: 0;
            }

            .sidebar {
                padding-top: 0px;
            }

            .sidebar-title {
                font-size: 15px;
                line-height: 1.15;
                font-weight: 600;
                margin-bottom: 8px;
            }

            .shiny-input-container {
                margin-bottom: 2px !important;
            }

            label,
            .form-label {
                font-size: 13px;
                font-weight: 500;
                margin-bottom: 1px;
            }

            select,
            input {
                font-size: 13px !important;
            }

            .summary-card {
                padding: 12px 18px;
                border-radius: 14px;
                background: white;
                margin-bottom: 14px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
            }

            .summary-card h2 {
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 4px;
            }

            .summary-card p {
                margin-bottom: 0;
            }

            .game-card {
                display: flex;
                gap: 18px;
                align-items: flex-start;
                padding: 16px 18px;
                border-radius: 16px;
                background: white;
                margin-bottom: 14px;
                box-shadow: 0 3px 12px rgba(0, 0, 0, 0.06);
            }

            .game-info {
                flex: 1;
                min-width: 0;
            }

            .score {
                font-size: 22px;
                font-weight: 700;
                margin-bottom: 3px;
            }

            .game-title {
                font-size: 17px;
                font-weight: 700;
                margin-bottom: 6px;
            }

            .muted {
                color: #666;
                font-size: 12.5px;
                line-height: 1.4;
            }

            .game-img {
                width: 250px;
                height: 140px;
                object-fit: cover;
                border-radius: 12px;
                flex-shrink: 0;
            }

            .btn-primary {
                width: 100%;
                margin-top: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }

            @media (max-width: 900px) {
                .game-card {
                    flex-direction: column;
                }

                .game-img {
                    width: 100%;
                    height: 180px;
                }

                .main-title {
                    font-size: 26px;
                }
            }
            """
        )
    ),

    ui.div(
        ui.div("🎮 Video Game Recommender", class_="main-title"),
        ui.p(
            "Choose what kind of game you want to play right now, and get personalized recommendations with match scores.",
            class_="subtitle",
        ),
        class_="title-box",
    ),

    ui.layout_sidebar(
        ui.sidebar(
            ui.h3("Choose your preferences", class_="sidebar-title"),

            ui.input_select(
                "play_vibe",
                "Play vibe",
                choices=PLAY_VIBES,
                selected="Story-Driven",
            ),

            ui.input_select(
                "platform",
                "Platform",
                choices=PLATFORMS,
                selected="PC",
            ),

            ui.input_select(
                "play_style",
                "Play style",
                choices=PLAY_STYLES,
                selected="Solo",
            ),

            ui.input_select(
                "session_length",
                "Session length",
                choices=SESSION_LENGTHS,
                selected="Medium Session (1–3 Hours)",
            ),

            ui.input_slider(
                "top_n",
                "Recommendations",
                min=3,
                max=10,
                value=5,
            ),

            ui.input_action_button(
                "submit",
                "Find games",
                class_="btn-primary",
            ),

            width=240,
        ),

        ui.output_ui("status"),
        ui.output_ui("recommendations"),
    )
)


def server(input, output, session):

    @reactive.calc
    @reactive.event(input.submit)
    def fetch_recommendations():
        payload = {
            "play_vibe": input.play_vibe(),
            "platform": input.platform(),
            "play_style": input.play_style(),
            "session_length": SESSION_LABEL_TO_VALUE[input.session_length()],
            "top_n": input.top_n(),
            "min_score": 40,
        }

        try:
            response = requests.post(
                f"{API_URL}/recommend",
                json=payload,
                timeout=20,
            )
            response.raise_for_status()

            return {
                "ok": True,
                "data": response.json(),
                "error": None,
            }

        except Exception as exc:
            return {
                "ok": False,
                "data": None,
                "error": str(exc),
            }

    @output
    @render.ui
    def status():
        if input.submit() == 0:
            return ui.div(
                ui.h2("Ready to recommend"),
                ui.p(
                    "Select your preferences and click “Find games”",
                    class_="muted",
                ),
                class_="summary-card",
            )

        result = fetch_recommendations()

        if not result["ok"]:
            return ui.div(
                ui.h2("Could not reach the API"),
                ui.p(result["error"], class_="muted"),
                ui.p(
                    "Make sure the Flask API is running at http://127.0.0.1:8000.",
                    class_="muted",
                ),
                class_="summary-card",
            )

        recs = result["data"].get("recommendations", [])

        return ui.div(
            ui.h2(f"Found {len(recs)} recommendations"),
            ui.p(
                f"Using {input.play_vibe()}, {input.platform()}, "
                f"{input.play_style()}, {input.session_length()}.",
                class_="muted",
            ),
            class_="summary-card",
        )

    @output
    @render.ui
    def recommendations():
        if input.submit() == 0:
            return ui.div()

        result = fetch_recommendations()

        if not result["ok"]:
            return ui.div()

        recs = result["data"].get("recommendations", [])

        if not recs:
            return ui.div(
                ui.h2("No recommendations found"),
                ui.p(
                    "Try changing the platform, play vibe, or session length.",
                    class_="muted",
                ),
                class_="summary-card",
            )

        cards = []

        for rec in recs:
            image = rec.get("background_image")

            image_tag = (
                ui.img(src=image, class_="game-img")
                if image and str(image).startswith("http")
                else ui.div()
            )

            session_label = SESSION_VALUE_TO_LABEL.get(
                rec.get("session_length"),
                rec.get("session_length"),
            )

            cards.append(
                ui.div(
                    ui.div(
                        ui.div(
                            f"{rec.get('match_score')}% match",
                            class_="score",
                        ),
                        ui.div(
                            rec.get("name", "Unknown game"),
                            class_="game-title",
                        ),
                        ui.p(
                            f"Vibe: {rec.get('play_vibe')} | "
                            f"Platform: {rec.get('platforms')} | "
                            f"Style: {rec.get('play_style')} | "
                            f"Session: {session_label}",
                            class_="muted",
                        ),
                        ui.p(
                            f"Rating: {rec.get('rating')}",
                            class_="muted",
                        ),
                        class_="game-info",
                    ),
                    image_tag,
                    class_="game-card",
                )
            )

        return ui.div(*cards)


app = App(app_ui, server)
