"""
Rate limiting and quota management.
"""
import time
import logging
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, user_id: str) -> bool:
        """
        Check if user can make a request.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if allowed, False if rate limited
        """
        now = time.time()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Remove old requests outside time window
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.time_window
        ]
        
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(now)
            return True
        
        logger.warning(f"Rate limit exceeded for user {user_id}")
        return False
    
    def get_reset_time(self, user_id: str) -> float:
        """Get seconds until next request allowed."""
        if user_id not in self.requests or not self.requests[user_id]:
            return 0
        
        oldest_request = min(self.requests[user_id])
        reset_time = oldest_request + self.time_window
        seconds_until_reset = max(0, reset_time - time.time())
        
        return seconds_until_reset


# Global rate limiter instances
itinerary_limiter = RateLimiter(max_requests=5, time_window=300)  # 5 per 5 min
profile_limiter = RateLimiter(max_requests=20, time_window=60)    # 20 per min
