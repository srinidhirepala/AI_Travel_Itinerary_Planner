"""
Wandr — AI Travel Itinerary Planner
"""
import streamlit as st
import os
import html
from pathlib import Path
from dotenv import load_dotenv
from src.utils.common.styles import GLOBAL_CSS
from src.utils.auth.auth import render_login, logout
from src.utils.database.db import (init_db, save_itinerary, get_itineraries,
                      get_itinerary_data, delete_itinerary,
                      get_profile, save_profile)
from src.utils.llm.llm_handler import LLMHandler
from src.utils.llm.prompt_builder import build_itinerary_prompt, build_recommendations_prompt
from src.utils.recommendations.recommendations import get_recommendations
from src.utils.route.route_intelligence import analyze_route
from src.utils.recommendations.weekend_getaways import get_weekend_getaways
from src.utils.common.cache import get_cached_route_analysis, get_cached_weekend_getaways, get_cache_stats
from src.utils.common.validation import validate_trip_params, ValidationError
from src.utils.common.error_handler import ErrorHandler
from src.utils.common.rate_limiter import itinerary_limiter
from src.utils.common.constants import (
    FOOD_PREFERENCES,
    ALL_INTERESTS,
    TRAVEL_STYLES,
    MOOD_OPTIONS,
    DEFAULT_BUDGET,
    REQUIRED_ENV_VARS,
    FOOD_ICONS,
)

NAV_ITEMS = [
    ("Plan a Trip", "planner"),
    ("Weekend Getaway", "weekend"),
    ("My Itineraries", "history"),
    ("Recommendations", "recs"),
    ("Profile", "profile"),
]

NAV_PAGE_MAP = {label: page for label, page in NAV_ITEMS}
LEGACY_NAV_MAP = {
    "🗺️ Plan a Trip": "Plan a Trip",
    "🏖️ Weekend Getaway": "Weekend Getaway",
    "📚 My Itineraries": "My Itineraries",
    "✨ Recommendations": "Recommendations",
    "👤 Profile": "Profile",
}

# Load environment variables from the new config location, with legacy fallback.
_ROOT_DIR = Path(__file__).resolve().parent
_ENV_CANDIDATES = [
    _ROOT_DIR / "config" / ".env",
    _ROOT_DIR / ".env",
]
for _env_path in _ENV_CANDIDATES:
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path, override=False)
        break

def _apply_planner_route_to_state(cities: list[str]) -> None:
    """Populate the planner widgets from a suggested route."""
    clean_cities = [city.strip() for city in cities if city and city.strip()]
    if not clean_cities:
        return

    previous_stop_count = int(st.session_state.get("dest_count", 1) or 1)
    st.session_state["dest_count"] = max(1, len(clean_cities))

    for idx, city in enumerate(clean_cities):
        st.session_state[f"stop_{idx}"] = city

    for idx in range(len(clean_cities), previous_stop_count):
        stale_key = f"stop_{idx}"
        if stale_key in st.session_state:
            del st.session_state[stale_key]


def _validate_startup_config():
    """Validate required environment variables at startup."""
    demo_mode = os.getenv("DEMO_MODE") == "true"
    if not demo_mode:
        missing = [var for var in ["GROQ_API_KEY", "COOKIE_SECRET"] if not os.getenv(var)]
        if missing:
            st.error(f"❌ Missing required environment variables: {', '.join(missing)}")
            st.error("Please check your .env file and restart the app.")
            st.stop()


def _render_route_map(title, path_points, arcs, source_color, target_color):
    """Render a pydeck route map when coordinates are available."""
    if not path_points:
        return

    try:
        import pydeck as pdk
    except ImportError:
        st.info("Install pydeck for route maps: pip install pydeck")
        return

    st.markdown(f"##### {title}")
    latitudes = [point["coordinates"][1] for point in path_points]
    longitudes = [point["coordinates"][0] for point in path_points]
    mid_lat = sum(latitudes) / len(latitudes)
    mid_lon = sum(longitudes) / len(longitudes)
    lat_span = max(latitudes) - min(latitudes) if len(latitudes) > 1 else 0
    lon_span = max(longitudes) - min(longitudes) if len(longitudes) > 1 else 0
    max_span = max(lat_span, lon_span)

    if max_span > 18:
        zoom = 3.6
    elif max_span > 10:
        zoom = 4.2
    elif max_span > 5:
        zoom = 5.0
    elif max_span > 2:
        zoom = 5.8
    else:
        zoom = 6.5

    view = pdk.ViewState(latitude=mid_lat, longitude=mid_lon, zoom=zoom, pitch=28)

    layers = []
    if arcs:
        layers.append(
            pdk.Layer(
                "ArcLayer",
                data=arcs,
                get_source_position="source",
                get_target_position="target",
                get_source_color=source_color,
                get_target_color=target_color,
                get_width=4,
                auto_highlight=True,
                pickable=True,
            )
        )
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=path_points,
        get_position="coordinates",
        get_color=target_color,
        get_radius=35000,
        pickable=True,
    )
    text_layer = pdk.Layer(
        "TextLayer",
        data=path_points,
        get_position="coordinates",
        get_text="name",
        get_size=13,
        get_color=[54, 58, 68],
        get_alignment_baseline="'bottom'",
    )
    layers.extend([scatter_layer, text_layer])
    st.pydeck_chart(
        pdk.Deck(
            layers=layers,
            initial_view_state=view,
            map_provider="carto",
            map_style="light",
            tooltip={"text": "{source_name} -> {target_name}"},
        )
    )


port = int(os.environ.get("PORT", 8501))

