"""
Curated nearby weekend getaway suggestions.
The entered home city is treated as the origin, and getaways are ranked by
distance plus interest match. If a city does not have a hand-curated set yet,
the module falls back to a broader nearby-discovery catalog.
"""

from typing import Dict, List

from utils.route_intelligence import get_city_coords, haversine_distance


CITY_ALIASES = {
    "bangalore": "bengaluru",
    "bombay": "mumbai",
    "madras": "chennai",
    "delhi ncr": "delhi",
    "new delhi": "delhi",
    "panaji": "goa",
    "panjim": "goa",
    "north goa": "goa",
    "south goa": "goa",
    "cochin": "kochi",
    "trivandrum": "thiruvananthapuram",
    "pondy": "pondicherry",
}


WEEKEND_GETAWAYS: Dict[str, List[dict]] = {
    "hyderabad": [
        {"name": "Bhongir Fort", "distance_km": 50, "tags": ["Adventure", "Photography", "Culture"], "vibe": "Fort escape", "reason": "A quick climb, wide views, and a half-day heritage-adventure mix."},
        {"name": "Yadadri", "distance_km": 63, "tags": ["Culture", "Photography"], "vibe": "Temple trail", "reason": "Good for a calmer spiritual-cultural break with easy transit."},
        {"name": "Ananthagiri Hills", "distance_km": 70, "tags": ["Nature", "Adventure", "Photography"], "vibe": "Forest air", "reason": "Best for greenery, trails, and a quieter reset outside the city."},
    ],
    "bengaluru": [
        {"name": "Nandi Hills", "distance_km": 61, "tags": ["Nature", "Photography", "Adventure"], "vibe": "Sunrise hills", "reason": "Classic short escape for views, light hiking, and scenic mornings."},
        {"name": "Skandagiri", "distance_km": 62, "tags": ["Adventure", "Nature", "Photography"], "vibe": "Trek break", "reason": "Works well when you want a more active, outdoors-heavy getaway."},
        {"name": "Channapatna", "distance_km": 60, "tags": ["Shopping", "Culture", "Photography"], "vibe": "Craft town", "reason": "Great for handmade toy workshops, local culture, and colorful streets."},
        {"name": "Shivanasamudra", "distance_km": 86, "tags": ["Nature", "Photography", "Relax"], "vibe": "Waterfall reset", "reason": "A scenic escape for dramatic cascades and a slower, breezier day outdoors."},
    ],
    "chennai": [
        {"name": "Mahabalipuram", "distance_km": 58, "tags": ["Culture", "Photography", "Food"], "vibe": "Coastal heritage", "reason": "Stone temples, sea breeze, and an easy culture-focused day out."},
        {"name": "Pulicat", "distance_km": 56, "tags": ["Nature", "Photography", "Relax"], "vibe": "Lakeside calm", "reason": "Best for birding, open water views, and a slower-paced outing."},
        {"name": "Kanchipuram", "distance_km": 69, "tags": ["Culture", "Shopping", "Photography"], "vibe": "Temple & silk", "reason": "Strong pick for heritage lovers and local textile shopping."},
        {"name": "Pondicherry", "distance_km": 154, "tags": ["Food", "Relax", "Photography"], "vibe": "French quarter mood", "reason": "A slightly longer weekend run for cafes, seaside walks, and a softer pace."},
    ],
    "delhi": [
        {"name": "Neemrana", "distance_km": 67, "tags": ["Culture", "Photography", "Relax"], "vibe": "Fort stay", "reason": "A heritage-style short break that feels different without a long journey."},
        {"name": "Murthal", "distance_km": 52, "tags": ["Food", "Relax"], "vibe": "Food drive", "reason": "Simple, fun, and perfect if the weekend mood is mostly about food."},
        {"name": "Damdama Lake", "distance_km": 59, "tags": ["Adventure", "Nature", "Photography"], "vibe": "Lakeside outdoors", "reason": "A good close-range option for kayaking, open space, and short adventure."},
        {"name": "Sohna", "distance_km": 63, "tags": ["Relax", "Nature"], "vibe": "Hot-springs pause", "reason": "A calm short-haul break when the weekend should feel low-effort and restful."},
    ],
    "mumbai": [
        {"name": "Alibaug", "distance_km": 62, "tags": ["Nature", "Food", "Relax", "Photography"], "vibe": "Coastal unwind", "reason": "Strong all-rounder for beach mood, food stops, and easy weekend pacing."},
        {"name": "Karnala", "distance_km": 60, "tags": ["Nature", "Adventure", "Photography"], "vibe": "Green escape", "reason": "Best for trails, greenery, and a lighter outdoors-focused trip."},
        {"name": "Karjat", "distance_km": 68, "tags": ["Adventure", "Nature", "Relax"], "vibe": "Monsoon break", "reason": "Works well for villa stays, river views, and short adventure experiences."},
        {"name": "Matheran", "distance_km": 82, "tags": ["Nature", "Photography", "Relax"], "vibe": "Hill-station breath", "reason": "A softer, scenic retreat for viewpoints, toy-train charm, and easy wandering."},
    ],
    "pune": [
        {"name": "Lavasa", "distance_km": 57, "tags": ["Nature", "Photography", "Relax"], "vibe": "Lakeside town", "reason": "A simple scenic drive with a soft, laid-back weekend feel."},
        {"name": "Kolad", "distance_km": 70, "tags": ["Adventure", "Nature"], "vibe": "River rush", "reason": "Best if your weekend needs rafting, movement, and an outdoors-first mood."},
        {"name": "Mulshi", "distance_km": 52, "tags": ["Nature", "Relax", "Photography"], "vibe": "Monsoon calm", "reason": "A scenic, low-friction nature break that suits slower weekends."},
        {"name": "Lonavala", "distance_km": 67, "tags": ["Nature", "Food", "Relax"], "vibe": "Cloudy hills", "reason": "An easy crowd-pleaser for viewpoints, snacks, and comfortable short-distance travel."},
    ],
    "jaipur": [
        {"name": "Sambhar Lake", "distance_km": 64, "tags": ["Nature", "Photography"], "vibe": "Salt lake views", "reason": "A visual, quiet getaway for open landscapes and photography."},
        {"name": "Abhaneri", "distance_km": 67, "tags": ["Culture", "Photography"], "vibe": "Stepwell heritage", "reason": "Perfect for history, architecture, and photo-heavy day plans."},
        {"name": "Bhangarh", "distance_km": 69, "tags": ["Adventure", "Photography", "Culture"], "vibe": "Legend trail", "reason": "Adds a dramatic heritage-adventure twist to a short break."},
    ],
    "kochi": [
        {"name": "Cherai", "distance_km": 34, "tags": ["Relax", "Nature", "Food"], "vibe": "Beach pause", "reason": "A quick shore break for seafood, sunset, and a low-pressure weekend rhythm."},
        {"name": "Athirappilly", "distance_km": 66, "tags": ["Nature", "Photography", "Relax"], "vibe": "Waterfall day", "reason": "A beautiful short escape for misty views and a strong nature reset."},
        {"name": "Kumarakom", "distance_km": 56, "tags": ["Relax", "Nature", "Photography"], "vibe": "Backwater calm", "reason": "A slower, feel-good weekend pick with boats, birds, and quiet scenery."},
    ],
    "chandigarh": [
        {"name": "Morni Hills", "distance_km": 45, "tags": ["Nature", "Adventure", "Photography"], "vibe": "Hill drive", "reason": "One of the cleanest nearby nature escapes for a short, active weekend."},
        {"name": "Kasauli", "distance_km": 61, "tags": ["Relax", "Nature", "Photography"], "vibe": "Hill-station ease", "reason": "A cozy option for cafes, viewpoints, and a gentle mountain mood."},
        {"name": "Pinjore", "distance_km": 24, "tags": ["Culture", "Relax", "Photography"], "vibe": "Garden break", "reason": "A quick heritage-garden outing when you want a very easy half-day reset."},
    ],
    "mysore": [
        {"name": "Srirangapatna", "distance_km": 19, "tags": ["Culture", "Photography"], "vibe": "Heritage close-by", "reason": "A very easy short-hop for history, riverside views, and palace-era stories."},
        {"name": "BR Hills", "distance_km": 84, "tags": ["Nature", "Adventure", "Photography"], "vibe": "Forest weekend", "reason": "Best for wildlife, road-trip energy, and a more outdoorsy weekend reset."},
        {"name": "Shivanasamudra", "distance_km": 78, "tags": ["Nature", "Photography", "Relax"], "vibe": "Waterfall reset", "reason": "A scenic day for waterfalls, viewpoints, and lighter travel fatigue."},
    ],
}


