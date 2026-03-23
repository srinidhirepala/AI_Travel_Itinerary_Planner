"""
Global CSS for Light Mode
Vibrant, colorful travel theme with clean alignments and soft shadows.
"""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400;1,700&family=DM+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

:root {
    --bg-main: #f9fafb;
    --bg-card: #ffffff;
    --border: #e5e7eb;
    --text-main: #111827;
    --text-muted: #6b7280;
    --accent-primary: #3b82f6;
    --accent-hover: #2563eb;
    --gradient-primary: linear-gradient(135deg, #3b82f6, #8b5cf6);
    --font-serif: 'Playfair Display', serif;
    --font-sans: 'DM Sans', 'Inter', sans-serif;
    --radius-md: 12px;
    --radius-lg: 16px;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-main) !important;
    background-image: none !important;
    color: var(--text-main) !important;
    font-family: var(--font-sans) !important;
}

[data-testid="stHeader"] {
    background-color: transparent !important;
}

[data-testid="stSidebar"] {
    background-color: var(--bg-card) !important;
    background-image: none !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-main) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: var(--gradient-primary) !important;
    color: white !important;
    border-radius: var(--radius-md) !important;
    border: none !important;
    font-weight: 600 !important;
    padding: 0.6rem 1rem !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-md) !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-serif) !important;
    color: var(--text-main) !important;
}
p, span, div, li {
    font-family: var(--font-sans);
}
h1 {
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem !important;
}

input, textarea, select, [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-main) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.75rem 1rem !important;
    box-shadow: var(--shadow-sm) !important;
}
input:focus, textarea:focus, select:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
}

[data-baseweb="tab-list"] {
    background-color: var(--bg-card) !important;
    border-radius: var(--radius-lg) !important;
    padding: 0.3rem !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    border-radius: var(--radius-md) !important;
    padding: 0.6rem 1.2rem !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: var(--gradient-primary) !important;
    color: white !important;
    box-shadow: var(--shadow-sm) !important;
}

.activity-card, .meal-card, .itin-card, .rec-card {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 1.25rem !important;
    margin-bottom: 1rem !important;
    box-shadow: var(--shadow-sm) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}
.activity-card:hover, .meal-card:hover, .itin-card:hover, .rec-card:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-md) !important;
    border-color: var(--accent-primary) !important;
}

.activity-card .time {
    color: var(--accent-primary) !important;
    font-weight: 700 !important;
}
.activity-card .act {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: var(--text-main) !important;
}
.activity-card .meta {
    color: var(--text-muted) !important;
    font-size: 0.9rem !important;
}

[data-testid="stMetric"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stMetricValue"] {
    color: var(--text-main) !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
}

[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
}

.place-pill, .badge {
    background-color: #eff6ff !important;
    color: var(--accent-primary) !important;
    border: 1px solid #bfdbfe !important;
    border-radius: 999px !important;
    padding: 0.25rem 0.75rem !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    display: inline-flex !important;
    align-items: center !important;
}

hr {
    border-color: var(--border) !important;
}

[data-testid="stDownloadButton"] button {
    background: var(--gradient-primary) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
}

.stRadio > div {
    gap: 0.75rem !important;
}
.stCheckbox label, .stRadio label {
    color: var(--text-main) !important;
}
</style>
"""