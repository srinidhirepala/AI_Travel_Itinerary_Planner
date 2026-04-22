"""
Metrics and analytics for the travel planner.
Tracks usage statistics, popular destinations, and system health.
"""
from src.utils.database.db import _conn
from typing import Dict, Any


def get_total_itineraries(user_id: str = None) -> int:
    """Get total number of itineraries generated."""
    with _conn() as conn:
        if user_id:
            result = conn.execute(
                "SELECT COUNT(*) as count FROM itineraries WHERE user_id=?", (user_id,)
            ).fetchone()
        else:
            result = conn.execute("SELECT COUNT(*) as count FROM itineraries").fetchone()
        return result["count"] if result else 0


def get_unique_cities_count() -> int:
    """Get count of unique destinations planned."""
    with _conn() as conn:
        result = conn.execute(
            "SELECT COUNT(DISTINCT destination) as count FROM itineraries"
        ).fetchone()
        return result["count"] if result else 0


def get_avg_budget() -> float:
    """Get average daily budget across all itineraries."""
    with _conn() as conn:
        result = conn.execute(
            "SELECT AVG(budget) as avg_budget FROM itineraries"
        ).fetchone()
        return round(result["avg_budget"], 0) if result and result["avg_budget"] else 0


def get_popular_destinations(limit: int = 5) -> list:
    """Get most popular destinations."""
    with _conn() as conn:
        results = conn.execute(
            """
            SELECT destination, COUNT(*) as count 
            FROM itineraries 
            GROUP BY destination 
            ORDER BY count DESC 
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
        return [{"destination": r["destination"], "count": r["count"]} for r in results]


def get_popular_interests(limit: int = 5) -> list:
    """Get most popular interests across all users."""
    with _conn() as conn:
        results = conn.execute(
            "SELECT interests FROM profiles WHERE interests != '[]'"
        ).fetchall()
        
        interest_counts = {}
        for row in results:
            import json
            interests = json.loads(row["interests"])
            for interest in interests:
                interest_counts[interest] = interest_counts.get(interest, 0) + 1
        
        sorted_interests = sorted(interest_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"interest": k, "count": v} for k, v in sorted_interests[:limit]]


def get_user_stats(user_id: str) -> Dict[str, Any]:
    """Get statistics for a specific user."""
    with _conn() as conn:
        # Total itineraries
        total = conn.execute(
            "SELECT COUNT(*) as count FROM itineraries WHERE user_id=?", (user_id,)
        ).fetchone()
        
        # Total days traveled
        days = conn.execute(
            "SELECT SUM(days) as total_days FROM itineraries WHERE user_id=?", (user_id,)
        ).fetchone()
        
        # Unique destinations
        destinations = conn.execute(
            "SELECT COUNT(DISTINCT destination) as count FROM itineraries WHERE user_id=?", (user_id,)
        ).fetchone()
        
        # Liked places
        liked = conn.execute(
            "SELECT COUNT(*) as count FROM liked_places WHERE user_id=?", (user_id,)
        ).fetchone()
        
        return {
            "total_itineraries": total["count"] if total else 0,
            "total_days_planned": days["total_days"] if days and days["total_days"] else 0,
            "unique_destinations": destinations["count"] if destinations else 0,
            "liked_places": liked["count"] if liked else 0,
        }


def get_food_preference_distribution() -> Dict[str, int]:
    """Get distribution of food preferences across users."""
    with _conn() as conn:
        results = conn.execute(
            """
            SELECT food_pref, COUNT(*) as count 
            FROM profiles 
            GROUP BY food_pref
            """
        ).fetchall()
        return {r["food_pref"]: r["count"] for r in results}


def get_system_health() -> Dict[str, Any]:
    """Get overall system health metrics."""
    from src.utils.common.cache import get_cache_stats
    
    return {
        "total_users": get_total_users(),
        "total_itineraries": get_total_itineraries(),
        "unique_cities": get_unique_cities_count(),
        "avg_budget": get_avg_budget(),
        "cache_stats": get_cache_stats(),
    }


def get_total_users() -> int:
    """Get total number of registered users."""
    with _conn() as conn:
        result = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()
        return result["count"] if result else 0