DISCOVERY_GETAWAYS = [
    {"name": "Neemrana", "coordinates": (27.9896, 76.3852), "tags": ["Culture", "Photography", "Relax"], "vibe": "Fort stay", "reason": "A compact heritage break with fort views and slower pacing."},
    {"name": "Murthal", "coordinates": (29.0330, 77.0628), "tags": ["Food", "Relax"], "vibe": "Food drive", "reason": "Best when the whole weekend mood is about comfort food and easy driving."},
    {"name": "Damdama Lake", "coordinates": (28.3104, 77.1092), "tags": ["Nature", "Adventure", "Photography"], "vibe": "Lakeside outdoors", "reason": "A short nature-activity reset without needing a heavy travel day."},
    {"name": "Bhongir Fort", "coordinates": (17.5156, 78.8856), "tags": ["Adventure", "Photography", "Culture"], "vibe": "Fort escape", "reason": "A quick heritage-adventure outing with strong views and light travel."},
    {"name": "Yadadri", "coordinates": (17.5873, 78.9436), "tags": ["Culture", "Photography", "Relax"], "vibe": "Temple trail", "reason": "A calmer cultural reset when the weekend should stay simple and smooth."},
    {"name": "Ananthagiri Hills", "coordinates": (17.3214, 77.8654), "tags": ["Nature", "Adventure", "Photography"], "vibe": "Forest air", "reason": "Great for greenery, trails, and a fresher-feeling break."},
    {"name": "Nandi Hills", "coordinates": (13.3702, 77.6835), "tags": ["Nature", "Photography", "Adventure"], "vibe": "Sunrise hills", "reason": "A classic short escape for fresh air, viewpoints, and light movement."},
    {"name": "Skandagiri", "coordinates": (13.3847, 77.6947), "tags": ["Adventure", "Nature", "Photography"], "vibe": "Trek break", "reason": "A stronger fit for active weekends and early-morning energy."},
    {"name": "Channapatna", "coordinates": (12.6518, 77.2067), "tags": ["Shopping", "Culture", "Photography"], "vibe": "Craft town", "reason": "Adds color, local making, and a softer culture-shopping mix."},
    {"name": "Shivanasamudra", "coordinates": (12.3031, 77.1686), "tags": ["Nature", "Photography", "Relax"], "vibe": "Waterfall reset", "reason": "A good call when the weekend should feel scenic, photogenic, and easygoing."},
    {"name": "Mahabalipuram", "coordinates": (12.6208, 80.1931), "tags": ["Culture", "Photography", "Food"], "vibe": "Coastal heritage", "reason": "Sea breeze, stone temples, and a very dependable culture-food day out."},
    {"name": "Pulicat", "coordinates": (13.4230, 80.3203), "tags": ["Nature", "Photography", "Relax"], "vibe": "Lakeside calm", "reason": "A quiet open-water pick for birding and slower pacing."},
    {"name": "Kanchipuram", "coordinates": (12.8342, 79.7036), "tags": ["Culture", "Shopping", "Photography"], "vibe": "Temple & silk", "reason": "Ideal for heritage detail, textiles, and photo-rich local color."},
    {"name": "Alibaug", "coordinates": (18.6414, 72.8722), "tags": ["Nature", "Food", "Relax", "Photography"], "vibe": "Coastal unwind", "reason": "An easy beach-led weekend with food and lower travel burnout."},
    {"name": "Karnala", "coordinates": (18.8900, 73.1150), "tags": ["Nature", "Adventure", "Photography"], "vibe": "Green escape", "reason": "A light outdoors pick for trails, greenery, and birdlife."},
    {"name": "Karjat", "coordinates": (18.9100, 73.3230), "tags": ["Adventure", "Nature", "Relax"], "vibe": "Monsoon break", "reason": "Great for a villa stay or nature-heavy short break."},
    {"name": "Matheran", "coordinates": (18.9860, 73.2679), "tags": ["Nature", "Photography", "Relax"], "vibe": "Hill-station breath", "reason": "A scenic classic with viewpoints and lower-stress wandering."},
    {"name": "Lavasa", "coordinates": (18.4064, 73.5065), "tags": ["Nature", "Relax", "Photography"], "vibe": "Lakeside town", "reason": "A soft, low-effort drive for scenery and laid-back time outdoors."},
    {"name": "Kolad", "coordinates": (18.4320, 73.3200), "tags": ["Adventure", "Nature"], "vibe": "River rush", "reason": "A stronger adventure fit if the weekend needs more motion."},
    {"name": "Mulshi", "coordinates": (18.5314, 73.5146), "tags": ["Nature", "Relax", "Photography"], "vibe": "Monsoon calm", "reason": "A reliable scenic option when you want the weekend to feel unhurried."},
    {"name": "Lonavala", "coordinates": (18.7546, 73.4062), "tags": ["Nature", "Food", "Relax"], "vibe": "Cloudy hills", "reason": "One of the easiest crowd-pleasers for views, snacks, and short-distance ease."},
    {"name": "Sambhar Lake", "coordinates": (26.9124, 75.1970), "tags": ["Nature", "Photography"], "vibe": "Salt lake views", "reason": "A visually distinct quiet escape with open landscapes and photo appeal."},
    {"name": "Abhaneri", "coordinates": (27.0087, 76.6031), "tags": ["Culture", "Photography"], "vibe": "Stepwell heritage", "reason": "Perfect for architecture lovers and a focused heritage outing."},
    {"name": "Bhangarh", "coordinates": (27.0954, 76.2867), "tags": ["Adventure", "Photography", "Culture"], "vibe": "Legend trail", "reason": "A more dramatic, story-driven weekend option."},
    {"name": "Cherai", "coordinates": (10.1413, 76.1783), "tags": ["Relax", "Nature", "Food"], "vibe": "Beach pause", "reason": "A quick seaside reset with lighter logistics and easy food stops."},
    {"name": "Athirappilly", "coordinates": (10.2851, 76.5678), "tags": ["Nature", "Photography", "Relax"], "vibe": "Waterfall day", "reason": "Strong nature energy without demanding a long trip."},
    {"name": "Kumarakom", "coordinates": (9.6176, 76.4301), "tags": ["Relax", "Nature", "Photography"], "vibe": "Backwater calm", "reason": "Best for slower pacing, birds, boats, and low-burnout scenery."},
    {"name": "Morni Hills", "coordinates": (30.7619, 77.0735), "tags": ["Nature", "Adventure", "Photography"], "vibe": "Hill drive", "reason": "A close mountain mood with light adventure built in."},
    {"name": "Kasauli", "coordinates": (30.8983, 76.9648), "tags": ["Relax", "Nature", "Photography"], "vibe": "Hill-station ease", "reason": "A cozy weekend pick for viewpoints, cafes, and softer pacing."},
    {"name": "Pinjore", "coordinates": (30.7964, 76.9182), "tags": ["Culture", "Relax", "Photography"], "vibe": "Garden break", "reason": "A very easy short break when the weekend should stay gentle."},
    {"name": "Srirangapatna", "coordinates": (12.4226, 76.6932), "tags": ["Culture", "Photography"], "vibe": "Heritage close-by", "reason": "A short-hop history day with strong cultural texture."},
    {"name": "BR Hills", "coordinates": (11.9974, 77.1460), "tags": ["Nature", "Adventure", "Photography"], "vibe": "Forest weekend", "reason": "A better fit when wildlife and greenery matter more than city comforts."},
    {"name": "Dudhsagar", "coordinates": (15.3144, 74.3142), "tags": ["Nature", "Adventure", "Photography"], "vibe": "Waterfall rush", "reason": "A dramatic nature pick with a stronger adventure feel."},
    {"name": "Divar Island", "coordinates": (15.5300, 73.8730), "tags": ["Relax", "Culture", "Photography"], "vibe": "Island calm", "reason": "A softer river-island day for villages, ferries, and slower wandering."},
]


