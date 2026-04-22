"""Budget feasibility helpers used before itinerary generation."""

from typing import Any, Dict, List, Tuple


def estimate_minimum_budget(
    destination: str,
    days: int,
    cities: List[str],
    total_distance_km: float,
    food_pref: str,
    num_people: int = 1,
) -> Dict[str, int]:
    """Estimate a conservative minimum budget for the trip."""
    food_costs = {
        "Vegetarian": 400,
        "Non-Vegetarian": 600,
        "Both (Veg & Non-Veg)": 500,
        "Vegan": 450,
        "Jain": 400,
        "Halal": 550,
    }
    accommodation_costs = {
        "budget": 500,
        "mid": 1500,
        "luxury": 3000,
    }

    food_per_day = food_costs.get(food_pref, 500)
    accommodation_per_night = accommodation_costs["budget"]

    from src.utils.route.transport_recommender import estimate_bus_cost, estimate_train_cost

    transport_total = (
        min(estimate_train_cost(total_distance_km), estimate_bus_cost(total_distance_km))
        if total_distance_km > 0
        else 0
    )
    activities_per_day = 200

    food_total = food_per_day * days
    accommodation_total = accommodation_per_night * max(0, days - 1)
    activities_total = activities_per_day * days

    subtotal = food_total + accommodation_total + transport_total + activities_total
    miscellaneous = int(subtotal * 0.1)
    grand_total = subtotal + miscellaneous

    return {
        "food_total": food_total,
        "accommodation_total": accommodation_total,
        "transport_total": transport_total,
        "activities_total": activities_total,
        "miscellaneous": miscellaneous,
        "grand_total": grand_total,
        "per_day_average": grand_total // max(1, days),
    }


def check_budget_feasibility(
    user_budget_per_day: int,
    days: int,
    destination: str,
    cities: List[str],
    total_distance_km: float,
    food_pref: str,
) -> Tuple[bool, Dict[str, Any]]:
    """Check whether the selected budget is likely to cover the trip."""
    user_total_budget = user_budget_per_day * days
    min_budget = estimate_minimum_budget(destination, days, cities, total_distance_km, food_pref)

    min_required = min_budget["grand_total"]
    shortfall = max(0, min_required - user_total_budget)
    surplus = max(0, user_total_budget - min_required)
    is_sufficient = user_total_budget >= min_required
    percentage = (user_total_budget / min_required) * 100 if min_required > 0 else 100

    return is_sufficient, {
        "user_budget_per_day": user_budget_per_day,
        "user_total_budget": user_total_budget,
        "min_required_total": min_required,
        "min_required_per_day": min_budget["per_day_average"],
        "shortfall": shortfall,
        "surplus": surplus,
        "percentage": percentage,
        "is_sufficient": is_sufficient,
        "breakdown": min_budget,
        "recommendation": _get_budget_recommendation(percentage, shortfall, surplus, days),
    }


def _get_budget_recommendation(
    percentage: float,
    shortfall: int,
    surplus: int,
    days: int,
) -> str:
    """Generate a short budget recommendation for the UI card."""
    if percentage >= 150:
        return (
            f"Budget looks comfortable. You still have INR {surplus:,} left for upgrades, shopping, "
            "or more flexible transport."
        )
    if percentage >= 100:
        return "Budget looks workable for a basic version of this trip. Add a small buffer for extra comfort."

    shortfall_per_day = shortfall // max(1, days)
    if percentage >= 80:
        return (
            f"Budget is tight. You are short by INR {shortfall:,} total "
            f"(around INR {shortfall_per_day}/day)."
        )
    return (
        f"Budget is below the recommended minimum by INR {shortfall:,} total "
        f"(around INR {shortfall_per_day}/day). Trim a stop, reduce days, or increase the daily budget."
    )


def format_budget_warning(feasibility: Dict[str, Any]) -> str:
    """Render the budget check as a small HTML info card for Streamlit."""
    if feasibility["is_sufficient"]:
        return f"""
<div style="background:#dff3e7;border:1px solid #b7dfc5;padding:1rem;border-radius:12px;margin:1rem 0;">
  <strong style="color:#14532d;">Budget Check: Good to go</strong>
  <p style="margin:0.5rem 0;color:#14532d;">
    Selected budget: INR {feasibility['user_budget_per_day']:,}/day
    (INR {feasibility['user_total_budget']:,} total)
  </p>
  <p style="margin:0;color:#14532d;font-size:0.92rem;">
    {feasibility['recommendation']}
  </p>
</div>
"""

    return f"""
<div style="background:#fbe7e8;border:1px solid #f2c3c8;padding:1rem;border-radius:12px;margin:1rem 0;">
  <strong style="color:#7f1d1d;">Budget Check: Needs attention</strong>
  <p style="margin:0.5rem 0;color:#7f1d1d;">
    Selected budget: INR {feasibility['user_budget_per_day']:,}/day
    (INR {feasibility['user_total_budget']:,} total)
  </p>
  <p style="margin:0.5rem 0;color:#7f1d1d;">
    Recommended minimum: INR {feasibility['min_required_per_day']:,}/day
    with a shortfall of INR {feasibility['shortfall']:,}.
  </p>
  <details style="margin-top:0.5rem;">
    <summary style="cursor:pointer;color:#7f1d1d;font-weight:bold;">View budget breakdown</summary>
    <ul style="margin:0.6rem 0 0;padding-left:1.5rem;color:#7f1d1d;">
      <li>Food: INR {feasibility['breakdown']['food_total']:,}</li>
      <li>Accommodation: INR {feasibility['breakdown']['accommodation_total']:,}</li>
      <li>Transport: INR {feasibility['breakdown']['transport_total']:,}</li>
      <li>Activities: INR {feasibility['breakdown']['activities_total']:,}</li>
      <li>Miscellaneous: INR {feasibility['breakdown']['miscellaneous']:,}</li>
    </ul>
  </details>
  <p style="margin:0.6rem 0 0;color:#7f1d1d;font-size:0.92rem;">
    {feasibility['recommendation']}
  </p>
</div>
"""


def add_budget_check_to_planner():
    """Compatibility placeholder retained for older integration notes."""
    pass
