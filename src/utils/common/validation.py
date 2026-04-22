"""
Input and schema validation with Pydantic.
"""
import re
from typing import Any
import logging
import json

logger = logging.getLogger(__name__)

# Constants
MAX_DESTINATION_LENGTH = 100
MAX_INTERESTS = 16
MAX_BUDGET = 100000
MIN_BUDGET = 100
MAX_DAYS = 30
MIN_DAYS = 1


class ValidationError(Exception):
    """Custom validation error."""
    pass


def sanitize_city_name(city: str) -> str:
    """Sanitize city name to prevent injection attacks."""
    if not city or not isinstance(city, str):
        raise ValidationError("City name must be a non-empty string")
    
    # Remove special characters except spaces, hyphens, apostrophes, commas
    sanitized = re.sub(r"[^a-zA-Z0-9\s\-',]", "", city.strip())
    
    if not sanitized:
        raise ValidationError("City name contains only invalid characters")
    
    if len(sanitized) > 100:
        raise ValidationError("City name too long (max 100 characters)")
    
    return sanitized


def validate_destination(destination: str) -> str:
    """Validate and sanitize destination input."""
    if not destination:
        raise ValidationError("Destination cannot be empty")
    
    destination = destination.strip()
    
    # Sanitize the entire destination string
    destination = sanitize_city_name(destination)
    
    if len(destination) > MAX_DESTINATION_LENGTH:
        raise ValidationError(
            f"Destination name too long. Max {MAX_DESTINATION_LENGTH} characters."
        )
    
    return destination


def validate_trip_params(
    destination: str, 
    days: int, 
    budget: int, 
    food_pref: str, 
    interests: list
) -> dict:
    """Validate all trip planning parameters."""
    errors = []
    
    # Destination validation
    try:
        destination = validate_destination(destination)
    except ValidationError as e:
        errors.append(str(e))
    
    # Days validation
    if not isinstance(days, int) or days < MIN_DAYS or days > MAX_DAYS:
        errors.append(f"Days must be between {MIN_DAYS} and {MAX_DAYS}")
    
    # Budget validation
    if not isinstance(budget, int) or budget < MIN_BUDGET or budget > MAX_BUDGET:
        errors.append(f"Budget must be between ₹{MIN_BUDGET} and ₹{MAX_BUDGET} per day")
    
    # Food preference validation
    valid_food_prefs = ["Vegetarian", "Non-Vegetarian", "Both (Veg & Non-Veg)", "Vegan", "Jain", "Halal"]
    if food_pref not in valid_food_prefs:
        errors.append(f"Food preference must be one of: {', '.join(valid_food_prefs)}")
    
    # Interests validation
    from src.utils.common.constants import ALL_INTERESTS
    if not isinstance(interests, list) or len(interests) == 0:
        errors.append("At least one interest must be selected")
    elif len(interests) > MAX_INTERESTS:
        errors.append(f"Maximum {MAX_INTERESTS} interests allowed")
    else:
        invalid = set(interests) - set(ALL_INTERESTS)
        if invalid:
            errors.append(f"Invalid interests: {', '.join(invalid)}")
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    return {
        "destination": destination,
        "days": days,
        "budget": budget,
        "food_pref": food_pref,
        "interests": interests
    }


def validate_itinerary_response(response: dict) -> dict:
    """Validate LLM-generated itinerary response."""
    required_keys = ["days", "budget_breakdown", "practical_tips"]
    
    # Check required top-level keys
    missing = [k for k in required_keys if k not in response]
    if missing:
        raise ValidationError(
            f"Invalid itinerary format: missing keys {missing}"
        )
    
    # Validate days structure
    if not isinstance(response["days"], list) or len(response["days"]) == 0:
        raise ValidationError("Itinerary must have at least one day")
    
    for idx, day in enumerate(response["days"]):
        if not isinstance(day, dict):
            raise ValidationError(f"Day {idx + 1}: invalid format")
        
        required_day_keys = ["day_number", "title", "schedule", "meals", "day_total_inr"]
        missing_day_keys = [k for k in required_day_keys if k not in day]
        if missing_day_keys:
            raise ValidationError(
                f"Day {idx + 1}: missing keys {missing_day_keys}"
            )
    
    # Validate budget breakdown
    if not isinstance(response["budget_breakdown"], dict):
        raise ValidationError("Budget breakdown must be an object")
    
    budget_keys = ["accommodation_per_night", "food_per_day", "transport_per_day", 
                   "activities_total", "miscellaneous", "grand_total"]
    for key in budget_keys:
        if key not in response["budget_breakdown"]:
            raise ValidationError(f"Budget breakdown missing: {key}")
    
    # Validate practical tips
    if not isinstance(response["practical_tips"], list):
        raise ValidationError("Practical tips must be a list")
    
    return response


def safe_json_loads(raw_text: str) -> dict:
    """Safely parse JSON with error handling."""
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error at line {e.lineno}: {e.msg}")
        raise ValidationError(
            f"Invalid response format. Please try again."
        ) from e