def _normalize_city(city: str) -> str:
    cleaned = city.strip().lower()
    return CITY_ALIASES.get(cleaned, cleaned)


def _score_option(option: dict, interests: list[str] | None = None, distance_km: int | None = None) -> dict:
    selected_interests = set(interests or [])
    tags = set(option.get("tags", []))
    overlap = tags & selected_interests
    trip_distance = distance_km if distance_km is not None else int(option.get("distance_km", 80))

    sweet_spot_bonus = max(0, 24 - abs(trip_distance - 65)) * 0.08
    score = len(overlap) * 3 + sweet_spot_bonus
    if 45 <= trip_distance <= 90:
        score += 1.8
    elif 30 <= trip_distance <= 130:
        score += 0.8
    else:
        score -= 1.0

    return {
        **option,
        "distance_km": trip_distance,
        "interest_overlap": sorted(overlap),
        "score": round(score, 2),
    }


def _discover_nearby_getaways(home_city: str, interests: list[str] | None = None, limit: int = 4) -> list[dict]:
    home_coords = get_city_coords(home_city)
    if not home_coords:
        return []

    ranked = []
    for option in DISCOVERY_GETAWAYS:
        distance_km = int(round(haversine_distance(home_coords, option["coordinates"])))
        if distance_km < 25 or distance_km > 220:
            continue

        ranked.append(_score_option(option, interests, distance_km=distance_km))

    ranked.sort(
        key=lambda item: (
            item["score"],
            -abs(item["distance_km"] - 65),
            -item["distance_km"],
        ),
        reverse=True,
    )

    unique = []
    seen = set()
    for option in ranked:
        key = option["name"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(option)
        if len(unique) == limit:
            break
    return unique


def get_weekend_getaways(home_city: str, interests: list[str] | None = None, limit: int = 4) -> list[dict]:
    city_key = _normalize_city(home_city)
    options = WEEKEND_GETAWAYS.get(city_key, [])

    if options:
        ranked = [_score_option(option, interests) for option in options]
        ranked.sort(
            key=lambda item: (item["score"], -abs(item["distance_km"] - 65), -item["distance_km"]),
            reverse=True,
        )
        return ranked[:limit]

    return _discover_nearby_getaways(city_key, interests, limit=limit)
