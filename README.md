# Wandr - AI Travel Itinerary Planner

Personalized travel planning with Google login, saved itineraries, route intelligence, recommendations, and weekend getaway suggestions.

## Stack
- Streamlit
- Groq API
- Google OAuth via `streamlit-google-auth`
- SQLite

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create `.env`
Create a `.env` file in the project root with:

```env
GROQ_API_KEY=your_key_here
COOKIE_SECRET=your_secret_here
```

### 3. Add Google OAuth credentials
Download your OAuth client JSON from Google Cloud and place it at:

```text
google_credentials.json
```

You can also point to a different path with `GOOGLE_CREDENTIALS_PATH`.

### 4. Run the app
```bash
streamlit run app.py
```

## Features
- Trip planner with multi-stop routing
- Smart route optimizer with reorder / replace / trim suggestions
- Weekend getaways based on home city and interests
- Saved itineraries and liked places
- Profile-based recommendations

## Project Structure
```text
AI_Travel_Itinerary_Planner/
├── app.py
├── README.md
├── requirements.txt
├── data/
│   └── travel.db
├── logs/
├── utils/
│   ├── auth.py
│   ├── constants.py
│   ├── db.py
│   ├── error_handler.py
│   ├── llm_handler.py
│   ├── prompt_builder.py
│   ├── rate_limiter.py
│   ├── recommendations.py
│   ├── route_intelligence.py
│   ├── styles.py
│   ├── validation.py
│   └── weekend_getaways.py
└── .gitignore
```

## Notes
- `.env` and `google_credentials.json` are local-only and ignored by git.
- `data/*.db` and `logs/*.log` are runtime artifacts and ignored too.
- Older planning notes and archived chat references are kept locally under `unused/` and ignored by git.
