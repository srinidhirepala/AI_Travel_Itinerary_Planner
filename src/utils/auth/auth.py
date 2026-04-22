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
from pathlib import Path
from urllib.parse import urlencode
from dotenv import load_dotenv
from src.utils.database.db import upsert_user, init_db

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_CANDIDATES = [
    _PROJECT_ROOT / "config" / ".env",
    _PROJECT_ROOT / ".env",
]
for _env_path in _ENV_CANDIDATES:
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path, override=False)
        break

# ── Google OAuth endpoints ────────────────────────────────────────────────────
GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v3/userinfo"


def _load_credentials():
    configured_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    candidates = []
    if configured_path:
        candidates.append(Path(configured_path))
    candidates.extend([
        _PROJECT_ROOT / "config" / "google_credentials.json",
        _PROJECT_ROOT / "google_credentials.json",
    ])

    for path in candidates:
        try:
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    creds = json.load(f)
                web = creds.get("web", creds)
                return web["client_id"], web["client_secret"]
        except Exception as e:
            st.error(f"Could not load {path}: {e}")
            return None, None

    st.error(
        "Could not find Google credentials file. Checked: "
        + ", ".join(str(p) for p in candidates)
    )
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
    if "_db_initialized" not in st.session_state:
        init_db()
        st.session_state["_db_initialized"] = True

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
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Manrope:wght@400;500;600;700;800&display=swap');

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top left, rgba(244, 194, 96, 0.24), transparent 26%),
            radial-gradient(circle at top right, rgba(26, 123, 116, 0.16), transparent 32%),
            linear-gradient(180deg, #f8f1e8 0%, #f2e7da 100%) !important;
        min-height: 100vh;
    }
    [data-testid="stHeader"]  { display: none; }
    [data-testid="stSidebar"] { display: none; }

    .land-shell {
        position: relative;
        min-height: 78vh;
        padding: 3rem 1.2rem 1rem;
    }
    .land-hero {
        position: relative;
        overflow: hidden;
        max-width: 1180px;
        margin: 0 auto;
        text-align: center;
        padding: 3.5rem 2.2rem 2.6rem;
        border-radius: 36px;
        background:
            radial-gradient(circle at top right, rgba(244, 194, 96, 0.18), transparent 28%),
            radial-gradient(circle at left center, rgba(26, 123, 116, 0.12), transparent 32%),
            linear-gradient(135deg, rgba(255, 252, 247, 0.96), rgba(247, 236, 221, 0.92));
        border: 1px solid rgba(92, 72, 49, 0.1);
        box-shadow: 0 28px 60px rgba(87, 63, 38, 0.14);
    }
    .land-hero::before,
    .land-hero::after {
        content: "";
        position: absolute;
        border-radius: 999px;
        pointer-events: none;
    }
    .land-hero::before {
        width: 240px;
        height: 240px;
        right: -80px;
        top: -70px;
        background: radial-gradient(circle, rgba(218, 115, 71, 0.18), rgba(218, 115, 71, 0));
    }
    .land-hero::after {
        width: 220px;
        height: 220px;
        left: -60px;
        bottom: -110px;
        background: radial-gradient(circle, rgba(26, 123, 116, 0.18), rgba(26, 123, 116, 0));
    }
    .land-brand {
        display: inline-flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 1.25rem;
    }
    .land-brand-mark {
        width: 48px;
        height: 48px;
        display: grid;
        place-items: center;
        border-radius: 16px;
        background: linear-gradient(135deg, #da7347 0%, #ef9c53 50%, #f5c56f 100%);
        color: #fff9f2;
        font-family: 'Fraunces', serif;
        font-size: 1.35rem;
        font-weight: 700;
        box-shadow: 0 18px 32px rgba(218, 115, 71, 0.24);
    }
    .land-brand-copy {
        text-align: left;
    }
    .land-brand-name {
        font-family: 'Fraunces', serif;
        font-size: 1.35rem;
        font-weight: 700;
        color: #1f2933;
        line-height: 1;
    }
    .land-brand-tag {
        margin-top: 0.2rem;
        font-family: 'Manrope', sans-serif;
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b665f;
    }
    .land-tag {
        display: inline-flex;
        padding: 0.45rem 0.85rem;
        border-radius: 999px;
        border: 1px solid rgba(26, 123, 116, 0.16);
        background: rgba(26, 123, 116, 0.08);
        color: #1a7b74;
        font-family: 'Manrope', sans-serif;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    .land-h1 {
        margin: 1.15rem auto 0.65rem;
        max-width: 12ch;
        font-family: 'Fraunces', serif;
        font-size: clamp(2.45rem, 5.8vw, 4.8rem);
        font-weight: 700;
        color: #1f2933;
        line-height: 1.02;
        letter-spacing: -0.04em;
    }
    .land-h1 em {
        font-style: normal;
        color: #da7347;
    }
    .land-sub {
        margin: 0 auto 2.2rem;
        max-width: 680px;
        font-family: 'Manrope', sans-serif;
        font-size: 0.96rem;
        line-height: 1.68;
        color: #6b665f;
    }
    .land-features {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1rem;
        margin-top: 2.2rem;
    }
    .land-feat {
        text-align: left;
        padding: 1.25rem 1.2rem;
        border-radius: 24px;
        background: rgba(255, 251, 246, 0.82);
        border: 1px solid rgba(92, 72, 49, 0.08);
        box-shadow: 0 12px 28px rgba(104, 74, 44, 0.08);
    }
    .land-feat:nth-child(1) {
        background: linear-gradient(180deg, rgba(255, 243, 234, 0.94), rgba(255, 248, 241, 0.88));
    }
    .land-feat:nth-child(2) {
        background: linear-gradient(180deg, rgba(255, 247, 226, 0.94), rgba(255, 250, 241, 0.88));
    }
    .land-feat:nth-child(3) {
        background: linear-gradient(180deg, rgba(237, 248, 246, 0.94), rgba(248, 252, 251, 0.88));
    }
    .land-feat:nth-child(4) {
        background: linear-gradient(180deg, rgba(243, 240, 255, 0.94), rgba(252, 249, 255, 0.88));
    }
    .land-feat .icon  {
        width: 48px;
        height: 48px;
        display: grid;
        place-items: center;
        border-radius: 16px;
        background: rgba(218, 115, 71, 0.12);
        font-size: 1.45rem;
        margin-bottom: 0.9rem;
    }
    .land-feat:nth-child(1) .icon {
        background: rgba(227, 107, 70, 0.16);
    }
    .land-feat:nth-child(2) .icon {
        background: rgba(215, 160, 63, 0.16);
    }
    .land-feat:nth-child(3) .icon {
        background: rgba(15, 139, 128, 0.16);
    }
    .land-feat:nth-child(4) .icon {
        background: rgba(79, 115, 239, 0.14);
    }
    .land-feat .label {
        font-family: 'Manrope', sans-serif;
        font-size: 0.88rem;
        color: #3d4a53;
        line-height: 1.55;
        font-weight: 700;
    }
    .google-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        width: 100%;
        max-width: 360px;
        background: rgba(255, 252, 247, 0.96);
        color: #2f3b43;
        border: 1px solid rgba(92, 72, 49, 0.12);
        border-radius: 18px;
        padding: 0.9rem 1.25rem;
        font-family: 'Manrope', sans-serif;
        font-size: 1rem;
        font-weight: 800;
        text-decoration: none;
        box-shadow: 0 16px 30px rgba(87, 63, 38, 0.1);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    .google-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 20px 34px rgba(87, 63, 38, 0.14);
    }
    .land-or {
        text-align: center;
        color: #7a7269;
        margin: 0.6rem 0 0.9rem;
        font-family: 'Manrope', sans-serif;
        font-size: 0.9rem;
        font-weight: 700;
    }
    @media (max-width: 900px) {
        .land-hero {
            padding: 2.5rem 1.3rem 2rem;
            border-radius: 28px;
        }
        .land-features {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    @media (max-width: 640px) {
        .land-shell {
            padding-top: 1.6rem;
        }
        .land-features {
            grid-template-columns: 1fr;
        }
        .land-brand {
            flex-direction: column;
        }
        .land-brand-copy {
            text-align: center;
        }
    }
    </style>

    <div class="land-shell">
        <div class="land-hero">
            <div class="land-brand">
                <div class="land-brand-mark">W</div>
                <div class="land-brand-copy">
                    <div class="land-brand-name">Wandr</div>
                    <div class="land-brand-tag">AI Travel Design Studio</div>
                </div>
            </div>
            <div class="land-tag">Craft better journeys</div>
            <h1 class="land-h1">Plan trips that feel <em>crafted</em>, not generated.</h1>
            <p class="land-sub">Build day-by-day itineraries with route logic, food-aware suggestions, budget planning, saved histories, and recommendations tuned to your travel style.</p>
            <div class="land-features">
                <div class="land-feat"><div class="icon">🤖</div><div class="label">AI-curated travel itinerary planners for all places and moods</div></div>
                <div class="land-feat"><div class="icon">💰</div><div class="label">Budget-aware plans for quick breaks and long routes</div></div>
                <div class="land-feat"><div class="icon">🗺️</div><div class="label">Multi-stop trip logic with route guidance and nearby picks</div></div>
                <div class="land-feat"><div class="icon">✨</div><div class="label">Profiles, liked places, and personalized recommendations</div></div>
            </div>
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

