"""
Constants used throughout the Wandr app.
"""

# Food preferences
FOOD_PREFERENCES = [
    "Vegetarian",
    "Non-Vegetarian",
    "Both (Veg & Non-Veg)",
    "Vegan",
    "Jain",
    "Halal",
]

# Travel interests
ALL_INTERESTS = [
    "Culture",
    "Food",
    "Adventure",
    "Nature",
    "Shopping",
    "Photography",
]

# Travel styles / paces
TRAVEL_STYLES = [
    "Explorer",
    "Foodie",
    "Cultural",
    "Relaxer",
    "Adventurer",
    "Shopaholic",
]

# Mood options for recommendation engine
MOOD_OPTIONS = [
    "Relax",
    "Adventure",
    "Devotional",
    "Culture",
    "Food",
]

# Default budget in INR per day
DEFAULT_BUDGET = 2000

# Required environment variables
REQUIRED_ENV_VARS = ["GROQ_API_KEY", "COOKIE_SECRET"]

# Food preference icons mapping
FOOD_ICONS = {
    "Vegetarian": "🟢",
    "Non-Vegetarian": "🔴",
    "Both (Veg & Non-Veg)": "🔵",
    "Vegan": "🌿",
    "Jain": "✨",
    "Halal": "☪️",
}
