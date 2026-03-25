import itertools
import math
from typing import Any, Dict, List, Tuple

DEFAULT_OPTIMIZATION_WEIGHTS = {
    "time": 0.35,
    "fatigue": 0.30,
    "cost": 0.20,
    "interests": 0.15,
}

# Approximate coordinates for major Indian tourist destinations.
# Coordinates are stored as (latitude, longitude).
CITY_COORDINATES = {
    # North
    "delhi": (28.6139, 77.2090),
    "agra": (27.1767, 78.0081),
    "jaipur": (26.9124, 75.7873),
    "udaipur": (24.5854, 73.7125),
    "jodhpur": (26.2389, 73.0243),
    "jaisalmer": (26.9157, 70.9083),
    "shimla": (31.1048, 77.1734),
    "manali": (32.2396, 77.1887),
    "rishikesh": (30.0869, 78.2676),
    "haridwar": (29.9457, 78.1642),
    "amritsar": (31.6340, 74.8723),
    "chandigarh": (30.7333, 76.7794),
    "varanasi": (25.3176, 83.0062),
    "lucknow": (26.8467, 80.9462),
    # West
    "mumbai": (19.0760, 72.8777),
    "pune": (18.5204, 73.8567),
    "goa": (15.2993, 74.1240),
    "ahmedabad": (23.0225, 72.5714),
    "surat": (21.1702, 72.8311),
    # South
    "bengaluru": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "kochi": (9.9312, 76.2673),
    "munnar": (10.0889, 77.0595),
    "alleppey": (9.4981, 76.3388),
    "mysore": (12.2958, 76.6394),
    "ooty": (11.4100, 76.6950),
    "kodaikanal": (10.2381, 77.4663),
    "pondicherry": (11.9416, 79.8083),
    "tirupati": (13.6288, 79.4192),
    "kanchipuram": (12.8185, 79.6947),
    "madurai": (9.9252, 78.1198),
    "rameswaram": (9.2876, 79.3129),
    "kanyakumari": (8.0883, 77.5385),
    "coimbatore": (11.0168, 76.9558),
    "thiruvananthapuram": (8.5241, 76.9366),
    # East / Central / Northeast
    "kolkata": (22.5726, 88.3639),
    "bhubaneswar": (20.2961, 85.8245),
    "puri": (19.8135, 85.8312),
    "ranchi": (23.3441, 85.3096),
    "patna": (25.5941, 85.1376),
    "guwahati": (26.1445, 91.7362),
    "shillong": (25.5788, 91.8933),
    "darjeeling": (27.0360, 88.2627),
    "gangtok": (27.3389, 88.6065),
    "bhopal": (23.2599, 77.4126),
    "indore": (22.7196, 75.8577),
}

