import streamlit as st
import requests
import pandas as pd
import re

from utils.auth import sign_up, log_in, log_out, reset_password
from utils.movie_recommender import recommend_movies_by_genres
from utils.music_recommender import recommend_music_by_preferences
from utils.tmdb import search_movie_poster


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="TasteMatchAI",
    page_icon="🎧",
    layout="wide"
)

RECOMMENDATION_LIMIT = 20
MAX_GENRES = 3

MOVIE_IMAGE = (
    "https://images.pexels.com/photos/109669/"
    "pexels-photo-109669.jpeg?auto=compress&dpr=1&h=750&w=1260"
)

MUSIC_IMAGE = (
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d"
    "?auto=format&fit=crop&w=1200&q=80"
)

GENRE_STYLE = {
    "Action": "💥",
    "Adventure": "🧭",
    "Animation": "🎨",
    "Biography": "🌟",
    "Comedy": "😂",
    "Crime": "🕵️",
    "Drama": "🎭",
    "Family": "👨‍👩‍👧‍👦",
    "Fantasy": "🪄",
    "Film-Noir": "🌃",
    "History": "🏛️",
    "Horror": "👻",
    "Music": "🎵",
    "Musical": "🎤",
    "Mystery": "🔍",
    "Romance": "💕",
    "Sci-Fi": "🚀",
    "Sport": "🏆",
    "Thriller": "😱",
    "War": "⚔️",
    "Western": "🤠"
}

MOVIE_GENRES = list(GENRE_STYLE.keys())


# ==================================================
# SESSION STATE
# ==================================================

defaults = {
    "logged_in": False,
    "user_email": "",
    "selected_movie_genres": [],
    "movie_result": None,
    "music_result": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def valid_email(email):
    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email.strip()
        )
    )


def has_value(value):
    if value is None:
        return False

    try:
        return not pd.isna(value) and str(value).strip() != ""
    except (TypeError, ValueError):
        return str(value).strip() != ""


@st.cache_data(ttl=86400, show_spinner=False)
def get_movie_poster(title):
    return search_movie_poster(title)


@st.cache_data(ttl=86400, show_spinner=False)
def get_music_artwork(track_name, artist):
    try:
        response = requests.get(
            "https://itunes.apple.com/search",
            params={
                "term": f"{track_name} {artist}",
                "entity": "song",
                "limit": 1
            },
            timeout=8
        )

        response.raise_for_status()

        results = response.json().get("results", [])

        if results:
            artwork = results[0].get("artworkUrl100")

            if artwork:
                return artwork.replace(
                    "100x100bb",
                    "600x600bb"
                )

    except requests.RequestException:
        pass

    return None


def show_movie_results(result):
    st.divider()
    st.subheader("🌟 Your movie personality")

    top_genres = result["top_genres"]
    profile_name = " & ".join(top_genres[:2])

    with st.container(border=True):
        st.markdown(f"### The {profile_name} Enthusiast")
        st.write(
            "Your preferences are particularly associated with "
            + ", ".join(top_genres)
            + " movies."
        )

    st.subheader("🍿 Movies picked for your taste")

    recommendations = result["recommendations"]

    st.caption(
        f"{len(recommendations)} recommendations selected for you."
    )

    for start in range(0, len(recommendations), 4):

        batch = recommendations.iloc[start:start + 4]
        columns = st.columns(4)

        for column, (_, movie) in zip(columns, batch.iterrows()):

            with column:

                title = str(movie["Movie Name"])
                year = movie.get("Year of Release", "")
                genre = movie.get("Genre", "")
                rating = movie.get("Movie Rating", "")

                with st.container(border=True):

                    poster = get_movie_poster(title)

                    if poster:
                        st.image(
                            poster,
                            use_container_width=True
                        )
                    else:
                        st.write("🎬 Poster unavailable")

                    st.markdown(f"*{title}*")

                    if has_value(year):
                        st.caption(str(year))

                    if has_value(genre):
                        st.caption(str(genre))

                    if has_value(rating):
                        st.caption(f"⭐ {rating}")


