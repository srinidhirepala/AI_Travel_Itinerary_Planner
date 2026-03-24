import math
from typing import List, Dict, Tuple, Any

CITY_COORDINATES = {
    # North India
    "delhi": (28.6139, 77.2090), "agra": (27.1767, 78.0081), "jaipur": (26.9124, 75.7873),
    "udaipur": (24.5854, 73.7125), "jodhpur": (26.2389, 73.0243), "jaisalmer": (26.9157, 70.9083),
    "shimla": (31.1048, 77.1734), "manali": (32.2396, 77.1887), "rishikesh": (30.0869, 78.2676),
    "haridwar": (29.9457, 78.1642), "amritsar": (31.6340, 74.8723), "chandigarh": (30.7333, 76.7794),
    "varanasi": (25.3176, 83.0062), "lucknow": (26.8467, 80.9462), "mathura": (27.4924, 77.6737),
    "vrindavan": (27.5794, 77.6965), "pushkar": (26.4900, 74.5516), "mount abu": (24.5926, 72.7156),
    "kasol": (32.0998, 77.3143), "dharamshala": (32.2190, 76.3234), "spiti": (32.2461, 78.0338),
    "leh": (34.1526, 77.5771), "srinagar": (34.0837, 74.7973),
    # West India
    "mumbai": (19.0760, 72.8777), "pune": (18.5204, 73.8567), "goa": (15.2993, 74.1240),
    "ahmedabad": (23.0225, 72.5714), "surat": (21.1702, 72.8311), "nashik": (19.9975, 73.7898),
    "aurangabad": (19.8762, 75.3433), "kolhapur": (16.6910, 74.2350),
    # South India
    "bengaluru": (12.9716, 77.5946), "hyderabad": (17.3850, 78.4867), "chennai": (13.0827, 80.2707),
    "kochi": (9.9312, 76.2673), "munnar": (10.0889, 77.0595), "alleppey": (9.4981, 76.3388),
    "mysore": (12.2958, 76.6394), "ooty": (11.4100, 76.6950), "kodaikanal": (10.2381, 77.4663),
    "pondicherry": (11.9416, 79.8083), "tirupati": (13.6288, 79.4192), "madurai": (9.9252, 78.1198),
    "rameswaram": (9.2876, 79.3129), "kanyakumari": (8.0883, 77.5385), "coimbatore": (11.0168, 76.9558),
    "thiruvananthapuram": (8.5241, 76.9366), "varkala": (8.7379, 76.7164), "kovalam": (8.3988, 77.0121),
    "hampi": (15.3350, 76.4600), "gokarna": (14.5479, 74.3188), "wayanad": (11.6854, 76.1320),
    "vizag": (17.6868, 83.2185), "visakhapatnam": (17.6868, 83.2185),
    # East / Central / Northeast
    "kolkata": (22.5726, 88.3639), "bhubaneswar": (20.2961, 85.8245), "puri": (19.8135, 85.8312),
    "ranchi": (23.3441, 85.3096), "patna": (25.5941, 85.1376), "guwahati": (26.1445, 91.7362),
    "shillong": (25.5788, 91.8933), "darjeeling": (27.0360, 88.2627), "gangtok": (27.3389, 88.6065),
    "bhopal": (23.2599, 77.4126), "indore": (22.7196, 75.8577), "ujjain": (23.1828, 75.7772),
    "jagdalpur": (19.0754, 82.0187), "khajuraho": (24.8318, 79.9199),
}


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def get_city_coords(city_name: str):
    return CITY_COORDINATES.get(city_name.strip().lower())


def estimate_travel_time_hours(distance_km: float) -> float:
    if distance_km < 100:
        return distance_km / 40.0
    elif distance_km < 500:
        return distance_km / 60.0
    else:
        return (distance_km / 600.0) + 4.0


def analyze_route(cities: List[str], total_days: int) -> Dict[str, Any]:
    if len(cities) <= 1:
        return {
            "is_valid": True, "total_distance_km": 0,
            "total_travel_time_hrs": 0, "burnout_risk": "LOW",
            "warnings": [], "illogical_jumps": [], "status": "success",
            "arcs": [], "valid_path": []
        }

    warnings = []
    illogical_jumps = []
    total_distance = 0.0
    total_travel_time = 0.0
    missing_coords = []

    # Build full valid_path for ALL cities (fix: was only using first 2)
    valid_path = []
    for city in cities:
        coords = get_city_coords(city)
        if coords:
            valid_path.append({
                "name": city,
                "coordinates": [coords[1], coords[0]]  # pydeck: [lon, lat]
            })
        else:
            missing_coords.append(city)

    # Build arcs for ALL consecutive pairs
    arcs = []
    for i in range(len(valid_path) - 1):
        arcs.append({
            "source":      valid_path[i]["coordinates"],
            "target":      valid_path[i+1]["coordinates"],
            "source_name": valid_path[i]["name"],
            "target_name": valid_path[i+1]["name"],
        })

    # Distance and time across all legs
    for i in range(len(cities) - 1):
        c1 = get_city_coords(cities[i])
        c2 = get_city_coords(cities[i+1])
        if c1 and c2:
            dist = haversine_distance(c1, c2)
            time_hrs = estimate_travel_time_hours(dist)
            total_distance += dist
            total_travel_time += time_hrs
            if dist > 800:
                illogical_jumps.append(
                    f"{cities[i]} → {cities[i+1]} ({int(dist)} km, ~{int(time_hrs)} hrs)"
                )

    missing_coords = list(set(missing_coords))
    active_trip_hours = total_days * 14
    travel_percentage = (total_travel_time / active_trip_hours * 100) if active_trip_hours > 0 else 0

    if travel_percentage > 40:
        burnout_risk, status = "HIGH", "danger"
        warnings.append(f"You'll spend ~{travel_percentage:.0f}% of waking hours in transit.")
    elif travel_percentage > 25:
        burnout_risk, status = "MEDIUM", "warning"
        warnings.append(f"Significant transit time (~{travel_percentage:.0f}% of waking hours).")
    else:
        burnout_risk, status = "LOW", "success"

    if illogical_jumps:
        warnings.append("Long jumps (>800 km) detected between consecutive cities.")
        status = "danger"

    if len(cities) > (total_days * 0.8):
        warnings.append("Too many cities for the days available. Consider removing 1–2 stops.")
        burnout_risk, status = "HIGH", "danger"

    return {
        "is_valid":              len(missing_coords) == 0,
        "missing_cities":        missing_coords,
        "total_distance_km":     int(total_distance),
        "total_travel_time_hrs": int(total_travel_time),
        "travel_percentage":     travel_percentage,
        "burnout_risk":          burnout_risk,
        "warnings":              warnings,
        "illogical_jumps":       illogical_jumps,
        "status":                status,
        "arcs":                  arcs,
        "valid_path":            valid_path,
    }