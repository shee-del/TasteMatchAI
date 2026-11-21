from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from utils.auth import get_supabase


def get_current_user_id():
    """Get the ID of the currently authenticated user."""
    try:
        response = get_supabase().auth.get_user()
        user = response.user

        if user:
            return user.id

        return None

    except Exception:
        return None


def is_admin():
    """Check administrator access securely through Supabase."""
    try:
        response = get_supabase().rpc(
            "is_admin", {}
        ).execute()

        return response.data is True

    except Exception as error:
        print(f"Admin verification error: {error}")
        return False


def record_activity(activity_type, preferences=None):
    """Record a successful movie or music recommendation request."""
    if activity_type not in ("movie", "music"):
        return False

    user_id = get_current_user_id()

    if not user_id:
        return False

    try:
        get_supabase().table("user_activity").insert({
            "user_id": user_id,
            "activity_type": activity_type,
            "preferences": preferences or {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()

        return True

    except Exception as error:
        print(f"Analytics recording error: {error}")
        return False


def get_activity_data():
    """Retrieve activity records accessible to the administrator."""
    if not is_admin():
        return pd.DataFrame()

    try:
        response = (
            get_supabase()
            .table("user_activity")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return pd.DataFrame(response.data or [])

    except Exception as error:
        st.error(f"Could not load analytics: {error}")
        return pd.DataFrame()


def get_analytics_summary(data):
    """Calculate basic usage statistics."""
    if data.empty:
        return {
            "total_requests": 0,
            "movie_requests": 0,
            "music_requests": 0,
            "unique_users": 0
        }

    return {
        "total_requests": len(data),
        "movie_requests": int(
            (data["activity_type"] == "movie").sum()
        ),
        "music_requests": int(
            (data["activity_type"] == "music").sum()
        ),
        "unique_users": int(data["user_id"].nunique())
    }


def get_preference_distribution(data, activity_type, preference_key):
    """
    Calculate preference counts and percentages
    for movie genres or music preferences.
    """
    if data.empty or "preferences" not in data.columns:
        return pd.DataFrame(
            columns=["Preference", "Count", "Percentage"]
        )

    selected_data = data[
        data["activity_type"] == activity_type
    ]

    preference_counts = {}

    for preferences in selected_data["preferences"]:
        if not isinstance(preferences, dict):
            continue

        values = preferences.get(preference_key, [])

        if isinstance(values, str):
            values = [values]

        if not isinstance(values, (list, tuple)):
            continue

        for value in values:
            if value and str(value).strip():
                name = str(value).strip().title()
                preference_counts[name] = (
                    preference_counts.get(name, 0) + 1
                )

    if not preference_counts:
        return pd.DataFrame(
            columns=["Preference", "Count", "Percentage"]
        )

    result = pd.DataFrame([
        {
            "Preference": name,
            "Count": count
        }
        for name, count in preference_counts.items()
    ])

    total = result["Count"].sum()

    result["Percentage"] = (
        result["Count"] / total * 100
    ).round(1)

    return result.sort_values(
        "Count", ascending=False
    ).reset_index(drop=True)


def get_movie_genre_distribution(data):
    """Get movie genre distribution for the doughnut chart."""
    return get_preference_distribution(
        data, "movie", "genres"
    )


def get_music_preference_distribution(data):
    """Get music preference distribution for the doughnut chart."""
    return get_preference_distribution(
        data, "music", "songs"
    )


def export_activity_csv(data):
    """Convert activity records into a downloadable CSV."""
    if data.empty:
        return None

    return data.to_csv(index=False).encode("utf-8")