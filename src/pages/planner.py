"""
Planner Page - Trip planning and route optimization.

This module handles:
- Multi-city trip planning
- Weekend getaway planning
- Route analysis and optimization
- Itinerary generation via LLM
"""
import streamlit as st
import html
from typing import Dict, Any, List, Tuple

from src.utils.common.validation import validate_trip_params, ValidationError
from src.utils.common.cache import get_cached_route_analysis, get_cached_weekend_getaways
from src.utils.llm.llm_handler import LLMHandler
from src.utils.llm.prompt_builder import build_itinerary_prompt
from src.utils.database.db import save_itinerary, get_profile
from src.utils.common.error_handler import ErrorHandler
from src.utils.common.rate_limiter import itinerary_limiter
from src.utils.common.constants import FOOD_PREFERENCES, ALL_INTERESTS


def render_planner_page(user: dict, is_weekend: bool = False):
    """
    Render the trip planner page.
    
    Args:
        user: User dict with id, email, name, picture
        is_weekend: If True, render weekend getaway mode
    """
    # Page header
    if is_weekend:
        st.markdown("""
        <div class="page-hero hero-clean">
          <div class="hero-pill">Weekend Getaway</div>
          <h1>Slip away for a lighter, lovelier weekend</h1>
          <p>Choose your city and get a quick reset with easier travel, better pacing, and food stops that actually fit the mood.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="page-hero hero-clean">
          <div class="hero-pill">Plan a Trip</div>
          <h1>Shape a trip that feels exciting before it even begins</h1>
          <p>Map the route, tune the budget, match the food, and turn a list of places into a trip that flows naturally.</p>
        </div>""", unsafe_allow_html=True)
    
    prof = get_profile(user["id"])
    
    # Render form and get inputs
    form_data = render_planner_form(prof, is_weekend)
    
    # Handle generation
    if form_data["generate_clicked"]:
        handle_trip_generation(user, form_data, prof, is_weekend)


