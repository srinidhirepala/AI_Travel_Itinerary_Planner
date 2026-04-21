"""
Unit tests for route intelligence module.

Run with: pytest tests/test_route_intelligence.py
"""
import pytest
from src.utils.route.route_intelligence import (
    haversine_distance,
    get_city_coords,
    estimate_travel_time_hours,
    analyze_route,
)


class TestHaversineDistance:
    """Test haversine distance calculations."""
    
    def test_delhi_to_agra_distance(self):
        """Test known distance between Delhi and Agra."""
        delhi = get_city_coords("delhi")
        agra = get_city_coords("agra")
        
        distance = haversine_distance(delhi, agra)
        
        # Delhi to Agra is approximately 230 km
        assert 220 <= distance <= 240, f"Expected ~230km, got {distance}km"
    
    def test_same_city_distance(self):
        """Test distance from a city to itself is zero."""
        mumbai = get_city_coords("mumbai")
        
        distance = haversine_distance(mumbai, mumbai)
        
        assert distance == 0, "Distance to same city should be 0"
    
    def test_symmetric_distance(self):
        """Test that distance(A, B) == distance(B, A)."""
        bangalore = get_city_coords("bengaluru")
        chennai = get_city_coords("chennai")
        
        dist_ab = haversine_distance(bangalore, chennai)
        dist_ba = haversine_distance(chennai, bangalore)
        
        assert abs(dist_ab - dist_ba) < 0.01, "Distance should be symmetric"


class TestCityCoordinates:
    """Test city coordinate lookups."""
    
    def test_known_city_returns_coords(self):
        """Test that known cities return valid coordinates."""
        coords = get_city_coords("delhi")
        
        assert coords is not None
        assert len(coords) == 2
        assert -90 <= coords[0] <= 90  # Valid latitude
        assert -180 <= coords[1] <= 180  # Valid longitude
    
    def test_unknown_city_returns_none(self):
        """Test that unknown cities return None."""
        coords = get_city_coords("atlantis")
        
        assert coords is None
    
    def test_city_alias_resolution(self):
        """Test that city aliases are resolved correctly."""
        bangalore = get_city_coords("bangalore")
        bengaluru = get_city_coords("bengaluru")
        
        assert bangalore == bengaluru, "Aliases should resolve to same coords"


class TestTravelTimeEstimation:
    """Test travel time estimation logic."""
    
    def test_short_distance_time(self):
        """Test travel time for short distances (<100km)."""
        time = estimate_travel_time_hours(50)
        
        # 50km at 40km/h = 1.25 hours
        assert 1.0 <= time <= 1.5
    
    def test_medium_distance_time(self):
        """Test travel time for medium distances (100-500km)."""
        time = estimate_travel_time_hours(300)
        
        # 300km at 60km/h = 5 hours
        assert 4.5 <= time <= 5.5
    
    def test_long_distance_time(self):
        """Test travel time for long distances (>500km)."""
        time = estimate_travel_time_hours(1000)
        
        # Should include flight time overhead
        assert time > 5


class TestRouteAnalysis:
    """Test route analysis and optimization."""
    
    def test_single_city_route(self):
        """Test that single-city routes return valid analysis."""
        result = analyze_route(["delhi"], total_days=3)
        
        assert result["is_valid"] is True
        assert result["total_distance_km"] == 0
        assert result["burnout_risk"] == "LOW"
    
    def test_multi_city_route_analysis(self):
        """Test multi-city route analysis."""
        cities = ["delhi", "agra", "jaipur"]
        result = analyze_route(cities, total_days=3)
        
        assert result["is_valid"] is True
        assert result["total_distance_km"] > 0
        assert "current_order" in result
        assert "optimized_order" in result
        assert len(result["leg_details"]) == 2  # 3 cities = 2 legs
    
    def test_high_burnout_detection(self):
        """Test that high burnout routes are flagged."""
        # Long route with few days = high burnout
        cities = ["delhi", "mumbai", "bangalore", "chennai"]
        result = analyze_route(cities, total_days=2)
        
        assert result["burnout_risk"] in ["HIGH", "MEDIUM"]
        assert len(result["warnings"]) > 0
    
    def test_optimization_reduces_distance(self):
        """Test that optimization reduces total distance."""
        cities = ["delhi", "jaipur", "agra"]  # Inefficient order
        result = analyze_route(cities, total_days=3)
        
        original_distance = result["total_distance_km"]
        optimized_distance = result["optimized_total_distance_km"]
        
        # Optimized should be <= original
        assert optimized_distance <= original_distance


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_city_list(self):
        """Test handling of empty city list."""
        result = analyze_route([], total_days=3)
        
        assert result["total_distance_km"] == 0
    
    def test_unknown_cities_handled(self):
        """Test that unknown cities don't crash the system."""
        cities = ["delhi", "atlantis", "narnia"]
        result = analyze_route(cities, total_days=3)
        
        # Should return partial results
        assert "missing_cities" in result
        assert len(result["missing_cities"]) == 2


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
