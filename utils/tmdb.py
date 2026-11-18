import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def search_movie_poster(movie_title):
    """
    Search TMDB for a movie and return its poster URL.
    """

    if not TMDB_API_KEY or not movie_title:
        return None

    try:
        response = requests.get(
            f"{BASE_URL}/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": movie_title
            },
            timeout=10
        )

        response.raise_for_status()

        results = response.json().get("results", [])

        if results:
            poster_path = results[0].get("poster_path")

            if poster_path:
                return f"{IMAGE_BASE_URL}{poster_path}"

    except requests.RequestException:
        return None

    return None