"""
Profile Page - User profile and preferences management.

This module handles:
- User profile display
- Travel preferences editing
- Liked places management
- User statistics dashboard
"""
import streamlit as st
from typing import Dict, Any

from src.utils.database.db import (
    get_profile,
    save_profile,
    get_liked_places,
    add_liked_place,
    delete_liked_place,
)
from src.utils.common.metrics import get_user_stats
from src.utils.common.constants import FOOD_PREFERENCES, ALL_INTERESTS, TRAVEL_STYLES


def render_profile_page(user: dict):
    """
    Render the user profile page.
    
    Args:
        user: User dict with id, email, name, picture
    """
    st.markdown("""
    <div class="page-hero">
      <div class="eyebrow">✦ Account</div>
      <h1>Your Profile</h1>
      <p>Preferences saved here pre-fill every itinerary and personalise your recommendations.</p>
    </div>""", unsafe_allow_html=True)
    
    prof = get_profile(user["id"])
    liked = get_liked_places(user["id"])
    user_stats = get_user_stats(user["id"])
    
    # Display user statistics
    render_user_stats(user_stats)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Two-column layout
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        render_preferences_form(user["id"], prof)
    
    with col_right:
        render_liked_places(user["id"], liked)


def render_user_stats(stats: Dict[str, Any]):
    """Render user statistics dashboard."""
    st.markdown("### 📊 Your Travel Stats")
    stat_cols = st.columns(4)
    
    with stat_cols[0]:
        st.metric("Itineraries Created", stats["total_itineraries"])
    with stat_cols[1]:
        st.metric("Days Planned", stats["total_days_planned"])
    with stat_cols[2]:
        st.metric("Destinations", stats["unique_destinations"])
    with stat_cols[3]:
        st.metric("Liked Places", stats["liked_places"])


def render_preferences_form(user_id: str, prof: Dict[str, Any]):
    """Render travel preferences form."""
    st.markdown("#### Travel Preferences")
    
    with st.form("profile_form"):
        # Food preference
        current_food = prof.get("food_pref", "Vegetarian")
        food_idx = FOOD_PREFERENCES.index(current_food) if current_food in FOOD_PREFERENCES else 0
        new_food = st.selectbox("🍽️ Default food preference", FOOD_PREFERENCES, index=food_idx)
        
        # Interests
        new_interests = st.multiselect(
            "🎯 Interests",
            ALL_INTERESTS,
            default=[i for i in prof.get("interests", []) if i in ALL_INTERESTS],
        )
        
        # Home city
        new_home = st.text_input(
            "🏠 Home city (for Weekend Getaway)",
            value=prof.get("home_city", ""),
            placeholder="e.g. Hyderabad",
        )
        
        # Travel style
        new_style = st.selectbox(
            "🧳 Travel style",
            TRAVEL_STYLES,
            index=TRAVEL_STYLES.index(prof.get("travel_style", "Explorer"))
            if prof.get("travel_style", "Explorer") in TRAVEL_STYLES else 0,
        )
        
        # Budget
        new_budget = st.number_input(
            "💰 Default daily budget (₹)",
            min_value=500,
            max_value=50000,
            value=prof.get("budget_default", 2000),
            step=500,
        )
        
        # Submit
        if st.form_submit_button("💾 Save Preferences", use_container_width=True):
            save_profile(user_id, new_food, new_interests, new_home, new_style, new_budget)
            st.success("✅ Preferences saved! They'll apply to your next itinerary.")
            st.rerun()


def render_liked_places(user_id: str, liked: list):
    """Render liked places section."""
    st.markdown("#### Liked Places")
    
    if liked:
        for place in liked:
            pcol1, pcol2 = st.columns([5, 1])
            with pcol1:
                icon = "🏙️" if place.get("place_type") == "city" else "📍"
                st.markdown(f"""
                <div class="place-pill">
                  {icon} <strong>{place['place_name']}</strong>
                  &nbsp;<span style='color:var(--muted)'>{place.get('country', '')}</span>
                </div>""", unsafe_allow_html=True)
            with pcol2:
                if st.button("✕", key=f"del_{place['id']}", help="Remove"):
                    delete_liked_place(place["id"])
                    st.rerun()
    else:
        st.markdown("<p style='color:var(--muted);font-size:0.9rem'>No liked places yet.</p>",
                    unsafe_allow_html=True)
    
    # Add place form
    with st.expander("Add a place"):
        with st.form("add_place"):
            st.markdown("**Place name**")
            p_name = st.text_input(
                "Place name",
                placeholder="Jaipur or Hampi",
                label_visibility="collapsed",
            )
            st.markdown("**Type**")
            p_type = st.selectbox(
                "Type",
                ["city", "attraction", "restaurant"],
                label_visibility="collapsed",
            )
            st.markdown("**Country**")
            p_country = st.text_input(
                "Country",
                placeholder="India",
                label_visibility="collapsed",
            )
            st.markdown("**Notes**")
            p_notes = st.text_area(
                "Notes (optional)",
                height=60,
                label_visibility="collapsed",
                placeholder="Why do you like this place?",
            )
            if st.form_submit_button("Add", use_container_width=True):
                if p_name:
                    add_liked_place(user_id, p_name, p_type, p_country, p_notes)
                    st.success(f"Added {p_name}!")
                    st.rerun()