def render_planner_form(prof: dict, is_weekend: bool) -> Dict[str, Any]:
    """
    Render the planner input form.
    
    Returns:
        Dict with form data including destination, days, budget, etc.
    """
    form_data = {
        "destination": "",
        "start_city": "",
        "days": 3,
        "budget": prof.get("budget_default", 2000),
        "food_pref": prof.get("food_pref", "Vegetarian"),
        "interests": prof.get("interests", ["Culture", "Food"]),
        "hometown": "",
        "optimizer_weights": None,
        "enable_what_if": False,
        "generate_clicked": False,
    }
    
    if is_weekend:
        # Weekend mode: simpler form
        top_fields = st.columns([1.6, 0.8, 0.9], gap="medium")
        with top_fields[0]:
            form_data["hometown"] = st.text_input(
                "Your city",
                value=prof.get("home_city", ""),
                placeholder="e.g. Hyderabad",
                key="wk_hometown",
            )
        with top_fields[1]:
            form_data["days"] = st.number_input("Days", min_value=1, max_value=2, value=2, key="wk_days")
        with top_fields[2]:
            form_data["budget"] = st.number_input(
                "Budget/day (₹)",
                min_value=500,
                max_value=50000,
                value=prof.get("budget_default", 2000),
                step=500,
                key="wk_budget",
            )
        
        # Weekend getaway options
        weekend_options = get_cached_weekend_getaways(form_data["hometown"], form_data["interests"] or [], limit=4)
        
        if form_data["hometown"].strip() and weekend_options:
            st.markdown(
                '<div class="sidebar-section-label">Nearby weekend matches</div>',
                unsafe_allow_html=True,
            )
            
            # Display options
            option_cols = st.columns(len(weekend_options), gap="medium")
            selected_weekend = st.session_state.get("wk_selected_getaway")
            
            for idx, option in enumerate(weekend_options):
                with option_cols[idx]:
                    is_selected = option["name"] == selected_weekend
                    card_class = "getaway-card selected" if is_selected else "getaway-card"
                    
                    st.markdown(f"""
                    <div class="{card_class}">
                      <div class="dest-name">{html.escape(option["name"])}</div>
                      <div class="route-metric-pill">{option["distance_km"]} km</div>
                      <div class="tag">{html.escape(option.get("vibe", "Weekend pick"))}</div>
                    </div>""", unsafe_allow_html=True)
                    
                    if st.button(
                        "Selected" if is_selected else f"Choose {option['name']}",
                        key=f"wk_choose_{idx}",
                        type="primary" if is_selected else "secondary",
                        use_container_width=True,
                    ):
                        st.session_state["wk_selected_getaway"] = option["name"]
                        st.rerun()
            
            form_data["destination"] = selected_weekend or ""
        
    else:
        # Full trip mode: multi-stop form
        top_fields = st.columns([1.5, 0.8, 0.9], gap="medium")
        with top_fields[0]:
            start_city = st.text_input(
                "Starting location",
                placeholder="e.g. Delhi",
                key="start_city",
            )
            form_data["start_city"] = start_city.strip()
        with top_fields[1]:
            form_data["days"] = st.number_input("Days", min_value=1, max_value=30, value=3, key="pl_days")
        with top_fields[2]:
            form_data["budget"] = st.number_input(
                "Budget/day (₹)",
                min_value=500,
                max_value=50000,
                value=prof.get("budget_default", 2000),
                step=500,
                key="pl_budget",
            )
        
        # Multi-stop management
        st.markdown('<div class="sidebar-section-label">Destinations / Stops</div>', unsafe_allow_html=True)
        stops = []
        dest_count = st.session_state.get("dest_count", 1)
        
        for i in range(dest_count):
            stop_val = st.text_input(f"Stop {i + 1}", key=f"stop_{i}", placeholder="e.g. Agra")
            if stop_val.strip():
                stops.append(stop_val.strip())
        
        manage_cols = st.columns([1, 1, 4], gap="small")
        with manage_cols[0]:
            if st.button("Add stop", key="add_stop", use_container_width=True):
                st.session_state.dest_count = dest_count + 1
                st.rerun()
        with manage_cols[1]:
            if dest_count > 1 and st.button("Remove", key="rm_stop", use_container_width=True):
                st.session_state.dest_count = dest_count - 1
                st.rerun()
        
        form_data["destination"] = ", ".join(stops)
        
        # Optimizer settings
        with st.expander("Multi-route optimizer", expanded=False):
            st.caption("Set priorities to rank route options by time, fatigue, transport cost proxy, and interest fit.")
            w_cols = st.columns(4, gap="small")
            with w_cols[0]:
                w_time = st.slider("Time", min_value=0, max_value=100, value=35, key="opt_w_time")
            with w_cols[1]:
                w_fatigue = st.slider("Fatigue", min_value=0, max_value=100, value=30, key="opt_w_fatigue")
            with w_cols[2]:
                w_cost = st.slider("Cost", min_value=0, max_value=100, value=20, key="opt_w_cost")
            with w_cols[3]:
                w_interests = st.slider("Interests", min_value=0, max_value=100, value=15, key="opt_w_interests")
            
            raw_total = w_time + w_fatigue + w_cost + w_interests
            if raw_total <= 0:
                raw_total = 1
            
            form_data["optimizer_weights"] = {
                "time": w_time / raw_total,
                "fatigue": w_fatigue / raw_total,
                "cost": w_cost / raw_total,
                "interests": w_interests / raw_total,
            }
            form_data["enable_what_if"] = st.checkbox(
                "Show what-if route simulations",
                value=True,
                key="opt_enable_what_if",
            )
    
    # Food and interests (common to both modes)
    pref_cols = st.columns([1.1, 1.9], gap="medium")
    saved_food = prof.get("food_pref", "Vegetarian")
    food_idx = FOOD_PREFERENCES.index(saved_food) if saved_food in FOOD_PREFERENCES else 0
    
    with pref_cols[0]:
        form_data["food_pref"] = st.selectbox(
            "Food preference",
            FOOD_PREFERENCES,
            index=food_idx,
            key="food_pref_sel",
        )
    with pref_cols[1]:
        saved_interests = prof.get("interests", [])
        form_data["interests"] = st.multiselect(
            "Interests",
            ALL_INTERESTS,
            default=[i for i in saved_interests if i in ALL_INTERESTS] or ["Culture", "Food"],
            key="interests_sel",
        )
    
    # Generate button
    form_data["generate_clicked"] = st.button(
        "Plan Your Trip" if not is_weekend else "Find My Weekend Trip",
        type="primary",
        use_container_width=True,
        key="generate_trip_plan",
    )
    
    return form_data