CITY_TAGS = {
    "delhi": {"Culture", "Food", "Shopping"},
    "agra": {"Culture", "Photography"},
    "jaipur": {"Culture", "Shopping", "Photography"},
    "udaipur": {"Culture", "Photography", "Food"},
    "jodhpur": {"Culture", "Photography", "Food"},
    "jaisalmer": {"Culture", "Adventure", "Photography"},
    "shimla": {"Nature", "Photography", "Relax"},
    "manali": {"Adventure", "Nature", "Photography"},
    "rishikesh": {"Adventure", "Nature", "Culture"},
    "haridwar": {"Culture", "Relax"},
    "amritsar": {"Culture", "Food"},
    "chandigarh": {"Shopping", "Food", "Relax"},
    "varanasi": {"Culture", "Photography", "Food"},
    "lucknow": {"Culture", "Food", "Shopping"},
    "mumbai": {"Food", "Shopping", "Photography"},
    "pune": {"Food", "Relax", "Nature"},
    "goa": {"Nature", "Adventure", "Food", "Photography"},
    "ahmedabad": {"Food", "Culture", "Shopping"},
    "surat": {"Food", "Shopping"},
    "bengaluru": {"Food", "Shopping", "Relax"},
    "hyderabad": {"Food", "Culture", "Shopping"},
    "chennai": {"Food", "Culture", "Photography"},
    "kochi": {"Food", "Culture", "Nature"},
    "munnar": {"Nature", "Photography", "Relax"},
    "alleppey": {"Nature", "Relax", "Photography"},
    "mysore": {"Culture", "Photography", "Relax"},
    "ooty": {"Nature", "Photography", "Relax"},
    "kodaikanal": {"Nature", "Photography", "Relax"},
    "pondicherry": {"Food", "Relax", "Photography"},
    "tirupati": {"Culture", "Relax"},
    "kanchipuram": {"Culture", "Photography"},
    "madurai": {"Culture", "Food"},
    "rameswaram": {"Culture", "Photography", "Relax"},
    "kanyakumari": {"Nature", "Photography", "Relax"},
    "coimbatore": {"Nature", "Food", "Relax"},
    "thiruvananthapuram": {"Nature", "Food", "Photography"},
    "kolkata": {"Food", "Culture", "Photography"},
    "bhubaneswar": {"Culture", "Photography"},
    "puri": {"Nature", "Culture", "Relax"},
    "ranchi": {"Nature", "Adventure"},
    "patna": {"Culture", "Food"},
    "guwahati": {"Nature", "Culture", "Adventure"},
    "shillong": {"Nature", "Adventure", "Photography"},
    "darjeeling": {"Nature", "Photography", "Relax"},
    "gangtok": {"Nature", "Adventure", "Photography"},
    "bhopal": {"Culture", "Nature"},
    "indore": {"Food", "Culture", "Shopping"},
}

CITY_ALIASES = {
    "bangalore": "bengaluru",
    "new delhi": "delhi",
    "delhi ncr": "delhi",
    "panaji": "goa",
    "panjim": "goa",
    "north goa": "goa",
    "south goa": "goa",
    "pondy": "pondicherry",
    "trivandrum": "thiruvananthapuram",
    "cochin": "kochi",
}


def _normalize_city_name(city_name: str) -> str:
    cleaned = city_name.strip().lower()
    return CITY_ALIASES.get(cleaned, cleaned)


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculate distance in km between two lat/lon coordinates."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    radius_km = 6371.0

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * (math.sin(dlon / 2) ** 2)
    )
    c = 2 * math.asin(math.sqrt(a))
    return radius_km * c


def get_city_coords(city_name: str) -> Tuple[float, float] | None:
    """Return coordinates for a city if known."""
    return CITY_COORDINATES.get(_normalize_city_name(city_name))


def estimate_travel_time_hours(distance_km: float) -> float:
    """Estimate travel time from a distance in km."""
    if distance_km < 100:
        return distance_km / 40.0
    if distance_km < 500:
        return distance_km / 60.0
    return (distance_km / 600.0) + 4.0


def _city_tags(city_name: str) -> set[str]:
    return CITY_TAGS.get(_normalize_city_name(city_name), set())


def _normalize_weights(custom_weights: Dict[str, float] | None) -> Dict[str, float]:
    if not custom_weights:
        return DEFAULT_OPTIMIZATION_WEIGHTS.copy()

    merged = DEFAULT_OPTIMIZATION_WEIGHTS.copy()
    for key in merged:
        raw = custom_weights.get(key, merged[key])
        try:
            merged[key] = max(0.0, float(raw))
        except (TypeError, ValueError):
            pass

    total = sum(merged.values())
    if total <= 0:
        return DEFAULT_OPTIMIZATION_WEIGHTS.copy()

    return {k: (v / total) for k, v in merged.items()}


def _interest_coverage_score(cities: List[str], interests: List[str] | None) -> float:
    interests_set = set(interests or [])
    if not cities or not interests_set:
        return 0.0

    cumulative = 0.0
    for city in cities:
        tags = _city_tags(city)
        if not tags:
            continue
        cumulative += len(tags & interests_set) / max(1, len(interests_set))

    return cumulative / max(1, len(cities))


