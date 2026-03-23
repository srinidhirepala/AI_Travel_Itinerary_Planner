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


def get_recommendations(profile: dict, liked_places: list[dict], n: int = 6) -> list[dict]:
    """
    Return top-n destination recommendations with a reason string.
    """
    user_interests = set(profile.get("interests") or [])
    travel_style   = profile.get("travel_style", "Explorer")
    style_tags     = set(STYLE_BOOST.get(travel_style, []))

    # Build country affinity from liked places
    liked_countries = Counter(p["country"] for p in liked_places if p.get("country"))
    already_liked   = {p["place_name"].lower() for p in liked_places}

    scored = []
    for dest in DESTINATIONS:
        if dest["name"].lower() in already_liked:
            continue

        dest_tags = set(dest["tags"])
        interest_overlap = dest_tags & user_interests
        style_overlap    = dest_tags & style_tags
        country_score    = liked_countries.get(dest["country"], 0) * 1.5

        score = len(interest_overlap) * 2 + len(style_overlap) + country_score

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

        scored.append({**dest, "score": score, "reason": reason})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:n]