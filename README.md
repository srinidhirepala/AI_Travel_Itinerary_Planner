# 🌍 Wandr — AI Travel Itinerary Planner

Personalised travel planning with Google login, profile, saved itineraries, and a recommendation engine.

## Stack
- **Frontend/App**: Streamlit
- **AI**: Groq API + LLaMA 3.3-70B
- **Auth**: Google OAuth via `streamlit-google-auth`
- **Database**: SQLite (local, zero config)

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Groq API key
Get a free key at https://console.groq.com

### 3. Set up Google OAuth
1. Go to https://console.cloud.google.com
2. Create a project → **APIs & Services → Credentials → Create OAuth 2.0 Client ID**
3. Application type: **Web Application**
4. Add Authorised Redirect URI: `http://localhost:8501`
5. Download the JSON — save it as `google_credentials.json` in the project root

### 4. Create your `.env` file
```bash
cp .env.example .env
# Fill in GROQ_API_KEY and COOKIE_SECRET
```

### 5. Run the App

#### Option A: With Google Login (Recommended for Production)
```bash
streamlit run app.py
```
This requires Google OAuth configuration. See `OAUTH_SETUP.md` if you encounter login issues.

#### Option B: Demo Mode (Testing Without Authentication)
```bash
set DEMO_MODE=true
streamlit run app.py
```
Opens at http://localhost:8501 with automatic login as demo user.

---

## 🔄 Authenticated vs Demo Mode

| Feature | Authenticated Login | Demo Mode |
|---------|-------------------|-----------|
| **Setup** | Requires Google OAuth config | No setup needed |
| **User Profile** | Persistent across sessions | Temporary per session |
| **Saved Itineraries** | Saved to database | Lost after refresh |
| **Favorites** | Permanently saved | Session only |
| **Recommendations** | Personalized per user | Generic |
| **Use Case** | Production/Real usage | Testing/Exploration |

---

## Features

| Feature | Description |
|---|---|
| 🔐 Google Login | OAuth 2.0 — no passwords, secure sessions |
| 🗺️ Trip Planner | Destination + days + budget + food + interests → full itinerary |
| 👤 Profile | Save food preference, interests, travel style, home city |
| ❤️ Liked Places | Save cities/attractions/restaurants you love |
| 📚 My Itineraries | Every generated plan auto-saved, browse and re-read anytime |
| ✨ Recommendations | Scored by your interests, style, and liked-place history |

## Project Structure

```
IOMP/
├── app.py                      # Main app — all 4 pages
├── requirements.txt
├── .env                       
├── google_credentials.json     
│
├── utils/
│   ├── auth.py                 # Google OAuth + landing page
│   ├── db.py                   # SQLite — users, profiles, liked places, itineraries
│   ├── llm_handler.py          # API calls, structured JSON output
│   ├── prompt_builder.py       # Prompt + schema construction
│   ├── recommendations.py      # Scoring engine
│   └── styles.py               
│
└── data/
    └── travel.db               # Auto-created on first run
```

## Security Notes
- `.env` and `google_credentials.json` are in `.gitignore` — never commit them
- Change `COOKIE_SECRET` to a random string before deploying
- For production deploy, update `REDIRECT_URI` to your public domain
