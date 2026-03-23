"""
Google OAuth — no third-party auth library.
Uses plain requests + Google's OAuth2 endpoints directly.

Flow:
  1. User clicks "Sign in with Google"
  2. We redirect to Google's auth URL
  3. Google redirects back to localhost:8501?code=XXX&state=YYY
  4. We exchange the code for tokens, fetch user info, done.
"""

import os
import json
import secrets
import requests
import streamlit as st
from urllib.parse import urlencode
from dotenv import load_dotenv
from utils.db import upsert_user, init_db

load_dotenv()

# ── Google OAuth endpoints ────────────────────────────────────────────────────
GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v3/userinfo"


def _load_credentials():
    path = os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json")
    try:
        with open(path) as f:
            creds = json.load(f)
        web = creds.get("web", creds)
        return web["client_id"], web["client_secret"]
    except Exception as e:
        st.error(f"Could not load {path}: {e}")
        return None, None


def _redirect_uri():
    return os.getenv("REDIRECT_URI", "http://localhost:8501")


def _build_auth_url(state: str) -> str:
    client_id, _ = _load_credentials()
    params = {
        "client_id":     client_id,
        "redirect_uri":  _redirect_uri(),
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         state,
        "access_type":   "online",
        "prompt":        "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _exchange_code(code: str) -> dict | None:
    client_id, client_secret = _load_credentials()
    try:
        resp = requests.post(GOOGLE_TOKEN_URL, data={
            "code":          code,
            "client_id":     client_id,
            "client_secret": client_secret,
            "redirect_uri":  _redirect_uri(),
            "grant_type":    "authorization_code",
        }, timeout=10)
        resp.raise_for_status()
        access_token = resp.json().get("access_token")

        uinfo = requests.get(
            GOOGLE_USERINFO,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        uinfo.raise_for_status()
        return uinfo.json()
    except requests.RequestException as e:
        st.error(f"OAuth token exchange failed: {e}")
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def render_login() -> bool:
    """
    Call at the top of every page.
    Returns True if authenticated, False otherwise.
    """
    init_db()

    # 1. Already logged in
    if st.session_state.get("user"):
        return True

    # 2. Demo mode
    if os.getenv("DEMO_MODE") == "true" or st.session_state.get("demo_mode"):
        st.session_state.user = {
            "id":      "demo_user_" + str(hash("demo") % 10000),
            "email":   "demo@wandrtravel.app",
            "name":    "🌍 Demo Traveller",
            "picture": "",
        }
        return True

    params = st.query_params.to_dict()

    # 3. Google redirected back with ?code=...
    if "code" in params:
        code  = params["code"]
        state = params.get("state", "")

        # Validate state (CSRF protection)
        expected = st.session_state.get("oauth_state")
        if expected and state != expected:
            st.error("Security check failed. Please try signing in again.")
            st.query_params.clear()
            st.session_state.pop("oauth_state", None)
            st.rerun()

        with st.spinner("Signing you in..."):
            user_info = _exchange_code(code)

        st.query_params.clear()
        st.session_state.pop("oauth_state", None)

        if user_info:
            sub     = user_info.get("sub", "")
            email   = user_info.get("email", "")
            name    = user_info.get("name", "")
            picture = user_info.get("picture", "")

            upsert_user(sub, email, name, picture)
            st.session_state.user = {
                "id":      sub,
                "email":   email,
                "name":    name,
                "picture": picture,
            }
            st.rerun()
        else:
            st.error("Could not retrieve your Google account info. Please try again.")

        return False

    # 4. Google returned an error (e.g. user cancelled)
    if "error" in params:
        st.warning(f"Google login was cancelled or failed: {params['error']}")
        st.query_params.clear()

    # 5. Not logged in — show landing page
    _render_landing()
    return False


def logout():
    st.session_state.pop("user", None)
    st.session_state.pop("oauth_state", None)
    st.session_state.pop("demo_mode", None)
    st.query_params.clear()
    st.rerun()


# ── Landing page ──────────────────────────────────────────────────────────────

def _render_landing():
    if "oauth_state" not in st.session_state:
        st.session_state.oauth_state = secrets.token_urlsafe(16)

    auth_url = _build_auth_url(st.session_state.oauth_state)

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400;1,700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0e27 0%, #0f1437 50%, #151b3a 100%) !important;
        min-height: 100vh;
    }
    [data-testid="stHeader"]  { display: none; }
    [data-testid="stSidebar"] { display: none; }

    .land-hero {
        min-height: 80vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 4rem 2rem 2rem;
    }
    .land-tag {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.8rem; font-weight: 700;
        letter-spacing: 0.35em; text-transform: uppercase;
        background: linear-gradient(135deg, #6366f1, #06b6d4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; margin-bottom: 1.5rem;
    }
    .land-h1 {
        font-family: 'Playfair Display', serif;
        font-size: clamp(3rem, 10vw, 6.5rem);
        font-weight: 700; color: #f8f9fa;
        line-height: 1.05; margin: 0 0 0.4rem; letter-spacing: -1px;
    }
    .land-h1 em {
        font-style: italic;
        background: linear-gradient(135deg, #6366f1, #ec4899);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .land-sub {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.2rem; color: #8892b0;
        margin: 1.5rem 0 2rem; max-width: 520px; line-height: 1.7;
    }
    .land-divider {
        width: 80px; height: 3px;
        background: linear-gradient(90deg, #6366f1, #06b6d4, #ec4899);
        margin: 0 auto 1.5rem; border-radius: 2px;
    }
    .land-features {
        display: flex; gap: 2.5rem; margin: 2rem 0;
        flex-wrap: wrap; justify-content: center;
    }
    .land-feat {
        background: linear-gradient(135deg, rgba(21,27,58,0.5), rgba(26,34,80,0.3));
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 20px; padding: 2rem 2.2rem; width: 200px; text-align: center;
    }
    .land-feat .icon  { font-size: 2.5rem; margin-bottom: 0.8rem; display: inline-block; }
    .land-feat .label { font-family: 'DM Sans', sans-serif; font-size: 0.9rem; color: #d0d4e0; line-height: 1.5; font-weight: 500; }
    .google-btn {
        display: inline-flex; align-items: center; gap: 12px;
        background: #fff; color: #3c4043;
        border: 1px solid #dadce0; border-radius: 4px;
        padding: 10px 24px; font-family: 'DM Sans', sans-serif;
        font-size: 1rem; font-weight: 500;
        text-decoration: none; cursor: pointer;
        transition: box-shadow 0.2s; margin-bottom: 12px;
    }
    .google-btn:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
    </style>

    <div class="land-hero">
        <div class="land-tag">✦ AI Travel Planner</div>
        <h1 class="land-h1">Your Journey,<br>Personalized with <em>AI</em></h1>
        <div class="land-divider"></div>
        <p class="land-sub">Get intelligent day-by-day itineraries powered by Groq LLaMA AI. Tailored to your budget, interests, and travel style.</p>
        <div class="land-features">
            <div class="land-feat"><div class="icon">🤖</div><div class="label">AI-Generated Itineraries</div></div>
            <div class="land-feat"><div class="icon">💰</div><div class="label">Smart Budget Planning</div></div>
            <div class="land-feat"><div class="icon">❤️</div><div class="label">Save Your Favorites</div></div>
            <div class="land-feat"><div class="icon">✨</div><div class="label">Personalized Recommendations</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align:center; margin-bottom: 16px;">
            <a href="{auth_url}" class="google-btn" target="_self">
                <svg width="20" height="20" viewBox="0 0 48 48">
                    <path fill="#EA4335" d="M24 9.5c3.1 0 5.8 1.1 8 2.9l6-6C34.4 3 29.5 1 24 1 14.7 1 6.8 6.7 3.4 14.9l7 5.4C12.1 13.6 17.6 9.5 24 9.5z"/>
                    <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h12.7c-.6 3-2.3 5.5-4.8 7.2l7.4 5.7c4.3-4 6.8-9.9 7.2-16.9z"/>
                    <path fill="#FBBC05" d="M10.4 28.6A14.9 14.9 0 0 1 9.5 24c0-1.6.3-3.1.8-4.6l-7-5.4A23.9 23.9 0 0 0 .5 24c0 3.9.9 7.5 2.8 10.7l7.1-6.1z"/>
                    <path fill="#34A853" d="M24 47c5.4 0 9.9-1.8 13.2-4.8l-7.4-5.7c-1.8 1.2-4.1 1.9-5.8 1.9-6.4 0-11.8-4.3-13.6-10.1l-7.1 6.1C6.8 41.3 14.7 47 24 47z"/>
                </svg>
                Sign in with Google
            </a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='text-align:center; color:#666; margin: 8px 0;'>or</div>",
                    unsafe_allow_html=True)

        if st.button("🚀 Continue with Demo Mode", use_container_width=True):
            st.session_state.demo_mode = True
            st.rerun()