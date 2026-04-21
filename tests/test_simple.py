"""
Simple test script to verify core functionality without pytest.
Run with: python test_simple.py
"""
import sys
sys.path.insert(0, '.')

from src.utils.route.route_intelligence import (
    haversine_distance,
    get_city_coords,
    estimate_travel_time_hours,
    analyze_route,
)

print("=" * 60)
print("WANDR - Simple Functionality Test")
print("=" * 60)

# Test 1: City Coordinates
print("\n[TEST 1] City Coordinate Lookup")
delhi = get_city_coords("delhi")
agra = get_city_coords("agra")
print(f"OK Delhi coordinates: {delhi}")
print(f"OK Agra coordinates: {agra}")

# Test 2: Haversine Distance
print("\n[TEST 2] Haversine Distance Calculation")
distance = haversine_distance(delhi, agra)
print(f"OK Delhi to Agra: {distance:.2f} km")
assert 170 <= distance <= 190, f"Expected ~178km, got {distance}km"
print("OK Distance is within expected range (170-190 km)")

# Test 3: Travel Time Estimation
print("\n[TEST 3] Travel Time Estimation")
time = estimate_travel_time_hours(distance)
print(f"OK Estimated travel time: {time:.2f} hours")
assert 2 <= time <= 5, f"Expected 2-5 hours, got {time}"
print("OK Travel time is reasonable")

# Test 4: Route Analysis (Single City)
print("\n[TEST 4] Single City Route Analysis")
result = analyze_route(["delhi"], total_days=3)
print(f"OK Valid route: {result['is_valid']}")
print(f"OK Total distance: {result['total_distance_km']} km")
print(f"OK Burnout risk: {result['burnout_risk']}")
assert result["total_distance_km"] == 0, "Single city should have 0 distance"
assert result["burnout_risk"] == "LOW", "Single city should have LOW burnout"
print("OK Single city analysis passed")

# Test 5: Route Analysis (Multi-City)
print("\n[TEST 5] Multi-City Route Analysis")
cities = ["delhi", "agra", "jaipur"]
result = analyze_route(cities, total_days=3)
print(f"OK Valid route: {result['is_valid']}")
print(f"OK Total distance: {result['total_distance_km']} km")
print(f"OK Total travel time: {result['total_travel_time_hrs']} hours")
print(f"OK Burnout risk: {result['burnout_risk']}")
print(f"OK Current order: {' -> '.join(result['current_order'])}")
print(f"OK Optimized order: {' -> '.join(result['optimized_order'])}")
print(f"OK Distance saved: {result['distance_saved_km']} km")
assert result["total_distance_km"] > 0, "Multi-city should have distance"
assert len(result["leg_details"]) == 2, "3 cities should have 2 legs"
print("OK Multi-city analysis passed")

# Test 6: Caching
print("\n[TEST 6] Caching Layer")
from src.utils.common.cache import get_cached_route_analysis, get_cache_stats

# First call (uncached)
result1 = get_cached_route_analysis(cities, 3, ["Culture", "Food"])
stats1 = get_cache_stats()
print(f"OK Cache misses: {stats1['route_analysis']['misses']}")

# Second call (cached)
result2 = get_cached_route_analysis(cities, 3, ["Culture", "Food"])
stats2 = get_cache_stats()
print(f"OK Cache hits: {stats2['route_analysis']['hits']}")
assert stats2['route_analysis']['hits'] > stats1['route_analysis']['hits'], "Cache should have hit"
print("OK Caching is working")

# Test 7: Weekend Getaways
print("\n[TEST 7] Weekend Getaway Recommendations")
from src.utils.common.cache import get_cached_weekend_getaways

getaways = get_cached_weekend_getaways("hyderabad", ["Adventure", "Nature"], limit=3)
print(f"OK Found {len(getaways)} weekend options")
if getaways:
    for idx, option in enumerate(getaways, 1):
        print(f"  {idx}. {option['name']} - {option['distance_km']} km - {option['vibe']}")
print("OK Weekend getaway recommendations working")

# Test 8: Input Validation
print("\n[TEST 8] Input Validation")
from src.utils.common.validation import validate_trip_params, ValidationError

try:
    validated = validate_trip_params(
        destination="Delhi, Agra",
        days=3,
        budget=2000,
        food_pref="Vegetarian",
        interests=["Culture", "Food"]
    )
    print(f"OK Valid input accepted: {validated['destination']}")
except ValidationError as e:
    print(f"X Validation failed: {e}")
    sys.exit(1)

try:
    validate_trip_params(
        destination="",
        days=3,
        budget=2000,
        food_pref="Vegetarian",
        interests=["Culture"]
    )
    print("X Empty destination should have failed")
    sys.exit(1)
except ValidationError:
    print("OK Empty destination correctly rejected")

print("\n" + "=" * 60)
print("SUCCESS: ALL TESTS PASSED!")
print("=" * 60)
print("\nYour Wandr installation is working correctly!")
print("Ready to run: streamlit run app.py")
