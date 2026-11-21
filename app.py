import streamlit as st
import requests
import pandas as pd
import re
import plotly.express as px

from utils.auth import sign_up, log_in, log_out, reset_password
from utils.movie_recommender import recommend_movies_by_genres
from utils.music_recommender import recommend_music_by_preferences
from utils.tmdb import search_movie_poster

from utils.analytics import (
    is_admin,
    record_activity,
    get_activity_data,
    get_analytics_summary,
    get_movie_genre_distribution,
    get_music_preference_distribution,
    export_activity_csv
)


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

HERO_IMAGE = (
    "https://images.unsplash.com/photo-1536440136628-849c177e76a1"
    "?auto=format&fit=crop&w=1400&q=70"
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

GENRE_COLORS = {
    "Action": ("#ff4b4b", "#7a1010"),
    "Adventure": ("#22c1c3", "#0b4f6c"),
    "Animation": ("#ff9a9e", "#7b4fc9"),
    "Biography": ("#f6d365", "#b45309"),
    "Comedy": ("#feca57", "#ff6b6b"),
    "Crime": ("#485563", "#1f2630"),
    "Drama": ("#9d50bb", "#4a1d6e"),
    "Family": ("#43cea2", "#185a9d"),
    "Fantasy": ("#8e2de2", "#4a00e0"),
    "Film-Noir": ("#434343", "#0c0c0c"),
    "History": ("#c79081", "#7b4b2a"),
    "Horror": ("#3b0a0a", "#8b0000"),
    "Music": ("#4776e6", "#8e54e9"),
    "Musical": ("#ee0979", "#ff6a00"),
    "Mystery": ("#134e5e", "#71b280"),
    "Romance": ("#ff5f6d", "#ffc371"),
    "Sci-Fi": ("#0f2027", "#2c5364"),
    "Sport": ("#11998e", "#38ef7d"),
    "Thriller": ("#3a1c71", "#d76d77"),
    "War": ("#4b5320", "#1c1c1c"),
    "Western": ("#c2833a", "#6b3e1b")
}

_U = "https://images.unsplash.com/photo-{}?auto=format&fit=crop&w=600&q=70"

GENRE_IMAGES = {
    "Action": _U.format("1534809027769-b00d750a6bac"),
    "Adventure": _U.format("1501555088652-021faa106b9b"),
    "Animation": _U.format("1513364776144-60967b0f800f"),
    "Biography": _U.format("1455390582262-044cdead277a"),
    "Comedy": _U.format("1527224857830-43a7acc85260"),
    "Crime": _U.format("1453873531674-2151bcd01707"),
    "Drama": _U.format("1503095396549-807759245b35"),
    "Family": _U.format("1511895426328-dc8714191300"),
    "Fantasy": _U.format("1518709268805-4e9042af9f23"),
    "Film-Noir": _U.format("1489599849927-2ee91cede3ba"),
    "History": _U.format("1461360370896-922624d12aa1"),
    "Horror": _U.format("1509248961158-e54f6934749c"),
    "Music": _U.format("1511379938547-c1f69419868d"),
    "Musical": _U.format("1507676184212-d03ab07a01bf"),
    "Mystery": _U.format("1505664194779-8beaceb93744"),
    "Romance": _U.format("1518199266791-5375a83190b7"),
    "Sci-Fi": _U.format("1446776811953-b23d57bd21aa"),
    "Sport": _U.format("1461896836934-ffe607ba8211"),
    "Thriller": _U.format("1478720568477-152d9b164e26"),
    "War": _U.format("1580130775562-0ef92da4c3e6"),
    "Western": _U.format("1473496169904-658ba7c44d8a")
}


# ==================================================
# SESSION STATE
# ==================================================

defaults = {
    "logged_in": False,
    "user_email": "",
    "selected_movie_genres": [],
    "movie_result": None,
    "music_result": None,
    "navigation": "Home"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# LOGIN PAGE STYLE
# ==================================================

def inject_login_style():
    st.markdown("""
<style>
.stApp {
    background: linear-gradient(-45deg, #0b0b12, #1d0b33, #330a24, #0a1f33);
    background-size: 400% 400%;
    animation: bgShift 14s ease infinite;
}
@keyframes bgShift {
    0% {background-position: 0% 50%}
    50% {background-position: 100% 50%}
    100% {background-position: 0% 50%}
}
@keyframes floaty {
    0%, 100% {transform: translateY(0)}
    50% {transform: translateY(-12px)}
}
@keyframes fadeUp {
    from {opacity: 0; transform: translateY(24px)}
    to {opacity: 1; transform: translateY(0)}
}
@keyframes drift {
    0% {transform: translateY(0) rotate(0deg); opacity: 0}
    10% {opacity: .5}
    90% {opacity: .5}
    100% {transform: translateY(-115vh) rotate(360deg); opacity: 0}
}
@keyframes shine {
    to {background-position: 300% center}
}
.brand {
    font-size: 3.2rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(90deg, #ff4b4b, #ff9f43, #feca57, #ff4b4b);
    background-size: 300% auto;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 6s linear infinite, fadeUp .8s ease both;
}
.tagline {
    color: #c9c9d6;
    margin-bottom: 1rem;
    animation: fadeUp 1s ease both;
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #ffffff;
    margin: 1rem 0 .3rem;
    animation: fadeUp .9s ease both;
}
.hero-sub {
    color: #c9c9d6;
    font-size: 1.1rem;
}
.chip {
    display: inline-block;
    padding: 6px 14px;
    margin: 10px 8px 0 0;
    border-radius: 999px;
    font-size: .85rem;
    color: #ffffff;
    background: rgba(255, 255, 255, .08);
    border: 1px solid rgba(255, 255, 255, .18);
    transition: all .25s ease;
}
.chip:hover {
    background: #ff4b4b;
    transform: translateY(-3px);
}
[data-testid="stImage"] img {
    border-radius: 22px;
    box-shadow: 0 20px 60px rgba(255, 75, 75, .3);
    animation: floaty 6s ease-in-out infinite;
}
[data-testid="stForm"] {
    background: rgba(255, 255, 255, .05);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, .14);
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: 0 10px 40px rgba(0, 0, 0, .4);
    animation: fadeUp .8s ease both;
}
[data-testid="stTextInput"] input {
    border-radius: 12px;
    transition: box-shadow .2s ease;
}
[data-testid="stTextInput"] input:focus {
    box-shadow: 0 0 0 2px #ff4b4b, 0 0 18px rgba(255, 75, 75, .45);
}
[data-testid="stBaseButton-primaryFormSubmit"],
button[kind="primaryFormSubmit"] {
    background: linear-gradient(90deg, #ff4b4b, #ff9f43);
    border: none;
    border-radius: 12px;
    font-weight: 700;
    transition: transform .2s ease, box-shadow .2s ease;
}
[data-testid="stBaseButton-primaryFormSubmit"]:hover,
button[kind="primaryFormSubmit"]:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 25px rgba(255, 75, 75, .5);
}
.float-emoji {
    position: fixed;
    bottom: -60px;
    font-size: 1.8rem;
    z-index: 0;
    pointer-events: none;
    animation: drift linear infinite;
}
</style>

<span class="float-emoji" style="left:8%; animation-duration:16s;">🎬</span>
<span class="float-emoji" style="left:22%; animation-duration:21s; animation-delay:3s;">🎵</span>
<span class="float-emoji" style="left:45%; animation-duration:18s; animation-delay:6s;">🍿</span>
<span class="float-emoji" style="left:68%; animation-duration:23s; animation-delay:1s;">🎧</span>
<span class="float-emoji" style="left:88%; animation-duration:19s; animation-delay:8s;">🎤</span>
""", unsafe_allow_html=True)


# ==================================================
# DASHBOARD STYLE
# ==================================================

def inject_dashboard_style():
    st.markdown("""
<style>
html {font-size: 15px;}

.stApp {
    background:
        radial-gradient(circle at 10% 15%, rgba(255,107,107,.55), transparent 40%),
        radial-gradient(circle at 90% 10%, rgba(78,205,196,.50), transparent 40%),
        radial-gradient(circle at 80% 90%, rgba(254,202,87,.45), transparent 40%),
        radial-gradient(circle at 15% 85%, rgba(162,89,255,.55), transparent 45%),
        linear-gradient(135deg, #3a2a8c, #5b3aa6 50%, #8a3fb0);
    background-size: 160% 160%;
    animation: bgMove 20s ease-in-out infinite alternate;
}
@keyframes bgMove {
    0% {background-position: 0% 0%}
    100% {background-position: 100% 100%}
}
@keyframes fadeUp {
    from {opacity: 0; transform: translateY(14px)}
    to {opacity: 1; transform: translateY(0)}
}
.block-container {padding-top: 2rem; max-width: 1200px;}

.topbrand {
    font-size: 1.9rem;
    font-weight: 800;
    margin: 0;
    color: #ffffff;
    text-shadow: 0 2px 0 #3a2a8c, 0 4px 14px rgba(20,8,60,.6);
    letter-spacing: .5px;
}
.toptag {
    color: #ffffff;
    font-size: .85rem;
    text-shadow: 0 1px 6px rgba(20,8,60,.7);
}
.hero {
    border-radius: 20px;
    padding: 26px 30px;
    margin: 10px 0 14px;
    background-size: cover;
    background-position: center;
    border: 1px solid rgba(255,255,255,.3);
    box-shadow: 0 12px 36px rgba(20,8,60,.35);
    animation: fadeUp .6s ease both;
}
.hero-eyebrow {
    color: #ffe08a;
    font-size: .7rem;
    letter-spacing: .16em;
    text-transform: uppercase;
    font-weight: 700;
}
.hero-h {
    color: #fff;
    font-size: 1.7rem;
    font-weight: 800;
    line-height: 1.2;
    margin: 6px 0 4px;
}
.hero-p {color: #f1ecff; font-size: .95rem; max-width: 480px;}

.tile {
    border: 1px solid rgba(255,255,255,.3);
    border-radius: 16px;
    padding: 12px 16px;
    backdrop-filter: blur(8px);
    transition: transform .2s ease;
}
.tile:hover {transform: translateY(-3px);}
.tile-val {color: #fff; font-size: 1.3rem; font-weight: 800;}
.tile-lab {color: #f1ecff; font-size: .75rem;}

.gcard {
    position: relative;
    height: 125px;
    border-radius: 16px;
    overflow: hidden;
    border: 2px solid rgba(255,255,255,.25);
    background-size: cover;
    background-position: center;
    box-shadow: 0 6px 18px rgba(20,8,60,.3);
    transition: transform .25s ease, box-shadow .25s ease;
    margin-bottom: 6px;
}
.gcard:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 12px 28px rgba(255,200,87,.45);
}
.gcard.selected {
    border-color: #ffe08a;
    box-shadow: 0 0 0 3px rgba(255,224,138,.5), 0 12px 28px rgba(255,200,87,.5);
}
.gcard.dim {opacity: .5; filter: grayscale(.5);}
.gemoji {
    position: absolute; top: 8px; left: 10px; font-size: 1.2rem;
    background: rgba(0,0,0,.35); border-radius: 10px; padding: 2px 7px;
}
.gname {
    position: absolute; left: 12px; bottom: 9px; color: #fff;
    font-size: .95rem; font-weight: 800;
    text-shadow: 0 2px 8px rgba(0,0,0,.7);
}
.gcheck {
    position: absolute; top: 8px; right: 10px; width: 24px; height: 24px;
    border-radius: 50%; background: #ffe08a; color: #3a2a8c;
    font-weight: 800; text-align: center; line-height: 24px; font-size: .85rem;
}
.pill {
    display: inline-block; padding: 5px 12px; margin: 3px 6px 3px 0;
    border-radius: 999px; font-size: .8rem; color: #3a2a8c;
    background: linear-gradient(90deg, #ffe08a, #ffb3c7); font-weight: 700;
}
.pill-empty {color: #e6defa; font-size: .85rem;}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,.12);
    border: 1px solid rgba(255,255,255,.28) !important;
    border-radius: 16px;
    backdrop-filter: blur(8px);
    transition: transform .2s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #ffe08a !important;
}
[data-testid="stImage"] img {border-radius: 12px; transition: transform .3s ease;}
[data-testid="stImage"] img:hover {transform: scale(1.03);}
[data-baseweb="tab"] {font-size: .95rem; font-weight: 700; color: #fff;}

[data-testid="stBaseButton-secondary"] {
    background: rgba(40, 20, 100, .55);
    color: #ffffff;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,.4);
    border-radius: 12px;
}
[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(40, 20, 100, .8);
    border-color: #ffe08a;
    color: #ffffff;
}
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, #ff6b6b, #ffb347);
    color: #fff;
    border: none;
    border-radius: 12px;
    font-weight: 800;
}
[data-testid="stTextInput"] input {border-radius: 12px;}
.sec-title {color: #fff; font-size: 1.25rem; font-weight: 800; margin: 6px 0 2px;}
.sec-sub {color: #e6defa; font-size: .9rem; margin-bottom: 10px;}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(25, 14, 67, .96);
}
[data-testid="stSidebar"] * {
    color: #ffffff;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    border-radius: 10px;
    padding: 5px 8px;
    transition: background .2s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,.12);
}
</style>
""", unsafe_allow_html=True)


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


def genre_card_html(genre, selected, dim):
    c1, c2 = GENRE_COLORS.get(genre, ("#333333", "#111111"))
    image = GENRE_IMAGES.get(genre, "")

    background = (
        "linear-gradient(180deg, rgba(0,0,0,.05) 25%, rgba(0,0,0,.8)), "
        f"url('{image}'), "
        f"linear-gradient(135deg, {c1}, {c2})"
    )

    classes = "gcard"

    if selected:
        classes += " selected"

    if dim:
        classes += " dim"

    check = '<div class="gcheck">✓</div>' if selected else ""

    return (
        f'<div class="{classes}" style="background: {background}; '
        'background-size: cover; background-position: center;">'
        f'<div class="gemoji">{GENRE_STYLE[genre]}</div>'
        f"{check}"
        f'<div class="gname">{genre}</div>'
        "</div>"
    )


def stat_tile(value, label, accent):
    return (
        f'<div class="tile" style="background: linear-gradient(135deg, '
        f'{accent}66, rgba(255,255,255,.10)); border-color: {accent};">'
        f'<div class="tile-val">{value}</div>'
        f'<div class="tile-lab">{label}</div>'
        "</div>"
    )


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
                return artwork.replace("100x100bb", "600x600bb")

    except requests.RequestException:
        pass

    return None


# ==================================================
# NAVIGATION CALLBACKS
# ==================================================

def go_to_home():
    st.session_state.navigation = "Home"


def go_to_movies():
    st.session_state.navigation = "Movies"


def go_to_music():
    st.session_state.navigation = "Music"


# ==================================================
# MOVIE RESULTS
# ==================================================

def show_movie_results(result):
    st.divider()

    st.markdown(
        '<div class="sec-title">🌟 Your movie personality</div>',
        unsafe_allow_html=True
    )

    top_genres = result["top_genres"]
    profile_name = " & ".join(top_genres[:2])

    with st.container(border=True):
        st.markdown(f"### The {profile_name} Enthusiast")
        st.write(
            "Your preferences are particularly associated with "
            + ", ".join(top_genres)
            + " movies."
        )

    st.markdown(
        '<div class="sec-title">🍿 Movies picked for your taste</div>',
        unsafe_allow_html=True
    )

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
                        st.image(poster, use_container_width=True)
                    else:
                        st.write("🎬 Poster unavailable")

                    st.markdown(f"{title}")

                    if has_value(year):
                        st.caption(str(year))

                    if has_value(genre):
                        st.caption(str(genre))

                    if has_value(rating):
                        st.caption(f"⭐ {rating}")


# ==================================================
# MUSIC RESULTS
# ==================================================

def show_music_results(result):
    st.divider()

    st.markdown(
        '<div class="sec-title">🌟 Your music personality</div>',
        unsafe_allow_html=True
    )

    profile = result["taste_profile"]

    with st.container(border=True):
        st.markdown(f"### {profile['profile_name']}")
        st.write(profile["description"])
        st.caption(" • ".join(profile["traits"]))

    st.markdown(
        '<div class="sec-title">🎼 Your music selections</div>',
        unsafe_allow_html=True
    )

    for item in result["matched_inputs"]:
        st.markdown(
            f"{item['input']} — "
            f"{item['matched_count']} matching tracks"
        )

        if item["examples"]:
            st.caption("Examples: " + ", ".join(item["examples"]))

    st.markdown(
        '<div class="sec-title">🎧 Recommended for your ears</div>',
        unsafe_allow_html=True
    )

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
                        st.image(artwork, use_container_width=True)
                    else:
                        st.write("🎵 Artwork unavailable")

                    st.markdown(f"{track}")
                    st.caption(artist)

                    if has_value(genre):
                        st.caption(str(genre))

                    if has_value(popularity):
                        st.caption(f"Popularity: {popularity}")


# ==================================================
# AUTHENTICATION PAGE
# ==================================================

if not st.session_state.logged_in:

    inject_login_style()

    image_col, login_col = st.columns([1.1, 0.9], gap="large")

    with image_col:
        st.image(MOVIE_IMAGE, use_container_width=True)

        st.markdown("""
<div class="hero-title">Your next favourite is waiting.</div>
<div class="hero-sub">
Discover movies and music selected around what you love.
</div>
<span class="chip">🎬 Movies</span>
<span class="chip">🎵 Music</span>
<span class="chip">✨ Your taste</span>
""", unsafe_allow_html=True)

    with login_col:
        st.markdown(
            '<h1 class="brand">TasteMatchAI</h1>'
            '<div class="tagline">'
            'Discover your vibe. Explore your world.'
            '</div>',
            unsafe_allow_html=True
        )

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
                        st.session_state.navigation = "Home"

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
# AUTHENTICATED APPLICATION
# ==================================================

inject_dashboard_style()

admin_access = is_admin()

navigation_options = [
    "Home",
    "Movies",
    "Music"
]

if admin_access:
    navigation_options.append("Analytics & Reports")

navigation_options.append("My Account")


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

with st.sidebar:

    st.markdown("## 🎧 TasteMatchAI")
    st.caption("Discover your vibe. Explore your world.")

    st.divider()

    sidebar_icons = {
        "Home": "🏠 Home",
        "Movies": "🎬 Movies",
        "Music": "🎵 Music",
        "Analytics & Reports": "📊 Analytics & Reports",
        "My Account": "👤 My Account"
    }

    selected_page = st.radio(
        "Navigation",
        navigation_options,
        format_func=lambda page: sidebar_icons[page],
        key="navigation"
    )

    st.divider()

    st.caption("Signed in as")
    st.caption(st.session_state.user_email)

    st.write("")

    if st.button(
        "🚪 Log out",
        use_container_width=True,
        key="sidebar_logout"
    ):
        log_out()

        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.selected_movie_genres = []
        st.session_state.movie_result = None
        st.session_state.music_result = None

        st.rerun()


# ==================================================
# TOP BRANDING
# ==================================================

st.markdown(
    '<div class="topbrand">🎧 TasteMatchAI</div>'
    '<div class="toptag">Discover your vibe. Explore your world.</div>',
    unsafe_allow_html=True
)


# ==================================================
# HOME PAGE
# ==================================================

if selected_page == "Home":

    st.markdown(f"""
<div class="hero" style="background-image:
linear-gradient(90deg, rgba(58,42,140,.88) 0%,
rgba(58,42,140,.35) 55%, rgba(58,42,140,0) 100%),
url('{HERO_IMAGE}'), linear-gradient(135deg, #ff6b6b, #ffb347);">
<div class="hero-eyebrow">Your personal entertainment guide</div>
<div class="hero-h">Tell us what you love.<br>We'll find what's next.</div>
<div class="hero-p">
Pick your favourite movie genres or tell us which songs and artists you enjoy.
</div>
</div>
""", unsafe_allow_html=True)

    selected_genres = st.session_state.selected_movie_genres

    tile1, tile2, tile3, tile4 = st.columns(4)

    with tile1:
        st.markdown(
            stat_tile(
                len(MOVIE_GENRES),
                "Genres to explore",
                "#ff6b6b"
            ),
            unsafe_allow_html=True
        )

    with tile2:
        st.markdown(
            stat_tile(
                f"{len(selected_genres)}/{MAX_GENRES}",
                "Genres picked",
                "#4ecdc4"
            ),
            unsafe_allow_html=True
        )

    with tile3:
        st.markdown(
            stat_tile(
                RECOMMENDATION_LIMIT,
                "Picks per search",
                "#ffe08a"
            ),
            unsafe_allow_html=True
        )

    with tile4:
        st.markdown(
            stat_tile(
                "🎬 + 🎵",
                "Movies and music",
                "#c9a0ff"
            ),
            unsafe_allow_html=True
        )

    st.write("")

    movie_col, music_col = st.columns(2)

    with movie_col:
        st.image(MOVIE_IMAGE, use_container_width=True)
        st.subheader("🎬 Discover your movie taste")
        st.write(
            "Choose three movie genres and discover recommendations "
            "matched to your preferences."
        )

        st.button(
            "Explore Movies",
            key="home_movies",
            use_container_width=True,
            on_click=go_to_movies
        )

    with music_col:
        st.image(MUSIC_IMAGE, use_container_width=True)
        st.subheader("🎵 Discover your music taste")
        st.write(
            "Enter three songs or artists you enjoy and discover "
            "music recommendations."
        )

        st.button(
            "Explore Music",
            key="home_music",
            use_container_width=True,
            on_click=go_to_music
        )


# ==================================================
# MOVIES PAGE
# ==================================================

elif selected_page == "Movies":

    selected_genres = st.session_state.selected_movie_genres

    st.markdown(
        '<div class="sec-title">Find my movie group</div>'
        '<div class="sec-sub">Choose exactly three genres you enjoy.</div>',
        unsafe_allow_html=True
    )

    st.progress(
        len(selected_genres) / MAX_GENRES,
        text=f"{len(selected_genres)} of {MAX_GENRES} genres selected"
    )

    if selected_genres:
        pills = "".join(
            f'<span class="pill">{GENRE_STYLE[g]} {g}</span>'
            for g in selected_genres
        )
    else:
        pills = '<span class="pill-empty">No genres picked yet</span>'

    st.markdown(pills, unsafe_allow_html=True)
    st.write("")

    for start in range(0, len(MOVIE_GENRES), 4):

        row_genres = MOVIE_GENRES[start:start + 4]
        row_columns = st.columns(4)

        for column, genre in zip(row_columns, row_genres):

            with column:

                is_selected = genre in selected_genres

                disabled = (
                    len(selected_genres) >= MAX_GENRES
                    and not is_selected
                )

                st.markdown(
                    genre_card_html(genre, is_selected, disabled),
                    unsafe_allow_html=True
                )

                if st.button(
                    "✓ Selected" if is_selected else "Select",
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

    st.write("")

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

                        record_activity(
                            "movie",
                            {"genres": selected_genres}
                        )

                except Exception as error:
                    st.error(f"Movie recommendation error: {error}")

    if st.session_state.movie_result:
        show_movie_results(st.session_state.movie_result)


# ==================================================
# MUSIC PAGE
# ==================================================

elif selected_page == "Music":

    st.markdown(
        '<div class="sec-title">Find my music taste</div>'
        '<div class="sec-sub">Enter three songs or artists you enjoy.</div>',
        unsafe_allow_html=True
    )

    st.markdown(f"""
<div class="hero" style="padding: 22px 30px;
background-image: linear-gradient(90deg,
rgba(58,42,140,.85) 0%, rgba(58,42,140,.2) 70%),
url('{MUSIC_IMAGE}'), linear-gradient(135deg, #8a3fb0, #ff6b6b);">
<div class="hero-eyebrow">Sound check</div>
<div class="hero-h" style="font-size: 1.3rem;">
What are you listening to?
</div>
</div>
""", unsafe_allow_html=True)

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

                        record_activity(
                            "music",
                            {"songs": music_inputs}
                        )

                except Exception as error:
                    st.error(f"Music recommendation error: {error}")

    if st.session_state.music_result:
        show_music_results(st.session_state.music_result)


# ==================================================
# ADMIN ANALYTICS PAGE
# ==================================================

elif selected_page == "Analytics & Reports":

    if not admin_access:
        st.error("You do not have permission to view this page.")
        st.stop()

    st.title("📊 Analytics & Reports")

    st.caption(
        "Explore user activity and entertainment preferences."
    )

    activity_data = get_activity_data()
    summary = get_analytics_summary(activity_data)

    # USAGE OVERVIEW
    st.subheader("📈 Usage overview")

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric("Total requests", summary["total_requests"])
    metric2.metric("Movie requests", summary["movie_requests"])
    metric3.metric("Music requests", summary["music_requests"])
    metric4.metric("Unique users", summary["unique_users"])

    st.divider()

    # PREFERENCE ANALYSIS
    st.subheader("🎯 Entertainment Preference Analysis")

    movie_distribution = get_movie_genre_distribution(
        activity_data
    )

    music_distribution = get_music_preference_distribution(
        activity_data
    )

    movie_col, music_col = st.columns(2)

    # MOVIE GENRE DOUGHNUT
    with movie_col:

        st.markdown("### 🎬 Movie Genre Distribution")

        if movie_distribution.empty:
            st.info(
                "Movie genre preferences will appear here after "
                "users request movie recommendations."
            )

        else:
            movie_fig = px.pie(
                movie_distribution,
                names="Preference",
                values="Count",
                hole=0.55,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )

            movie_fig.update_traces(
                textposition="inside",
                textinfo="label+percent",
                hovertemplate=(
                    "%{label}<br>"
                    "Selections: %{value}<br>"
                    "Share: %{percent}<extra></extra>"
                )
            )

            movie_fig.update_layout(
                showlegend=True,
                legend_title_text="Genres",
                margin=dict(t=20, b=20, l=10, r=10),
                height=370
            )

            st.plotly_chart(
                movie_fig,
                use_container_width=True
            )

    # MUSIC PREFERENCE DOUGHNUT
    with music_col:

        st.markdown("### 🎵 Music Preference Distribution")

        if music_distribution.empty:
            st.info(
                "Music preferences will appear here after "
                "users request music recommendations."
            )

        else:
            music_fig = px.pie(
                music_distribution,
                names="Preference",
                values="Count",
                hole=0.55,
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            music_fig.update_traces(
                textposition="inside",
                textinfo="label+percent",
                hovertemplate=(
                    "%{label}<br>"
                    "Selections: %{value}<br>"
                    "Share: %{percent}<extra></extra>"
                )
            )

            music_fig.update_layout(
                showlegend=True,
                legend_title_text="Songs and artists",
                margin=dict(t=20, b=20, l=10, r=10),
                height=370
            )

            st.plotly_chart(
                music_fig,
                use_container_width=True
            )

    st.divider()

    # ACTIVITY RECORDS
    st.subheader("📋 Recommendation Activity")

    if activity_data.empty:

        st.info("No recommendation activity has been recorded yet.")

    else:

        display_data = activity_data.copy()

        if "created_at" in display_data.columns:
            display_data["created_at"] = pd.to_datetime(
                display_data["created_at"],
                errors="coerce"
            )

        preferred_columns = [
            column for column in [
                "created_at",
                "activity_type",
                "user_id",
                "preferences"
            ]
            if column in display_data.columns
        ]

        st.dataframe(
            display_data[preferred_columns],
            use_container_width=True,
            hide_index=True
        )

    # CSV DOWNLOAD - PRESERVED
    st.divider()

    st.subheader("📥 Download Reports")

    csv_data = export_activity_csv(activity_data)

    if csv_data:
        st.download_button(
            "⬇️ Download CSV Report",
            data=csv_data,
            file_name="tastematchai_activity_report.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.caption(
            "Your downloadable report will be available once "
            "activity is recorded."
        )


# ==================================================
# MY ACCOUNT PAGE
# ==================================================

elif selected_page == "My Account":

    st.title("👤 My Account")

    st.subheader("Account information")

    st.write("Email address")
    st.write(st.session_state.user_email)

    st.divider()

    st.caption(
        "Your account is used to access TasteMatchAI's "
        "movie and music recommendation features."
    )

    st.info(
        "To sign out, use the Log out option at the bottom "
        "of the sidebar."
    )


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