def _transport_cost_proxy(total_distance_km: int, budget_per_day: int | None, total_days: int) -> float:
    estimated_transport = max(0.0, total_distance_km * 6.0)
    if not budget_per_day or total_days <= 0:
        return estimated_transport
    total_budget = budget_per_day * total_days
    if total_budget <= 0:
        return estimated_transport
    return estimated_transport / total_budget


def _rank_route_candidates(
    candidates: List[Dict[str, Any]],
    weights: Dict[str, float],
) -> List[Dict[str, Any]]:
    if not candidates:
        return []

    metrics = {
        "time": [c["time_metric"] for c in candidates],
        "fatigue": [c["fatigue_metric"] for c in candidates],
        "cost": [c["cost_metric"] for c in candidates],
        "interests": [c["interest_metric"] for c in candidates],
    }

    bounds = {}
    for key, values in metrics.items():
        minimum = min(values)
        maximum = max(values)
        bounds[key] = (minimum, maximum)

    def _scale(value: float, key: str) -> float:
        minimum, maximum = bounds[key]
        if abs(maximum - minimum) < 1e-9:
            return 0.0
        return (value - minimum) / (maximum - minimum)

    ranked = []
    for candidate in candidates:
        time_penalty = _scale(candidate["time_metric"], "time")
        fatigue_penalty = _scale(candidate["fatigue_metric"], "fatigue")
        cost_penalty = _scale(candidate["cost_metric"], "cost")
        interest_penalty = 1.0 - _scale(candidate["interest_metric"], "interests")
        objective_score = (
            weights["time"] * time_penalty
            + weights["fatigue"] * fatigue_penalty
            + weights["cost"] * cost_penalty
            + weights["interests"] * interest_penalty
        )
        ranked.append({**candidate, "objective_score": round(objective_score, 4)})

    return sorted(ranked, key=lambda c: c["objective_score"])


def _route_payload(cities: List[str]) -> Dict[str, Any]:
    valid_path = []
    arcs = []
    illogical_jumps = []
    leg_details = []
    missing_coords = []
    total_distance = 0.0
    total_travel_time = 0.0

    for city in cities:
        coords = get_city_coords(city)
        if coords:
            valid_path.append({"name": city, "coordinates": [coords[1], coords[0]]})
        else:
            missing_coords.append(city)

    for i in range(len(cities) - 1):
        city1 = cities[i]
        city2 = cities[i + 1]
        c1 = get_city_coords(city1)
        c2 = get_city_coords(city2)
        if not c1 or not c2:
            continue

        dist = haversine_distance(c1, c2)
        time_hrs = estimate_travel_time_hours(dist)
        total_distance += dist
        total_travel_time += time_hrs
        leg_details.append(
            {
                "from": city1,
                "to": city2,
                "distance_km": int(dist),
                "travel_time_hrs": round(time_hrs, 1),
            }
        )

        arcs.append(
            {
                "source": [c1[1], c1[0]],
                "target": [c2[1], c2[0]],
                "source_name": city1,
                "target_name": city2,
            }
        )

        if dist > 800:
            illogical_jumps.append(f"{city1} -> {city2} ({int(dist)} km, ~{int(time_hrs)} hrs)")

    return {
        "valid_path": valid_path,
        "arcs": arcs,
        "leg_details": leg_details,
        "illogical_jumps": illogical_jumps,
        "missing_cities": sorted(set(missing_coords)),
        "total_distance_km": int(total_distance),
        "total_travel_time_hrs": round(total_travel_time, 1),
    }


def _travel_percentage(total_travel_time_hrs: float, total_days: int) -> float:
    active_trip_hours = total_days * 14
    if active_trip_hours <= 0:
        return 0.0
    return (total_travel_time_hrs / active_trip_hours) * 100


