"""
Prompt Builder - Constructs prompts for LLM
"""
import json


def build_itinerary_prompt(destination: str, days: int, budget: int, food_pref: str, interests: list, travel_style: str = "Explorer", route_analysis: dict = None) -> str:
    """
    Build a structured itinerary prompt that requests a strict JSON response.
    destination: user-provided, can be anywhere in the world (no hardcoded India).
    """
    interests_str = ", ".join(interests) if interests else "General sightseeing"

    schema = {
        "destination": "string",
        "days": [
            {
                "day_number": "integer",
                "title": "string (e.g. 'Old City & Palaces')",
                "schedule": [
                    {
                        "time": "string (e.g. '8:00 AM')",
                        "activity": "string",
                        "location": "string",
                        "duration_minutes": "integer",
                        "cost_inr": "integer (0 if free)",
                        "notes": "string (tip, transport, or food note)"
                    }
                ],
                "meals": {
                    "breakfast": {"place": "string", "dish": "string", "cost_inr": "integer"},
                    "lunch": {"place": "string", "dish": "string", "cost_inr": "integer"},
                    "dinner": {"place": "string", "dish": "string", "cost_inr": "integer"}
                },
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
        "practical_tips": [
            "string"
        ],
        "best_areas_to_stay": ["string"],
        "local_transport": ["string"]
    }

    route_guidance = ""
    if route_analysis and route_analysis.get("burnout_risk") in ["HIGH", "MEDIUM"]:
        route_guidance = (
            f"\nCRITICAL ROUTE INTELLIGENCE:\n"
            f"- Route has highly exhausting travel ({route_analysis.get('total_distance_km')} km total, ~{route_analysis.get('total_travel_time_hrs')} hrs).\n"
            f"- Burnout Risk is {route_analysis.get('burnout_risk')}.\n"
            f"-> YOU MUST design the itinerary to mitigate this burnout. Insert 'Travel / Recovery' blocks. Start mornings late and keep evenings relaxed on heavy travel days."
        )

    prompt = f"""Create a detailed {days}-day travel itinerary for {destination}.

TRAVELER DETAILS:
- Duration: {days} days
- Daily Budget: ₹{budget} (Indian Rupees)
- Food Preference: {food_pref}
- Interests: {interests_str}
- Travel Style / Pace: {travel_style}
{route_guidance}

REQUIREMENTS:
- Provide hour-by-hour schedule with real place names
- Include travel time between locations
- Respect food preference ({food_pref}) for ALL meal suggestions
- Be specific: real restaurant names, real attraction names, real entry fees
- Budget totals must be realistic and consistent with ₹{budget}/day limit
- If destination is outside India, convert costs to INR approximately

Respond ONLY with a JSON object exactly matching this schema:
{json.dumps(schema, indent=2)}

No preamble. No explanation. No markdown fences. Pure JSON only."""

    return prompt