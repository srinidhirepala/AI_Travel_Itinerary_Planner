"""
Prompt Builder - Constructs prompts for LLM
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
        optimized_guidance = ""
        optimized_order = route_analysis.get("optimized_order", [])
        current_order = route_analysis.get("current_order", [])
        if optimized_order and optimized_order != current_order:
            optimized_guidance = (
                f"\n- A lower-fatigue visit order exists: {' -> '.join(optimized_order)}."
                f" This saves about {route_analysis.get('distance_saved_km', 0)} km and"
                f" {route_analysis.get('time_saved_hrs', 0)} hours."
            )

        replacement_guidance = ""
        replacement_suggestions = route_analysis.get("replacement_suggestions", [])
        if replacement_suggestions:
            top_swap = replacement_suggestions[0]
            replacement_guidance = (
                f"\n- If the route still feels too aggressive, consider swapping"
                f" {top_swap.get('replace_city', '')} with {top_swap.get('replacement_city', '')}"
                f" for a nearby alternative with similar appeal."
            )

        trim_guidance = ""
        trim_suggestion = route_analysis.get("trim_suggestion")
        if trim_suggestion:
            trim_guidance = (
                f"\n- If keeping every stop makes the route too tiring, the cleanest trim is to remove"
                f" {trim_suggestion.get('removed_city', '')}. That saves about"
                f" {trim_suggestion.get('distance_saved_km', 0)} km and"
                f" {trim_suggestion.get('time_saved_hrs', 0)} hours."
            )

        route_guidance = (
            f"\nCRITICAL ROUTE INTELLIGENCE:\n"
            f"- Route has highly exhausting travel ({route_analysis.get('total_distance_km')} km total, ~{route_analysis.get('total_travel_time_hrs')} hrs).\n"
            f"- Burnout Risk is {route_analysis.get('burnout_risk')}.\n"
            f"-> YOU MUST design the itinerary to mitigate this burnout. Insert 'Travel / Recovery' blocks. Start mornings late and keep evenings relaxed on heavy travel days."
            f"{optimized_guidance}{replacement_guidance}{trim_guidance}"
        )

    hometown_guidance = f"- Origin City: {hometown}\n" if hometown else ""
    weekend_guidance = "- This is a weekend getaway: keep transit light and prioritize nearby/high-value experiences.\n" if is_weekend_getaway else ""

    prompt = f"""Create a detailed {days}-day travel itinerary for {destination}.

TRAVELER DETAILS:
- Duration: {days} days
- Daily Budget: ₹{budget} (Indian Rupees)
- Food Preference: {food_pref}
- Interests: {interests_str}
- Travel Style / Pace: {travel_style}
{hometown_guidance}{weekend_guidance}
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


def build_recommendations_prompt(profile: dict, liked_places: list[dict], context: dict | None = None) -> str:
    """
    Build a prompt for AI to generate destination recommendations.
    Based on user profile and previously liked places.
    """
    interests = profile.get("interests", [])
    travel_style = profile.get("travel_style", "Explorer")
    food_pref = profile.get("food_pref", "No preference")
    budget = profile.get("budget_default", 5000)
    context = context or {}
    current_location = context.get("current_location", "")
    mood = context.get("mood", "")
    time_window_type = context.get("time_window_type", "Days")
    time_window_value = context.get("time_window_value", "")
    
    interests_str = ", ".join(interests) if interests else "General sightseeing"
    liked_places_str = ", ".join([p.get("place_name", "") for p in liked_places]) if liked_places else "None yet"
    
    schema = {
        "recommendations": [
            {
                "destination": "string (place name)",
                "country": "string",
                "why_recommended": "string (2-3 sentences explaining the match)",
                "best_season": "string (e.g., 'Oct-Mar')",
                "estimated_budget_per_day": "integer (in INR)",
                "highlights": ["string"],
                "best_time": "string (best season/months)",
                "transport_hint": "string (how to reach from current location, if provided)",
                "match_score": "integer (1-10 scale)"
            }
        ]
    }

    context_block = ""
    if current_location or mood or time_window_value:
        context_block = "\nRECOMMENDATION CONTEXT:\n"
        if current_location:
            context_block += f"- Current Location: {current_location}\n"
        if mood:
            context_block += f"- User Mood: {mood}\n"
        if time_window_value:
            context_block += f"- Available Time Window: {time_window_value} {time_window_type}\n"
    
    prompt = f"""Based on the user's travel profile, recommend 5-6 unique and exciting travel destinations worldwide.

USER PROFILE:
- Travel Style: {travel_style}
- Interests: {interests_str}
- Food Preference: {food_pref}
- Daily Budget: ₹{budget}
- Previously Liked: {liked_places_str}
{context_block}

REQUIREMENTS:
- Recommend destinations they haven't been to (if liked places are provided)
- Match recommendations to their interests and travel style
- Include a mix of country diversity where possible
- Provide realistic budgets in INR
- Explain why each destination matches their profile
- If current location is provided, add a short transport hint from there
- Rank by match relevance (best matches first)

Respond ONLY with a JSON object exactly matching this schema:
{json.dumps(schema, indent=2)}

No preamble. No explanation. No markdown fences. Pure JSON only."""
    
    return prompt
