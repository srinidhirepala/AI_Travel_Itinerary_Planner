# Wandr

Wandr is an AI travel itinerary planner built with Streamlit. It combines itinerary generation, route intelligence, budget feasibility checks, personalized recommendations, weekend getaway discovery, and trip exports in one showcase-friendly application.

## What The App Does

- Build day-by-day itineraries for multi-city trips and short weekend breaks.
- Analyze route quality with distance, travel-time, fatigue, and route alternatives.
- Estimate whether the selected budget is realistic before the itinerary is generated.
- Recommend destinations based on profile, liked places, mood, time window, and scope.
- Save itineraries to history and export them as text, JSON, or PDF.

## Showcase Highlights

- Demo starters are built into the planner so evaluators can load polished sample trips in one click.
- Route intelligence compares the current route with reordered, swapped, or trimmed alternatives.
- Budget checks run before generation so the app feels practical, not just generative.
- Transport suggestions are shown per route leg for a more complete trip-planning story.
- Weekend getaway mode gives fast nearby options from a selected home city.

## Quick Demo Flow

1. Start the app and sign in with Google, or enable demo mode.
2. Load one of the built-in demo starters from the landing page, planner, or weekend page.
3. Generate the itinerary and walk through the budget card, route map, optimizer alternatives, and transport suggestions.
4. Open the saved itinerary in history and show the export options.

## Tech Stack

- Frontend and app shell: Streamlit
- LLM generation: Groq
- Persistence: SQLite
- Mapping: PyDeck
- Auth: Google OAuth
- PDFs: ReportLab

## Project Structure

```text
AI_Travel_Itinerary_Planner/
|-- app.py
|-- README.md
|-- requirements.txt
|-- config/
|-- data/
|-- docs/
|-- src/
|   |-- pages/
|   |-- utils/
|   |   |-- auth/
|   |   |-- common/
|   |   |-- database/
|   |   |-- llm/
|   |   |-- recommendations/
|   |   `-- route/
`-- tests/
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add environment values in `config/.env` or `.env`:

```env
GROQ_API_KEY=your_groq_api_key
COOKIE_SECRET=your_cookie_secret
REDIRECT_URI=http://localhost:8501
GEOAPIFY_API_KEY=optional_for_dynamic_geocoding
DEMO_MODE=false
GOOGLE_CREDENTIALS_PATH=config/google_credentials.json
```

4. Add Google OAuth credentials:

- Either place `google_credentials.json` in `config/`
- Or set `GOOGLE_CREDENTIALS_PATH` to the file location

5. Run the app:

```bash
streamlit run app.py
```

## Authentication Notes

- Standard mode uses Google OAuth.
- Demo mode skips Google login and logs in as a local demo traveller.
- The app expects a redirect URI that matches your Google OAuth configuration.

## Recommended Env Options

- `GROQ_API_KEY`: required for itinerary and AI recommendation generation
- `COOKIE_SECRET`: required for secure app session handling
- `REDIRECT_URI`: optional override for local or deployed auth callback
- `GEOAPIFY_API_KEY`: optional, improves dynamic geocoding and weekend discovery
- `DEMO_MODE=true`: useful for presentations and quick local testing

## Tests

Run the tests with:

```bash
pytest -q
```

There are route intelligence tests plus lightweight sanity tests in `tests/`.

## Best Pages To Showcase

- `Plan a Trip`: best for route optimization, budget validation, and exports
- `Weekend Getaway`: best for quick travel discovery and low-friction demos
- `Recommendations`: best for profile-aware personalization
- `History`: best for showing persistence and saved outputs

## Current Strengths

- Strong demo usability through built-in sample trips
- Budget-aware and route-aware generation flow
- Modularized `src/` utilities for auth, routing, data, and recommendations
- Export-ready output formats for evaluation and presentation

## Next Nice Additions

- Screenshot section or short demo GIF in the README
- More automated tests for budget and recommendation edge cases
- More refined share and export views for presentations
