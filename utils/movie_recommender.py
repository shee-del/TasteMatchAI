import ast
import joblib
import pandas as pd
from pathlib import Path


# PROJECT PATHS
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = BASE_DIR / "data" / "data.csv"
MODEL_PATH = BASE_DIR / "models" / "movies" / "movies_model.pkl"


# LOAD DATA AND MODEL
movies_df = pd.read_csv(DATA_PATH)
artifacts = joblib.load(MODEL_PATH)

model = artifacts["model"]
scaler = artifacts["scaler"]

GENRE_FEATURES = [
    "Action", "Adventure", "Animation", "Biography",
    "Comedy", "Crime", "Drama", "Family", "Fantasy",
    "Film-Noir", "History", "Horror", "Music",
    "Musical", "Mystery", "Romance", "Sci-Fi",
    "Sport", "Thriller", "War", "Western"
]


# CONVERT GENRE STRINGS INTO LISTS
def parse_genres(value):
    try:
        genres = ast.literal_eval(value)

        if isinstance(genres, list):
            return [str(g).strip() for g in genres]

    except (ValueError, SyntaxError, TypeError):
        pass

    return []


# CREATE GENRE FEATURES
movies_df["parsed_genres"] = movies_df["Genre"].apply(parse_genres)

genre_features = pd.DataFrame(
    {
        genre: movies_df["parsed_genres"].apply(
            lambda genres: int(genre in genres)
        )
        for genre in GENRE_FEATURES
    },
    index=movies_df.index
)

movies_df[GENRE_FEATURES] = genre_features


# PREDICT CLUSTERS FOR ALL MOVIES
scaled_movies = scaler.transform(movies_df[GENRE_FEATURES])

movies_df["Cluster"] = model.predict(scaled_movies)


# RECOMMEND MOVIES FROM A USER'S THREE GENRES
def recommend_movies_by_genres(selected_genres, limit=8):

    if len(selected_genres) != 3:
        raise ValueError("Please select exactly three genres.")

    invalid_genres = [
        genre for genre in selected_genres
        if genre not in GENRE_FEATURES
    ]

    if invalid_genres:
        raise ValueError("One or more selected genres are invalid.")

    # Create the user's genre preference profile
    user_profile = pd.DataFrame(
        [[
            int(genre in selected_genres)
            for genre in GENRE_FEATURES
        ]],
        columns=GENRE_FEATURES
    )

    # Predict the user's cluster
    scaled_profile = scaler.transform(user_profile)
    user_cluster = int(model.predict(scaled_profile)[0])

    # Find movies belonging to that cluster
    recommendations = movies_df[
        movies_df["Cluster"] == user_cluster
    ].copy()

    # Avoid showing duplicate movie titles
    recommendations = recommendations.drop_duplicates(
        subset=["Movie Name"]
    )

    # Calculate the most common genres in this cluster
    cluster_movies = movies_df[
        movies_df["Cluster"] == user_cluster
    ]

    genre_profile = cluster_movies[GENRE_FEATURES].mean()

    top_genres = (
        genre_profile
        .sort_values(ascending=False)
        .head(5)
    )

    top_genres = [
        genre for genre, score in top_genres.items()
        if score > 0
    ]

    # Return recommendations and the cluster explanation
    columns = [
        "Movie Name",
        "Year of Release",
        "Genre",
        "Movie Rating",
        "Votes"
    ]

    available_columns = [
        col for col in columns
        if col in recommendations.columns
    ]

    return {
        "cluster": user_cluster,
        "recommendations": recommendations[
            available_columns
        ].head(limit),
        "top_genres": top_genres
    }