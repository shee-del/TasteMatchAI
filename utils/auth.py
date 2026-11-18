import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def get_supabase():
    """Create or retrieve the Supabase client for this user session."""

    if "_supabase_client" not in st.session_state:

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        # Also support Streamlit Cloud secrets
        if not url or not key:
            try:
                url = url or st.secrets["SUPABASE_URL"]
                key = key or st.secrets["SUPABASE_KEY"]
            except Exception:
                pass

        if not url or not key:
            raise ValueError(
                "Supabase URL or Publishable Key is missing."
            )

        st.session_state["_supabase_client"] = create_client(
            url,
            key
        )

    return st.session_state["_supabase_client"]


def sign_up(email, password):
    try:
        response = get_supabase().auth.sign_up({
            "email": email,
            "password": password
        })
        return response, None

    except Exception as error:
        return None, str(error)


def log_in(email, password):
    try:
        response = get_supabase().auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response, None

    except Exception as error:
        return None, str(error)


def log_out():
    try:
        get_supabase().auth.sign_out()
        return True, None

    except Exception as error:
        return False, str(error)


def reset_password(email):
    try:
        get_supabase().auth.reset_password_for_email(email)
        return True, None

    except Exception as error:
        return False, str(error)