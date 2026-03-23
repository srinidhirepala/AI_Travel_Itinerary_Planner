import math
from typing import List, Dict, Tuple, Any

# Approximate coordinates for major Indian tourist destinations
# Add more as needed. Coordinates are (Latitude, Longitude)
CITY_COORDINATES = {
    # North
    "delhi": (28.6139, 77.2090), "agra": (27.1767, 78.0081), "jaipur": (26.9124, 75.7873),
    "udaipur": (24.5854, 73.7125), "jodhpur": (26.2389, 73.0243), "jaisalmer": (26.9157, 70.9083),
    "shimla": (31.1048, 77.1734), "manali": (32.2396, 77.1887), "rishikesh": (30.0869, 78.2676),
    "haridwar": (29.9457, 78.1642), "amritsar": (31.6340, 74.8723), "chandigarh": (30.7333, 76.7794),
    "varanasi": (25.3176, 83.0062), "lucknow": (26.8467, 80.9462),
    # West
    "mumbai": (19.0760, 72.8777), "pune": (18.5204, 73.8567), "goa": (15.2993, 74.1240),
    "ahmedabad": (23.0225, 72.5714), "surat": (21.1702, 72.8311),
    # South
    "bengaluru": (12.9716, 77.5946), "hyderabad": (17.3850, 78.4867), "chennai": (13.0827, 80.2707),
    "kochi": (9.9312, 76.2673), "munnar": (10.0889, 77.0595), "alleppey": (9.4981, 76.3388),
    "mysore": (12.2958, 76.6394), "ooty": (11.4100, 76.6950), "kodaikanal": (10.2381, 77.4663),
    "pondicherry": (11.9416, 79.8083), "tirupati": (13.6288, 79.4192), "kanchipuram": (12.8185, 79.6947),
    "madurai": (9.9252, 78.1198), "rameswaram": (9.2876, 79.3129), "kanyakumari": (8.0883, 77.5385),
    "coimbatore": (11.0168, 76.9558), "thiruvananthapuram": (8.5241, 76.9366),
    # East / Central / Northeast
    "kolkata": (22.5726, 88.3639), "bhubaneswar": (20.2961, 85.8245), "puri": (19.8135, 85.8312),
    "ranchi": (23.3441, 85.3096), "patna": (25.5941, 85.1376), "guwahati": (26.1445, 91.7362),
    "shillong": (25.5788, 91.8933), "darjeeling": (27.0360, 88.2627), "gangtok": (27.3389, 88.6065),
    "bhopal": (23.2599, 77.4126), "indore": (22.7196, 75.8577)
}


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculate distance in km between two lat/lon coordinates."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371.0  # Earth radius in kilometers

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2)**2) + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * (math.sin(dlon / 2)**2)
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def get_city_coords(city_name: str) -> Tuple[float, float]:
    """Return coordinates for a city. If not found, returns None."""
    norm_name = city_name.strip().lower()
    return CITY_COORDINATES.get(norm_name)


def estimate_travel_time_hours(distance_km: float) -> float:
    """
    Estimate travel time based on distance.
    Assumes mixed transport (train/bus/flight) taking into account airport/station overhead.
    """
    if distance_km < 100:
        return distance_km / 40.0  # ~40 km/h average on local roads
    elif distance_km < 500:
        return distance_km / 60.0  # ~60 km/h avg train/bus
    else:
        # Flights + 4 hours airport overhead
        return (distance_km / 600.0) + 4.0


def analyze_route(cities: List[str], total_days: int) -> Dict[str, Any]:
    """
    Analyze a multi-city route for efficiency, total travel time, and burnout risk.
    """
    if len(cities) <= 1:
        return {
            "is_valid": True,
            "total_distance_km": 0,
            "total_travel_time_hrs": 0,
            "burnout_risk": "LOW",
            "warnings": [],
            "illogical_jumps": [],
            "status": "perfect"
        }

    warnings = []
    
    # Generate Map Arc Coordinates payload (pydeck requires [longitude, latitude])
    valid_path = []
    for city in cities:
        coords = get_city_coords(city)
        if coords:
            valid_path.append({"name": city, "coordinates": [coords[1], coords[0]]})
            
    arcs = []
    for i in range(len(valid_path) - 1):
        arcs.append({
            "source": valid_path[i]["coordinates"],
            "target": valid_path[i+1]["coordinates"],
            "source_name": valid_path[i]["name"],
            "target_name": valid_path[i+1]["name"]
        })
    illogical_jumps = []
    total_distance = 0.0
    total_travel_time = 0.0
    missing_coords = []

    for i in range(len(cities) - 1):
        city1 = cities[i]
        city2 = cities[i + 1]
        c1 = get_city_coords(city1)
        c2 = get_city_coords(city2)

        if not c1: missing_coords.append(city1)
        if not c2: missing_coords.append(city2)
        
        if c1 and c2:
            dist = haversine_distance(c1, c2)
            time_hrs = estimate_travel_time_hours(dist)
            total_distance += dist
            total_travel_time += time_hrs

            if dist > 800:
                illogical_jumps.append(f"{city1} → {city2} ({int(dist)} km, ~{int(time_hrs)} hrs)")

    # Deduplicate missing coords
    missing_coords = list(set(missing_coords))

    # Burnout calculation
    total_trip_hours = total_days * 24
    active_trip_hours = total_days * 14  # Assume 10 hrs for sleep/rest per day
    
    travel_percentage = (total_travel_time / active_trip_hours) * 100 if active_trip_hours > 0 else 0

    if travel_percentage > 40:
        burnout_risk = "HIGH"
        status = "danger"
        warnings.append(f"You will spend ~{travel_percentage:.0f}% of your waking hours in transit.")
    elif travel_percentage > 25:
        burnout_risk = "MEDIUM"
        status = "warning"
        warnings.append(f"Significant travel time (~{travel_percentage:.0f}% of waking hours). Prepare for fatigue.")
    else:
        burnout_risk = "LOW"
        status = "success"

    if illogical_jumps:
        warnings.append("Detected exhausting jumps (>800 km) between consecutive cities.")
        status = "danger" if status != "danger" else "danger"

    # Too many cities for the given days
    if len(cities) > (total_days * 0.8):
        warnings.append("You are squeezing too many cities into too few days. Try removing 1-2 cities.")
        status = "danger" if status != "danger" else "danger"
        burnout_risk = "HIGH"

    return {
        "is_valid": len(missing_coords) == 0,
        "missing_cities": missing_coords,
        "total_distance_km": int(total_distance),
        "total_travel_time_hrs": int(total_travel_time),
        "travel_percentage": travel_percentage,
        "burnout_risk": burnout_risk,
        "warnings": warnings,
        "illogical_jumps": illogical_jumps,
        "status": status,
        "arcs": arcs,
        "valid_path": valid_path
    }
