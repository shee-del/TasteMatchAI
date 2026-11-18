import streamlit as st

from utils.movie_recommender import recommend_movies_by_genres
from utils.music_recommender import recommend_music_by_preferences


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="TasteMatchAI",
    page_icon="🎧",
    layout="wide"
)

# Number of recommendations displayed
RECOMMENDATION_LIMIT = 20


# --------------------------------------------------
# CUSTOM DESIGN
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #10111A;
    color: #F5F5F5;
}

h1, h2, h3, p, label {
    color: #F5F5F5;
}

.stButton > button {
    border-radius: 10px;
    min-height: 42px;
    border: 1px solid #44475A;
    background-color: #202231;
    color: white;
    font-weight: 600;
}

.stButton > button:hover {
    border: 1px solid #8B8FA8;
    color: white;
    background-color: #303448;
}

div[data-baseweb="input"] input {
    background-color: #202231;
    color: white;
}

div[data-baseweb="tab-list"] {
    gap: 12px;
}

div[data-baseweb="tab"] {
    background-color: #202231;
    border-radius: 8px;
    padding: 10px 20px;
}

div[data-testid="stDataFrame"] {
    background-color: #202231;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🎧 TasteMatchAI")

st.caption(
    "Discover your entertainment personality through "
    "intelligent machine learning recommendations."
)


# --------------------------------------------------
# TABS
# --------------------------------------------------

movie_tab, music_tab = st.tabs(["🎬 Movies", "🎵 Music"])


# ==================================================
# MOVIES
# ==================================================

with movie_tab:

    st.header("Discover Your Movie Taste")

    st.write(
        "Choose three movie genres that you enjoy. "
        "Our machine learning model will identify your "
        "movie taste group and recommend films you may enjoy."
    )

    movie_genres = [
        "Action", "Adventure", "Animation",
        "Biography", "Comedy", "Crime",
        "Drama", "Family", "Fantasy",
        "Film-Noir", "History", "Horror",
        "Music", "Musical", "Mystery",
        "Romance", "Sci-Fi", "Sport",
        "Thriller", "War", "Western"
    ]

    if "selected_movie_genres" not in st.session_state:
        st.session_state.selected_movie_genres = []

    selected_genres = st.session_state.selected_movie_genres

    st.write("### Select exactly 3 genres")

    columns = st.columns(3)

    for index, genre in enumerate(movie_genres):

        with columns[index % 3]:

            is_selected = genre in selected_genres

            label = f"✓ {genre}" if is_selected else genre

            if st.button(
                label,
                key=f"movie_genre_{genre}",
                use_container_width=True
            ):

                if is_selected:
                    selected_genres.remove(genre)

                elif len(selected_genres) < 3:
                    selected_genres.append(genre)

                st.rerun()

    st.write("")

    st.write(f"*Selected genres: {len(selected_genres)}/3*")

    if selected_genres:
        st.write(" • ".join(selected_genres))

    clear_col, search_col = st.columns(2)

    with clear_col:

        if st.button("Clear Selections", use_container_width=True):
            st.session_state.selected_movie_genres = []
            st.rerun()

    with search_col:

        find_movies = st.button(
            "Find My Movie Group",
            use_container_width=True
        )

    if find_movies:

        if len(selected_genres) != 3:

            st.warning("Please select exactly three genres.")

        else:

            with st.spinner("Discovering your movie taste..."):

                try:

                    result = recommend_movies_by_genres(
                        selected_genres,
                        limit=RECOMMENDATION_LIMIT
                    )

                    if "error" in result:

                        st.error(result["error"])

                    else:

                        st.success(
                            "Your movie taste profile has been identified!"
                        )

                        top_genres = result["top_genres"]

                        profile_name = " & ".join(top_genres[:2])

                        st.subheader(
                            f"The {profile_name} Enthusiast"
                        )

                        st.write(
                            "Your movie preferences are particularly "
                            "associated with "
                            + ", ".join(top_genres)
                            + " movie genres."
                        )

                        st.write("### Recommended Movies")

                        st.dataframe(
                            result["recommendations"],
                            use_container_width=True,
                            hide_index=True
                        )

                        st.caption(
                            f"Showing {len(result['recommendations'])} recommendations."
                        )

                except Exception as error:

                    st.error(f"Something went wrong: {error}")


# ==================================================
# MUSIC
# ==================================================

with music_tab:

    st.header("Discover Your Music Taste")

    st.write(
        "Enter any three songs or artists you enjoy. "
        "Our machine learning model will analyse your "
        "preferences and discover your music personality."
    )

    st.write("### Enter three songs or artists")

    col1, col2, col3 = st.columns(3)

    with col1:

        music_input_1 = st.text_input(
            "Song or Artist 1",
            placeholder="e.g. Adele",
            key="music_input_1"
        )

    with col2:

        music_input_2 = st.text_input(
            "Song or Artist 2",
            placeholder="e.g. Shape of You",
            key="music_input_2"
        )

    with col3:

        music_input_3 = st.text_input(
            "Song or Artist 3",
            placeholder="e.g. Taylor Swift",
            key="music_input_3"
        )

    st.write("")

    find_music = st.button(
        "Find My Music Taste",
        use_container_width=True
    )

    if find_music:

        music_inputs = [
            music_input_1.strip(),
            music_input_2.strip(),
            music_input_3.strip()
        ]

        if not all(music_inputs):

            st.warning("Please fill in all three music entries.")

        else:

            with st.spinner("Analysing your music preferences..."):

                try:

                    result = recommend_music_by_preferences(
                        music_inputs,
                        limit=RECOMMENDATION_LIMIT
                    )

                    if "error" in result:

                        st.error(result["error"])

                    else:

                        st.success(
                            "Your music taste profile has been identified!"
                        )

                        # Matched inputs
                        st.subheader("Your Music Selections")

                        for item in result["matched_inputs"]:

                            st.write(
                                f"*{item['input']}* — "
                                f"{item['matched_count']} matching tracks"
                            )

                            if item["examples"]:

                                st.caption(
                                    "Examples: "
                                    + ", ".join(item["examples"])
                                )

                        # Taste profile
                        profile = result["taste_profile"]

                        st.subheader(profile["profile_name"])

                        st.write(profile["description"])

                        st.write("### Your Music Traits")

                        st.write(" • ".join(profile["traits"]))

                        # Recommendations
                        st.write("### Recommended Songs")

                        st.dataframe(
                            result["recommendations"],
                            use_container_width=True,
                            hide_index=True
                        )

                        st.caption(
                            f"Showing {len(result['recommendations'])} recommendations."
                        )

                except Exception as error:

                    st.error(f"Something went wrong: {error}")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.write("")
st.divider()

st.caption(
    "TasteMatchAI | Intelligent Recommendations Powered by Machine Learning"
)