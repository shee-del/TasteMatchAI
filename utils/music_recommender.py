import joblib
import pandas as pd
from pathlib import Path

# 1. LOAD DATA AND MODEL

BASE_DIR = Path(__file__).resolve().parent.parent

music_df = pd.read_csv(BASE_DIR / "data" / "spotify-tracks-dataset.csv")
artifacts = joblib.load(BASE_DIR / "models" / "music" / "music_model.pkl")

model = artifacts["model"]
scaler = artifacts["scaler"]
features = artifacts["features"]

music_df[features] = music_df[features].fillna(music_df[features].mean())

scaled_music = pd.DataFrame(
    scaler.transform(music_df[features]),
    columns=features,
    index=music_df.index
)

music_df["cluster"] = model.predict(scaled_music)


# 2. MATCH SONGS OR ARTISTS

def find_music_matches(search_term):

    term = search_term.strip().lower()

    if not term:
        return pd.DataFrame()

    titles = music_df["track_name"].fillna("").str.strip().str.lower()
    artists = music_df["artists"].fillna("").str.lower()

    # Exact song title first
    exact_title = music_df[titles == term]

    if not exact_title.empty:
        return exact_title

    # Exact artist name
    exact_artist = music_df[
        artists.apply(
            lambda value: any(
                artist.strip().lower() == term
                for artist in value.split(";")
            )
        )
    ]

    if not exact_artist.empty:
        return exact_artist

    # Partial artist match
    artist_matches = music_df[
        artists.str.contains(term, regex=False)
    ]

    if not artist_matches.empty:
        return artist_matches

    # Partial song title match
    return music_df[
        titles.str.contains(term, regex=False)
    ]


# 3. CREATE A TASTE PROFILE

def get_music_profile(cluster_id):

    cluster_data = music_df[music_df["cluster"] == cluster_id]

    overall = music_df[features].mean()
    cluster_mean = cluster_data[features].mean()

    std = music_df[features].std().replace(0, 1)
    differences = (cluster_mean - overall) / std

    traits = []

    checks = [
        ("danceability", 0.35, "Danceable"),
        ("energy", 0.35, "Energetic"),
        ("valence", 0.35, "Upbeat"),
        ("acousticness", 0.35, "Acoustic"),
        ("instrumentalness", 0.35, "Instrumental"),
        ("speechiness", 0.35, "Speech-driven"),
        ("liveness", 0.35, "Live-sounding"),
        ("tempo", 0.35, "Fast-paced"),
        ("loudness", 0.35, "Bold-sounding")
    ]

    for feature, threshold, label in checks:
        if differences[feature] > threshold:
            traits.append(label)

    if differences["valence"] < -0.35:
        traits.append("Melancholic")

    if differences["energy"] < -0.35:
        traits.append("Calm")

    if not traits:
        traits = ["Balanced"]

    profile_name = "The " + " & ".join(traits[:2]) + " Listener"

    description = (
        "Your listening preferences are particularly associated with "
        + ", ".join(traits)
        + " musical characteristics."
    )

    return {
        "profile_name": profile_name,
        "description": description,
        "traits": traits
    }


# 4. RECOMMEND SONGS FROM THREE INPUTS

def recommend_music_by_preferences(search_terms, limit=8):

    if len(search_terms) != 3:
        return {"error": "Please enter exactly three songs or artists."}

    profiles = []
    matched_indices = []
    matched_inputs = []

    for term in search_terms:

        if not isinstance(term, str) or not term.strip():
            return {"error": "Please fill in all three entries."}

        matches = find_music_matches(term)

        if matches.empty:
            return {
                "error": f"We could not find '{term}' in the music dataset. Try another song or artist."
            }

        # Each input contributes one equally weighted profile
        input_profile = matches[features].mean()
        profiles.append(input_profile)

        matched_indices.extend(matches.index.tolist())

        matched_inputs.append({
            "input": term,
            "matched_count": len(matches),
            "examples": matches["track_name"].drop_duplicates().head(3).tolist()
        })

    # Average the three input profiles equally
    user_profile = pd.DataFrame(
        [sum(profiles) / len(profiles)],
        columns=features
    )

    scaled_profile = scaler.transform(user_profile)
    predicted_cluster = int(model.predict(scaled_profile)[0])

    taste_profile = get_music_profile(predicted_cluster)

    # Recommend songs from the predicted cluster
    recommendations = music_df[
        music_df["cluster"] == predicted_cluster
    ].copy()

    # Exclude songs already matched from user inputs
    recommendations = recommendations.drop(
        index=list(set(matched_indices)),
        errors="ignore"
    )

    recommendations = recommendations.drop_duplicates(
        subset=["track_name", "artists"]
    )

    recommendations = recommendations.head(limit)

    display_columns = [
        "track_name",
        "artists",
        "track_genre",
        "popularity"
    ]

    return {
        "taste_profile": taste_profile,
        "recommendations": recommendations[display_columns],
        "matched_inputs": matched_inputs
    }


# 5. BACKWARD COMPATIBILITY

def recommend_music(track_name, limit=8):
    return recommend_music_by_preferences(
        [track_name, track_name, track_name],
        limit
    )