def handle_trip_generation(user: dict, form_data: dict, prof: dict, is_weekend: bool):
    """
    Handle trip generation logic.
    
    Args:
        user: User dict
        form_data: Form inputs from render_planner_form
        prof: User profile
        is_weekend: Weekend mode flag
    """
    dest_to_use = form_data["destination"].strip()
    
    # Validation
    if is_weekend and not form_data["hometown"].strip():
        st.error("Please enter your home city first.")
        return

    if not is_weekend and not form_data["start_city"].strip():
        st.error("Please enter your starting location.")
        return
    
    if not dest_to_use:
        if is_weekend:
            st.error("Please enter a destination or choose a weekend getaway option.")
        else:
            st.error("Please enter at least one destination stop for sightseeing.")
        return
    
    # Rate limiting
    if not itinerary_limiter.is_allowed(user["id"]):
        reset = itinerary_limiter.get_reset_time(user["id"])
        st.warning(f"Rate limit reached. Try again in {int(reset)}s.")
        return
    
    # Progressive status
    status_text = st.empty()
    
    try:
        status_text.info("📋 Validating your trip details...")
        
        validated = validate_trip_params(
            destination=dest_to_use,
            days=form_data["days"],
            budget=form_data["budget"],
            food_pref=form_data["food_pref"],
            interests=form_data["interests"] or [],
        )
        
        # Route analysis: include origin -> first stop leg for planner mode
        route_analysis = None
        cities = [c.strip() for c in dest_to_use.split(",") if c.strip()]
        analysis_cities = cities
        if not is_weekend and form_data["start_city"].strip():
            start = form_data["start_city"].strip()
            if not cities or cities[0].lower() != start.lower():
                analysis_cities = [start] + cities
        
        if len(analysis_cities) > 1:
            status_text.info("🗺️ Analyzing your route...")
            route_analysis = get_cached_route_analysis(
                analysis_cities,
                validated["days"],
                interests=validated["interests"],
                optimization_weights=form_data["optimizer_weights"],
                budget_per_day=validated["budget"],
                enable_what_if=form_data["enable_what_if"],
            )
        
        # Generate itinerary
        status_text.info("🤖 Generating your personalized itinerary...")
        
        travel_style = prof.get("travel_style", "Explorer")
        prompt = build_itinerary_prompt(
            destination=validated["destination"],
            days=validated["days"],
            budget=validated["budget"],
            food_pref=validated["food_pref"],
            interests=validated["interests"],
            travel_style=travel_style,
            route_analysis=route_analysis,
            hometown=form_data["hometown"].strip() if is_weekend else form_data["start_city"].strip(),
            is_weekend_getaway=is_weekend,
        )
        
        result = LLMHandler().generate_itinerary(prompt)
        st.session_state.itinerary = result
        st.session_state.last_inputs = {
            "destination": validated["destination"],
            "start_city": form_data["hometown"].strip() if is_weekend else form_data["start_city"].strip(),
            "days": validated["days"],
            "budget": validated["budget"],
            "food_pref": validated["food_pref"],
            "interests": sorted(validated["interests"]),
            "is_weekend": is_weekend,
            "home_city": form_data["hometown"].strip() if is_weekend else "",
        }
        
        # Save to database
        status_text.info("💾 Saving your itinerary...")
        save_itinerary(
            user_id=user["id"],
            destination=validated["destination"],
            days=validated["days"],
            budget=validated["budget"],
            food_pref=validated["food_pref"],
            interests=validated["interests"],
            data=result,
        )
        
        status_text.empty()
        st.success("✅ Itinerary ready — saved to your history!")
        
    except ValidationError as e:
        ErrorHandler.handle_validation_error(e)
    except ValueError as e:
        st.error(f"⚠️ {e}")
    except Exception as e:
        ErrorHandler.handle_api_error(e)
