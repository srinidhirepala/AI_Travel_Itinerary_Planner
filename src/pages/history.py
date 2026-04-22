"""
History Page - Itinerary history and viewing.

This module handles:
- Displaying list of saved itineraries
- Viewing individual itinerary details
- Deleting itineraries
"""
import streamlit as st
from typing import Dict, Any

from src.utils.database.db import get_itineraries, get_itinerary_data, delete_itinerary
from src.utils.common.constants import FOOD_ICONS


def render_history_page(user: dict):
    """
    Render the itinerary history page.
    
    Args:
        user: User dict with id, email, name, picture
    """
    st.markdown("""
    <div class="page-hero">
      <div class="eyebrow">✦ Saved Plans</div>
      <h1>My Itineraries</h1>
      <p>Every trip you've planned, saved automatically with your food preferences.</p>
    </div>""", unsafe_allow_html=True)
    
    itins = get_itineraries(user["id"])  # Newest first
    
    if not itins:
        render_empty_state()
        return
    
    # Check if viewing specific itinerary
    viewing_id = st.session_state.get("viewing_itin_id")
    
    if viewing_id:
        render_itinerary_detail(viewing_id, itins)
    else:
        render_itinerary_list(itins)


def render_empty_state():
    """Render empty state when no itineraries exist."""
    st.markdown("""
    <div style='text-align:center;padding:3rem 0'>
      <div style='font-size:3rem'>📭</div>
      <p style='font-family:var(--serif);font-size:1.3rem;margin:0.5rem 0;color:var(--text)'>
        No itineraries yet
      </p>
      <p style='color:var(--muted)'>Plan a trip and it'll appear here automatically.</p>
    </div>""", unsafe_allow_html=True)


def render_itinerary_list(itins: list):
    """Render list of itineraries."""
    st.markdown("""
    <div style='color: #7a6f69; font-size: 0.9rem; margin-bottom: 1.5rem;'>
    ⏱️ <strong>Newest itineraries first</strong> — Click any to view full details
    </div>""", unsafe_allow_html=True)
    
    for itin in itins:
        food_saved = itin.get("food_pref", "—")
        food_icon = FOOD_ICONS.get(food_saved, "🍽️")
        
        c1, c2 = st.columns([6, 1])
        with c1:
            label = (
                f"📍 {itin['destination']} · {itin['days']} days · "
                f"₹{itin['budget']:,}/day · {food_icon} {food_saved} · "
                f"{itin['created_at'][:10]}"
            )
            if st.button(label, key=f"view_{itin['id']}", use_container_width=True):
                st.session_state.viewing_itin_id = itin["id"]
                st.rerun()
        with c2:
            if st.button("🗑️", key=f"del_{itin['id']}", help="Delete"):
                delete_itinerary(itin["id"])
                st.rerun()


def render_itinerary_detail(viewing_id: int, itins: list):
    """Render detailed view of a single itinerary."""
    itin_data = get_itinerary_data(viewing_id)
    current_meta = next((i for i in itins if i["id"] == viewing_id), None)
    
    if st.button("← Back to all itineraries"):
        st.session_state.viewing_itin_id = None
        st.rerun()
    
    if not itin_data or not current_meta:
        st.error("Itinerary not found.")
        return
    
    # Header
    food_saved = current_meta.get("food_pref", "—")
    st.markdown(f"### {current_meta['destination']} — {current_meta['days']} days")
    st.markdown(
        f"<p style='color:var(--muted)'>{current_meta['created_at'][:10]} &nbsp;·&nbsp; "
        f"{food_saved} &nbsp;·&nbsp; ₹{current_meta['budget']:,}/day</p>",
        unsafe_allow_html=True,
    )
    
    # Tabs for days + budget
    itin_days = itin_data.get("days", [])
    n = len(itin_days)
    tabs = st.tabs([f"Day {d['day_number']}" for d in itin_days] + ["💰 Budget"])
    
    # Day tabs
    for idx, day in enumerate(itin_days):
        with tabs[idx]:
            render_day_detail(day)
    
    # Budget tab
    with tabs[n]:
        render_budget_breakdown(itin_data.get("budget_breakdown", {}))


def render_day_detail(day: Dict[str, Any]):
    """Render a single day's details."""
    st.markdown(f"### {day.get('title', '')}")
    
    # Food highlights
    food_highlights = day.get("food_highlights", [])
    if food_highlights:
        st.markdown(
            f'<div class="food-highlight-bar">🍴 {" · ".join(food_highlights[:3])}</div>',
            unsafe_allow_html=True,
        )
    
    # Schedule
    for item in day.get("schedule", []):
        cost = f"₹{item['cost_inr']}" if item.get("cost_inr", 0) > 0 else "Free"
        food_html = (
            f"<div class='meta'>🍴 {item['food_item']}</div>"
            if item.get("food_item") else ""
        )
        st.markdown(f"""
        <div class="activity-card">
          <div class="time">{item.get('time', '')}</div>
          <div class="act">{item.get('activity', '')}</div>
          <div class="meta">📍 {item.get('location', '')} · {cost}</div>
          {food_html}
          <div class="meta" style="color:#7880a0">{item.get('notes', '')}</div>
        </div>""", unsafe_allow_html=True)
    
    # Meals
    meals = day.get("meals", {})
    if meals:
        st.markdown(
            '<div class="section-header"><span>Meals</span><div class="line"></div></div>',
            unsafe_allow_html=True,
        )
        mc1, mc2, mc3 = st.columns(3)
        for col, (label, icon, key) in zip(
            [mc1, mc2, mc3],
            [("Breakfast", "🌅", "breakfast"),
             ("Lunch", "☀️", "lunch"),
             ("Dinner", "🌙", "dinner")],
        ):
            m = meals.get(key, {})
            with col:
                st.markdown(f"""
                <div class="meal-card">
                  <div class="meal-label">{icon} {label}</div>
                  <div class="place">{m.get('place', '—')}</div>
                  <div class="dish">{m.get('dish', '')}</div>
                  <div class="cost">₹{m.get('cost_inr', '—')}</div>
                </div>""", unsafe_allow_html=True)


def render_budget_breakdown(bd: Dict[str, Any]):
    """Render budget breakdown."""
    if bd:
        for k, v in bd.items():
            cls = "budget-row total" if k == "grand_total" else "budget-row"
            if v:
                st.markdown(
                    f'<div class="{cls}"><span class="blabel">'
                    f'{k.replace("_", " ").title()}</span>'
                    f'<span class="bval">₹{v:,}</span></div>',
                    unsafe_allow_html=True,
                )