def _route_status(cities: List[str], total_days: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    warnings = []
    travel_percentage = _travel_percentage(payload["total_travel_time_hrs"], total_days)

    if travel_percentage > 40:
        burnout_risk = "HIGH"
        status = "danger"
        warnings.append(f"You will spend ~{travel_percentage:.0f}% of your waking hours in transit.")
    elif travel_percentage > 25:
        burnout_risk = "MEDIUM"
        status = "warning"
        warnings.append(
            f"Significant travel time (~{travel_percentage:.0f}% of waking hours). Prepare for fatigue."
        )
    else:
        burnout_risk = "LOW"
        status = "ok"

    if payload["illogical_jumps"]:
        warnings.append("Detected exhausting jumps (>800 km) between consecutive cities.")
        status = "danger"

    if payload["missing_cities"]:
        warnings.append(
            "Some stops could not be mapped exactly, so route previews and optimization may be partial."
        )

    if len(cities) > (total_days * 0.8):
        warnings.append("You are squeezing too many cities into too few days. Try removing 1-2 cities.")
        burnout_risk = "HIGH"
        status = "danger"

    return {
        "burnout_risk": burnout_risk,
        "status": status,
        "warnings": warnings,
        "travel_percentage": travel_percentage,
    }


def _nearest_neighbor_order(start: str, remaining: List[str]) -> List[str]:
    ordered = [start]
    current = start
    pool = remaining[:]

    while pool:
        current_coords = get_city_coords(current)
        if not current_coords:
            ordered.extend(pool)
            break

        next_city = min(
            pool,
            key=lambda city: haversine_distance(current_coords, get_city_coords(city))
            if get_city_coords(city)
            else float("inf"),
        )
        ordered.append(next_city)
        pool.remove(next_city)
        current = next_city

    return ordered


def _best_optimized_order(cities: List[str]) -> List[str]:
    if len(cities) <= 2:
        return cities[:]

    start = cities[0]
    remaining = cities[1:]
    if any(get_city_coords(city) is None for city in cities):
        return cities[:]

    if len(remaining) <= 6:
        best_order = cities[:]
        best_distance = float("inf")
        for permutation in itertools.permutations(remaining):
            candidate = [start, *permutation]
            candidate_distance = _route_payload(candidate)["total_distance_km"]
            if candidate_distance < best_distance:
                best_distance = candidate_distance
                best_order = candidate
        return best_order

    return _nearest_neighbor_order(start, remaining)


def _build_replacement_suggestions(
    cities: List[str], interests: List[str] | None, current_payload: Dict[str, Any]
) -> List[Dict[str, Any]]:
    interests_set = set(interests or [])
    used = {city.strip().lower() for city in cities}
    suggestions = []

    ranked_legs = sorted(
        current_payload["leg_details"],
        key=lambda leg: leg["distance_km"],
        reverse=True,
    )

    for leg in ranked_legs[:3]:
        replace_city = leg["to"]
        replace_idx = cities.index(replace_city)
        previous_city = cities[replace_idx - 1] if replace_idx > 0 else None
        next_city = cities[replace_idx + 1] if replace_idx + 1 < len(cities) else None
        original_coords = get_city_coords(replace_city)
        previous_coords = get_city_coords(previous_city) if previous_city else None
        next_coords = get_city_coords(next_city) if next_city else None
        if not original_coords or not previous_coords:
            continue

        target_tags = _city_tags(replace_city) | interests_set
        best_candidate = None
        best_score = float("-inf")

        for candidate_name, candidate_coords in CITY_COORDINATES.items():
            if candidate_name in used or candidate_name == replace_city.strip().lower():
                continue

            candidate_tags = _city_tags(candidate_name)
            shared_tags = target_tags & candidate_tags
            if not shared_tags:
                continue

            original_leg_cost = haversine_distance(previous_coords, original_coords)
            candidate_leg_cost = haversine_distance(previous_coords, candidate_coords)
            if next_coords:
                original_leg_cost += haversine_distance(original_coords, next_coords)
                candidate_leg_cost += haversine_distance(candidate_coords, next_coords)

            distance_saved = original_leg_cost - candidate_leg_cost
            proximity_to_original = haversine_distance(original_coords, candidate_coords)
            if distance_saved < 80 or proximity_to_original > 520:
                continue

            score = (
                distance_saved
                + (len(shared_tags) * 90)
                + (len(interests_set & candidate_tags) * 45)
                - (proximity_to_original * 0.18)
            )

            if score > best_score:
                best_score = score
                best_candidate = {
                    "replace_city": replace_city,
                    "replacement_city": candidate_name.title(),
                    "distance_saved_km": int(distance_saved),
                    "similarity_tags": sorted(shared_tags)[:3],
                }

        if not best_candidate:
            continue

        replacement_order = cities[:]
        replacement_order[replace_idx] = best_candidate["replacement_city"]
        replacement_payload = _route_payload(replacement_order)
        suggestion = {
            **best_candidate,
            "suggested_order": replacement_order,
            "suggested_total_distance_km": replacement_payload["total_distance_km"],
            "suggested_total_travel_time_hrs": replacement_payload["total_travel_time_hrs"],
            "suggested_path": replacement_payload["valid_path"],
            "suggested_arcs": replacement_payload["arcs"],
        }

        if not any(
            existing["replace_city"].lower() == suggestion["replace_city"].lower()
            for existing in suggestions
        ):
            suggestions.append(suggestion)

        if len(suggestions) == 2:
            break

    return suggestions


def _build_trim_suggestion(cities: List[str], current_payload: Dict[str, Any]) -> Dict[str, Any] | None:
    if len(cities) <= 2:
        return None

    best_suggestion = None

    for idx in range(1, len(cities)):
        candidate_order = cities[:idx] + cities[idx + 1 :]
        candidate_payload = _route_payload(candidate_order)
        distance_saved = current_payload["total_distance_km"] - candidate_payload["total_distance_km"]
        time_saved = current_payload["total_travel_time_hrs"] - candidate_payload["total_travel_time_hrs"]
        if distance_saved <= 120 and time_saved <= 1.5:
            continue

        candidate = {
            "removed_city": cities[idx],
            "suggested_order": candidate_order,
            "distance_saved_km": max(0, int(distance_saved)),
            "time_saved_hrs": max(0.0, round(time_saved, 1)),
            "suggested_total_distance_km": candidate_payload["total_distance_km"],
            "suggested_total_travel_time_hrs": candidate_payload["total_travel_time_hrs"],
            "suggested_path": candidate_payload["valid_path"],
            "suggested_arcs": candidate_payload["arcs"],
        }

        if not best_suggestion:
            best_suggestion = candidate
            continue

        best_score = (
            best_suggestion["distance_saved_km"] * 0.65
            + best_suggestion["time_saved_hrs"] * 110
        )
        candidate_score = (
            candidate["distance_saved_km"] * 0.65
            + candidate["time_saved_hrs"] * 110
        )
        if candidate_score > best_score:
            best_suggestion = candidate

    return best_suggestion


def analyze_route(
    cities: List[str],
    total_days: int,
    interests: List[str] | None = None,
    optimization_weights: Dict[str, float] | None = None,
    budget_per_day: int | None = None,
    enable_what_if: bool = True,
) -> Dict[str, Any]:
    """
    Analyze a multi-city route for efficiency, total travel time, and burnout risk.
    Also returns two recovery strategies for high-fatigue routes:
    1. Reordering the same places.
    2. Swapping one exhausting stop for a nearby similar stop.
    """
    if len(cities) <= 1:
        return {
            "is_valid": True,
            "current_order": cities[:],
            "total_distance_km": 0,
            "total_travel_time_hrs": 0,
            "travel_percentage": 0,
            "burnout_risk": "LOW",
            "warnings": [],
            "illogical_jumps": [],
            "status": "ok",
            "arcs": [],
            "valid_path": [],
            "optimized_order": cities[:],
            "optimized_arcs": [],
            "optimized_path": [],
            "optimized_total_distance_km": 0,
            "optimized_total_travel_time_hrs": 0,
            "distance_saved_km": 0,
            "time_saved_hrs": 0,
            "travel_percentage_reduction": 0,
            "replacement_suggestions": [],
            "trim_suggestion": None,
            "optimization_weights_applied": _normalize_weights(optimization_weights),
            "recommended_option": None,
            "what_if_scenarios": [],
        }

    current_payload = _route_payload(cities)
    route_state = _route_status(cities, total_days, current_payload)

    optimized_order = _best_optimized_order(cities)
    optimized_payload = _route_payload(optimized_order)
    optimized_state = _route_status(optimized_order, total_days, optimized_payload)

    distance_saved = max(
        0,
        current_payload["total_distance_km"] - optimized_payload["total_distance_km"],
    )
    time_saved = max(
        0.0,
        current_payload["total_travel_time_hrs"] - optimized_payload["total_travel_time_hrs"],
    )
    replacement_suggestions = []
    trim_suggestion = None
    should_suggest_recovery = (
        route_state["status"] in {"danger", "warning"}
        or route_state["burnout_risk"] in {"HIGH", "MEDIUM"}
    )
    if should_suggest_recovery:
        replacement_suggestions = _build_replacement_suggestions(cities, interests, current_payload)
        trim_suggestion = _build_trim_suggestion(cities, current_payload)

    applied_weights = _normalize_weights(optimization_weights)
    candidates = [
        {
            "option_key": "current",
            "label": "Current route",
            "order": cities[:],
            "path": current_payload["valid_path"],
            "arcs": current_payload["arcs"],
            "total_distance_km": current_payload["total_distance_km"],
            "total_travel_time_hrs": current_payload["total_travel_time_hrs"],
            "travel_percentage": route_state["travel_percentage"],
            "interest_score": _interest_coverage_score(cities, interests),
        },
        {
            "option_key": "reorder",
            "label": "Reordered route",
            "order": optimized_order,
            "path": optimized_payload["valid_path"],
            "arcs": optimized_payload["arcs"],
            "total_distance_km": optimized_payload["total_distance_km"],
            "total_travel_time_hrs": optimized_payload["total_travel_time_hrs"],
            "travel_percentage": optimized_state["travel_percentage"],
            "interest_score": _interest_coverage_score(optimized_order, interests),
        },
    ]

    if replacement_suggestions:
        first_swap = replacement_suggestions[0]
        candidates.append(
            {
                "option_key": "replacement",
                "label": "Nearby replacement route",
                "order": first_swap.get("suggested_order", cities[:]),
                "path": first_swap.get("suggested_path", []),
                "arcs": first_swap.get("suggested_arcs", []),
                "total_distance_km": first_swap.get("suggested_total_distance_km", current_payload["total_distance_km"]),
                "total_travel_time_hrs": first_swap.get("suggested_total_travel_time_hrs", current_payload["total_travel_time_hrs"]),
                "travel_percentage": _travel_percentage(
                    first_swap.get("suggested_total_travel_time_hrs", current_payload["total_travel_time_hrs"]),
                    total_days,
                ),
                "interest_score": _interest_coverage_score(first_swap.get("suggested_order", cities[:]), interests),
            }
        )

    if trim_suggestion:
        candidates.append(
            {
                "option_key": "trim",
                "label": "Trimmed route",
                "order": trim_suggestion.get("suggested_order", cities[:]),
                "path": trim_suggestion.get("suggested_path", []),
                "arcs": trim_suggestion.get("suggested_arcs", []),
                "total_distance_km": trim_suggestion.get("suggested_total_distance_km", current_payload["total_distance_km"]),
                "total_travel_time_hrs": trim_suggestion.get("suggested_total_travel_time_hrs", current_payload["total_travel_time_hrs"]),
                "travel_percentage": _travel_percentage(
                    trim_suggestion.get("suggested_total_travel_time_hrs", current_payload["total_travel_time_hrs"]),
                    total_days,
                ),
                "interest_score": _interest_coverage_score(trim_suggestion.get("suggested_order", cities[:]), interests),
            }
        )

    for candidate in candidates:
        candidate["time_metric"] = float(candidate["total_travel_time_hrs"])
        candidate["fatigue_metric"] = float(candidate["travel_percentage"])
        candidate["cost_metric"] = _transport_cost_proxy(
            int(candidate["total_distance_km"]),
            budget_per_day,
            total_days,
        )
        candidate["interest_metric"] = float(candidate["interest_score"])

    ranked_candidates = _rank_route_candidates(candidates, applied_weights)
    recommended_option = ranked_candidates[0] if ranked_candidates else None

    what_if_scenarios = []
    if enable_what_if and len(cities) > 2:
        scenario_weights = [
            ("Time First", {"time": 0.60, "fatigue": 0.20, "cost": 0.15, "interests": 0.05}),
            ("Low Fatigue", {"time": 0.20, "fatigue": 0.60, "cost": 0.10, "interests": 0.10}),
            ("Budget Friendly", {"time": 0.20, "fatigue": 0.15, "cost": 0.55, "interests": 0.10}),
            ("Interest Heavy", {"time": 0.15, "fatigue": 0.20, "cost": 0.10, "interests": 0.55}),
        ]
        for scenario_name, scenario_weight in scenario_weights:
            scenario_ranked = _rank_route_candidates(candidates, _normalize_weights(scenario_weight))
            if not scenario_ranked:
                continue
            best = scenario_ranked[0]
            what_if_scenarios.append(
                {
                    "scenario": scenario_name,
                    "weights": _normalize_weights(scenario_weight),
                    "recommended_option": best.get("label"),
                    "order": best.get("order", []),
                    "total_distance_km": best.get("total_distance_km", 0),
                    "total_travel_time_hrs": best.get("total_travel_time_hrs", 0),
                    "objective_score": best.get("objective_score", 0),
                }
            )

    return {
        "is_valid": len(current_payload["missing_cities"]) == 0,
        "missing_cities": current_payload["missing_cities"],
        "current_order": cities[:],
        "total_distance_km": current_payload["total_distance_km"],
        "total_travel_time_hrs": current_payload["total_travel_time_hrs"],
        "travel_percentage": route_state["travel_percentage"],
        "burnout_risk": route_state["burnout_risk"],
        "warnings": route_state["warnings"],
        "illogical_jumps": current_payload["illogical_jumps"],
        "status": route_state["status"],
        "arcs": current_payload["arcs"],
        "valid_path": current_payload["valid_path"],
        "leg_details": current_payload["leg_details"],
        "optimized_order": optimized_order,
        "optimized_arcs": optimized_payload["arcs"],
        "optimized_path": optimized_payload["valid_path"],
        "optimized_total_distance_km": optimized_payload["total_distance_km"],
        "optimized_total_travel_time_hrs": optimized_payload["total_travel_time_hrs"],
        "optimized_travel_percentage": optimized_state["travel_percentage"],
        "distance_saved_km": distance_saved,
        "time_saved_hrs": round(time_saved, 1),
        "travel_percentage_reduction": max(
            0.0,
            route_state["travel_percentage"] - optimized_state["travel_percentage"],
        ),
        "replacement_suggestions": replacement_suggestions,
        "trim_suggestion": trim_suggestion,
        "optimization_weights_applied": applied_weights,
        "ranked_route_options": ranked_candidates,
        "recommended_option": recommended_option,
        "what_if_scenarios": what_if_scenarios,
    }
