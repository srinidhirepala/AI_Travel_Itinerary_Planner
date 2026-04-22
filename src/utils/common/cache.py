"""
Simple caching layer for expensive operations.
Uses functools.lru_cache for in-memory caching.
"""
from functools import lru_cache
from typing import Dict, List, Any
import hashlib
import json


def _make_hashable(obj):
    """Convert lists/dicts to hashable tuples for caching."""
    if isinstance(obj, list):
        return tuple(_make_hashable(item) for item in obj)
    elif isinstance(obj, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in obj.items()))
    return obj


@lru_cache(maxsize=256)
def cached_route_analysis(
    cities_tuple: tuple,
    total_days: int,
    interests_tuple: tuple,
    weights_tuple: tuple,
    budget_per_day: int,
    enable_what_if: bool,
) -> Dict[str, Any]:
    """
    Cached wrapper for route analysis.
    Converts mutable args to immutable for caching.
    """
    from src.utils.route.route_intelligence import analyze_route
    
    cities = list(cities_tuple)
    interests = list(interests_tuple) if interests_tuple else None
    weights = dict(weights_tuple) if weights_tuple else None
    
    return analyze_route(
        cities=cities,
        total_days=total_days,
        interests=interests,
        optimization_weights=weights,
        budget_per_day=budget_per_day,
        enable_what_if=enable_what_if,
    )


def get_cached_route_analysis(
    cities: List[str],
    total_days: int,
    interests: List[str] = None,
    optimization_weights: Dict[str, float] = None,
    budget_per_day: int = None,
    enable_what_if: bool = True,
) -> Dict[str, Any]:
    """
    Public interface for cached route analysis.
    Converts mutable types to hashable tuples.
    """
    cities_tuple = tuple(cities)
    interests_tuple = tuple(sorted(interests)) if interests else ()
    weights_tuple = tuple(sorted(optimization_weights.items())) if optimization_weights else ()
    
    return cached_route_analysis(
        cities_tuple=cities_tuple,
        total_days=total_days,
        interests_tuple=interests_tuple,
        weights_tuple=weights_tuple,
        budget_per_day=budget_per_day or 0,
        enable_what_if=enable_what_if,
    )


@lru_cache(maxsize=128)
def cached_weekend_getaways(
    home_city: str,
    interests_tuple: tuple,
    limit: int,
) -> List[Dict[str, Any]]:
    """Cached wrapper for weekend getaways."""
    from src.utils.recommendations.weekend_getaways import get_weekend_getaways
    
    interests = list(interests_tuple) if interests_tuple else None
    return get_weekend_getaways(home_city, interests, limit)


def get_cached_weekend_getaways(
    home_city: str,
    interests: List[str] = None,
    limit: int = 4,
) -> List[Dict[str, Any]]:
    """Public interface for cached weekend getaways."""
    interests_tuple = tuple(sorted(interests)) if interests else ()
    return cached_weekend_getaways(home_city, interests_tuple, limit)


def get_cache_stats() -> Dict[str, Any]:
    """Return cache statistics for monitoring."""
    return {
        "route_analysis": {
            "hits": cached_route_analysis.cache_info().hits,
            "misses": cached_route_analysis.cache_info().misses,
            "size": cached_route_analysis.cache_info().currsize,
            "maxsize": cached_route_analysis.cache_info().maxsize,
        },
        "weekend_getaways": {
            "hits": cached_weekend_getaways.cache_info().hits,
            "misses": cached_weekend_getaways.cache_info().misses,
            "size": cached_weekend_getaways.cache_info().currsize,
            "maxsize": cached_weekend_getaways.cache_info().maxsize,
        },
    }


def clear_all_caches():
    """Clear all caches (useful for testing or manual refresh)."""
    cached_route_analysis.cache_clear()
    cached_weekend_getaways.cache_clear()
