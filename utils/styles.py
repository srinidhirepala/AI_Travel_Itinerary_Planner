"""
Global CSS — Wandr Travel Planner
Clean, modern travel theme. Warm earth tones + teal accent.
"""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400;1,700&family=DM+Sans:wght@400;500;600;700&display=swap');

:root {
    --bg:        #f7f5f2;
    --bg2:       #ffffff;
    --bg3:       #f0ede8;
    --border:    #e2ddd7;
    --text:      #1a1612;
    --muted:     #7a7068;
    --accent:    #d97706;
    --accent2:   #0d9488;
    --accent3:   #7c3aed;
    --grad:      linear-gradient(135deg, #d97706 0%, #0d9488 100%);
    --grad2:     linear-gradient(135deg, #7c3aed 0%, #0d9488 100%);
    --serif:     'Playfair Display', Georgia, serif;
    --sans:      'DM Sans', system-ui, sans-serif;
    --radius:    14px;
    --radius-sm: 8px;
    --shadow:    0 2px 12px rgba(0,0,0,0.07);
    --shadow-md: 0 6px 24px rgba(0,0,0,0.10);
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}
[data-testid="stHeader"] { background: transparent !important; }

[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .stButton > button {
    background: var(--grad) !important;
    color: #fff !important; border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important; padding: 0.55rem 1rem !important;
    transition: opacity 0.2s !important;
}
[data-testid="stSidebar"] .stButton > button:hover { opacity: 0.88 !important; }

h1, h2, h3, h4 { font-family: var(--serif) !important; color: var(--text) !important; }
h1 { font-size: 2.4rem !important; font-weight: 700 !important; }
p, span, div, li { font-family: var(--sans); }

input, textarea, [data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background: var(--bg2) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.65rem 1rem !important;
}
input:focus, textarea:focus {
    border-color: var(--accent2) !important;
    box-shadow: 0 0 0 3px rgba(13,148,136,0.15) !important;
}

[data-baseweb="tab-list"] {
    background: var(--bg3) !important;
    border-radius: var(--radius) !important;
    padding: 4px !important;
    border: 1px solid var(--border) !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    font-weight: 500 !important;
    border-radius: var(--radius-sm) !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: var(--bg2) !important;
    color: var(--accent2) !important;
    font-weight: 600 !important;
    box-shadow: var(--shadow) !important;
}

[data-testid="stMetric"] {
    background: var(--bg2) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important; padding: 1rem 1.2rem !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.82rem !important; }

.page-hero { padding: 2rem 0 1.5rem; border-bottom: 1px solid var(--border); margin-bottom: 2rem; }
.page-hero .eyebrow { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent2); margin-bottom: 0.5rem; }
.page-hero h1 { font-family: var(--serif) !important; font-size: 2.6rem !important; color: var(--text) !important; line-height: 1.1 !important; margin: 0 0 0.5rem !important; -webkit-text-fill-color: var(--text) !important; background: none !important; }
.page-hero p { color: var(--muted); font-size: 1rem; margin: 0; }

.user-avatar-bar { display: flex; align-items: center; gap: 10px; padding: 0.5rem 0; }
.user-avatar-bar img { width: 38px; height: 38px; border-radius: 50%; border: 2px solid var(--border); object-fit: cover; }
.user-avatar-bar .uname { font-weight: 600; font-size: 0.95rem; }
.user-avatar-bar .uemail { display: none; }

.activity-card { background: var(--bg2) !important; border: 1px solid var(--border) !important; border-left: 3px solid var(--accent2) !important; border-radius: var(--radius) !important; padding: 1.1rem 1.3rem !important; margin-bottom: 0.85rem !important; box-shadow: var(--shadow) !important; transition: box-shadow 0.2s !important; }
.activity-card:hover { box-shadow: var(--shadow-md) !important; }
.activity-card .time { color: var(--accent2) !important; font-weight: 700 !important; font-size: 0.82rem !important; margin-bottom: 2px; }
.activity-card .act  { font-size: 1rem !important; font-weight: 600 !important; color: var(--text) !important; }
.activity-card .meta { color: var(--muted) !important; font-size: 0.85rem !important; margin-top: 4px; }

.meal-card { background: var(--bg2) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; padding: 1rem !important; text-align: center !important; box-shadow: var(--shadow) !important; }
.meal-card .meal-label { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin-bottom: 6px; }
.meal-card .place { font-weight: 600; font-size: 0.95rem; color: var(--text); }
.meal-card .dish  { font-size: 0.85rem; color: var(--muted); margin: 3px 0; }
.meal-card .cost  { font-size: 0.85rem; color: var(--accent2); font-weight: 600; }

.budget-row { display: flex; justify-content: space-between; align-items: center; padding: 0.7rem 1rem; border-radius: var(--radius-sm); margin-bottom: 6px; background: var(--bg3); }
.budget-row.total { background: var(--bg2); border: 2px solid var(--accent2); font-weight: 700; margin-top: 8px; }
.budget-row .blabel { color: var(--text); font-size: 0.9rem; }
.budget-row .bval   { color: var(--accent2); font-weight: 600; }
.budget-row.total .bval { font-size: 1.1rem; }

.rec-card { background: var(--bg2) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; padding: 1.4rem !important; margin-bottom: 1rem !important; box-shadow: var(--shadow) !important; transition: box-shadow 0.2s, transform 0.2s !important; }
.rec-card:hover { box-shadow: var(--shadow-md) !important; transform: translateY(-2px) !important; }
.rec-card .dest-name { font-family: var(--serif); font-size: 1.3rem; font-weight: 700; color: var(--text); }
.rec-card .country   { font-size: 0.8rem; color: var(--muted); margin-bottom: 6px; }
.rec-card .vibe      { font-size: 0.9rem; color: var(--accent2); font-style: italic; margin-bottom: 8px; }
.rec-card .reason    { font-size: 0.85rem; color: var(--muted); line-height: 1.6; }

.getaway-card { background: linear-gradient(135deg, #fef3c7, #ecfdf5) !important; border: 1px solid #a7f3d0 !important; border-radius: var(--radius) !important; padding: 1.4rem !important; margin-bottom: 1rem !important; box-shadow: var(--shadow) !important; }
.getaway-card .dest-name { font-family: var(--serif); font-size: 1.2rem; font-weight: 700; color: var(--text); }
.getaway-card .tag { display: inline-block; background: rgba(13,148,136,0.1); color: var(--accent2); border: 1px solid rgba(13,148,136,0.25); border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; margin-right: 4px; margin-bottom: 6px; }

.section-header { display: flex; align-items: center; gap: 1rem; margin: 1.4rem 0 0.9rem; }
.section-header span { font-weight: 700; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); white-space: nowrap; }
.section-header .line { flex: 1; height: 1px; background: var(--border); }

.tip-chip { display: inline-block; background: var(--bg3); border: 1px solid var(--border); border-radius: 30px; padding: 0.4rem 1rem; font-size: 0.85rem; color: var(--text); margin: 4px 6px 4px 0; }
.place-pill { display: flex; align-items: center; gap: 6px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 30px; padding: 0.35rem 1rem; font-size: 0.88rem; color: var(--text); margin-bottom: 6px; }

hr { border-color: var(--border) !important; }
[data-testid="stDownloadButton"] button { background: var(--grad) !important; color: #fff !important; border: none !important; border-radius: var(--radius-sm) !important; }
[data-testid="stAlert"] { border-radius: var(--radius-sm) !important; }
</style>
"""