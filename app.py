"""
Wandr — AI Travel Itinerary Planner
"""
import streamlit as st
from utils.styles import GLOBAL_CSS
from utils.Auth import render_login, logout
from utils.db import (init_db, save_itinerary, get_itineraries,
                      get_itinerary_data, delete_itinerary)
from utils.llm_handler import LLMHandler
from utils.prompt_builder import build_itinerary_prompt
from utils.recommendations import get_recommendations
from utils.route_intelligence import analyze_route
from utils.validation import validate_trip_params, ValidationError
from utils.error_handler import ErrorHandler
from utils.rate_limiter import itinerary_limiter

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wandr — AI Travel Planner",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

init_db()

# ── Auth gate - Strict enforcement ────────────────────────────────────────────
if not render_login():
    st.stop()

user = st.session_state.get("user")
if not user:
    st.error("⛔ **Unauthorized Access** — Please log in first")
    st.stop()

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("itinerary", None),
    ("last_inputs", {}),
    ("active_tab", "planner"),
    ("viewing_itin_id", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    pic   = user.get("picture", "")
    name  = user.get("name", "Traveller")
    email = user.get("email", "")
    if pic:
        st.markdown(f"""
        <div class="user-avatar-bar">
            <img src="{pic}" referrerpolicy="no-referrer"/>
            <div>
                <div class="uname">{name.split()[0]}</div>
                <div class="uemail">{email}</div>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"**{name}**")

    st.divider()

    nav = st.radio(
        "Navigate",
        ["🗺️ Plan a Trip", "👤 My Profile", "📚 My Itineraries", "✨ Recommendations"],
        label_visibility="collapsed"
    )
    page = {
        "🗺️ Plan a Trip":      "planner",
        "👤 My Profile":        "profile",
        "📚 My Itineraries":    "history",
        "✨ Recommendations":   "recs",
    }[nav]

    st.divider()

    if page == "planner":
        st.markdown("##### ✈️ Trip Details")

        start_city = st.text_input("📍 Starting Location", placeholder="e.g. Delhi")
        
        st.markdown("##### 🗺️ Stops / Destinations")
        
        if "dest_count" not in st.session_state:
            st.session_state.dest_count = 1
            
        stops = []
        for i in range(st.session_state.dest_count):
            stop = st.text_input(f"Stop {i+1}", key=f"stop_{i}", placeholder="e.g. Agra")
            if stop.strip():
                stops.append(stop.strip())
                
        if st.sidebar.button("➕ Add another stop", use_container_width=True):
            st.session_state.dest_count += 1
            st.rerun()

        # Combine route back to legacy string format for downstream systems
        destination = ", ".join([start_city.strip()] + stops) if start_city and start_city.strip() else ", ".join(stops)

        # Stacking vertically ensures perfect alignment in the narrow sidebar
        days = st.number_input("📅 Days", min_value=1, max_value=30, value=3)
        
        budget = st.select_slider(
            "💰 Budget/day",
            options=[500, 1000, 1500, 2000, 3000, 5000, 10000],
            value=2000,
            format_func=lambda x: f"₹{x}"
        )

        food_pref = st.selectbox(
            "🍽️ Food",
            ["Vegetarian", "Non-Vegetarian", "Vegan", "Jain", "Halal"]
        )
        interests = st.multiselect(
            "🎯 Interests",
            ["Culture", "Food", "Adventure", "Nature", "Shopping", "Photography"],
            default=["Culture", "Food"]
        )

        # Pre-fill interests from profile if user hasn't selected any
        from utils.db import get_profile
        prof = get_profile(user["id"])
        if prof.get("interests") and not interests:
            interests = prof["interests"]

        st.divider()
        generate_btn = st.button("🚀 Generate Itinerary", type="primary", use_container_width=True)
    else:
        generate_btn = False
        destination = days = budget = food_pref = interests = None

    st.divider()
    if st.button("Sign out", use_container_width=True):
        logout()


# ── PLANNER PAGE ──────────────────────────────────────────────────────────────
if page == "planner":
    st.markdown("""
    <div class="page-hero">
        <div class="eyebrow">✦ AI Travel Planner</div>
        <h1>Where to next?</h1>
        <p>Fill in your trip details and get a full day-by-day itinerary, tailored to you.</p>
    </div>""", unsafe_allow_html=True)

    if generate_btn:
        if not destination or not destination.strip():
            st.error("⚠️ Please enter a destination!")
        else:
            current_inputs = {
                "destination": destination.strip(), "days": days, "budget": budget,
                "food_pref": food_pref, "interests": sorted(interests or [])
            }
            if current_inputs != st.session_state.last_inputs:
                st.session_state.itinerary = None

            with st.spinner("Building your itinerary…"):
                try:
                    # Rate limit check
                    if not itinerary_limiter.is_allowed(user["id"]):
                        reset_time = itinerary_limiter.get_reset_time(user["id"])
                        st.warning(f"⏱️ Rate limit reached. Try again in {int(reset_time)} seconds.")
                        st.stop()

                    # Validate inputs
                    validated = validate_trip_params(
                        destination=destination.strip(),
                        days=days, budget=budget,
                        food_pref=food_pref, interests=interests or []
                    )

                    
                    # Multi-city route intelligence
                    cities = [c.strip() for c in destination.split(",") if c.strip()]
                    route_analysis = None
                    if len(cities) > 1:
                        route_analysis = analyze_route(cities, validated["days"])
                        
                        # Display Reality Check to user
                        if route_analysis:
                            st.markdown("### 🚨 ROUTE REALITY CHECK")
                            if route_analysis["status"] == "danger":
                                st.error("⚠️ **High Burnout Risk Detected!**")
                            elif route_analysis["status"] == "warning":
                                st.warning("⚠️ **Moderate Burnout Risk**")
                            else:
                                st.success("✅ **Looks like a well-paced route!**")
                                
                            col_rc1, col_rc2 = st.columns(2)
                            with col_rc1:
                                st.metric("Total Travel Distance", f"{route_analysis['total_distance_km']} km")
                            with col_rc2:
                                st.metric("Est. Time in Transit", f"{route_analysis['total_travel_time_hrs']} hours")
                                
                            if route_analysis["warnings"]:
                                for w in route_analysis["warnings"]:
                                    st.markdown(f"- 🚩 {w}")
                            if route_analysis["illogical_jumps"]:
                                st.markdown("**Illogical Jumps:**")
                                for j in route_analysis["illogical_jumps"]:
                                    st.markdown(f"- 🦘 {j}")
                                    
                            if route_analysis.get("arcs"):
                                import pydeck as pdk
                                st.markdown("### 🗺️ Route Map")
                                view_state = pdk.ViewState(
                                    latitude=route_analysis["valid_path"][0]["coordinates"][1],
                                    longitude=route_analysis["valid_path"][0]["coordinates"][0],
                                    zoom=4,
                                    pitch=45
                                )
                                arc_layer = pdk.Layer(
                                    "ArcLayer",
                                    data=route_analysis["arcs"],
                                    get_source_position="source",
                                    get_target_position="target",
                                    get_source_color=[59, 130, 246, 200],  # Blue
                                    get_target_color=[236, 72, 153, 200],  # Pink
                                    get_width=4,
                                    auto_highlight=True,
                                    pickable=True
                                )
                                scatter_layer = pdk.Layer(
                                    "ScatterplotLayer",
                                    data=route_analysis["valid_path"],
                                    get_position="coordinates",
                                    get_color=[59, 130, 246, 255],
                                    get_radius=20000,
                                    pickable=True
                                )
                                r = pdk.Deck(
                                    layers=[arc_layer, scatter_layer],
                                    initial_view_state=view_state,
                                    tooltip={"text": "{source_name} to {target_name}"}
                                )
                                st.pydeck_chart(r)
                            
                            st.divider()

                    # Generate via AI
                    llm    = LLMHandler()
                    
                    # Fetch travel style / pacing from DB
                    prof = get_profile(user["id"])
                    travel_style = prof.get("travel_style", "Explorer")

                    prompt = build_itinerary_prompt(
                        destination=validated["destination"],
                        days=validated["days"],
                        budget=validated["budget"],
                        food_pref=validated["food_pref"],
                        interests=validated["interests"],
                        travel_style=travel_style,
                        route_analysis=route_analysis
                    )
                    result = llm.generate_itinerary(prompt)

                    st.session_state.itinerary  = result
                    st.session_state.last_inputs = current_inputs

                    # Auto-save
                    save_itinerary(
                        user_id=user["id"],
                        destination=validated["destination"],
                        days=validated["days"],
                        budget=validated["budget"],
                        food_pref=validated["food_pref"],
                        interests=validated["interests"],
                        data=result,
                    )
                    st.success("✅ Itinerary ready — also saved to your history!")

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

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("📍 Destination", inp["destination"])
        with c2: st.metric("📅 Duration",    f"{inp['days']} days")
        with c3: st.metric("💰 Budget",      f"₹{inp['budget']}/day")
        with c4: st.metric("🍽️ Food",        inp["food_pref"].split()[0])

        st.markdown("<br>", unsafe_allow_html=True)

        itinerary_days = data.get("days", [])
        n = len(itinerary_days)
        tabs = st.tabs(
            [f"Day {d['day_number']}" for d in itinerary_days] +
            ["💰 Budget", "💡 Tips", "📥 Export"]
        )

        # Day tabs
        for idx, day in enumerate(itinerary_days):
            with tabs[idx]:
                day_title = day.get('title', f"Day {day['day_number']}")
                st.markdown(f"### {day_title}")

                schedule = day.get("schedule", [])
                if schedule:
                    st.markdown('<div class="section-header"><span>Schedule</span><div class="line"></div></div>', unsafe_allow_html=True)
                    for item in schedule:
                        cost = f"₹{item['cost_inr']}" if item.get("cost_inr", 0) > 0 else "Free"
                        dur  = f" · {item['duration_minutes']} min" if item.get("duration_minutes") else ""
                        st.markdown(f"""
                        <div class="activity-card">
                            <div class="time">{item.get('time','')}</div>
                            <div class="act">{item.get('activity','')}</div>
                            <div class="meta">📍 {item.get('location','')} &nbsp;·&nbsp; {cost}{dur}</div>
                            <div class="meta" style="margin-top:0.3rem;color:#aaa">{item.get('notes','')}</div>
                        </div>""", unsafe_allow_html=True)

                meals = day.get("meals", {})
                if meals:
                    st.markdown('<div class="section-header"><span>Meals</span><div class="line"></div></div>', unsafe_allow_html=True)
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

                day_total = day.get("day_total_inr")
                if day_total:
                    st.markdown(
                        f"<br><p style='text-align:right;color:var(--muted);font-size:0.85rem'>"
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

        # Export tab
        with tabs[n + 2]:
            st.markdown("### Export")
            lines = [f"TRAVEL ITINERARY: {inp['destination'].upper()}", "=" * 50, ""]
            for day in itinerary_days:
                lines.append(f"DAY {day['day_number']}: {day.get('title','')}")
                lines.append("-" * 40)
                for item in day.get("schedule", []):
                    lines.append(f"  {item.get('time','')}  {item.get('activity','')} @ {item.get('location','')}")
                    if item.get("notes"): lines.append(f"         → {item['notes']}")
                meals = day.get("meals", {})
                if meals:
                    lines += ["", "  MEALS:"]
                    for mkey in ["breakfast", "lunch", "dinner"]:
                        m = meals.get(mkey, {})
                        if m: lines.append(f"    {mkey.title()}: {m.get('place','')} — {m.get('dish','')} (₹{m.get('cost_inr','')})")
                lines.append("")
            bd = data.get("budget_breakdown", {})
            if bd:
                lines += ["BUDGET BREAKDOWN", "-" * 40]
                for k, v in bd.items():
                    if v: lines.append(f"  {k.replace('_',' ').title()}: ₹{v:,}")
            slug = inp["destination"].lower().replace(" ", "_")
            st.download_button("📄 Download as Text", "\n".join(lines),
                               f"{slug}_itinerary.txt", "text/plain", use_container_width=True)

    else:
        st.markdown("""
        <div style='text-align:center;padding:4rem 0 2rem;'>
            <div style='font-size:4rem;margin-bottom:1rem'>🌍</div>
            <p style='font-family:var(--serif);font-size:1.6rem;color:var(--text);margin-bottom:0.5rem'>Ready when you are</p>
            <p style='color:var(--muted)'>Enter your destination and trip details in the sidebar to get started.</p>
        </div>""", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        for col, icon, title, desc in [
            (c1, "📅", "Day-by-day Schedule", "Timed activities with real locations and costs"),
            (c2, "🍽️", "Food Guide",           "Restaurants matching your dietary preference"),
            (c3, "💰", "Budget Breakdown",     "Itemised estimates for the full trip"),
        ]:
            with col:
                st.markdown(f"""
                <div style='background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);
                            padding:1.5rem;text-align:center;height:100%'>
                    <div style='font-size:2rem;margin-bottom:0.8rem'>{icon}</div>
                    <div style='font-family:var(--serif);font-size:1.1rem;margin-bottom:0.5rem'>{title}</div>
                    <div style='font-size:0.85rem;color:var(--muted)'>{desc}</div>
                </div>""", unsafe_allow_html=True)


# ── PROFILE PAGE ──────────────────────────────────────────────────────────────
elif page == "profile":
    from utils.db import get_profile, save_profile, get_liked_places, add_liked_place, delete_liked_place

    st.markdown("""
    <div class="page-hero">
        <div class="eyebrow">✦ Account</div>
        <h1>Your Profile</h1>
        <p>Your travel preferences power the recommendation engine.</p>
    </div>""", unsafe_allow_html=True)

    prof  = get_profile(user["id"])
    liked = get_liked_places(user["id"])

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("#### ✏️ Travel Preferences")
        with st.form("profile_form"):
            food_opts  = ["Vegetarian", "Non-Vegetarian", "Vegan", "Jain", "Halal"]
            style_opts = ["Explorer", "Foodie", "Cultural", "Relaxer", "Adventurer", "Shopaholic"]
            new_food = st.selectbox("🍽️ Default food preference", food_opts,
                index=food_opts.index(prof.get("food_pref", "Vegetarian")))
            new_interests = st.multiselect(
                "🎯 Your interests",
                ["Culture", "Food", "Adventure", "Nature", "Shopping", "Photography"],
                default=prof.get("interests", [])
            )
            new_home  = st.text_input("🏠 Home city", value=prof.get("home_city", ""),
                                      placeholder="Mumbai, Hyderabad…")
            new_style = st.selectbox("🧳 Travel style", style_opts,
                index=style_opts.index(prof.get("travel_style", "Explorer")))
            if st.form_submit_button("💾 Save Preferences", use_container_width=True):
                save_profile(user["id"], new_food, new_interests, new_home, new_style)
                st.success("Preferences saved!")
                st.rerun()

    with col_right:
        st.markdown("#### ❤️ Liked Places")
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
            st.markdown("<p style='color:var(--muted);font-size:0.9rem'>No liked places yet. Add some below!</p>",
                        unsafe_allow_html=True)

        with st.expander("➕ Add a place"):
            with st.form("add_place"):
                p_name    = st.text_input("Place name", placeholder="Jaipur, Eiffel Tower…")
                p_type    = st.selectbox("Type", ["city", "attraction", "restaurant"])
                p_country = st.text_input("Country", placeholder="India, France…")
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
    else:
        if st.session_state.viewing_itin_id:
            itin_data    = get_itinerary_data(st.session_state.viewing_itin_id)
            current_meta = next((i for i in itins if i["id"] == st.session_state.viewing_itin_id), None)

            if st.button("← Back to all itineraries"):
                st.session_state.viewing_itin_id = None
                st.rerun()

            if itin_data and current_meta:
                st.markdown(f"### {current_meta['destination']} — {current_meta['days']} days")
                st.markdown(
                    f"<p style='color:var(--muted)'>{current_meta['created_at'][:10]} · "
                    f"{current_meta['food_pref']} · ₹{current_meta['budget']}/day</p>",
                    unsafe_allow_html=True
                )
                itin_days = itin_data.get("days", [])
                n    = len(itin_days)
                tabs = st.tabs([f"Day {d['day_number']}" for d in itin_days] + ["💰 Budget"])

                for idx, day in enumerate(itin_days):
                    with tabs[idx]:
                        st.markdown(f"### {day.get('title', '')}")
                        for item in day.get("schedule", []):
                            cost = f"₹{item['cost_inr']}" if item.get("cost_inr", 0) > 0 else "Free"
                            st.markdown(f"""
                            <div class="activity-card">
                                <div class="time">{item.get('time','')}</div>
                                <div class="act">{item.get('activity','')}</div>
                                <div class="meta">📍 {item.get('location','')} · {cost}</div>
                                <div class="meta" style="color:#aaa">{item.get('notes','')}</div>
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
                        f"₹{itin['budget']}/day  ·  {itin['created_at'][:10]}",
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
    from utils.db import get_profile, get_liked_places

    st.markdown("""
    <div class="page-hero">
        <div class="eyebrow">✦ Personalised For You</div>
        <h1>Where should you go?</h1>
        <p>Based on your interests, travel style, and saved places.</p>
    </div>""", unsafe_allow_html=True)

    prof  = get_profile(user["id"])
    liked = get_liked_places(user["id"])
    recs  = get_recommendations(prof, liked)

    if not prof.get("interests"):
        st.info("👤 Set your interests in **My Profile** to get better recommendations.")

    if not recs:
        st.markdown(
            "<p style='color:var(--muted)'>No recommendations yet — "
            "add some interests and liked places in your profile!</p>",
            unsafe_allow_html=True
        )
    else:
        cols = st.columns(3)
        for i, rec in enumerate(recs):
            with cols[i % 3]:
                tags_html = "".join(
                    f"<span style='background:rgba(79,195,161,0.12);color:var(--accent3);"
                    f"border:1px solid rgba(79,195,161,0.25);border-radius:20px;"
                    f"padding:0.1rem 0.6rem;font-size:0.72rem;margin-right:0.3rem'>{t}</span>"
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

    st.markdown(
        '<div class="section-header"><span>How recommendations work</span><div class="line"></div></div>',
        unsafe_allow_html=True
    )
    st.markdown("""
    <p style='color:var(--muted);font-size:0.85rem;line-height:1.7'>
    Recommendations are scored by matching destination tags against your saved interests and travel style.
    Countries you've liked before get a boost. The more you add to your profile, the better these get.
    </p>""", unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center;color:var(--muted);font-size:0.75rem;"
    "font-family:var(--sans)'>Wandr · AI Travel Planner</p>",
    unsafe_allow_html=True
)