def show_music_results(result):
    st.divider()
    st.subheader("🌟 Your music personality")

    profile = result["taste_profile"]

    with st.container(border=True):
        st.markdown(f"### {profile['profile_name']}")
        st.write(profile["description"])
        st.caption(" • ".join(profile["traits"]))

    st.subheader("🎼 Your music selections")

    for item in result["matched_inputs"]:
        st.markdown(
            f"*{item['input']}* — "
            f"{item['matched_count']} matching tracks"
        )

        if item["examples"]:
            st.caption(
                "Examples: " + ", ".join(item["examples"])
            )

    st.subheader("🎧 Recommended for your ears")

    recommendations = result["recommendations"]

    st.caption(
        f"{len(recommendations)} songs selected for your taste."
    )

    for start in range(0, len(recommendations), 4):

        batch = recommendations.iloc[start:start + 4]
        columns = st.columns(4)

        for column, (_, song) in zip(columns, batch.iterrows()):

            with column:

                track = str(song["track_name"])
                artist = str(song["artists"])
                genre = song.get("track_genre", "")
                popularity = song.get("popularity", "")

                with st.container(border=True):

                    artwork = get_music_artwork(track, artist)

                    if artwork:
                        st.image(
                            artwork,
                            use_container_width=True
                        )
                    else:
                        st.write("🎵 Artwork unavailable")

                    st.markdown(f"*{track}*")
                    st.caption(artist)

                    if has_value(genre):
                        st.caption(str(genre))

                    if has_value(popularity):
                        st.caption(
                            f"Popularity: {popularity}"
                        )


# ==================================================
# AUTHENTICATION PAGE
# ==================================================

if not st.session_state.logged_in:

    image_col, login_col = st.columns(
        [1.1, 0.9],
        gap="large"
    )

    with image_col:

        st.image(
            MOVIE_IMAGE,
            use_container_width=True
        )

        st.title("Your next favourite is waiting.")

        st.write(
            "Discover movies and music selected around "
            "what you love."
        )

        st.caption(
            "🎬 MOVIES  •  🎵 MUSIC  •  ✨ YOUR TASTE"
        )

    with login_col:

        st.title("TasteMatchAI")
        st.caption("Discover your vibe. Explore your world.")

        login_tab, signup_tab, reset_tab = st.tabs([
            "Log in",
            "Create account",
            "Forgot password"
        ])

        # LOGIN

        with login_tab:

            st.subheader("Welcome back")

            with st.form("login_form"):

                email = st.text_input(
                    "Email address",
                    placeholder="you@example.com"
                )

                password = st.text_input(
                    "Password",
                    type="password"
                )

                login_submitted = st.form_submit_button(
                    "Log in",
                    use_container_width=True,
                    type="primary"
                )

            if login_submitted:

                email = email.strip()

                if not email or not password:
                    st.warning("Enter your email and password.")

                elif not valid_email(email):
                    st.warning("Enter a valid email address.")

                else:

                    with st.spinner("Signing you in..."):
                        response, error = log_in(email, password)

                    if error:
                        st.error("Login unsuccessful.")
                        st.caption(error)

                    elif response and response.user:

                        st.session_state.logged_in = True
                        st.session_state.user_email = (
                            response.user.email or email
                        )

                        st.session_state.selected_movie_genres = []
                        st.session_state.movie_result = None
                        st.session_state.music_result = None

                        st.rerun()

        # SIGN UP

        with signup_tab:

            st.subheader("Create your account")

            with st.form("signup_form"):

                new_email = st.text_input(
                    "Email address",
                    placeholder="you@example.com"
                )

                new_password = st.text_input(
                    "Create password",
                    type="password"
                )

                confirm_password = st.text_input(
                    "Confirm password",
                    type="password"
                )

                signup_submitted = st.form_submit_button(
                    "Create account",
                    use_container_width=True,
                    type="primary"
                )

            if signup_submitted:

                new_email = new_email.strip()

                if not new_email or not new_password or not confirm_password:
                    st.warning("Please fill in all fields.")

                elif not valid_email(new_email):
                    st.warning("Enter a valid email address.")

                elif len(new_password) < 8:
                    st.warning(
                        "Password must contain at least 8 characters."
                    )

                elif new_password != confirm_password:
                    st.warning("Your passwords do not match.")

                else:

                    with st.spinner("Creating your account..."):
                        response, error = sign_up(
                            new_email,
                            new_password
                        )

                    if error:
                        st.error("We couldn't create your account.")
                        st.caption(error)

                    else:
                        st.success(
                            "Account created! You can now log in."
                        )

        # PASSWORD RESET

        with reset_tab:

            st.subheader("Reset your password")

            with st.form("reset_form"):

                reset_email = st.text_input(
                    "Email address",
                    placeholder="you@example.com"
                )

                reset_submitted = st.form_submit_button(
                    "Send recovery email",
                    use_container_width=True,
                    type="primary"
                )

            if reset_submitted:

                reset_email = reset_email.strip()

                if not valid_email(reset_email):
                    st.warning("Enter a valid email address.")

                else:

                    with st.spinner("Sending recovery email..."):
                        success, error = reset_password(reset_email)

                    if error:
                        st.error("Unable to send recovery email.")
                        st.caption(error)

                    else:
                        st.success(
                            "If an account exists for that email, "
                            "a recovery email will be sent."
                        )

    st.stop()


# ==================================================
# MAIN APPLICATION
# ==================================================

