import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Read the key from Streamlit Cloud Secrets or local .env
TMDB_API_KEY = (
    st.secrets.get("TMDB_API_KEY", "")
    or os.getenv("TMDB_API_KEY", "")
)

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def search_movie_poster(movie_title):
    if not TMDB_API_KEY or not movie_title:
        return None

    try:
        response = requests.get(
            f"{BASE_URL}/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": movie_title
            },
            timeout=15
        )

        response.raise_for_status()

        results = response.json().get("results", [])

        if results:
            poster_path = results[0].get("poster_path")

            if poster_path:
                return f"{IMAGE_BASE_URL}{poster_path}"

    except requests.RequestException as e:
        print(f"TMDB error: {e}")

    return None