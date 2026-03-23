"""
Prompt Builder - Constructs prompts for LLM itinerary generation
"""
import json


def build_itinerary_prompt(
    destination: str,
    days: int,
    budget: int,
    food_pref: str,
    interests: list,
    travel_style: str = "Explorer",
    route_analysis: dict = None,
    hometown: str = "",
    is_weekend_getaway: bool = False,
) -> str:
    interests_str = ", ".join(interests) if interests else "General sightseeing"

    schema = {
        "destination": "string",
        "days": [
            {
                "day_number": "integer",
                "title": "string (e.g. 'Old City & Street Food Trail')",
                "theme": "string (e.g. 'Heritage & Cuisine')",
                "schedule": [
                    {
                        "time": "string (e.g. '8:00 AM')",
                        "activity": "string",
                        "location": "string",
                        "duration_minutes": "integer",
                        "cost_inr": "integer (0 if free)",
                        "notes": "string (tip, transport, or food note)",
                        "food_item": "string (if this activity involves eating, name the specific dish)"
                    }
                ],
                "meals": {
                    "breakfast": {
                        "place": "string",
                        "dish": "string (specific dish matching food preference)",
                        "cuisine": "string",
                        "cost_inr": "integer",
                        "why": "string (one-line reason this fits the traveler)"
                    },
                    "lunch": {
                        "place": "string",
                        "dish": "string",
                        "cuisine": "string",
                        "cost_inr": "integer",
                        "why": "string"
                    },
                    "dinner": {
                        "place": "string",
                        "dish": "string",
                        "cuisine": "string",
                        "cost_inr": "integer",
                        "why": "string"
                    }
                },
                "food_highlights": ["string (notable dish or food experience of the day)"],
                "nearby_alternatives": [
                    {
                        "name": "string (nearby place as alternative to main plan)",
                        "why": "string (why it saves time or complements the day)",
                        "distance_km": "number"
                    }
                ],
                "day_total_inr": "integer"
            }
        ],
        "budget_breakdown": {
            "accommodation_per_night": "integer",
            "food_per_day": "integer",
            "transport_per_day": "integer",
            "activities_total": "integer",
            "miscellaneous": "integer",
            "grand_total": "integer"
        },
        "practical_tips": ["string"],
        "best_areas_to_stay": ["string"],
        "local_transport": ["string"],
        "nearby_destinations": [
            {
                "name": "string",
                "distance_km": "number",
                "why_visit": "string",
                "best_for": "string"
            }
        ]
    }

    route_guidance = ""
    if route_analysis and route_analysis.get("burnout_risk") in ["HIGH", "MEDIUM"]:
        route_guidance = (
            f"\nCRITICAL ROUTE INTELLIGENCE:\n"
            f"- Total distance: {route_analysis.get('total_distance_km')} km, "
            f"~{route_analysis.get('total_travel_time_hrs')} hrs in transit.\n"
            f"- Burnout Risk: {route_analysis.get('burnout_risk')}.\n"
            f"-> Insert 'Travel / Recovery' blocks. Start mornings late on heavy travel days.\n"
            f"-> Suggest nearby_alternatives that cluster stops to reduce transit."
        )

    weekend_note = ""
    if is_weekend_getaway:
        weekend_note = (
            f"\nWEEKEND GETAWAY MODE: This is a short 1-2 day trip from {hometown or 'the traveler hometown'}. "
            f"Focus on nearby destinations reachable within 3-4 hours. Keep it relaxed and refreshing.\n"
        )

    food_instruction = {
        "Vegetarian":     "ALL meals and food items must be strictly vegetarian (no meat, no fish, no eggs).",
        "Non-Vegetarian": "Meals may include meat, fish, and eggs. Suggest local non-veg specialties.",
        "Vegan":          "ALL meals must be strictly vegan (no meat, fish, eggs, dairy, or honey).",
        "Jain":           "ALL meals must be Jain-friendly (no meat, no root vegetables like onion/garlic/potato).",
        "Halal":          "ALL meals must be Halal. No pork or alcohol.",
        "Both":           "Mix vegetarian and non-vegetarian options. Label each dish clearly.",
    }.get(food_pref, f"Respect food preference: {food_pref}")

    prompt = f"""Create a detailed {days}-day travel itinerary for {destination}.

TRAVELER PROFILE:
- Duration: {days} days
- Daily Budget: ₹{budget} (Indian Rupees)
- Food Preference: {food_pref} — {food_instruction}
- Interests: {interests_str}
- Travel Style / Pace: {travel_style}
{weekend_note}{route_guidance}

REQUIREMENTS:
1. FOOD: Every meal must respect the {food_pref} preference. Name the actual dish, not just cuisine type.
   Include food_highlights per day — the must-try food experience.
2. SCHEDULE: Hour-by-hour with real place names, real entry fees, travel time between stops.
3. NEARBY ALTERNATIVES: For each day, suggest 1-2 nearby places that can substitute a stop to save travel time.
4. NEARBY DESTINATIONS: At the end, list 3-4 destinations within 100-300 km worth a side trip.
5. BUDGET: Totals must be realistic and consistent with ₹{budget}/day.
6. If outside India, convert costs to INR approximately.

Respond ONLY with a JSON object exactly matching this schema:
{json.dumps(schema, indent=2)}

No preamble. No explanation. No markdown fences. Pure JSON only."""

    return prompt