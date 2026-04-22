"""
Geocoding service using OpenStreetMap Nominatim API.
Provides international city coordinate lookup with caching.
"""
import requests
import time
import os
from pathlib import Path
from typing import Tuple, Optional
from functools import lru_cache
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
for _env_path in (_PROJECT_ROOT / "config" / ".env", _PROJECT_ROOT / ".env"):
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path, override=True)
        break

# Nominatim API endpoint (free, no API key required)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Geoapify geocoding endpoint used as a dynamic fallback when Nominatim
# cannot resolve a city name or a typo.
GEOAPIFY_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"

# User agent required by Nominatim terms of service
USER_AGENT = "Wandr-Travel-Planner/1.0"

# Rate limiting: Max 1 request per second (Nominatim policy)
_last_request_time = 0
_min_request_interval = 1.0  # seconds


@lru_cache(maxsize=500)
def geocode_city(city_name: str, country: str = None) -> Optional[Tuple[float, float]]:
    """
    Get coordinates for a city using OpenStreetMap Nominatim API.
    
    Args:
        city_name: Name of the city (e.g., "Paris", "Tokyo")
        country: Optional country name for disambiguation (e.g., "France", "Japan")
    
    Returns:
        Tuple of (latitude, longitude) or None if not found
    
    Example:
        >>> geocode_city("Paris", "France")
        (48.8566, 2.3522)
    """
    global _last_request_time
    
    # Rate limiting (Nominatim requires 1 req/sec max)
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    if time_since_last < _min_request_interval:
        time.sleep(_min_request_interval - time_since_last)
    
    # Build query
    query = city_name
    if country:
        query = f"{city_name}, {country}"
    
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    
    headers = {
        "User-Agent": USER_AGENT
    }
    
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=5)
        _last_request_time = time.time()
        
        if response.status_code == 200:
            results = response.json()
            if results:
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
                logger.info(f"Geocoded {city_name}: ({lat}, {lon})")
                return (lat, lon)
        
        logger.warning(f"Could not geocode {city_name}: No results")
        return None
        
    except Exception as e:
        logger.error(f"Geocoding error for {city_name}: {e}")
        return _geocode_city_with_geoapify(city_name, country)


def _geocode_city_with_geoapify(city_name: str, country: str = None) -> Optional[Tuple[float, float]]:
    """Fallback geocoding via Geoapify when Nominatim does not resolve a city."""
    api_key = os.getenv("GEOAPIFY_API_KEY", "").strip()
    if not api_key:
        return None

    params = {
        "text": city_name,
        "type": "city",
        "limit": 5,
        "format": "json",
        "apiKey": api_key,
    }
    if country:
        params["country"] = country
    else:
        params["filter"] = "countrycode:in"

    try:
        response = requests.get(GEOAPIFY_GEOCODE_URL, params=params, timeout=8)
        response.raise_for_status()
        payload = response.json()
    except Exception as e:
        logger.error(f"Geoapify geocoding error for {city_name}: {e}")
        return None

    results = payload.get("results", []) if isinstance(payload, dict) else []
    if not isinstance(results, list) or not results:
        return None

    try:
        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
        logger.info(f"Geoapify geocoded {city_name}: ({lat}, {lon})")
        return (lat, lon)
    except Exception:
        return None


def get_city_coords_with_fallback(city_name: str) -> Optional[Tuple[float, float]]:
    """
    Get city coordinates with fallback strategy:
    1. Check database cache (previously geocoded cities)
    2. Fallback to Nominatim API (slow, but comprehensive)
    Note: hardcoded dict check is done in route_intelligence.get_city_coords before calling here.
    """
    from src.utils.database.db import get_cached_coordinates, cache_coordinates
    from src.utils.route.route_intelligence import _normalize_city_name

    normalized = _normalize_city_name(city_name)

    # Strategy 1: Check database cache (fast)
    cached = get_cached_coordinates(normalized)
    if cached:
        return cached

    # Strategy 2: Geocode via API (~1 second)
    coords = geocode_city(city_name)
    if coords:
        cache_coordinates(normalized, coords[0], coords[1])
        return coords

    geoapify_coords = _geocode_city_with_geoapify(city_name)
    if geoapify_coords:
        cache_coordinates(normalized, geoapify_coords[0], geoapify_coords[1])
        return geoapify_coords

    return None


def batch_geocode_cities(cities: list[str]) -> dict[str, Optional[Tuple[float, float]]]:
    """
    Geocode multiple cities efficiently.
    
    Args:
        cities: List of city names
    
    Returns:
        Dict mapping city name to coordinates
    """
    results = {}
    for city in cities:
        results[city] = get_city_coords_with_fallback(city)
        # Respect rate limit
        time.sleep(_min_request_interval)
    return results


# Database caching functions (add to utils/db.py)
def add_to_db_py():
    """
    Add these functions to utils/db.py:
    
    ```python
    def get_cached_coordinates(city_name: str) -> Optional[Tuple[float, float]]:
        with _conn() as conn:
            row = conn.execute(
                "SELECT latitude, longitude FROM city_coordinates WHERE city_name=?",
                (city_name,)
            ).fetchone()
            return (row["latitude"], row["longitude"]) if row else None
    
    def cache_coordinates(city_name: str, latitude: float, longitude: float):
        with _conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO city_coordinates (city_name, latitude, longitude) VALUES (?, ?, ?)",
                (city_name, latitude, longitude)
            )
    ```
    
    And add this table to init_db():
    
    ```sql
    CREATE TABLE IF NOT EXISTS city_coordinates (
        city_name TEXT PRIMARY KEY,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        cached_at TEXT DEFAULT (datetime('now'))
    );
    ```
    """
    pass
