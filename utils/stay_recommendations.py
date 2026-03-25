"""
Budget-aware stay recommendations for itinerary destinations.
These are heuristic suggestions (not live hotel inventory).
"""

from typing import Dict, List

CITY_STAY_AREAS: Dict[str, List[str]] = {
    "delhi": ["Connaught Place", "Karol Bagh", "Aerocity"],
    "mumbai": ["Andheri East", "Bandra", "Colaba"],
    "bengaluru": ["Indiranagar", "MG Road", "Koramangala"],
    "hyderabad": ["Banjara Hills", "Hitech City", "Begumpet"],
    "chennai": ["T Nagar", "Mylapore", "OMR"],
    "jaipur": ["MI Road", "Bani Park", "Civil Lines"],
    "goa": ["Calangute", "Candolim", "Panjim"],
    "kochi": ["Fort Kochi", "Ernakulam", "Marine Drive"],
    "kolkata": ["Park Street", "Salt Lake", "New Town"],
    "pune": ["Koregaon Park", "Shivaji Nagar", "Hinjewadi"],
    "mysore": ["Gokulam", "Nazarbad", "Vijayanagar"],
    "udaipur": ["Lal Ghat", "Hiran Magri", "Fateh Sagar"],
    "varanasi": ["Assi Ghat", "Godowlia", "Cantonment"],
}

HOTEL_TEMPLATES = {
    "budget": [
        "Smart budget hotel",
        "Clean guesthouse",
        "Backpacker hostel",
    ],
    "mid": [
        "Comfort business hotel",
        "Boutique city stay",
        "Family-friendly hotel",
    ],
    "premium": [
        "Upscale boutique hotel",
        "Premium city hotel",
        "Luxury heritage stay",
    ],
}


def _destination_key(destination: str) -> str:
    return (destination or "").split(",")[0].strip().lower()


def _budget_segment(budget_per_day: int) -> str:
    if budget_per_day <= 2500:
        return "budget"
    if budget_per_day <= 7000:
        return "mid"
    return "premium"


def _nightly_range(budget_per_day: int, segment: str) -> tuple[int, int]:
    if segment == "budget":
        low = max(800, int(budget_per_day * 0.35))
        high = max(low + 500, int(budget_per_day * 0.65))
        return low, high
    if segment == "mid":
        low = max(2500, int(budget_per_day * 0.45))
        high = max(low + 1000, int(budget_per_day * 0.85))
        return low, high

    low = max(6000, int(budget_per_day * 0.55))
    high = max(low + 2500, int(budget_per_day * 1.2))
    return low, high


def get_stay_recommendations(destination: str, budget_per_day: int, limit: int = 3) -> List[dict]:
    city_key = _destination_key(destination)
    areas = CITY_STAY_AREAS.get(city_key, ["City Center", "Transit Hub", "Old Town"])

    segment = _budget_segment(budget_per_day)
    nightly_low, nightly_high = _nightly_range(budget_per_day, segment)
    templates = HOTEL_TEMPLATES[segment]

    suggestions = []
    for idx, area in enumerate(areas[:limit]):
        stay_type = templates[idx % len(templates)]
        price_low = nightly_low + (idx * 250)
        price_high = nightly_high + (idx * 400)
        suggestions.append(
            {
                "area": area,
                "stay_type": stay_type,
                "price_range_inr": [price_low, price_high],
                "why": "Good balance of commute convenience and local access.",
            }
        )

    return suggestions
