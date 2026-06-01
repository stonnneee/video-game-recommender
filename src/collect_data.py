"""
Collects video game data from the RAWG API and saves it to a CSV file.
Fetches game information including titles, ratings, genres, platforms, and release dates.
"""

import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RAWG_API_KEY")
BASE_URL = "https://api.rawg.io/api/games"

if not API_KEY:
    raise ValueError("Missing RAWG_API_KEY. Add it to your .env file.")

def extract_names(items):
    if not items:
        return []
    return [item.get("name") for item in items if item.get("name")]

def extract_platforms(platforms):
    if not platforms:
        return []
    return [
        item.get("platform", {}).get("name")
        for item in platforms
        if item.get("platform", {}).get("name")
    ]

def collect_games(pages=10, page_size=40):
    all_games = []

    for page in range(1, pages + 1):
        print(f"Collecting page {page}...")

        params = {
            "key": API_KEY,
            "page": page,
            "page_size": page_size,
            "ordering": "-rating"
        }

        response = requests.get(BASE_URL, params=params, timeout=15)

        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            break

        data = response.json()
        games = data.get("results", [])

        for game in games:
            row = {
                "id": game.get("id"),
                "name": game.get("name"),
                "released": game.get("released"),
                "rating": game.get("rating"),
                "ratings_count": game.get("ratings_count"),
                "metacritic": game.get("metacritic"),
                "playtime": game.get("playtime"),
                "genres": ", ".join(extract_names(game.get("genres"))),
                "tags": ", ".join(extract_names(game.get("tags"))),
                "platforms": ", ".join(extract_platforms(game.get("platforms"))),
                "stores": ", ".join(extract_names(game.get("stores"))),
                "background_image": game.get("background_image"),
            }
            all_games.append(row)

        time.sleep(0.5)

    return pd.DataFrame(all_games)

if __name__ == "__main__":
    df = collect_games(pages=13, page_size=40)

    df.to_csv("data/raw/rawg_games_raw.csv", index=False)
    df.to_csv("data/processed/games_clean.csv", index=False)

    print(f"Saved {len(df)} games.")
    print(df.head())