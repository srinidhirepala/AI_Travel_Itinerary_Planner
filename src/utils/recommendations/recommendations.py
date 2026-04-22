"""
Lightweight recommendation engine.
Scores destinations based on user profile: interests, travel style,
liked places (country/type weighting), and food preference.
No ML — pure heuristics, fast and explainable.
"""
from collections import Counter

# Destination catalogue: each entry has tags that match interest categories
DESTINATIONS = [
    {"name": "Jaipur",        "country": "India",   "tags": ["Culture", "Shopping", "Photography", "Food"],    "vibe": "Heritage"},
    {"name": "Goa",           "country": "India",   "tags": ["Adventure", "Food", "Photography", "Nature"],    "vibe": "Coastal"},
    {"name": "Varanasi",      "country": "India",   "tags": ["Culture", "Photography", "Food"],                "vibe": "Spiritual"},
    {"name": "Munnar",        "country": "India",   "tags": ["Nature", "Adventure", "Photography"],             "vibe": "Hills"},
    {"name": "Udaipur",       "country": "India",   "tags": ["Culture", "Photography", "Food", "Shopping"],    "vibe": "Romantic"},
    {"name": "Rishikesh",     "country": "India",   "tags": ["Adventure", "Nature", "Culture"],                "vibe": "Adventure"},
    {"name": "Hampi",         "country": "India",   "tags": ["Culture", "Photography", "Nature"],              "vibe": "Ruins"},
    {"name": "Manali",        "country": "India",   "tags": ["Adventure", "Nature", "Photography"],             "vibe": "Mountains"},
    {"name": "Bangkok",       "country": "Thailand","tags": ["Food", "Shopping", "Culture", "Adventure"],      "vibe": "Urban"},
    {"name": "Bali",          "country": "Indonesia","tags": ["Nature", "Culture", "Adventure", "Photography"],"vibe": "Tropical"},
    {"name": "Kyoto",         "country": "Japan",   "tags": ["Culture", "Food", "Photography", "Nature"],      "vibe": "Traditional"},
    {"name": "Paris",         "country": "France",  "tags": ["Culture", "Food", "Shopping", "Photography"],    "vibe": "Romantic"},
    {"name": "Istanbul",      "country": "Turkey",  "tags": ["Culture", "Food", "Shopping", "Photography"],    "vibe": "Historical"},
    {"name": "Kathmandu",     "country": "Nepal",   "tags": ["Adventure", "Culture", "Photography", "Nature"], "vibe": "Adventure"},
    {"name": "Colombo",       "country": "Sri Lanka","tags": ["Food", "Culture", "Nature", "Photography"],     "vibe": "Coastal"},
    {"name": "Chiang Mai",    "country": "Thailand","tags": ["Culture", "Nature", "Food", "Adventure"],        "vibe": "Temples"},
    {"name": "Dubai",         "country": "UAE",     "tags": ["Shopping", "Adventure", "Food"],                 "vibe": "Luxury"},
    {"name": "Singapore",     "country": "Singapore","tags": ["Food", "Shopping", "Culture"],                  "vibe": "Modern"},
    {"name": "Bhutan",        "country": "Bhutan",  "tags": ["Culture", "Nature", "Adventure", "Photography"], "vibe": "Peaceful"},
    {"name": "Coorg",         "country": "India",   "tags": ["Nature", "Adventure", "Photography"],             "vibe": "Hills"},
]

STYLE_BOOST = {
    "Explorer":    ["Adventure", "Nature", "Photography"],
    "Foodie":      ["Food", "Culture", "Shopping"],
    "Cultural":    ["Culture", "Photography", "Nature"],
    "Relaxer":     ["Nature", "Food"],
    "Adventurer":  ["Adventure", "Nature"],
    "Shopaholic":  ["Shopping", "Food", "Urban"],
}

MOOD_BOOST = {
    "Relax": ["Nature", "Food"],
    "Adventure": ["Adventure", "Nature"],
    "Devotional": ["Culture"],
    "Culture": ["Culture", "Photography"],
    "Food": ["Food", "Shopping"],
}


def get_recommendations(profile: dict, liked_places: list[dict], n: int = 6, context: dict | None = None, location_filter: str = "all") -> list[dict]:
    """
    Return top-n destination recommendations with a reason string.
    
    Args:
        profile: User profile dict
        liked_places: List of liked places
        n: Number of recommendations
        context: Additional context (mood, location, time)
        location_filter: "all", "india", or "international"
    
    Returns:
        List of recommended destinations
    """
    user_interests = set(profile.get("interests") or [])
    travel_style   = profile.get("travel_style", "Explorer")
    style_tags     = set(STYLE_BOOST.get(travel_style, []))
    context = context or {}
    mood = context.get("mood", "")
    mood_tags = set(MOOD_BOOST.get(mood, []))
    current_location = context.get("current_location", "")
    time_window_type = context.get("time_window_type", "Days")
    time_window_value = context.get("time_window_value", 0)

    # Build country affinity from liked places
    liked_countries = Counter(p["country"] for p in liked_places if p.get("country"))
    already_liked   = {p["place_name"].lower() for p in liked_places}

    scored = []
    for dest in DESTINATIONS:
        if dest["name"].lower() in already_liked:
            continue
        
        # Apply location filter
        if location_filter == "india" and dest["country"] != "India":
            continue
        elif location_filter == "international" and dest["country"] == "India":
            continue

        dest_tags = set(dest["tags"])
        interest_overlap = dest_tags & user_interests
        style_overlap    = dest_tags & style_tags
        mood_overlap     = dest_tags & mood_tags
        country_score    = liked_countries.get(dest["country"], 0) * 1.5

        score = len(interest_overlap) * 2 + len(style_overlap) + len(mood_overlap) + country_score

        # Prefer nearby domestic suggestions for short time windows
        if current_location and time_window_type == "Hours" and time_window_value and time_window_value <= 12:
            if dest.get("country") == "India":
                score += 1.5

        if score == 0:
            continue

        # Build a natural reason sentence
        if interest_overlap:
            reason_tags = list(interest_overlap)[:2]
            reason = f"Matches your interest in {' & '.join(reason_tags).lower()}"
        else:
            reason = f"Great for {travel_style.lower()} travellers"
        if liked_countries.get(dest["country"], 0) > 0:
            reason += f" · You've liked {dest['country']} before"

        if current_location:
            transport_hint = f"Best reached from {current_location} by flight/train based on budget and time"
        else:
            transport_hint = "Best reached by flight/train based on budget"

        if time_window_type == "Hours" and time_window_value:
            budget_level = "Quick escape"
        elif time_window_type == "Days" and time_window_value and time_window_value <= 3:
            budget_level = "Short trip"
        else:
            budget_level = "Flexible trip"

        scored.append({
            **dest,
            "score": score,
            "reason": reason,
            "budget_level": budget_level,
            "best_time": "Oct-Mar",
            "transport_hint": transport_hint,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:n]