brand_col, account_col = st.columns([2, 1])

with brand_col:
    st.title("🎧 TasteMatchAI")
    st.caption("Discover your vibe. Explore your world.")

with account_col:

    st.write(f"Signed in as *{st.session_state.user_email}*")

    if st.button("Log out", use_container_width=True):

        success, error = log_out()

        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.selected_movie_genres = []
        st.session_state.movie_result = None
        st.session_state.music_result = None

        st.rerun()


st.divider()

hero_col, image_col = st.columns(
    [1.2, 1],
    gap="large"
)

with hero_col:

    st.title("Tell us what you love.")
    st.subheader("We'll find what's next.")

    st.write(
        "Choose your favourite movie genres or tell us "
        "which songs and artists you enjoy."
    )

    st.write(
        "Our machine learning models will help discover "
        "your entertainment taste."
    )

with image_col:

    st.image(
        MOVIE_IMAGE,
        use_container_width=True
    )


# ==================================================
# MOVIE AND MUSIC TABS
# ==================================================

movie_tab, music_tab = st.tabs([
    "🎬 Movies",
    "🎵 Music"
])


# ==================================================
# MOVIES
# ==================================================

with movie_tab:

    st.header("Find my movie group")

    st.write(
        "Choose exactly three genres you enjoy."
    )

    selected_genres = st.session_state.selected_movie_genres

    st.progress(
        len(selected_genres) / MAX_GENRES,
        text=f"{len(selected_genres)} of 3 genres selected"
    )

    columns = st.columns(3)

    for index, genre in enumerate(MOVIE_GENRES):

        with columns[index % 3]:

            is_selected = genre in selected_genres

            label = (
                f"✓ {GENRE_STYLE[genre]} {genre}"
                if is_selected
                else f"{GENRE_STYLE[genre]} {genre}"
            )

            disabled = (
                len(selected_genres) >= MAX_GENRES
                and not is_selected
            )

            if st.button(
                label,
                key=f"genre_{genre}",
                use_container_width=True,
                disabled=disabled
            ):

                if is_selected:
                    selected_genres.remove(genre)
                else:
                    selected_genres.append(genre)

                st.session_state.movie_result = None
                st.rerun()

    st.write(
        "Selected: "
        + (
            ", ".join(selected_genres)
            if selected_genres
            else "None yet"
        )
    )

    clear_col, discover_col = st.columns([1, 2])

    with clear_col:

        if st.button("Clear choices", use_container_width=True):
            st.session_state.selected_movie_genres = []
            st.session_state.movie_result = None
            st.rerun()

    with discover_col:

        discover_movies = st.button(
            "✨ Find my movie group",
            use_container_width=True,
            type="primary"
        )

    if discover_movies:

        if len(selected_genres) != MAX_GENRES:

            st.warning("Please choose exactly three genres.")

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
                        st.session_state.movie_result = result

                except Exception as error:
                    st.error(f"Movie recommendation error: {error}")

    if st.session_state.movie_result:
        show_movie_results(st.session_state.movie_result)


# ==================================================
# MUSIC
# ==================================================

with music_tab:

    st.header("Find my music taste")

    st.write(
        "Enter three songs or artists you enjoy."
    )

    music_col1, music_col2, music_col3 = st.columns(3)

    with music_col1:

        music_input_1 = st.text_input(
            "First song or artist",
            placeholder="e.g. Adele",
            key="music_input_1"
        )

    with music_col2:

        music_input_2 = st.text_input(
            "Second song or artist",
            placeholder="e.g. Shape of You",
            key="music_input_2"
        )

    with music_col3:

        music_input_3 = st.text_input(
            "Third song or artist",
            placeholder="e.g. Taylor Swift",
            key="music_input_3"
        )

    st.image(
        MUSIC_IMAGE,
        use_container_width=True
    )

    discover_music = st.button(
        "🎧 Find my music taste",
        use_container_width=True,
        type="primary"
    )

    if discover_music:

        music_inputs = [
            music_input_1.strip(),
            music_input_2.strip(),
            music_input_3.strip()
        ]

        if not all(music_inputs):

            st.warning("Please fill in all three boxes.")

        else:

            with st.spinner("Discovering your music taste..."):

                try:

                    result = recommend_music_by_preferences(
                        music_inputs,
                        limit=RECOMMENDATION_LIMIT
                    )

                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state.music_result = result

                except Exception as error:
                    st.error(f"Music recommendation error: {error}")

    if st.session_state.music_result:
        show_music_results(st.session_state.music_result)


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "TasteMatchAI | Intelligent entertainment recommendations "
    "powered by machine learning."
)

st.caption(
    "This product uses the TMDB API but is not endorsed "
    "or certified by TMDB."
)