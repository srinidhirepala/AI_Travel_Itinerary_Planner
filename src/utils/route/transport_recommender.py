"""
Transportation mode recommendation based on distance, budget, and time.
Suggests best transport options (flight, train, bus, car) with cost estimates.
"""
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TransportOption:
    """Transportation option with cost and time estimates."""
    mode: str  # "flight", "train", "bus", "car"
    cost_per_person: int  # INR
    duration_hours: float
    comfort_level: str  # "High", "Medium", "Low"
    availability: str  # "Common", "Limited", "Rare"
    booking_hint: str  # Where to book
    icon: str  # Emoji


def recommend_transport(
    distance_km: float,
    budget_per_person: int,
    from_city: str,
    to_city: str,
    num_people: int = 1
) -> List[TransportOption]:
    """
    Recommend transportation modes based on distance and budget.
    
    Args:
        distance_km: Distance between cities
        budget_per_person: Available budget per person (INR)
        from_city: Starting city
        to_city: Destination city
        num_people: Number of travelers
    
    Returns:
        List of TransportOption sorted by recommendation score
    """
    options = []
    
    # Flight (for distances > 500km)
    if distance_km > 500:
        flight_cost = estimate_flight_cost(distance_km)
        flight_time = estimate_flight_time(distance_km)
        
        if flight_cost <= budget_per_person * 1.5:  # Allow 50% budget flexibility
            options.append(TransportOption(
                mode="Flight",
                cost_per_person=flight_cost,
                duration_hours=flight_time,
                comfort_level="High",
                availability="Common" if distance_km > 800 else "Limited",
                booking_hint="MakeMyTrip, Goibibo, or airline websites",
                icon="✈️"
            ))
    
    # Train (for distances > 100km)
    if distance_km > 100:
        train_cost = estimate_train_cost(distance_km)
        train_time = estimate_train_time(distance_km)
        
        options.append(TransportOption(
            mode="Train",
            cost_per_person=train_cost,
            duration_hours=train_time,
            comfort_level="Medium",
            availability="Common",
            booking_hint="IRCTC, ConfirmTkt, or RailYatri",
            icon="🚂"
        ))
    
    # Bus (for distances 50-500km)
    if 50 <= distance_km <= 500:
        bus_cost = estimate_bus_cost(distance_km)
        bus_time = estimate_bus_time(distance_km)
        
        options.append(TransportOption(
            mode="Bus",
            cost_per_person=bus_cost,
            duration_hours=bus_time,
            comfort_level="Low" if distance_km > 300 else "Medium",
            availability="Common",
            booking_hint="RedBus, AbhiBus, or state transport",
            icon="🚌"
        ))
    
    # Car/Taxi (for distances < 300km or groups of 4+)
    if distance_km < 300 or num_people >= 4:
        car_cost_total = estimate_car_cost(distance_km)
        car_cost_per_person = car_cost_total // num_people
        car_time = estimate_car_time(distance_km)
        
        options.append(TransportOption(
            mode="Car/Taxi",
            cost_per_person=car_cost_per_person,
            duration_hours=car_time,
            comfort_level="High",
            availability="Common",
            booking_hint="Ola Outstation, Uber Intercity, or local taxi",
            icon="🚗"
        ))
    
    # Sort by cost (cheapest first)
    options.sort(key=lambda x: x.cost_per_person)
    
    return options


def estimate_flight_cost(distance_km: float) -> int:
    """
    Estimate flight cost based on distance.
    
    Formula: Base fare + distance-based pricing
    """
    base_fare = 2000  # INR
    per_km_rate = 2.5  # INR/km
    
    cost = base_fare + (distance_km * per_km_rate)
    
    # Apply distance discounts
    if distance_km > 1500:
        cost *= 0.9  # 10% discount for long flights
    
    return int(cost)


def estimate_flight_time(distance_km: float) -> float:
    """Estimate flight time including airport overhead."""
    flight_time = distance_km / 600  # 600 km/h average
    airport_overhead = 2.5  # Check-in, security, boarding
    return flight_time + airport_overhead