st.set_page_config(
    page_title="Wandr — AI Travel Planner",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
init_db()
_validate_startup_config()

if not render_login():
    st.stop()

user = st.session_state.get("user")
if not user:
    st.error("Please log in first.")
    st.stop()

# ── Session defaults ──────────────────────────────────────────────────────────
for key, default in [
    ("itinerary", None),
    ("last_inputs", {}),
    ("viewing_itin_id", None),
    ("dest_count", 1),
    ("ai_recs_cache", None),
    ("pending_nav", None),
    ("wk_selected_getaway", None),
    ("route_autogenerate", False),
    ("route_choice_label", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Apply deferred navigation target before sidebar widgets are instantiated
if st.session_state.get("pending_nav"):
    pending_nav = st.session_state.pop("pending_nav")
    st.session_state["nav_select"] = LEGACY_NAV_MAP.get(pending_nav, pending_nav)

# Clear itinerary when user navigates away from planner/weekend pages
_active_page = NAV_PAGE_MAP.get(st.session_state.get("nav_select"))
_prev_page = st.session_state.get("_last_page")
if _prev_page in ("planner", "weekend") and _active_page not in ("planner", "weekend"):
    st.session_state["itinerary"] = None
    st.session_state["last_inputs"] = {}
st.session_state["_last_page"] = _active_page

if st.session_state.get("pending_route_plan_override"):
    _apply_planner_route_to_state(st.session_state.pop("pending_route_plan_override"))

prof = get_profile(user["id"])

current_nav = st.session_state.get("nav_select")
current_nav = LEGACY_NAV_MAP.get(current_nav, current_nav) if current_nav else None
st.session_state["nav_select"] = current_nav

top_left, top_center, top_right = st.columns([1.45, 4.6, 1.45], gap="medium")
with top_left:
    st.markdown("""
    <div class="brand-lockup top-brand-lockup">
      <div class="brand-mark">W</div>
      <div>
        <div class="brand-name">Wandr</div>
        <div class="brand-tagline">AI travel design studio</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with top_center:
    nav_cols = st.columns([1.2, 1.55, 1.45, 1.55, 1], gap="small")
    for col, (label, page_key) in zip(nav_cols, NAV_ITEMS):
        with col:
            if st.button(
                label,
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if current_nav == label else "secondary",
            ):
                st.session_state["nav_select"] = label
                st.rerun()

with top_right:
    pic = user.get("picture", "")
    first_name = user.get("name", "Traveller").split()[0]
    if pic:
        st.markdown(f"""
        <div class="top-account-chip">
          <img src="{pic}" referrerpolicy="no-referrer"/>
          <span>{first_name}</span>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='top-account-chip no-image'><span>{first_name}</span></div>",
            unsafe_allow_html=True,
        )
    if st.button("Sign out", key="sign_out_top", use_container_width=True):
        logout()

page = NAV_PAGE_MAP.get(current_nav)
destination = days = budget = food_pref = interests = None
hometown = ""
weekend_options = []
selected_weekend_getaway = None
generate_btn = False
optimizer_weights = None
enable_what_if = False

if page is None:
    st.markdown("""
    <div class="page-hero hero-clean landing-hero">
      <div class="hero-pill">Wandr Travel Studio</div>
      <h1>Start with a vibe, leave with a plan worth taking</h1>
      <p>Build bold city breaks, quiet weekend escapes, and smarter itineraries from the header above whenever inspiration hits.</p>
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PLANNER & WEEKEND GETAWAY
# ═════════════════════════════════════════════════════════════════════════════
if page in ("planner", "weekend"):
    is_weekend = (page == "weekend")

    if is_weekend:
        st.markdown("""
        <div class="page-hero hero-clean">
          <div class="hero-pill">Weekend Getaway</div>
          <h1>Slip away for a lighter, lovelier weekend</h1>
          <p>Choose your city and get a quick reset with easier travel, better pacing, and food stops that actually fit the mood.</p>
        </div>""", unsafe_allow_html=True)
        st.markdown("""
        <div class="planner-panel-intro weekend-panel-intro">
          <div class="planner-kicker">Weekend Setup</div>
          <h3>Quick inputs for a shorter trip</h3>
          <p>Use this lighter form only for nearby weekend ideas.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="page-hero hero-clean">
          <div class="hero-pill">Plan a Trip</div>
          <h1>Shape a trip that feels exciting before it even begins</h1>
          <p>Map the route, tune the budget, match the food, and turn a list of places into a trip that flows naturally.</p>
        </div>""", unsafe_allow_html=True)

    if is_weekend:
        top_fields = st.columns([1.6, 0.8, 0.9], gap="medium")
        with top_fields[0]:
            hometown = st.text_input(
                "Your city",
                value=prof.get("home_city", ""),
                placeholder="e.g. Hyderabad",
                key="wk_hometown",
            )
        with top_fields[1]:
            days = st.number_input("Days", min_value=1, max_value=2, value=2, key="wk_days")
        with top_fields[2]:
            budget = st.number_input(
                "Budget/day (₹)",
                min_value=500,
                max_value=50000,
                value=prof.get("budget_default", 2000),
                step=500,
                key="wk_budget",
            )
    else:
        if st.session_state.get("prefill_dest"):
            st.session_state["start_city"] = st.session_state.pop("prefill_dest")

        top_fields = st.columns([1.5, 0.8, 0.9], gap="medium")
        with top_fields[0]:
            start_city = st.text_input(
                "Starting location",
                placeholder="e.g. Delhi",
                key="start_city",
            )
        with top_fields[1]:
            days = st.number_input("Days", min_value=1, max_value=30, value=3, key="pl_days")
        with top_fields[2]:
            budget = st.number_input(
                "Budget/day (₹)",
                min_value=500,
                max_value=50000,
                value=prof.get("budget_default", 2000),
                step=500,
                key="pl_budget",
            )

        st.markdown('<div class="sidebar-section-label">Destinations / Stops</div>', unsafe_allow_html=True)
        stops = []
        for i in range(st.session_state.dest_count):
            stop_val = st.text_input(f"Stop {i + 1}", key=f"stop_{i}", placeholder="e.g. Agra")
            if stop_val.strip():
                stops.append(stop_val.strip())

        manage_cols = st.columns([1, 1, 4], gap="small")
        with manage_cols[0]:
            if st.button("Add stop", key="add_stop", use_container_width=True):
                st.session_state.dest_count += 1
                st.rerun()
        with manage_cols[1]:
            if st.session_state.dest_count > 1 and st.button("Remove", key="rm_stop", use_container_width=True):
                st.session_state.dest_count -= 1
                st.rerun()

        destination = ", ".join(stops)

    pref_cols = st.columns([1.1, 1.9], gap="medium")
    saved_food = prof.get("food_pref", "Vegetarian")
    food_idx = FOOD_PREFERENCES.index(saved_food) if saved_food in FOOD_PREFERENCES else 0
    with pref_cols[0]:
        food_pref = st.selectbox(
            "Food preference",
            FOOD_PREFERENCES,
            index=food_idx,
            key="food_pref_sel",
        )
    with pref_cols[1]:
        saved_interests = prof.get("interests", [])
        interests = st.multiselect(
            "Interests",
            ALL_INTERESTS,
            default=[i for i in saved_interests if i in ALL_INTERESTS] or ["Culture", "Food"],
            key="interests_sel",
        )

    if not is_weekend:
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
            optimizer_weights = {
                "time": w_time / raw_total,
                "fatigue": w_fatigue / raw_total,
                "cost": w_cost / raw_total,
                "interests": w_interests / raw_total,
            }
            enable_what_if = st.checkbox(
                "Show what-if route simulations",
                value=True,
                key="opt_enable_what_if",
            )

    if is_weekend:
        # Use cached weekend getaways
        weekend_options = get_cached_weekend_getaways(hometown, interests or [], limit=4)
        option_names = [option["name"] for option in weekend_options]
        current_selection = st.session_state.get("wk_selected_getaway")

        if option_names and current_selection not in option_names:
            st.session_state["wk_selected_getaway"] = option_names[0]
        elif not option_names:
            st.session_state["wk_selected_getaway"] = None

        selected_weekend_getaway = st.session_state.get("wk_selected_getaway")
        destination = selected_weekend_getaway or ""

        st.markdown(
            '<div class="sidebar-section-label">Nearby weekend matches</div>',
            unsafe_allow_html=True,
        )

        if hometown.strip() and weekend_options:
            st.caption(
                "Your city is the starting point. These weekend picks are ranked by interest fit first, then by how easy they are to reach for a lighter short break."
            )
            lead_option = weekend_options[0]
            lead_overlap = ", ".join(lead_option.get("interest_overlap", [])) or "easy-going weekend energy"
            st.markdown(
                f"""
                <div class="food-highlight-bar">
                  Best match right now: <strong>{html.escape(lead_option["name"])}</strong> sits about
                  <strong>{lead_option["distance_km"]} km</strong> away and leans into
                  <strong>{html.escape(lead_overlap)}</strong>.
                </div>
                """,
                unsafe_allow_html=True,
            )
            option_cols = st.columns(len(weekend_options), gap="medium")
            for idx, option in enumerate(weekend_options):
                overlap = option.get("interest_overlap", [])
                overlap_text = ", ".join(overlap) if overlap else "Easy all-round match"
                is_selected = option["name"] == selected_weekend_getaway
                card_class = "getaway-card selected" if is_selected else "getaway-card"
                with option_cols[idx]:
                    st.markdown(
                        f"""
                        <div class="{card_class}">
                          <div class="dest-name">{html.escape(option["name"])}</div>
                          <div class="route-metric-pill">{option["distance_km"]} km from {html.escape(hometown.strip())}</div>
                          <div class="tag">{html.escape(option.get("vibe", "Weekend pick"))}</div>
                          <div style='font-size:0.84rem;color:var(--muted);margin-top:0.75rem'>
                            <strong>Best for:</strong> {html.escape(overlap_text)}
                          </div>
                          <div style='font-size:0.84rem;color:var(--muted);margin-top:0.45rem'>
                            {html.escape(option.get("reason", ""))}
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Selected" if is_selected else f"Choose {option['name']}",
                        key=f"wk_choose_{idx}",
                        type="primary" if is_selected else "secondary",
                        use_container_width=True,
                    ):
                        st.session_state["wk_selected_getaway"] = option["name"]
                        st.rerun()

            if selected_weekend_getaway:
                chosen_option = next(
                    (option for option in weekend_options if option["name"] == selected_weekend_getaway),
                    None,
                )
                if chosen_option:
                    st.markdown(
                        f"""
                        <div class="food-highlight-bar">
                          Weekend plan ready: start from <strong>{html.escape(hometown.strip())}</strong>,
                          slip away to <strong>{html.escape(selected_weekend_getaway)}</strong>,
                          and keep the travel light at around <strong>{chosen_option["distance_km"]} km</strong>.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        elif hometown.strip():
            st.info(
                "I couldn't find a strong nearby weekend match yet for that city. Try a nearby metro name or a larger base city like Delhi, Bengaluru, Hyderabad, Mumbai, Pune, Chennai, Kochi, Chandigarh, Mysore, or Jaipur."
            )
        else:
            st.info("Enter your home city to unlock nearby weekend picks matched to your interests.")

    generate_btn = st.button(
        "Plan Your Trip" if not is_weekend else "Find My Weekend Trip",
        type="primary",
        use_container_width=True,
        key="generate_trip_plan",
    )
    if not generate_btn and st.session_state.get("route_autogenerate"):
        generate_btn = True
        st.session_state["route_autogenerate"] = False

    if not is_weekend and st.session_state.get("route_choice_label"):
        st.info(f"Using {st.session_state['route_choice_label']} for itinerary generation.")

    # ── Generate ──────────────────────────────────────────────────────────────
    if generate_btn:
        dest_to_use = (destination or "").strip()
        if is_weekend and not hometown.strip():
            st.error("Please enter your home city first.")
        elif not is_weekend and not start_city.strip():
            st.error("Please enter your starting location.")
        elif is_weekend and not dest_to_use:
            st.error("Please choose one of the nearby weekend getaway options before generating the trip.")
        elif not dest_to_use:
            st.error("Please enter at least one destination stop for sightseeing.")
        else:
            current_inputs = {
                "destination": dest_to_use,
                "start_city": hometown.strip() if is_weekend else start_city.strip(),
                "days": days,
                "budget": budget,
                "food_pref": food_pref,
                "interests": sorted(interests or []),
                "is_weekend": is_weekend,
                "home_city": hometown.strip() if is_weekend else "",
            }

            # Always clear previous itinerary when a new generation starts
            st.session_state.itinerary = None
            st.session_state.last_inputs = {}

            # Progressive status updates
            progress_col = st.columns(1)[0]
            status_text = progress_col.empty()
            
            status_text.info("📋 Validating your trip details...")

            try:
                if not itinerary_limiter.is_allowed(user["id"]):
                    reset = itinerary_limiter.get_reset_time(user["id"])
                    st.warning(f"Rate limit reached. Try again in {int(reset)}s.")
                    st.stop()

                validated = validate_trip_params(
                    destination=dest_to_use, days=days, budget=budget,
                    food_pref=food_pref, interests=interests or [],
                )
                
                status_text.info("🗺️ Analyzing your route...")

                # ── Budget feasibility check (planner only) ────────────────
                if not is_weekend:
                    from src.utils.common.budget_validator import check_budget_feasibility, format_budget_warning
                    _cities_for_budget = [c.strip() for c in dest_to_use.split(",") if c.strip()]
                    if start_city.strip() and (
                        not _cities_for_budget or _cities_for_budget[0].lower() != start_city.strip().lower()
                    ):
                        _cities_for_budget = [start_city.strip()] + _cities_for_budget
                    _dist_for_budget = 0
                    if len(_cities_for_budget) > 1:
                        from src.utils.route.route_intelligence import get_city_coords, haversine_distance
                        for _i in range(len(_cities_for_budget) - 1):
                            _c1 = get_city_coords(_cities_for_budget[_i])
                            _c2 = get_city_coords(_cities_for_budget[_i + 1])
                            if _c1 and _c2:
                                _dist_for_budget += haversine_distance(_c1, _c2)
                    _budget_ok, _budget_feasibility = check_budget_feasibility(
                        user_budget_per_day=validated["budget"],
                        days=validated["days"],
                        destination=validated["destination"],
                        cities=_cities_for_budget,
                        total_distance_km=_dist_for_budget,
                        food_pref=validated["food_pref"],
                    )
                    st.markdown(format_budget_warning(_budget_feasibility), unsafe_allow_html=True)
                    if not _budget_ok:
                        if not st.checkbox("I understand my budget is tight — proceed anyway", key="budget_override"):
                            st.stop()

                # ── Route analysis (all stops, bug fixed) ────────────────
                cities = [c.strip() for c in dest_to_use.split(",") if c.strip()]
                analysis_cities = cities
                if not is_weekend and start_city.strip():
                    if not cities or cities[0].lower() != start_city.strip().lower():
                        analysis_cities = [start_city.strip()] + cities
                route_analysis = None

                if len(analysis_cities) > 1:
                    # Use cached route analysis to avoid expensive recalculations
                    route_analysis = get_cached_route_analysis(
                        analysis_cities,
                        validated["days"],
                        interests=validated["interests"],
                        optimization_weights=optimizer_weights,
                        budget_per_day=validated["budget"],
                        enable_what_if=enable_what_if,
                    )

                    if route_analysis:
                        status = route_analysis.get("status", "ok")
                        status_map = {
                            "ok": {"cls": "ok", "icon": "✅", "text": "Well-paced route"},
                            "warning": {"cls": "warn", "icon": "⚠️", "text": "Moderate travel load"},
                            "danger": {"cls": "danger", "icon": "🚨", "text": "High travel fatigue detected"},
                            "success": {"cls": "ok", "icon": "✅", "text": "Well-paced route"},
                            "perfect": {"cls": "ok", "icon": "✅", "text": "Well-paced route"},
                        }
                        badge = status_map.get(status, status_map["ok"])
                        badge_cls = badge["cls"]
                        badge_icon = badge["icon"]
                        badge_text = badge["text"]

                        st.markdown(f"""
                            <div class="route-badge {badge_cls}">
                              {badge_icon} {badge_text} &nbsp;·&nbsp;
                              {route_analysis['total_distance_km']} km total &nbsp;·&nbsp;
                              {route_analysis['total_travel_time_hrs']} hrs transit
                            </div>""", unsafe_allow_html=True)

                        for w in route_analysis.get("warnings", []):
                            st.caption(f"ℹ️ {w}")
                        for j in route_analysis.get("illogical_jumps", []):
                            st.warning(f"Long jump: {j}")

                        # ── Transport options per leg ────────────────────────────────
                        leg_details = route_analysis.get("leg_details", [])
                        if leg_details:
                            from src.utils.route.transport_recommender import get_transport_summary
                            with st.expander("🚌 Transport options per leg", expanded=True):
                                for leg in leg_details:
                                    transport = get_transport_summary(
                                        leg["from"], leg["to"],
                                        leg["distance_km"], validated["budget"]
                                    )
                                    st.markdown(
                                        f"**{leg['from']} → {leg['to']}** · "
                                        f"{leg['distance_km']} km · ~{leg['travel_time_hrs']} hrs"
                                    )
                                    if transport.get("available"):
                                        t_cols = st.columns(len(transport["all_options"]))
                                        for t_col, opt in zip(t_cols, transport["all_options"]):
                                            with t_col:
                                                st.markdown(
                                                    f"{opt.icon} **{opt.mode}**  \n"
                                                    f"₹{opt.cost_per_person:,}/person  \n"
                                                    f"~{opt.duration_hours:.1f} hrs  \n"
                                                    f"{opt.booking_hint}"
                                                )
                                    else:
                                        st.caption(transport.get("message", "Local transport recommended."))
                                    st.divider()

                        # ── Route map + clean 2-option optimizer ────────────────────────
                        vp   = route_analysis.get("valid_path", [])
                        arcs = route_analysis.get("arcs", [])
                        optimized_order = route_analysis.get("optimized_order", [])
                        optimized_path  = route_analysis.get("optimized_path", [])
                        optimized_arcs  = route_analysis.get("optimized_arcs", [])
                        replacement_suggestions = route_analysis.get("replacement_suggestions", [])
                        trim_suggestion = route_analysis.get("trim_suggestion")

                        if route_analysis.get("missing_cities"):
                            st.info(f"Map coverage partial — couldn't place: {', '.join(route_analysis['missing_cities'])}")

                        # Build the two best alternatives
                        alt_a = None  # Reorder (same cities, better sequence)
                        alt_b = None  # Swap or Trim (change a city / drop one)

                        show_reorder = (
                            optimized_order
                            and optimized_order != route_analysis.get("current_order", [])
                            and route_analysis.get("distance_saved_km", 0) > 0
                        )
                        if show_reorder:
                            alt_a = {
                                "label": "Reorder stops",
                                "desc": f"Same cities, smarter sequence — saves {route_analysis['distance_saved_km']} km and {route_analysis['time_saved_hrs']} hrs",
                                "order": optimized_order,
                                "path": optimized_path,
                                "arcs": optimized_arcs,
                                "key": "opt_reorder",
                                "choice_label": "Reordered stops",
                                "src_color": [85, 107, 214, 220],
                                "tgt_color": [182, 90, 122, 235],
                            }

                        if replacement_suggestions:
                            top_swap = replacement_suggestions[0]
                            tags = ", ".join(top_swap.get("similarity_tags", [])) or "similar vibe"
                            alt_b = {
                                "label": f"Swap {top_swap['replace_city']} → {top_swap['replacement_city']}",
                                "desc": f"Closer alternative with {tags} — saves ~{top_swap['distance_saved_km']} km",
                                "order": top_swap.get("suggested_order", []),
                                "path": top_swap.get("suggested_path", []),
                                "arcs": top_swap.get("suggested_arcs", []),
                                "key": "opt_swap",
                                "choice_label": f"Swap {top_swap['replace_city']} with {top_swap['replacement_city']}",
                                "src_color": [26, 123, 116, 220],
                                "tgt_color": [244, 194, 96, 235],
                            }
                        elif trim_suggestion:
                            alt_b = {
                                "label": f"Drop {trim_suggestion['removed_city']}",
                                "desc": f"Lighter route — saves {trim_suggestion['distance_saved_km']} km and {trim_suggestion['time_saved_hrs']} hrs",
                                "order": trim_suggestion.get("suggested_order", []),
                                "path": trim_suggestion.get("suggested_path", []),
                                "arcs": trim_suggestion.get("suggested_arcs", []),
                                "key": "opt_trim",
                                "choice_label": f"Trimmed: removed {trim_suggestion['removed_city']}",
                                "src_color": [198, 154, 71, 220],
                                "tgt_color": [218, 115, 71, 235],
                            }

                        # Render: current map always shown; alternatives in tabs if present
                        has_alts = alt_a or alt_b
                        if has_alts:
                            tab_labels = ["Your Route"]
                            if alt_a:
                                tab_labels.append(f"⇄ {alt_a['label']}")
                            if alt_b:
                                tab_labels.append(f"✨ {alt_b['label']}")
                            route_tabs = st.tabs(tab_labels)

                            with route_tabs[0]:
                                _render_route_map("Current Route", vp, arcs, [218, 115, 71, 220], [26, 123, 116, 235])
                                if st.button("▶️ Use your route as-is", key="use_current_route", use_container_width=True):
                                    st.session_state["route_autogenerate"] = True
                                    st.rerun()

                            tab_idx = 1
                            for alt in [alt_a, alt_b]:
                                if not alt:
                                    continue
                                with route_tabs[tab_idx]:
                                    st.caption(alt["desc"])
                                    _render_route_map(
                                        alt["label"], alt["path"], alt["arcs"],
                                        alt["src_color"], alt["tgt_color"]
                                    )
                                    if st.button(
                                        f"✔️ Use this route",
                                        key=f"use_{alt['key']}",
                                        use_container_width=True,
                                    ):
                                        st.session_state["pending_route_plan_override"] = alt["order"]
                                        st.session_state["route_choice_label"] = alt["choice_label"]
                                        st.session_state["route_autogenerate"] = True
                                        st.rerun()
                                tab_idx += 1
                        else:
                            _render_route_map("Your Route", vp, arcs, [218, 115, 71, 220], [26, 123, 116, 235])

                        st.divider()

                    # ── Build prompt & call LLM ──────────────────────────────
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
                        hometown=hometown.strip() if is_weekend else start_city.strip(),
                        is_weekend_getaway=is_weekend,
                    )

                    result = LLMHandler().generate_itinerary(prompt)
                    st.session_state.itinerary = result
                    st.session_state.last_inputs = current_inputs

                    # BUG FIX: food_pref now explicitly saved
                    status_text.info("💾 Saving your itinerary...")
                    
                    save_itinerary(
                        user_id=user["id"],
                        destination=validated["destination"],
                        days=validated["days"],
                        budget=validated["budget"],
                        food_pref=validated["food_pref"],  # explicitly passed
                        interests=validated["interests"],
                        data=result,
                    )
                    
                    status_text.empty()
                    st.success("✅ Itinerary ready — saved to your history!")

                else:
                    # Single-city flow: skip route-graph analysis and generate itinerary directly
                    status_text.info("🤖 Generating your personalized itinerary...")

                    travel_style = prof.get("travel_style", "Explorer")
                    prompt = build_itinerary_prompt(
                        destination=validated["destination"],
                        days=validated["days"],
                        budget=validated["budget"],
                        food_pref=validated["food_pref"],
                        interests=validated["interests"],
                        travel_style=travel_style,
                        route_analysis=None,
                        hometown=hometown.strip() if is_weekend else start_city.strip(),
                        is_weekend_getaway=is_weekend,
                    )

                    result = LLMHandler().generate_itinerary(prompt)
                    st.session_state.itinerary = result
                    st.session_state.last_inputs = current_inputs

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

    # ── Display itinerary ─────────────────────────────────────────────────────
    if st.session_state.itinerary:
        data = st.session_state.itinerary
        inp = st.session_state.last_inputs

        trip_label = "Weekend getaway" if inp.get("is_weekend") else (
            "Multi-stop route" if "," in inp["destination"] else "City itinerary"
        )
        style_label = prof.get("travel_style", "Explorer")
        chips = [
            f"Style: {style_label}",
            f"Food: {inp['food_pref'].split(' (')[0]}",
        ]
        if inp.get("interests"):
            chips.append("Focus: " + " · ".join(inp["interests"][:3]))
        chip_html = "".join(f'<div class="summary-chip">{chip}</div>' for chip in chips)
        st.markdown(f"""
        <div class="summary-banner">
          <div>
            <div class="summary-label">{trip_label}</div>
            <div class="summary-title">{inp["destination"]}</div>
          </div>
          <div class="summary-chip-row">{chip_html}</div>
        </div>""", unsafe_allow_html=True)

        # ── Summary row ──────────────────────────────────────────────────────
        food_icon = FOOD_ICONS.get(inp.get("food_pref", ""), "🍽️")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("📍 Destination", inp["destination"].split(",")[0].strip())
        with c2:
            st.metric("📅 Duration", f"{inp['days']} day{'s' if inp['days'] != 1 else ''}")
        with c3:
            st.metric("💰 Budget", f"₹{inp['budget']:,}/day")
        with c4:
            st.metric(f"{food_icon} Food", inp["food_pref"].split(" (")[0])

        # Interest pills
        if inp.get("interests"):
            interest_html = "".join(
                f'<span class="interest-pill">{i}</span>'
                for i in inp["interests"]
            )
            st.markdown(f'<div class="interest-pills">{interest_html}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        itin_days = data.get("days", [])
        n = len(itin_days)

        tabs = st.tabs(
            [f"Day {d['day_number']}" for d in itin_days]
            + ["💰 Budget", "💡 Tips", "🗺️ Nearby", "📥 Export"]
        )

        # ── Day tabs ─────────────────────────────────────────────────────────
        for idx, day in enumerate(itin_days):
            with tabs[idx]:
                day_title = day.get("title") or f"Day {day['day_number']}"
                theme = day.get("theme", "")

                st.markdown(f"### {day_title}")
                if theme:
                    st.markdown(
                        f"<p style='color:var(--accent2);font-size:0.9rem;"
                        f"margin-top:-0.5rem;font-style:italic'>{theme}</p>",
                        unsafe_allow_html=True,
                    )

                # Food highlights banner
                food_highlights = day.get("food_highlights", [])
                if food_highlights:
                    highlights = " &nbsp;·&nbsp; ".join(f"🍴 {h}" for h in food_highlights[:3])
                    st.markdown(
                        f'<div class="food-highlight-bar">'
                        f'<strong>Today\'s food highlights:</strong> {highlights}</div>',
                        unsafe_allow_html=True,
                    )

                # Schedule
                schedule = day.get("schedule", [])
                if schedule:
                    st.markdown(
                        '<div class="section-header"><span>Schedule</span><div class="line"></div></div>',
                        unsafe_allow_html=True,
                    )
                    for item in schedule:
                        cost = f"₹{item['cost_inr']}" if item.get("cost_inr", 0) > 0 else "Free"
                        dur = f" · {item['duration_minutes']} min" if item.get("duration_minutes") else ""
                        food_item = item.get("food_item", "")
                        food_html = f"<div class='meta'>🍴 {food_item}</div>" if food_item else ""
                        notes = item.get("notes", "")
                        notes_html = (
                            f"<div class='meta' style='margin-top:4px;color:#7880a0'>{notes}</div>"
                            if notes else ""
                        )
                        st.markdown(f"""
                        <div class="activity-card">
                          <div class="time">{item.get('time', '')}</div>
                          <div class="act">{item.get('activity', '')}</div>
                          <div class="meta">📍 {item.get('location', '')} &nbsp;·&nbsp; {cost}{dur}</div>
                          {food_html}
                          {notes_html}
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
                            why = m.get("why", "")
                            cuisine = m.get("cuisine", "")
                            why_html = (
                                f"<div style='font-size:0.75rem;color:var(--accent2);margin-top:4px'>{why}</div>"
                                if why else ""
                            )
                            cuisine_html = (
                                f"<div style='font-size:0.75rem;color:var(--muted)'>{cuisine}</div>"
                                if cuisine else ""
                            )
                            st.markdown(f"""
                            <div class="meal-card">
                              <div class="meal-label">{icon} {label}</div>
                              <div class="place">{m.get('place', '—')}</div>
                              <div class="dish">{m.get('dish', '')}</div>
                              {cuisine_html}
                              <div class="cost">₹{m.get('cost_inr', '—')}</div>
                              {why_html}
                            </div>""", unsafe_allow_html=True)

                # Nearby alternatives
                alternatives = day.get("nearby_alternatives", [])
                if alternatives:
                    with st.expander("📍 Nearby alternatives to save travel time"):
                        for alt in alternatives:
                            dist = alt.get("distance_km", "?")
                            st.markdown(f"""
                            <div class="nearby-alt">
                              <strong>{alt.get('name', '')}</strong>
                              <span class="dist"> · {dist} km away</span>
                              <div style='color:var(--muted);font-size:0.82rem;margin-top:3px'>
                                {alt.get('why', '')}
                              </div>
                            </div>""", unsafe_allow_html=True)

                # Day total
                day_total = day.get("day_total_inr")
                if day_total:
                    st.markdown(
                        f"<div class='day-total-row'>Day total: "
                        f"<strong>₹{day_total:,}</strong></div>",
                        unsafe_allow_html=True,
                    )

                # ── Book Travel & Hotels ─────────────────────────────────────
                from datetime import date, timedelta
                from src.utils.common.booking_links import hotel_links, get_booking_links
                
                # Calculate travel date (trip start + day number - 1)
                day_num = day.get("day_number", 1)
                travel_date = date.today() + timedelta(days=day_num - 1)
                
                # Extract current city from schedule or destination
                current_city = inp["destination"].split(",")[0].strip()
                if "," in inp["destination"]:
                    cities_list = [c.strip() for c in inp["destination"].split(",")]
                    if day_num <= len(cities_list):
                        current_city = cities_list[day_num - 1]
                
                with st.expander("🎫 Book Travel & Hotels", expanded=False):
                    st.markdown("#### 🏨 Hotels in " + current_city)
                    checkin = travel_date
                    checkout = travel_date + timedelta(days=1)
                    h_links = hotel_links(current_city, checkin, checkout)
                    
                    h_cols = st.columns(len(h_links))
                    for h_col, link in zip(h_cols, h_links):
                        with h_col:
                            st.markdown(
                                f"<a href='{link['url']}' target='_blank' style='text-decoration:none'>"
                                f"<div style='padding:0.8rem;border-radius:16px;background:rgba(255,251,246,0.9);"
                                f"border:1px solid rgba(92,72,49,0.1);text-align:center;cursor:pointer;"
                                f"transition:transform 0.2s;'>"
                                f"<div style='font-size:1.8rem;margin-bottom:0.3rem'>{link['icon']}</div>"
                                f"<div style='font-weight:700;color:var(--text);font-size:0.85rem'>{link['name']}</div>"
                                f"</div></a>",
                                unsafe_allow_html=True
                            )
                    
                    # Transport to next city (if multi-city trip)
                    if "," in inp["destination"] and day_num < len(cities_list):
                        next_city = cities_list[day_num]
                        st.markdown(f"#### 🚆 Travel to {next_city}")
                        
                        # Get distance for smart transport suggestions
                        from src.utils.route.route_intelligence import get_city_coords, haversine_distance
                        c1 = get_city_coords(current_city)
                        c2 = get_city_coords(next_city)
                        distance = haversine_distance(c1, c2) if c1 and c2 else 200
                        
                        t_links = get_booking_links(current_city, next_city, distance, travel_date + timedelta(days=1))
                        
                        # Show all available transport modes
                        all_transport = []
                        if t_links.get("flight"):
                            all_transport.extend(t_links["flight"])
                        if t_links.get("train"):
                            all_transport.extend(t_links["train"])
                        if t_links.get("bus"):
                            all_transport.extend(t_links["bus"])
                        
                        if all_transport:
                            t_cols = st.columns(min(len(all_transport), 4))
                            for t_col, link in zip(t_cols, all_transport[:4]):
                                with t_col:
                                    st.markdown(
                                        f"<a href='{link['url']}' target='_blank' style='text-decoration:none'>"
                                        f"<div style='padding:0.8rem;border-radius:16px;background:rgba(255,251,246,0.9);"
                                        f"border:1px solid rgba(92,72,49,0.1);text-align:center;cursor:pointer;"
                                        f"transition:transform 0.2s;'>"
                                        f"<div style='font-size:1.8rem;margin-bottom:0.3rem'>{link['icon']}</div>"
                                        f"<div style='font-weight:700;color:var(--text);font-size:0.85rem'>{link['name']}</div>"
                                        f"</div></a>",
                                        unsafe_allow_html=True
                                    )

        # ── Budget tab ────────────────────────────────────────────────────────
        with tabs[n]:
            st.markdown("### Budget Breakdown")
            bd = data.get("budget_breakdown", {})
            if bd:
                labels = {
                    "food_per_day": "🍽️ Food / day",
                    "transport_per_day": "🚌 Transport / day",
                    "activities_total": "🎟️ Activities (total)",
                    "miscellaneous": "🛍️ Miscellaneous",
                    "grand_total": "💳 Grand Total",
                }
                for key, label in labels.items():
                    val = bd.get(key)
                    if val:
                        cls = "budget-row total" if key == "grand_total" else "budget-row"
                        st.markdown(
                            f'<div class="{cls}"><span class="blabel">{label}</span>'
                            f'<span class="bval">₹{val:,}</span></div>',
                            unsafe_allow_html=True,
                        )
            else:
                st.markdown("<p style='color:var(--muted)'>Budget data not available.</p>",
                            unsafe_allow_html=True)

        # ── Tips tab ──────────────────────────────────────────────────────────
        with tabs[n + 1]:
            st.markdown("### Tips & Practicalities")
            for tip in data.get("practical_tips", []):
                st.markdown(f'<div class="tip-chip">{tip}</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            transport = data.get("local_transport", [])
            if transport:
                st.markdown("**🚌 Getting around**")
                for t in transport:
                    st.markdown(f"- {t}")

        # ── Nearby destinations tab ───────────────────────────────────────────
        with tabs[n + 2]:
            st.markdown("### Nearby Destinations Worth Visiting")
            nearby = data.get("nearby_destinations", [])
            if nearby:
                nc = st.columns(min(len(nearby), 3))
                for i, dest in enumerate(nearby[:6]):
                    with nc[i % 3]:
                        tag = dest.get("best_for", "")
                        tag_html = (
                            f'<div class="tag">{tag}</div>' if tag else ""
                        )
                        st.markdown(f"""
                        <div class="getaway-card">
                          <div class="dest-name">{dest.get('name', '')}</div>
                          <div style='font-size:0.82rem;color:var(--muted);margin:4px 0'>
                            {dest.get('distance_km', '?')} km away
                          </div>
                          {tag_html}
                          <div style='font-size:0.85rem;color:var(--muted);margin-top:6px'>
                            {dest.get('why_visit', '')}
                          </div>
                        </div>""", unsafe_allow_html=True)

                        if st.button(
                            f"Plan {dest.get('name', '')} →",
                            key=f"plan_nearby_{i}",
                            use_container_width=True,
                        ):
                            chosen = dest.get("name", "")
                            st.session_state["prefill_dest"] = chosen
                            st.session_state.dest_count = 1
                            st.session_state["pending_nav"] = "Plan a Trip"
                            st.rerun()
            else:
                st.markdown("<p style='color:var(--muted)'>No nearby destinations in this itinerary.</p>",
                            unsafe_allow_html=True)

        # ── Export tab ────────────────────────────────────────────────────────
        with tabs[n + 3]:
            st.markdown("### Export Your Itinerary")
            food_label = inp.get("food_pref", "")
            interests_label = ", ".join(inp.get("interests", []))

            lines = [
                f"WANDR TRAVEL ITINERARY",
                f"Destination: {inp['destination'].upper()}",
                f"Duration: {inp['days']} days | Budget: ₹{inp['budget']:,}/day",
                f"Food: {food_label} | Interests: {interests_label}",
                "=" * 55,
                "",
            ]
            for day in itin_days:
                lines.append(f"DAY {day['day_number']}: {day.get('title', '')}")
                if day.get("theme"):
                    lines.append(f"Theme: {day['theme']}")
                lines.append("-" * 40)

                for item in day.get("schedule", []):
                    cost_str = f"₹{item['cost_inr']}" if item.get("cost_inr", 0) > 0 else "Free"
                    lines.append(
                        f"  {item.get('time', ''):9} {item.get('activity', '')} "
                        f"@ {item.get('location', '')} [{cost_str}]"
                    )
                    if item.get("food_item"):
                        lines.append(f"           🍴 {item['food_item']}")
                    if item.get("notes"):
                        lines.append(f"           → {item['notes']}")

                meals = day.get("meals", {})
                if meals:
                    lines += ["", "  MEALS:"]
                    for mkey, mlabel in [("breakfast", "Breakfast"), ("lunch", "Lunch"), ("dinner", "Dinner")]:
                        m = meals.get(mkey, {})
                        if m.get("place"):
                            lines.append(
                                f"  {mlabel:12} {m.get('place', '')} — "
                                f"{m.get('dish', '')} (₹{m.get('cost_inr', '')})"
                            )
                if day.get("day_total_inr"):
                    lines.append(f"\n  Day Total: ₹{day['day_total_inr']:,}")
                lines.append("")

            bd = data.get("budget_breakdown", {})
            if bd.get("grand_total"):
                lines += ["=" * 55, f"GRAND TOTAL: ₹{bd['grand_total']:,}", ""]

            for tip in data.get("practical_tips", []):
                lines.append(f"• {tip}")

            slug = inp["destination"].lower().replace(" ", "_")[:20]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    "📄 Download as Text",
                    "\n".join(lines),
                    f"{slug}_itinerary.txt",
                    "text/plain",
                    use_container_width=True,
                )
            with col2:
                st.download_button(
                    "📋 Download as JSON",
                    __import__("json").dumps(data, indent=2),
                    f"{slug}_itinerary.json",
                    "application/json",
                    use_container_width=True,
                )
            with col3:
                try:
                    # Generate PDF
                    from reportlab.lib.pagesizes import letter
                    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                    from reportlab.lib.units import inch
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
                    from reportlab.lib import colors
                    from io import BytesIO

                    def _pdf_safe(text):
                        sanitized = str(text or "")
                        sanitized = sanitized.encode("latin-1", "ignore").decode("latin-1")
                        return html.escape(sanitized)

                    pdf_buffer = BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
                    story = []
                    styles = getSampleStyleSheet()

                    # Title
                    title_style = ParagraphStyle(
                        'CustomTitle',
                        parent=styles['Heading1'],
                        fontSize=24,
                        textColor=colors.HexColor('#d4405c'),
                        spaceAfter=6,
                        alignment=1,
                    )
                    story.append(Paragraph("WANDR TRAVEL ITINERARY", title_style))
                    story.append(Spacer(1, 0.2*inch))

                    # Header info
                    header_text = (
                        f"<b>{_pdf_safe(inp['destination'].upper())}</b><br/>"
                        f"{inp['days']} days | INR {inp['budget']:,}/day<br/>"
                        f"{_pdf_safe(food_label)} | {_pdf_safe(interests_label)}"
                    )
                    story.append(Paragraph(header_text, styles['Normal']))
                    story.append(Spacer(1, 0.2*inch))

                    # Daily schedules
                    for day in itin_days:
                        day_heading = f"<b>DAY {day['day_number']}: {_pdf_safe(day.get('title', ''))}</b>"
                        if day.get("theme"):
                            day_heading += f"<br/><font size=9>Theme: {_pdf_safe(day['theme'])}</font>"
                        story.append(Paragraph(day_heading, styles['Heading2']))

                        for item in day.get("schedule", []):
                            cost_str = f"INR {item['cost_inr']}" if item.get("cost_inr", 0) > 0 else "Free"
                            schedule_item = (
                                f"<b>{_pdf_safe(item.get('time', ''))}</b> - "
                                f"{_pdf_safe(item.get('activity', ''))} @ {_pdf_safe(item.get('location', ''))} "
                                f"[{_pdf_safe(cost_str)}]"
                            )
                            story.append(Paragraph(schedule_item, styles['Normal']))
                            if item.get("food_item"):
                                story.append(Paragraph(f"<font size=9>Food: {_pdf_safe(item['food_item'])}</font>", styles['Normal']))

                        meals = day.get("meals", {})
                        if meals:
                            meals_text = "<b>MEALS:</b><br/>"
                            for mkey, mlabel in [("breakfast", "Breakfast"), ("lunch", "Lunch"), ("dinner", "Dinner")]:
                                m = meals.get(mkey, {})
                                if m.get("place"):
                                    meals_text += (
                                        f"{mlabel}: {_pdf_safe(m.get('place', ''))} - "
                                        f"{_pdf_safe(m.get('dish', ''))} (INR {_pdf_safe(m.get('cost_inr', ''))})<br/>"
                                    )
                            story.append(Paragraph(meals_text, styles['Normal']))

                        if day.get("day_total_inr"):
                            story.append(Paragraph(f"<b>Day Total: INR {day['day_total_inr']:,}</b>", styles['Normal']))

                        story.append(Spacer(1, 0.15*inch))

                    # Budget breakdown
                    bd = data.get("budget_breakdown", {})
                    if bd:
                        story.append(PageBreak())
                        story.append(Paragraph("<b>BUDGET BREAKDOWN</b>", styles['Heading2']))
                        budget_table_data = [["Category", "Amount"]]
                        for key, val in bd.items():
                            if key != "grand_total":
                                budget_table_data.append([key.replace("_", " ").title(), f"INR {val:,.0f}"])
                        budget_table_data.append(["GRAND TOTAL", f"INR {bd.get('grand_total', 0):,}"])
                        budget_table = Table(budget_table_data, colWidths=[3*inch, 1.5*inch])
                        budget_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f97316')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 11),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#fef9f3')]),
                            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f5d5c2')),
                        ]))
                        story.append(budget_table)

                    # Tips
                    if data.get("practical_tips"):
                        story.append(Spacer(1, 0.2*inch))
                        story.append(Paragraph("<b>PRACTICAL TIPS</b>", styles['Heading2']))
                        for tip in data.get("practical_tips", []):
                            story.append(Paragraph(f"- {_pdf_safe(tip)}", styles['Normal']))

                    doc.build(story)
                    pdf_buffer.seek(0)

                    st.download_button(
                        "📑 Download as PDF",
                        pdf_buffer.getvalue(),
                        f"{slug}_itinerary.pdf",
                        "application/pdf",
                        use_container_width=True,
                    )
                except Exception as pdf_error:
                    ErrorHandler.log_error(pdf_error, "pdf_export")
                    st.error("⚠️ PDF export failed for this itinerary. TXT/JSON downloads are still available.")

    else:
        # ── Empty state ───────────────────────────────────────────────────────
        st.markdown("""
        <div style='text-align:center;padding:3rem 0 2rem'>
          <div style='font-size:4rem;margin-bottom:1rem'>🌍</div>
          <p style='font-family:var(--serif);font-size:1.8rem;color:var(--text);margin-bottom:0.5rem'>
            Ready when you are
          </p>
          <p style='color:var(--muted);font-size:0.95rem'>
            Fill in the planner above to start building your trip.
          </p>
        </div>""", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        features = [
            ("📅", "Day-by-day Schedule", "Timed activities with real locations and costs"),
            ("🍽️", "Smart Food Guide", "Vegetarian, non-veg, vegan & more — every meal matched"),
            ("🗺️", "Multi-Stop Routes", "Complete route mapping for all your stops"),
        ]
        for col, (icon, title, desc) in zip([c1, c2, c3], features):
            with col:
                st.markdown(f"""
                <div class="feature-block">
                  <div class="icon">{icon}</div>
                  <div class="ftitle">{title}</div>
                  <div class="fdesc">{desc}</div>
                </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PROFILE PAGE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "profile":
    from src.utils.database.db import get_liked_places, add_liked_place, delete_liked_place
    from src.utils.common.metrics import get_user_stats

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
    st.markdown("### 📊 Your Travel Stats")
    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.metric("Itineraries Created", user_stats["total_itineraries"])
    with stat_cols[1]:
        st.metric("Days Planned", user_stats["total_days_planned"])
    with stat_cols[2]:
        st.metric("Destinations", user_stats["unique_destinations"])
    with stat_cols[3]:
        st.metric("Liked Places", user_stats["liked_places"])
    
    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("#### Travel Preferences")
        with st.form("profile_form"):
            current_food = prof.get("food_pref", "Vegetarian")
            food_idx = FOOD_PREFERENCES.index(current_food) if current_food in FOOD_PREFERENCES else 0
            new_food = st.selectbox("🍽️ Default food preference", FOOD_PREFERENCES, index=food_idx)

            new_interests = st.multiselect(
                "🎯 Interests",
                ALL_INTERESTS,
                default=[i for i in prof.get("interests", []) if i in ALL_INTERESTS],
            )

            new_home = st.text_input(
                "🏠 Home city (for Weekend Getaway)",
                value=prof.get("home_city", ""),
                placeholder="e.g. Hyderabad",
            )

            new_style = st.selectbox(
                "🧳 Travel style", TRAVEL_STYLES,
                index=TRAVEL_STYLES.index(prof.get("travel_style", "Explorer"))
                if prof.get("travel_style", "Explorer") in TRAVEL_STYLES else 0,
            )

            new_budget = st.number_input(
                "💰 Default daily budget (₹)",
                min_value=500, max_value=50000,
                value=prof.get("budget_default", 2000), step=500,
            )

            if st.form_submit_button("💾 Save Preferences", use_container_width=True):
                save_profile(user["id"], new_food, new_interests, new_home, new_style, new_budget)
                st.success("✅ Preferences saved! They'll apply to your next itinerary.")
                st.rerun()

    with col_right:
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
                        add_liked_place(user["id"], p_name, p_type, p_country, p_notes)
                        st.success(f"Added {p_name}!")
                        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# HISTORY PAGE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "history":
    st.markdown("""
    <div class="page-hero">
      <div class="eyebrow">✦ Saved Plans</div>
      <h1>My Itineraries</h1>
      <p>Every trip you've planned, saved automatically with your food preferences.</p>
    </div>""", unsafe_allow_html=True)

    itins = get_itineraries(user["id"])  # Returns in reverse chronological order (newest first)

    if not itins:
        st.markdown("""
        <div style='text-align:center;padding:3rem 0'>
          <div style='font-size:3rem'>📭</div>
          <p style='font-family:var(--serif);font-size:1.3rem;margin:0.5rem 0;color:var(--text)'>
            No itineraries yet
          </p>
          <p style='color:var(--muted)'>Plan a trip and it'll appear here automatically.</p>
        </div>""", unsafe_allow_html=True)

    elif st.session_state.viewing_itin_id:
        itin_data = get_itinerary_data(st.session_state.viewing_itin_id)
        current_meta = next((i for i in itins if i["id"] == st.session_state.viewing_itin_id), None)

        if st.button("← Back to all itineraries"):
            st.session_state.viewing_itin_id = None
            st.rerun()

        if itin_data and current_meta:
            food_saved = current_meta.get("food_pref", "—")
            st.markdown(f"### {current_meta['destination']} — {current_meta['days']} days")
            st.markdown(
                f"<p style='color:var(--muted)'>{current_meta['created_at'][:10]} &nbsp;·&nbsp; "
                f"{food_saved} &nbsp;·&nbsp; ₹{current_meta['budget']:,}/day</p>",
                unsafe_allow_html=True,
            )

            itin_days = itin_data.get("days", [])
            n = len(itin_days)
            tabs = st.tabs([f"Day {d['day_number']}" for d in itin_days] + ["💰 Budget"])

            for idx, day in enumerate(itin_days):
                with tabs[idx]:
                    st.markdown(f"### {day.get('title', '')}")

                    food_highlights = day.get("food_highlights", [])
                    if food_highlights:
                        st.markdown(
                            f'<div class="food-highlight-bar">🍴 {" · ".join(food_highlights[:3])}</div>',
                            unsafe_allow_html=True,
                        )

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

            with tabs[n]:
                bd = itin_data.get("budget_breakdown", {})
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

    else:
        # List view - displayed in reverse chronological order (newest first)
        if itins:
            st.markdown("""
            <div style='color: #7a6f69; font-size: 0.9rem; margin-bottom: 1.5rem;'>
            ⏱️ <strong>Newest itineraries first</strong> — Click any to view full details
            </div>""", unsafe_allow_html=True)
            
        for idx, itin in enumerate(itins):
            food_saved = itin.get("food_pref", "—")
            food_icon = {"Vegetarian": "🟢", "Non-Vegetarian": "🔴",
                         "Both (Veg & Non-Veg)": "🔵", "Vegan": "🌿",
                         "Jain": "🕊️", "Halal": "☪️"}.get(food_saved, "🍽️")

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


# ═════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS PAGE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "recs":
    from src.utils.database.db import get_liked_places

    st.markdown("""
    <div class="page-hero">
      <div class="eyebrow">✦ Personalised For You</div>
      <h1>Where should you go?</h1>
      <p>Based on your interests, travel style, and saved places.</p>
    </div>""", unsafe_allow_html=True)

    liked = get_liked_places(user["id"])

    if not prof.get("interests"):
        st.info("💡 Set your interests in **Profile** to get better recommendations.")

    # Context controls (based on recommendation architecture)
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        rec_current_location = st.text_input(
            "Current location",
            value=prof.get("home_city", ""),
            placeholder="e.g. Hyderabad",
            key="recs_current_location",
        )
    with rc2:
        rec_mood = st.selectbox("Mood", MOOD_OPTIONS, key="recs_mood")
    with rc3:
        rec_time_window_type = st.selectbox("Time window type", ["Days", "Hours"], key="recs_time_type")
        rec_time_window_value = st.number_input(
            "Available time",
            min_value=1,
            max_value=30 if rec_time_window_type == "Days" else 24,
            value=2 if rec_time_window_type == "Days" else 8,
            key="recs_time_value",
        )

    rec_context = {
        "current_location": rec_current_location,
        "mood": rec_mood,
        "time_window_type": rec_time_window_type,
        "time_window_value": int(rec_time_window_value),
    }

    # Option: AI-powered or curated
    rec_mode = st.radio(
        "Recommendation mode",
        ["🎯 Curated (instant)", "🤖 AI-powered (personalized)"],
        horizontal=True,
        label_visibility="collapsed",
    )

    location_filter_label = st.radio(
        "Destination scope",
        ["All Destinations", "🇮🇳 India Only", "🌍 International Only"],
        horizontal=True,
        key="recs_location_filter",
    )
    _filter_map = {
        "All Destinations": "all",
        "🇮🇳 India Only": "india",
        "🌍 International Only": "international",
    }
    _location_filter = _filter_map[location_filter_label]

    def _normalize_recommendations(payload):
        if isinstance(payload, dict):
            if isinstance(payload.get("recommendations"), list):
                normalized = []
                for rec in payload["recommendations"]:
                    if not isinstance(rec, dict):
                        continue
                    normalized.append({
                        "name": rec.get("name") or rec.get("destination", ""),
                        "country": rec.get("country", ""),
                        "vibe": rec.get("vibe", rec_context.get("mood", "")),
                        "tags": rec.get("tags", rec.get("highlights", [])),
                        "reason": rec.get("reason") or rec.get("why_recommended", ""),
                        "budget_level": rec.get("budget_level") or f"~₹{int(rec.get('estimated_budget_per_day', 0)):,}/day" if rec.get("estimated_budget_per_day") else "",
                        "best_time": rec.get("best_time") or rec.get("best_season", ""),
                        "transport_hint": rec.get("transport_hint", ""),
                    })
                return normalized
            return []
        if isinstance(payload, list):
            return [r for r in payload if isinstance(r, dict)]
        return []

    if "🤖" in rec_mode:
        if st.session_state.ai_recs_cache:
            recs = _normalize_recommendations(st.session_state.ai_recs_cache)
        else:
            if st.button("✨ Generate AI Recommendations", type="primary"):
                with st.spinner("Generating personalized recommendations…"):
                    try:
                        prompt = build_recommendations_prompt(prof, liked, rec_context)
                        raw_recs = LLMHandler().generate_recommendations(prompt)
                        recs = _normalize_recommendations(raw_recs)
                        st.session_state.ai_recs_cache = recs
                    except Exception as e:
                        ErrorHandler.handle_api_error(e)
                        recs = get_recommendations(prof, liked, context=rec_context)
            else:
                recs = []
    else:
        recs = get_recommendations(prof, liked, context=rec_context, location_filter=_location_filter)
        st.session_state.ai_recs_cache = None

    if recs:
        cols = st.columns(3)
        for i, rec in enumerate(recs):
            with cols[i % 3]:
                tags_html = "".join(
                    f"<span style='background:rgba(13,148,136,0.1);color:var(--accent2);"
                    f"border:1px solid rgba(13,148,136,0.2);border-radius:20px;"
                    f"padding:2px 10px;font-size:0.72rem;margin-right:4px'>{t}</span>"
                    for t in rec.get("tags", [])[:2]
                )
                reason_text = (rec.get("reason", "") or "").strip()
                if reason_text:
                    reason_text = reason_text.split(".")[0].strip()
                if len(reason_text) > 90:
                    reason_text = reason_text[:87].rstrip() + "..."

                st.markdown(f"""
                <div class="rec-card">
                  <div class="dest-name">{rec.get('name', '')}</div>
                  <div class="country">{rec.get('country', '')}</div>
                  <div class="vibe">{rec.get('vibe', '')}</div>
                  <div style="margin-bottom:0.7rem">{tags_html}</div>
                  <div class="reason" style="margin-top:8px">{reason_text}</div>
                </div>""", unsafe_allow_html=True)

                if st.button(
                    f"Plan {rec.get('name', '')} →",
                    key=f"plan_{i}_{rec.get('name', '')}",
                    use_container_width=True,
                ):
                    chosen = rec.get("name", "")
                    st.session_state["prefill_dest"] = chosen
                    st.session_state.dest_count = 1
                    st.session_state["pending_nav"] = "Plan a Trip"
                    st.rerun()
    elif "🤖" not in rec_mode:
        st.markdown(
            "<p style='color:var(--muted)'>Add interests and liked places in your Profile!</p>",
            unsafe_allow_html=True,
        )
