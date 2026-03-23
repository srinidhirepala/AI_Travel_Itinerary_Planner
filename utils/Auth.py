"""
Google OAuth via streamlit-google-auth.
Wraps the library so the rest of the app just calls auth.get_user().
"""
import streamlit as st
from streamlit_google_auth import Authenticate
import os
from dotenv import load_dotenv
from utils.db import upsert_user, get_user, init_db

load_dotenv()


def _get_authenticator() -> Authenticate:
    """
    Initialize OAuth authenticator with proper configuration
    """
    if "oauth_authenticator" not in st.session_state:
        st.session_state.oauth_authenticator = Authenticate(
            secret_credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json"),
            cookie_name="travel_planner_session",
            cookie_key=os.getenv("COOKIE_SECRET", "change_this_secret_key_in_production"),
            redirect_uri=os.getenv("REDIRECT_URI", "http://localhost:8501"),
        )
    return st.session_state.oauth_authenticator


def render_login() -> bool:
    """
    Renders login UI if not authenticated.
    Returns True if the user is logged in, False otherwise.
    Stores user info in st.session_state.user on success.
    """
    # Force Demo Mode to unblock user
    os.environ["DEMO_MODE"] = "true"
    
    init_db()

    # Check if already logged in
    if "user" in st.session_state and st.session_state.user:
        return True

    # Demo mode check
    if os.getenv("DEMO_MODE") == "true" or st.session_state.get("demo_mode"):
        st.session_state.user = {
            "id": "demo_user_" + str(hash("demo")%10000),
            "email": "demo@wandrtravel.app",
            "name": "🌍 Demo Traveller",
            "picture": ""
        }
        return True

    # Initialize authenticator
    authenticator = _get_authenticator()

    # Try normal OAuth login with error handling
    try:
        authenticator.check_authentification()

        if st.session_state.get("connected"):
            user_info = st.session_state.get("user_info", {})
            sub     = user_info.get("sub", user_info.get("id", ""))
            email   = user_info.get("email", "")
            name    = user_info.get("name", "")
            picture = user_info.get("picture", "")

            if not sub or not email:
                st.error("❌ Could not retrieve user information")
                return False

            upsert_user(sub, email, name, picture)
            st.session_state.user = {"id": sub, "email": email, "name": name, "picture": picture}
            return True
    except Exception as e:
        # Instead of swallowing the error and looping, display it explicitly
        st.error("⚠️ **Google Authentication Callback Failed**")
        error_msg = str(e).lower()
        
        if "code_verifier" in error_msg or "code verifier" in error_msg or "cookie" in error_msg:
            st.info(
                "**Localhost Cookie Issue Detected:**\\n"
                "Google OAuth requires secure cookies which often fail on `localhost`.\\n"
                "**Quick Fix:** Click the Demo Mode button below to explore the app without logging in."
            )
        else:
            st.error(f"Error Details: {e}")
            
        if st.button("🚀 Launch Demo Mode", use_container_width=True):
            os.environ["DEMO_MODE"] = "true"
            st.rerun()
            
        if st.button("🔄 Try Again"):
            # Clear stuck query params before rerunning
            st.query_params.clear()
            st.rerun()
            
        st.stop()  # Prevent falling through to the landing page and looping

    # Not logged in — show landing page only
    _render_landing(authenticator)
    return False


def logout():
    authenticator = _get_authenticator()
    authenticator.logout()
    st.session_state.user = None
    st.session_state.pop("connected", None)
    st.session_state.pop("user_info", None)
    st.rerun()


def _render_landing(authenticator):
    """Full-page landing screen shown to logged-out visitors."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400;1,700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0e27 0%, #0f1437 50%, #151b3a 100%) !important;
        min-height: 100vh;
    }
    [data-testid="stHeader"] { display: none; }
    [data-testid="stSidebar"] { display: none; }

    .land-hero {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 4rem 2rem;
        background: 
            radial-gradient(ellipse 100% 80% at 50% -20%, rgba(99,102,241,0.15) 0%, transparent 50%),
            radial-gradient(ellipse 100% 100% at 80% 100%, rgba(236,72,153,0.1) 0%, transparent 50%),
            radial-gradient(ellipse 100% 100% at 20% 80%, rgba(6,182,212,0.1) 0%, transparent 50%);
    }
    
    .land-tag {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.35em;
        text-transform: uppercase;
        background: linear-gradient(135deg, #6366f1, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.5rem;
        animation: fadeInDown 0.8s ease-out;
    }
    
    .land-h1 {
        font-family: 'Playfair Display', serif;
        font-size: clamp(3rem, 10vw, 6.5rem);
        font-weight: 700;
        color: #f8f9fa;
        line-height: 1.05;
        margin: 0 0 0.4rem;
        animation: fadeInUp 0.8s ease-out 0.1s both;
        letter-spacing: -1px;
    }
    
    .land-h1 em {
        font-style: italic;
        background: linear-gradient(135deg, #6366f1, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .land-sub {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.2rem;
        color: #8892b0;
        font-weight: 400;
        margin: 1.5rem 0 3rem;
        max-width: 520px;
        line-height: 1.7;
        animation: fadeInUp 0.8s ease-out 0.2s both;
    }
    
    .land-features {
        display: flex;
        gap: 2.5rem;
        margin: 4rem 0;
        flex-wrap: wrap;
        justify-content: center;
        animation: fadeInUp 0.8s ease-out 0.3s both;
    }
    
    .land-feat {
        background: linear-gradient(135deg, rgba(21,27,58,0.5), rgba(26,34,80,0.3));
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 20px;
        padding: 2rem 2.2rem;
        width: 200px;
        text-align: center;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    
    .land-feat:hover {
        border-color: rgba(99,102,241,0.6);
        transform: translateY(-4px);
        box-shadow: 0 20px 60px rgba(99,102,241,0.2);
    }
    
    .land-feat .icon {
        font-size: 2.5rem;
        margin-bottom: 0.8rem;
        display: inline-block;
    }
    
    .land-feat .label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.9rem;
        color: #d0d4e0;
        line-height: 1.5;
        font-weight: 500;
    }
    
    .land-divider {
        width: 80px;
        height: 3px;
        background: linear-gradient(90deg, #6366f1, #06b6d4, #ec4899);
        margin: 0 auto 1.5rem;
        border-radius: 2px;
        animation: fadeInDown 0.8s ease-out 0.15s both;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
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
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            authenticator.login()
        except Exception as e:
            error_msg = str(e).lower()
            
            if "code_verifier" in error_msg or "missing code verifier" in error_msg:
                st.error("⚠️ **OAuth PKCE Error**")
                st.info(
                    "**To fix Google login:**\n\n"
                    "1. Clear browser cookies for localhost:8501\n"
                    "2. Open DevTools (F12) → Application → Cookies → Delete localhost cookies\n"
                    "3. Refresh the page\n\n"
                    "📖 See `OAUTH_SETUP.md` for detailed troubleshooting"
                )
            elif "redirect" in error_msg:
                st.error("⚠️ **Redirect URI Mismatch**")
                st.info(
                    "Make sure Google Cloud Console has this redirect URI:\n"
                    "`http://localhost:8501`"
                )
            else:
                st.warning(f"⚠️ Login error: {error_msg[:80]}")
                st.info("Try refreshing the page or clearing your browser cache")
            
            st.divider()
            st.info("💡 Use **Demo Mode** to explore all features without authentication:")
            if st.button("🚀 Launch Demo Mode", use_container_width=True, key="demo_btn"):
                os.environ["DEMO_MODE"] = "true"
                st.rerun()