def estimate_train_cost(distance_km: float) -> int:
    """
    Estimate train cost (Sleeper class).
    
    Based on Indian Railways pricing:
    - Base fare: ₹30
    - Per km: ₹0.50-1.00 depending on distance
    """
    base_fare = 30
    
    if distance_km < 200:
        per_km_rate = 1.0
    elif distance_km < 500:
        per_km_rate = 0.75
    else:
        per_km_rate = 0.50
    
    cost = base_fare + (distance_km * per_km_rate)
    return int(cost)


def estimate_train_time(distance_km: float) -> float:
    """Estimate train travel time."""
    avg_speed = 50  # km/h for Indian trains
    return distance_km / avg_speed


def estimate_bus_cost(distance_km: float) -> int:
    """
    Estimate bus cost (AC Sleeper/Seater).
    
    Based on typical bus pricing in India.
    """
    base_fare = 100
    per_km_rate = 1.5 if distance_km < 200 else 1.2
    
    cost = base_fare + (distance_km * per_km_rate)
    return int(cost)


def estimate_bus_time(distance_km: float) -> float:
    """Estimate bus travel time."""
    avg_speed = 45  # km/h for buses
    return distance_km / avg_speed


def estimate_car_cost(distance_km: float) -> int:
    """
    Estimate car/taxi cost (total for vehicle).
    
    Based on typical outstation taxi rates in India.
    """
    per_km_rate = 12  # INR/km (includes fuel, driver, tolls)
    min_charge = 500  # Minimum charge
    
    cost = max(min_charge, distance_km * per_km_rate)
    return int(cost)


def estimate_car_time(distance_km: float) -> float:
    """Estimate car travel time."""
    avg_speed = 60  # km/h for highway driving
    return distance_km / avg_speed


def format_transport_recommendation(option: TransportOption, num_people: int = 1) -> str:
    """
    Format transport option for display.
    
    Returns:
        Formatted string with icon, mode, cost, time, and booking hint
    """
    total_cost = option.cost_per_person * num_people
    
    return f"""
{option.icon} **{option.mode}**
- Cost: ₹{option.cost_per_person:,}/person (₹{total_cost:,} total for {num_people})
- Duration: ~{option.duration_hours:.1f} hours
- Comfort: {option.comfort_level}
- Availability: {option.availability}
- Book via: {option.booking_hint}
"""


def get_transport_summary(from_city: str, to_city: str, distance_km: float, budget: int) -> Dict[str, Any]:
    """
    Get complete transport summary for a route.
    
    Returns:
        Dict with recommended options and total cost estimate
    """
    options = recommend_transport(distance_km, budget, from_city, to_city)
    
    if not options:
        return {
            "available": False,
            "message": f"Distance too short ({distance_km:.0f}km). Consider local transport."
        }
    
    # Best option (cheapest)
    best = options[0]
    
    # Fastest option
    fastest = min(options, key=lambda x: x.duration_hours)
    
    return {
        "available": True,
        "from": from_city,
        "to": to_city,
        "distance_km": int(distance_km),
        "all_options": options,
        "recommended": best,
        "fastest": fastest,
        "budget_sufficient": best.cost_per_person <= budget,
    }


# Example usage in route_intelligence.py:
def enhance_route_analysis_with_transport(route_analysis: dict, budget_per_day: int) -> dict:
    """
    Add transport recommendations to existing route analysis.
    
    Args:
        route_analysis: Output from analyze_route()
        budget_per_day: User's daily budget
    
    Returns:
        Enhanced route analysis with transport options
    """
    leg_details = route_analysis.get("leg_details", [])
    
    for leg in leg_details:
        from_city = leg["from"]
        to_city = leg["to"]
        distance = leg["distance_km"]
        
        transport_summary = get_transport_summary(from_city, to_city, distance, budget_per_day)
        leg["transport_options"] = transport_summary
    
    return route_analysis
