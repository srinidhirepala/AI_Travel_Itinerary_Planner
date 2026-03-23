"""
Wandr — AI Travel Itinerary Planner
"""
import streamlit as st
from utils.styles import GLOBAL_CSS
from utils.Auth import render_login, logout
from utils.db import (init_db, save_itinerary, get_itineraries,
                      get_itinerary_data, delete_itinerary,
                      get_profile, save_profile)
from utils.llm_handler import LLMHandler
from utils.prompt_builder import build_itinerary_prompt
from utils.recommendations import get_recommendations
from utils.route_intelligence import analyze_route
from utils.validation import validate_trip_params, ValidationError
from utils.error_handler import ErrorHandler
from utils.rate_limiter import itinerary_limiter

st.set_page_config(
    page_title="Wandr — AI Travel Planner",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
init_db()

if not render_login():
    st.stop()

user = st.session_state.get("user")
if not user:
    st.error("Please log in first.")
    st.stop()

for key, default in [
    ("itinerary", None), ("last_inputs", {}),
    ("viewing_itin_id", None), ("weekend_mode", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    pic  = user.get("picture", "")
    name = user.get("name", "Traveller")
    if pic:
        st.markdown(f"""
        <div class="user-avatar-bar">
            <img src="{pic}" referrerpolicy="no-referrer"/>
            <div><div class="uname">{name.split()[0]}</div></div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"**{name.split()[0]}**")

    st.divider()

    nav = st.radio(
        "Navigate",
        ["🗺️ Plan a Trip", "🏖️ Weekend Getaway", "📚 My Itineraries",
         "✨ Recommendations", "👤 Profile"],
        label_visibility="collapsed"
    )
    page = {
        "🗺️ Plan a Trip":    "planner",
        "🏖️ Weekend Getaway": "weekend",
        "📚 My Itineraries": "history",
        "✨ Recommendations":"recs",
        "👤 Profile":        "profile",
    }[nav]

    st.divider()

    prof = get_profile(user["id"])

    if page in ("planner", "weekend"):
        if page == "weekend":
            st.markdown("##### 🏖️ Weekend Getaway")
            hometown = st.text_input("🏠 Your city", value=prof.get("home_city", ""),
                                     placeholder="e.g. Hyderabad")
            days = st.number_input("📅 Days", min_value=1, max_value=2, value=2)
            budget = st.number_input("💰 Budget/day (₹)", min_value=500,
                                     max_value=50000, value=2000, step=500)
            destination = hometown  # will be expanded by LLM into nearby options
        else:
            st.markdown("##### ✈️ Trip Details")
            start_city = st.text_input("📍 Starting Location", placeholder="e.g. Delhi",
                                       value=st.session_state.pop("prefill_dest", ""))

            st.markdown("##### 🗺️ Destinations / Stops")
            if "dest_count" not in st.session_state:
                st.session_state.dest_count = 1

            stops = []
            for i in range(st.session_state.dest_count):
                s = st.text_input(f"Stop {i+1}", key=f"stop_{i}", placeholder="e.g. Agra")
                if s.strip():
                    stops.append(s.strip())

            if st.button("➕ Add stop", use_container_width=True):
                st.session_state.dest_count += 1
                st.rerun()

            destination = ", ".join(
                ([start_city.strip()] if start_city.strip() else []) + stops
            )

            days   = st.number_input("📅 Days", min_value=1, max_value=30, value=3)
            budget = st.number_input("💰 Budget/day (₹)", min_value=500,
                                     max_value=50000, value=2000, step=500)

        # ── Shared preferences ──
        food_pref = st.selectbox(
            "🍽️ Food preference",
            ["Vegetarian", "Non-Vegetarian", "Both (Veg & Non-Veg)", "Vegan", "Jain", "Halal"],
            index=["Vegetarian","Non-Vegetarian","Both (Veg & Non-Veg)","Vegan","Jain","Halal"]
                  .index(prof.get("food_pref", "Vegetarian"))
                  if prof.get("food_pref","Vegetarian") in
                     ["Vegetarian","Non-Vegetarian","Both (Veg & Non-Veg)","Vegan","Jain","Halal"]
                  else 0,
        )

        all_interests = ["Culture", "Food & Cuisine", "Adventure", "Nature",
                         "Shopping", "Photography", "History", "Nightlife",
                         "Wellness & Spa", "Religious Sites"]
        saved_interests = prof.get("interests", [])
        interests = st.multiselect(
            "🎯 Interests",
            all_interests,
            default=[i for i in saved_interests if i in all_interests] or ["Culture", "Food & Cuisine"]
        )

        st.divider()
        generate_btn = st.button(
            "🚀 Generate Itinerary", type="primary", use_container_width=True
        )
    else:
        generate_btn = False
        destination = days = budget = food_pref = interests = None
        hometown = ""

    st.divider()
    if st.button("Sign out", use_container_width=True):
        logout()


# ── PLANNER & WEEKEND GETAWAY ─────────────────────────────────────────────────
if page in ("planner", "weekend"):
    is_weekend = (page == "weekend")

    if is_weekend:
        st.markdown("""
        <div class="page-hero">
            <div class="eyebrow">✦ Quick Escape</div>
            <h1>Weekend Getaway</h1>
            <p>Short 1–2 day trips from your city. Optimised for minimal travel, maximum refresh.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="page-hero">
            <div class="eyebrow">✦ AI Travel Planner</div>
            <h1>Where to next?</h1>
            <p>Enter your destination and preferences to get a personalised day-by-day itinerary.</p>
        </div>""", unsafe_allow_html=True)

    if generate_btn:
        dest_to_use = destination.strip() if destination else ""
        if not dest_to_use:
            st.error("Please enter a destination or your home city.")
        else:
            current_inputs = {
                "destination": dest_to_use, "days": days, "budget": budget,
                "food_pref": food_pref, "interests": sorted(interests or []),
                "is_weekend": is_weekend,
            }
            if current_inputs != st.session_state.last_inputs:
                st.session_state.itinerary = None

            with st.spinner("Crafting your itinerary…"):
                try:
                    if not itinerary_limiter.is_allowed(user["id"]):
                        reset_time = itinerary_limiter.get_reset_time(user["id"])
                        st.warning(f"Rate limit reached. Try again in {int(reset_time)}s.")
                        st.stop()

                    validated = validate_trip_params(
                        destination=dest_to_use, days=days,
                        budget=budget, food_pref=food_pref, interests=interests or []
                    )

                    # Route analysis for multi-city
                    cities = [c.strip() for c in dest_to_use.split(",") if c.strip()]
                    route_analysis = None
                    if len(cities) > 1:
                        route_analysis = analyze_route(cities, validated["days"])
                        if route_analysis:
                            st.markdown("### 🗺️ Route Check")
                            if route_analysis["status"] == "danger":
                                st.error("⚠️ High travel fatigue detected")
                            elif route_analysis["status"] == "warning":
                                st.warning("⚠️ Moderate travel load")
                            else:
                                st.success("✅ Well-paced route")

                            c1, c2 = st.columns(2)
                            with c1: st.metric("Total Distance", f"{route_analysis['total_distance_km']} km")
                            with c2: st.metric("Transit Time", f"{route_analysis['total_travel_time_hrs']} hrs")

                            for w in route_analysis["warnings"]:
                                st.markdown(f"- {w}")
                            for j in route_analysis["illogical_jumps"]:
                                st.markdown(f"- ⚠️ Long jump: {j}")

                            # Full multi-stop map (fixed bug — all stops now shown)
                            if route_analysis.get("arcs") and len(route_analysis["arcs"]) > 0:
                                import pydeck as pdk
                                st.markdown("##### Complete Route Map")
                                vp = route_analysis["valid_path"]
                                if vp:
                                    view = pdk.ViewState(
                                        latitude=vp[0]["coordinates"][1],
                                        longitude=vp[0]["coordinates"][0],
                                        zoom=4, pitch=40
                                    )
                                    arc_layer = pdk.Layer(
                                        "ArcLayer",
                                        data=route_analysis["arcs"],
                                        get_source_position="source",
                                        get_target_position="target",
                                        get_source_color=[217, 119, 6, 220],
                                        get_target_color=[13, 148, 136, 220],
                                        get_width=5,
                                        auto_highlight=True, pickable=True,
                                    )
                                    scatter_layer = pdk.Layer(
                                        "ScatterplotLayer",
                                        data=vp,
                                        get_position="coordinates",
                                        get_color=[13, 148, 136, 255],
                                        get_radius=25000, pickable=True,
                                    )
                                    text_layer = pdk.Layer(
                                        "TextLayer",
                                        data=vp,
                                        get_position="coordinates",
                                        get_text="name",
                                        get_size=14,
                                        get_color=[26, 22, 18],
                                        get_alignment_baseline="'bottom'",
                                    )
                                    st.pydeck_chart(pdk.Deck(
                                        layers=[arc_layer, scatter_layer, text_layer],
                                        initial_view_state=view,
                                        tooltip={"text": "{source_name} → {target_name}"}
                                    ))
                            st.divider()

                    travel_style = prof.get("travel_style", "Explorer")
                    prompt = build_itinerary_prompt(
                        destination=validated["destination"],
                        days=validated["days"],
                        budget=validated["budget"],
                        food_pref=validated["food_pref"],
                        interests=validated["interests"],
                        travel_style=travel_style,
                        route_analysis=route_analysis,
                        hometown=prof.get("home_city", ""),
                        is_weekend_getaway=is_weekend,
                    )
                    result = LLMHandler().generate_itinerary(prompt)

                    st.session_state.itinerary  = result
                    st.session_state.last_inputs = current_inputs

                    save_itinerary(
                        user_id=user["id"],
                        destination=validated["destination"],
                        days=validated["days"],
                        budget=validated["budget"],
                        food_pref=validated["food_pref"],
                        interests=validated["interests"],
                        data=result,
                    )
                    st.success("Itinerary ready — saved to your history!")

                except ValidationError as e:
                    ErrorHandler.handle_validation_error(e)
                except ValueError as e:
                    st.error(f"⚠️ {e}")
                except Exception as e:
                    ErrorHandler.handle_api_error(e)

    # ── Display itinerary ─────────────────────────────────────────────────────
    if st.session_state.itinerary:
        data = st.session_state.itinerary
        inp  = st.session_state.last_inputs

        # Summary row
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("📍 Destination", inp["destination"].split(",")[0].strip())
        with c2: st.metric("📅 Duration",    f"{inp['days']} days")
        with c3: st.metric("💰 Budget",      f"₹{inp['budget']:,}/day")
        with c4: st.metric("🍽️ Food",        inp["food_pref"].split()[0])

        st.markdown("<br>", unsafe_allow_html=True)

        itin_days = data.get("days", [])
        n = len(itin_days)
        tabs = st.tabs(
            [f"Day {d['day_number']}" for d in itin_days] +
            ["💰 Budget", "💡 Tips", "🗺️ Nearby", "📥 Export"]
        )

        for idx, day in enumerate(itin_days):
            with tabs[idx]:
                theme = day.get("theme", "")
                day_title = day.get('title') or f"Day {day['day_number']}"
                st.markdown(f"### {day_title}")
                if theme:
                    st.markdown(f"<p style='color:var(--accent2);font-size:0.9rem;margin-top:-0.5rem'>{theme}</p>",
                                unsafe_allow_html=True)

                # Food highlights banner
                food_highlights = day.get("food_highlights", [])
                if food_highlights:
                    highlights_html = " &nbsp;·&nbsp; ".join(
                        f"🍴 {h}" for h in food_highlights[:3]
                    )
                    st.markdown(
                        f"<div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;"
                        f"padding:8px 14px;font-size:0.85rem;color:#166534;margin-bottom:1rem'>"
                        f"<strong>Today's food highlights:</strong> {highlights_html}</div>",
                        unsafe_allow_html=True
                    )

                # Schedule
                schedule = day.get("schedule", [])
                if schedule:
                    st.markdown('<div class="section-header"><span>Schedule</span><div class="line"></div></div>',
                                unsafe_allow_html=True)
                    for item in schedule:
                        cost = f"₹{item['cost_inr']}" if item.get("cost_inr", 0) > 0 else "Free"
                        dur  = f" · {item['duration_minutes']} min" if item.get("duration_minutes") else ""
                        food = f"<div class='meta'>🍴 {item['food_item']}</div>" if item.get("food_item") else ""
                        st.markdown(f"""
                        <div class="activity-card">
                            <div class="time">{item.get('time','')}</div>
                            <div class="act">{item.get('activity','')}</div>
                            <div class="meta">📍 {item.get('location','')} &nbsp;·&nbsp; {cost}{dur}</div>
                            {food}
                            <div class="meta" style="margin-top:4px;color:#aaa">{item.get('notes','')}</div>
                        </div>""", unsafe_allow_html=True)

                # Meals
                meals = day.get("meals", {})
                if meals:
                    st.markdown('<div class="section-header"><span>Meals</span><div class="line"></div></div>',
                                unsafe_allow_html=True)
                    mc1, mc2, mc3 = st.columns(3)
                    for col, (label, icon, key) in zip(
                        [mc1, mc2, mc3],
                        [("Breakfast","🌅","breakfast"), ("Lunch","☀️","lunch"), ("Dinner","🌙","dinner")]
                    ):
                        m = meals.get(key, {})
                        with col:
                            why = f"<div style='font-size:0.75rem;color:var(--accent2);margin-top:4px'>{m.get('why','')}</div>" if m.get("why") else ""
                            cuisine = f"<div style='font-size:0.75rem;color:var(--muted)'>{m.get('cuisine','')}</div>" if m.get("cuisine") else ""
                            st.markdown(f"""
                            <div class="meal-card">
                                <div class="meal-label">{icon} {label}</div>
                                <div class="place">{m.get('place','—')}</div>
                                <div class="dish">{m.get('dish','')}</div>
                                {cuisine}
                                <div class="cost">₹{m.get('cost_inr','—')}</div>
                                {why}
                            </div>""", unsafe_allow_html=True)

                # Nearby alternatives
                alternatives = day.get("nearby_alternatives", [])
                if alternatives:
                    with st.expander("📍 Nearby alternatives to save travel time"):
                        for alt in alternatives:
                            st.markdown(
                                f"**{alt.get('name','')}** "
                                f"({alt.get('distance_km','?')} km) — {alt.get('why','')}"
                            )

                day_total = day.get("day_total_inr")
                if day_total:
                    st.markdown(
                        f"<p style='text-align:right;color:var(--muted);font-size:0.85rem'>"
                        f"Day total: <strong style='color:var(--accent2)'>₹{day_total:,}</strong></p>",
                        unsafe_allow_html=True
                    )

        # Budget tab
        with tabs[n]:
            st.markdown("### Budget Breakdown")
            bd = data.get("budget_breakdown", {})
            if bd:
                for label, val in [
                    ("🏨 Accommodation / night", bd.get("accommodation_per_night")),
                    ("🍽️ Food / day",             bd.get("food_per_day")),
                    ("🚌 Transport / day",         bd.get("transport_per_day")),
                    ("🎟️ Activities (total)",      bd.get("activities_total")),
                    ("🛍️ Miscellaneous",           bd.get("miscellaneous")),
                ]:
                    if val:
                        st.markdown(f"""
                        <div class="budget-row">
                            <span class="blabel">{label}</span>
                            <span class="bval">₹{val:,}</span>
                        </div>""", unsafe_allow_html=True)
                grand = bd.get("grand_total")
                if grand:
                    st.markdown(f"""
                    <div class="budget-row total">
                        <span class="blabel">💳 Grand Total</span>
                        <span class="bval">₹{grand:,}</span>
                    </div>""", unsafe_allow_html=True)

        # Tips tab
        with tabs[n + 1]:
            st.markdown("### Tips & Practicalities")
            for tip in data.get("practical_tips", []):
                st.markdown(f'<div class="tip-chip">{tip}</div>', unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                stay = data.get("best_areas_to_stay", [])
                if stay:
                    st.markdown("**🏨 Where to stay**")
                    for s in stay: st.markdown(f"- {s}")
            with col_b:
                transport = data.get("local_transport", [])
                if transport:
                    st.markdown("**🚌 Getting around**")
                    for t in transport: st.markdown(f"- {t}")

        # Nearby destinations tab
        with tabs[n + 2]:
            st.markdown("### Nearby Destinations Worth Visiting")
            nearby = data.get("nearby_destinations", [])
            if nearby:
                nc = st.columns(min(len(nearby), 3))
                for i, dest in enumerate(nearby[:6]):
                    with nc[i % 3]:
                        tags = f"<span class='getaway-card tag'>{dest.get('best_for','')}</span>" if dest.get("best_for") else ""
                        st.markdown(f"""
                        <div class="getaway-card">
                            <div class="dest-name">{dest.get('name','')}</div>
                            <div style='font-size:0.82rem;color:var(--muted);margin:4px 0'>
                                {dest.get('distance_km','?')} km away
                            </div>
                            {tags}
                            <div style='font-size:0.85rem;color:var(--muted);margin-top:6px'>
                                {dest.get('why_visit','')}
                            </div>
                        </div>""", unsafe_allow_html=True)
                        if st.button(f"Plan {dest.get('name','')} →",
                                     key=f"plan_nearby_{i}", use_container_width=True):
                            st.session_state["prefill_dest"] = dest.get("name", "")
                            st.rerun()
            else:
                st.markdown("<p style='color:var(--muted)'>No nearby destinations in this itinerary.</p>",
                            unsafe_allow_html=True)

        # Export tab
        with tabs[n + 3]:
            st.markdown("### Export")
            lines = [f"TRAVEL ITINERARY: {inp['destination'].upper()}",
                     f"Food: {inp['food_pref']}  |  Budget: ₹{inp['budget']}/day",
                     "=" * 50, ""]
            for day in itin_days:
                lines.append(f"DAY {day['day_number']}: {day.get('title','')}")
                lines.append("-" * 40)
                for item in day.get("schedule", []):
                    lines.append(f"  {item.get('time','')}  {item.get('activity','')} @ {item.get('location','')}")
                    if item.get("food_item"):
                        lines.append(f"         🍴 {item['food_item']}")
                    if item.get("notes"):
                        lines.append(f"         → {item['notes']}")
                meals = day.get("meals", {})
                if meals:
                    lines += ["", "  MEALS:"]
                    for mkey in ["breakfast", "lunch", "dinner"]:
                        m = meals.get(mkey, {})
                        if m:
                            lines.append(
                                f"    {mkey.title()}: {m.get('place','')} — "
                                f"{m.get('dish','')} (₹{m.get('cost_inr','')})"
                            )
                lines.append("")
            slug = inp["destination"].lower().replace(" ", "_")[:20]
            st.download_button(
                "📄 Download as Text", "\n".join(lines),
                f"{slug}_itinerary.txt", "text/plain", use_container_width=True
            )
    else:
        st.markdown("""
        <div style='text-align:center;padding:4rem 0 2rem'>
            <div style='font-size:4rem;margin-bottom:1rem'>🌍</div>
            <p style='font-family:var(--serif);font-size:1.6rem;color:var(--text);margin-bottom:0.5rem'>
                Ready when you are
            </p>
            <p style='color:var(--muted)'>
                Fill in your trip details in the sidebar to get started.
            </p>
        </div>""", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        for col, icon, title, desc in [
            (c1, "📅", "Day-by-day Schedule", "Timed activities with real locations and costs"),
            (c2, "🍽️", "Food Guide", "Dishes that match your food preference, every meal"),
            (c3, "🗺️", "Nearby Alternatives", "Save time with smarter stop clustering"),
        ]:
            with col:
                st.markdown(f"""
                <div style='background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);
                            padding:1.5rem;text-align:center'>
                    <div style='font-size:2rem;margin-bottom:0.8rem'>{icon}</div>
                    <div style='font-family:var(--serif);font-size:1.05rem;margin-bottom:0.4rem'>{title}</div>
                    <div style='font-size:0.85rem;color:var(--muted)'>{desc}</div>
                </div>""", unsafe_allow_html=True)


# ── PROFILE PAGE ──────────────────────────────────────────────────────────────
elif page == "profile":
    from utils.db import get_liked_places, add_liked_place, delete_liked_place

    st.markdown("""
    <div class="page-hero">
        <div class="eyebrow">✦ Account</div>
        <h1>Your Profile</h1>
        <p>Preferences are used to personalise every itinerary and recommendation.</p>
    </div>""", unsafe_allow_html=True)

    prof  = get_profile(user["id"])
    liked = get_liked_places(user["id"])

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("#### Travel Preferences")
        with st.form("profile_form"):
            food_opts  = ["Vegetarian", "Non-Vegetarian", "Both (Veg & Non-Veg)", "Vegan", "Jain", "Halal"]
            style_opts = ["Explorer", "Foodie", "Cultural", "Relaxer", "Adventurer", "Shopaholic"]

            current_food = prof.get("food_pref", "Vegetarian")
            food_idx = food_opts.index(current_food) if current_food in food_opts else 0

            new_food = st.selectbox("🍽️ Default food preference", food_opts, index=food_idx)
            new_interests = st.multiselect(
                "🎯 Interests",
                ["Culture", "Food & Cuisine", "Adventure", "Nature", "Shopping",
                 "Photography", "History", "Nightlife", "Wellness & Spa", "Religious Sites"],
                default=prof.get("interests", [])
            )
            new_home = st.text_input(
                "🏠 Home city (for Weekend Getaway)",
                value=prof.get("home_city", ""),
                placeholder="e.g. Hyderabad"
            )
            new_style = st.selectbox(
                "🧳 Travel style", style_opts,
                index=style_opts.index(prof.get("travel_style", "Explorer"))
            )

            if st.form_submit_button("💾 Save Preferences", use_container_width=True):
                save_profile(user["id"], new_food, new_interests, new_home, new_style)
                st.success("Preferences saved!")
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
                        &nbsp;<span style='color:var(--muted)'>{place.get('country','')}</span>
                    </div>""", unsafe_allow_html=True)
                with pcol2:
                    if st.button("✕", key=f"del_{place['id']}", help="Remove"):
                        delete_liked_place(place["id"])
                        st.rerun()
        else:
            st.markdown("<p style='color:var(--muted);font-size:0.9rem'>No liked places yet.</p>",
                        unsafe_allow_html=True)

        with st.expander("➕ Add a place"):
            with st.form("add_place"):
                p_name    = st.text_input("Place name", placeholder="Jaipur, Hampi…")
                p_type    = st.selectbox("Type", ["city", "attraction", "restaurant"])
                p_country = st.text_input("Country", placeholder="India…")
                p_notes   = st.text_area("Notes (optional)", height=60)
                if st.form_submit_button("Add", use_container_width=True):
                    if p_name:
                        add_liked_place(user["id"], p_name, p_type, p_country, p_notes)
                        st.success(f"Added {p_name}!")
                        st.rerun()


# ── HISTORY PAGE ──────────────────────────────────────────────────────────────
elif page == "history":
    st.markdown("""
    <div class="page-hero">
        <div class="eyebrow">✦ Saved Plans</div>
        <h1>My Itineraries</h1>
        <p>Every trip you've planned, saved automatically.</p>
    </div>""", unsafe_allow_html=True)

    itins = get_itineraries(user["id"])

    if not itins:
        st.markdown("""
        <div style='text-align:center;padding:3rem 0'>
            <div style='font-size:3rem'>📭</div>
            <p style='font-family:var(--serif);font-size:1.3rem;margin:0.5rem 0'>No itineraries yet</p>
            <p style='color:var(--muted)'>Plan a trip and it'll appear here automatically.</p>
        </div>""", unsafe_allow_html=True)
    elif st.session_state.viewing_itin_id:
        itin_data    = get_itinerary_data(st.session_state.viewing_itin_id)
        current_meta = next((i for i in itins if i["id"] == st.session_state.viewing_itin_id), None)

        if st.button("← Back"):
            st.session_state.viewing_itin_id = None
            st.rerun()

        if itin_data and current_meta:
            st.markdown(f"### {current_meta['destination']} — {current_meta['days']} days")
            st.markdown(
                f"<p style='color:var(--muted)'>{current_meta['created_at'][:10]} · "
                f"{current_meta['food_pref']} · ₹{current_meta['budget']:,}/day</p>",
                unsafe_allow_html=True
            )
            itin_days = itin_data.get("days", [])
            n    = len(itin_days)
            tabs = st.tabs([f"Day {d['day_number']}" for d in itin_days] + ["💰 Budget"])

            for idx, day in enumerate(itin_days):
                with tabs[idx]:
                    st.markdown(f"### {day.get('title', '')}")
                    food_highlights = day.get("food_highlights", [])
                    if food_highlights:
                        st.markdown(
                            f"<div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;"
                            f"padding:8px 14px;font-size:0.85rem;color:#166534;margin-bottom:1rem'>"
                            f"🍴 {' · '.join(food_highlights[:3])}</div>",
                            unsafe_allow_html=True
                        )
                    for item in day.get("schedule", []):
                        cost = f"₹{item['cost_inr']}" if item.get("cost_inr", 0) > 0 else "Free"
                        food = f"<div class='meta'>🍴 {item['food_item']}</div>" if item.get("food_item") else ""
                        st.markdown(f"""
                        <div class="activity-card">
                            <div class="time">{item.get('time','')}</div>
                            <div class="act">{item.get('activity','')}</div>
                            <div class="meta">📍 {item.get('location','')} · {cost}</div>
                            {food}
                            <div class="meta" style="color:#aaa">{item.get('notes','')}</div>
                        </div>""", unsafe_allow_html=True)

                    meals = day.get("meals", {})
                    if meals:
                        st.markdown('<div class="section-header"><span>Meals</span><div class="line"></div></div>',
                                    unsafe_allow_html=True)
                        mc1, mc2, mc3 = st.columns(3)
                        for col, (label, icon, key) in zip(
                            [mc1, mc2, mc3],
                            [("Breakfast","🌅","breakfast"), ("Lunch","☀️","lunch"), ("Dinner","🌙","dinner")]
                        ):
                            m = meals.get(key, {})
                            with col:
                                st.markdown(f"""
                                <div class="meal-card">
                                    <div class="meal-label">{icon} {label}</div>
                                    <div class="place">{m.get('place','—')}</div>
                                    <div class="dish">{m.get('dish','')}</div>
                                    <div class="cost">₹{m.get('cost_inr','—')}</div>
                                </div>""", unsafe_allow_html=True)

            with tabs[n]:
                bd = itin_data.get("budget_breakdown", {})
                if bd:
                    for k, v in bd.items():
                        cls = "budget-row total" if k == "grand_total" else "budget-row"
                        if v:
                            st.markdown(
                                f'<div class="{cls}"><span class="blabel">'
                                f'{k.replace("_"," ").title()}</span>'
                                f'<span class="bval">₹{v:,}</span></div>',
                                unsafe_allow_html=True
                            )
    else:
        for itin in itins:
            c1, c2 = st.columns([6, 1])
            with c1:
                if st.button(
                    f"📍 {itin['destination']}  ·  {itin['days']} days  ·  "
                    f"₹{itin['budget']:,}/day  ·  {itin['food_pref']}  ·  {itin['created_at'][:10]}",
                    key=f"view_{itin['id']}", use_container_width=True
                ):
                    st.session_state.viewing_itin_id = itin["id"]
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_{itin['id']}", help="Delete"):
                    delete_itinerary(itin["id"])
                    st.rerun()


# ── RECOMMENDATIONS PAGE ──────────────────────────────────────────────────────
elif page == "recs":
    from utils.db import get_liked_places

    st.markdown("""
    <div class="page-hero">
        <div class="eyebrow">✦ Personalised For You</div>
        <h1>Where should you go?</h1>
        <p>Based on your interests, travel style, and saved places.</p>
    </div>""", unsafe_allow_html=True)

    liked = get_liked_places(user["id"])
    recs  = get_recommendations(prof, liked)

    if not prof.get("interests"):
        st.info("Set your interests in Profile to get better recommendations.")

    if not recs:
        st.markdown("<p style='color:var(--muted)'>Add interests and liked places in your profile!</p>",
                    unsafe_allow_html=True)
    else:
        cols = st.columns(3)
        for i, rec in enumerate(recs):
            with cols[i % 3]:
                tags_html = "".join(
                    f"<span style='background:rgba(13,148,136,0.1);color:var(--accent2);"
                    f"border:1px solid rgba(13,148,136,0.2);border-radius:20px;"
                    f"padding:2px 10px;font-size:0.72rem;margin-right:4px'>{t}</span>"
                    for t in rec["tags"][:3]
                )
                st.markdown(f"""
                <div class="rec-card">
                    <div class="dest-name">{rec['name']}</div>
                    <div class="country">{rec['country']}</div>
                    <div class="vibe">{rec['vibe']}</div>
                    <div style="margin-bottom:0.7rem">{tags_html}</div>
                    <div class="reason">{rec['reason']}</div>
                </div>""", unsafe_allow_html=True)

                if st.button(f"Plan {rec['name']} →", key=f"plan_{rec['name']}", use_container_width=True):
                    st.session_state["prefill_dest"] = rec["name"]
                    st.rerun()


# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center;color:var(--muted);font-size:0.75rem'>Wandr · AI Travel Planner</p>",
    unsafe_allow_html=True
)