"""
Global CSS for the Wandr Streamlit experience.
Designed to keep the existing product flow intact while giving the UI
an editorial travel-product feel.
"""

GLOBAL_CSS = """
<!-- UI v2.1 - Glassmorphism + Animations -->
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg-main: #f7efe4;
    --bg-card: rgba(255, 250, 244, 0.88);
    --bg-card-strong: #fffaf3;
    --bg-soft: #f3e1cd;
    --bg-sidebar: linear-gradient(180deg, #f4ede3 0%, #efe3d4 68%, #ead8c5 100%);
    --border: rgba(92, 72, 49, 0.14);
    --border-strong: rgba(92, 72, 49, 0.24);
    --text: #1f2933;
    --text-main: #1f2933;
    --muted: #6b665f;
    --text-muted: #6b665f;
    --accent: #e36b46;
    --accent-primary: #e36b46;
    --accent-hover: #cb5533;
    --accent2: #0f8b80;
    --accent3: #d7a03f;
    --accent4: #4f73ef;
    --accent5: #d1528d;
    --gradient-primary: linear-gradient(135deg, #e36b46 0%, #f09545 48%, #ffd166 100%);
    --gradient-secondary: linear-gradient(135deg, rgba(15, 139, 128, 0.2), rgba(227, 107, 70, 0.16));
    --gradient-tertiary: linear-gradient(135deg, rgba(79, 115, 239, 0.2), rgba(209, 82, 141, 0.16));
    --gradient-animated: linear-gradient(135deg, #e36b46, #f09545, #0f8b80, #4f73ef, #d1528d);
    --serif: 'Fraunces', serif;
    --font-serif: 'Fraunces', serif;
    --font-sans: 'Manrope', sans-serif;
    --radius-sm: 14px;
    --radius-md: 20px;
    --radius-lg: 28px;
    --shadow-sm: 0 10px 24px rgba(87, 63, 38, 0.08);
    --shadow-md: 0 18px 42px rgba(87, 63, 38, 0.12);
    --shadow-lg: 0 28px 60px rgba(87, 63, 38, 0.18);
    --shadow-glow: 0 8px 32px rgba(227, 107, 70, 0.15);
}

html,
body,
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top left, rgba(255, 189, 89, 0.22), transparent 28%),
        radial-gradient(circle at top right, rgba(15, 139, 128, 0.18), transparent 32%),
        radial-gradient(circle at 80% 30%, rgba(79, 115, 239, 0.14), transparent 24%),
        radial-gradient(circle at 15% 70%, rgba(209, 82, 141, 0.12), transparent 22%),
        linear-gradient(180deg, #fbf4eb 0%, #f6ecdf 48%, #f1e5d3 100%) !important;
    color: var(--text) !important;
    font-family: var(--font-sans) !important;
}

[data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::after {
    content: "";
    position: fixed;
    z-index: 0;
    border-radius: 999px;
    pointer-events: none;
    filter: blur(18px);
    opacity: 0.42;
}

[data-testid="stAppViewContainer"]::before {
    width: 320px;
    height: 320px;
    top: 88px;
    right: -120px;
    background: radial-gradient(circle, rgba(244, 194, 96, 0.5), rgba(244, 194, 96, 0));
}

[data-testid="stAppViewContainer"]::after {
    width: 280px;
    height: 280px;
    bottom: 60px;
    left: -80px;
    background: radial-gradient(circle, rgba(26, 123, 116, 0.28), rgba(26, 123, 116, 0));
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stAppToolbar"],
[data-testid="stToolbarActions"],
#MainMenu,
header button[kind="header"],
button[kind="header"] {
    display: none !important;
    visibility: hidden !important;
}

[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
section[data-testid="stSidebar"] {
    display: none !important;
    visibility: hidden !important;
}

.main .block-container {
    max-width: 1320px;
    padding-top: 1rem;
    padding-bottom: 4rem;
    position: relative;
    z-index: 1;
}

.control-panel {
    background: linear-gradient(180deg, rgba(255, 251, 246, 0.78), rgba(247, 238, 226, 0.72));
    border: 1px solid rgba(92, 72, 49, 0.1);
    border-radius: 28px;
    padding: 1.05rem 0.95rem 0.95rem;
    box-shadow: var(--shadow-sm);
    position: static;
}

.brand-lockup {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    padding: 0.55rem 0 1.1rem;
}

.top-brand-lockup {
    padding: 0.2rem 0 0.35rem;
}

.brand-mark {
    width: 48px;
    height: 48px;
    border-radius: 16px;
    display: grid;
    place-items: center;
    background: var(--gradient-primary);
    color: #fff8f0;
    font-family: var(--font-serif);
    font-size: 1.35rem;
    font-weight: 700;
    box-shadow: 0 16px 30px rgba(218, 115, 71, 0.22);
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-6px); }
}

.brand-name {
    font-family: var(--font-serif);
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1;
}

.brand-tagline {
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: 0.18rem;
}

.user-avatar-bar {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 0.95rem 1rem;
    margin: 0.35rem 0 0.1rem;
    border-radius: 20px;
    background: rgba(255, 252, 247, 0.72);
    border: 1px solid rgba(92, 72, 49, 0.08);
    box-shadow: var(--shadow-sm);
}

.user-avatar-bar img {
    width: 48px;
    height: 48px;
    object-fit: cover;
    border-radius: 16px;
    border: 2px solid rgba(255, 255, 255, 0.6);
}

.uname {
    font-weight: 800;
    font-size: 1.05rem;
    color: var(--text);
}

.top-account-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.65rem;
    width: 100%;
    min-height: 48px;
    margin-bottom: 0.55rem;
    padding: 0.55rem 0.9rem;
    border-radius: 999px;
    background: rgba(255, 252, 247, 0.82);
    border: 1px solid rgba(92, 72, 49, 0.08);
    box-shadow: var(--shadow-sm);
    color: var(--text);
    font-weight: 800;
}

.top-account-chip img {
    width: 30px;
    height: 30px;
    object-fit: cover;
    border-radius: 999px;
}

.top-account-chip.no-image {
    min-height: 42px;
}

.sidebar-section-label {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin: 1rem 0 0.6rem;
    padding: 0.45rem 0.8rem;
    border-radius: 999px;
    background: rgba(26, 123, 116, 0.08);
    border: 1px solid rgba(26, 123, 116, 0.12);
    color: var(--accent2);
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

h1,
h2,
h3,
h4,
h5,
h6 {
    font-family: var(--font-serif) !important;
    color: var(--text) !important;
    letter-spacing: -0.03em;
}

p,
div,
label,
li {
    font-family: var(--font-sans) !important;
}

h1 {
    font-size: clamp(2.15rem, 4.4vw, 3.85rem) !important;
    line-height: 1.02 !important;
    margin-bottom: 0.5rem !important;
}

h3 {
    font-size: 1.3rem !important;
}

a {
    color: var(--accent2);
}

hr,
[data-testid="stDivider"] {
    border-color: rgba(92, 72, 49, 0.12) !important;
}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
textarea,
[data-baseweb="select"] > div,
[data-baseweb="base-input"] {
    background: rgba(255, 251, 246, 0.9) !important;
    border: 1px solid rgba(92, 72, 49, 0.14) !important;
    border-radius: 16px !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 6px 18px rgba(104, 74, 44, 0.05) !important;
    color: var(--text) !important;
}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
textarea {
    padding: 0.8rem 0.95rem !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
textarea:focus,
[data-baseweb="select"] > div:focus-within,
[data-baseweb="base-input"]:focus-within {
    border-color: rgba(218, 115, 71, 0.38) !important;
    box-shadow: 0 0 0 4px rgba(218, 115, 71, 0.12), 0 10px 24px rgba(104, 74, 44, 0.08) !important;
}

[data-baseweb="tag"] {
    border-radius: 999px !important;
    background: rgba(26, 123, 116, 0.11) !important;
    border: 1px solid rgba(26, 123, 116, 0.14) !important;
}

[data-baseweb="tag"] span {
    color: var(--accent2) !important;
    font-weight: 700 !important;
}

.stButton > button,
[data-testid="stDownloadButton"] button,
[data-testid="baseButton-secondary"],
[data-testid="baseButton-primary"] {
    border: none !important;
    border-radius: 16px !important;
    font-weight: 800 !important;
    padding: 0.78rem 1rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative;
    overflow: hidden;
}

.stButton > button::before,
[data-testid="stDownloadButton"] button::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
}

.stButton > button:hover::before,
[data-testid="stDownloadButton"] button:hover::before {
    width: 300px;
    height: 300px;
}

.stButton > button[kind="primary"],
[data-testid="stDownloadButton"] button,
[data-testid="baseButton-primary"] {
    background: var(--gradient-primary) !important;
    color: #fffaf3 !important;
    box-shadow: 0 14px 30px rgba(218, 115, 71, 0.2) !important;
}

.stButton > button[kind="secondary"],
[data-testid="baseButton-secondary"] {
    background: rgba(255, 251, 246, 0.92) !important;
    color: var(--text) !important;
    border: 1px solid rgba(92, 72, 49, 0.1) !important;
    box-shadow: var(--shadow-sm) !important;
}

.stButton > button:hover,
[data-testid="stDownloadButton"] button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 20px 40px rgba(218, 115, 71, 0.28), var(--shadow-glow) !important;
    filter: saturate(1.08) brightness(1.05);
}

.stButton > button[kind="secondary"]:hover {
    box-shadow: var(--shadow-md) !important;
}

.stButton > button:focus,
[data-testid="stDownloadButton"] button:focus {
    box-shadow: 0 0 0 4px rgba(218, 115, 71, 0.12), 0 18px 34px rgba(218, 115, 71, 0.24) !important;
}

[data-testid="stForm"] {
    padding: 1.3rem 1.25rem 1.2rem;
    border-radius: 24px;
    background: rgba(255, 251, 246, 0.76);
    border: 1px solid rgba(92, 72, 49, 0.1);
    box-shadow: var(--shadow-sm);
}

[data-baseweb="tab-list"] {
    gap: 0.45rem !important;
    background: rgba(255, 249, 242, 0.72) !important;
    border: 1px solid rgba(92, 72, 49, 0.08) !important;
    border-radius: 22px !important;
    padding: 0.38rem !important;
    box-shadow: var(--shadow-sm) !important;
}

[data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 16px !important;
    color: var(--muted) !important;
    font-weight: 700 !important;
    min-height: 42px !important;
    padding: 0.6rem 1rem !important;
}

[aria-selected="true"][data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.92) !important;
    color: var(--text) !important;
    box-shadow: 0 8px 20px rgba(92, 72, 49, 0.08) !important;
}

[data-testid="stExpander"] {
    border: 1px solid rgba(92, 72, 49, 0.1) !important;
    border-radius: 18px !important;
    background: rgba(255, 251, 246, 0.72) !important;
    box-shadow: var(--shadow-sm) !important;
}

[data-testid="stExpander"] details summary p {
    font-weight: 700 !important;
    color: var(--text) !important;
    margin: 0 !important;
}

[data-testid="stExpander"] summary {
    align-items: center !important;
}

[data-testid="stExpander"] summary svg,
[data-testid="stExpander"] summary [aria-hidden="true"] {
    flex-shrink: 0;
}

[data-testid="stMetric"] {
    padding: 1.1rem 1.1rem 1rem !important;
    border-radius: 22px !important;
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(255, 249, 241, 0.88)) !important;
    border: 1px solid rgba(92, 72, 49, 0.1) !important;
    box-shadow: var(--shadow-sm) !important;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    transition: all 0.3s ease !important;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md), var(--shadow-glow) !important;
    border-color: rgba(227, 107, 70, 0.18) !important;
}

[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-weight: 700 !important;
}

[data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-weight: 800 !important;
    font-size: 1.35rem !important;
}

[data-testid="stAlert"] {
    border-radius: 18px !important;
    border: 1px solid rgba(92, 72, 49, 0.12) !important;
    background: rgba(255, 250, 244, 0.8) !important;
}

.page-hero {
    position: relative;
    overflow: hidden;
    padding: 2rem 2.1rem 1.9rem;
    margin-bottom: 1.5rem;
    border-radius: 30px;
    background:
        radial-gradient(circle at top right, rgba(244, 194, 96, 0.18), transparent 32%),
        radial-gradient(circle at left center, rgba(26, 123, 116, 0.08), transparent 34%),
        radial-gradient(circle at 78% 82%, rgba(85, 107, 214, 0.11), transparent 24%),
        linear-gradient(135deg, rgba(255, 252, 247, 0.94), rgba(248, 239, 226, 0.88));
    border: 1px solid rgba(92, 72, 49, 0.1);
    box-shadow: var(--shadow-md);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    animation: heroGlow 8s ease-in-out infinite;
}

@keyframes heroGlow {
    0%, 100% { box-shadow: var(--shadow-md), 0 0 40px rgba(227, 107, 70, 0.1); }
    50% { box-shadow: var(--shadow-md), 0 0 60px rgba(15, 139, 128, 0.15); }
}

.page-hero::before,
.page-hero::after {
    content: "";
    position: absolute;
    border-radius: 999px;
    pointer-events: none;
}

.page-hero::before {
    width: 200px;
    height: 200px;
    top: -80px;
    right: -30px;
    background: radial-gradient(circle, rgba(218, 115, 71, 0.18), rgba(218, 115, 71, 0));
}

.page-hero::after {
    width: 180px;
    height: 180px;
    bottom: -70px;
    left: 16%;
    background: radial-gradient(circle, rgba(26, 123, 116, 0.14), rgba(26, 123, 116, 0));
}

.page-hero h1 {
    margin: 0.25rem 0 0.55rem !important;
    max-width: 11ch;
}

.page-hero p {
    max-width: 640px;
    margin: 0;
    font-size: 1rem;
    line-height: 1.7;
    color: var(--muted);
}

.page-hero.hero-clean {
    min-height: 280px;
    margin-bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 2.2rem 2rem 2rem;
}

.landing-hero {
    min-height: 320px;
    margin-bottom: 1.35rem !important;
}

.landing-hero h1 {
    max-width: 12ch;
}

.landing-hero p {
    max-width: 720px;
}

.page-hero.hero-clean h1 {
    max-width: 12ch;
    margin: 0.8rem auto 0.65rem !important;
    font-size: clamp(2.2rem, 5.1vw, 3.8rem) !important;
    line-height: 1.02 !important;
}

.page-hero.hero-clean p {
    max-width: 760px;
    color: var(--muted);
    font-size: 0.96rem;
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 44px;
    padding: 0.5rem 1rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(92, 72, 49, 0.12);
    color: var(--text);
    box-shadow: var(--shadow-sm);
}

.hero-pill {
    font-size: 0.88rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.planner-panel-intro {
    margin: -1.1rem auto 1.35rem;
    max-width: 1080px;
    padding: 1.25rem 1.35rem;
    border-radius: 28px;
    background: rgba(255, 250, 244, 0.9);
    border: 1px solid rgba(92, 72, 49, 0.1);
    box-shadow: var(--shadow-lg);
    position: relative;
    z-index: 2;
}

.planner-panel-intro h3 {
    margin: 0.35rem 0 0.3rem !important;
}

.planner-panel-intro p {
    margin: 0;
    color: var(--muted);
}

.weekend-panel-intro {
    margin-top: 0.6rem;
}

.planner-kicker {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.42rem 0.75rem;
    border-radius: 999px;
    background: rgba(26, 123, 116, 0.08);
    border: 1px solid rgba(26, 123, 116, 0.12);
    color: var(--accent2);
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.45rem 0.85rem;
    border-radius: 999px;
    background: rgba(26, 123, 116, 0.08);
    border: 1px solid rgba(26, 123, 116, 0.16);
    color: var(--accent2);
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.summary-banner {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.9rem;
    margin: 1rem 0 1.15rem;
    padding: 1rem 1.15rem;
    border-radius: 24px;
    background:
        radial-gradient(circle at right top, rgba(85, 107, 214, 0.12), transparent 28%),
        linear-gradient(135deg, rgba(255, 250, 244, 0.92), rgba(255, 244, 229, 0.92));
    border: 1px solid rgba(92, 72, 49, 0.1);
    box-shadow: var(--shadow-sm);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    position: relative;
    overflow: hidden;
}

.summary-banner::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0% { left: -100%; }
    100% { left: 100%; }
}

.summary-label {
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--accent2);
}

.summary-title {
    margin-top: 0.18rem;
    font-family: var(--font-serif);
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--text);
}

.summary-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
}

.summary-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.5rem 0.8rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.74);
    border: 1px solid rgba(92, 72, 49, 0.08);
    color: var(--muted);
    font-size: 0.82rem;
    font-weight: 700;
}

.route-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin: 0 0 1rem;
    padding: 0.7rem 0.95rem;
    border-radius: 18px;
    border: 1px solid rgba(92, 72, 49, 0.1);
    background: rgba(255, 250, 244, 0.78);
    box-shadow: var(--shadow-sm);
    font-weight: 700;
}

.route-badge.ok {
    color: var(--accent2);
    border-color: rgba(26, 123, 116, 0.18);
    background: rgba(26, 123, 116, 0.08);
}

.route-badge.warn {
    color: #9a6b12;
    border-color: rgba(198, 154, 71, 0.22);
    background: rgba(198, 154, 71, 0.12);
}

.route-badge.danger {
    color: #a3452b;
    border-color: rgba(218, 115, 71, 0.24);
    background: rgba(218, 115, 71, 0.12);
}

.route-strategy-card {
    margin: 0.9rem 0 1rem;
    padding: 1rem 1.05rem;
    border-radius: 22px;
    border: 1px solid rgba(92, 72, 49, 0.1);
    background: linear-gradient(180deg, rgba(255, 252, 247, 0.96), rgba(250, 242, 232, 0.9));
    box-shadow: var(--shadow-sm);
}

.route-strategy-card.reorder {
    background:
        radial-gradient(circle at right top, rgba(85, 107, 214, 0.12), transparent 28%),
        linear-gradient(180deg, rgba(255, 252, 247, 0.96), rgba(245, 246, 255, 0.9));
}

.route-strategy-card.replace {
    background:
        radial-gradient(circle at right top, rgba(26, 123, 116, 0.12), transparent 28%),
        linear-gradient(180deg, rgba(255, 252, 247, 0.96), rgba(240, 249, 247, 0.92));
}

.route-strategy-label {
    display: inline-flex;
    padding: 0.35rem 0.65rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent2);
    background: rgba(26, 123, 116, 0.08);
}

.route-strategy-card.reorder .route-strategy-label {
    color: var(--accent4);
    background: rgba(85, 107, 214, 0.1);
}

.route-strategy-title {
    margin-top: 0.7rem;
    font-family: var(--font-serif);
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text);
}

.route-strategy-copy {
    margin-top: 0.4rem;
    color: var(--muted);
    line-height: 1.6;
}

.route-strategy-meta {
    margin-top: 0.8rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
}

.route-metric-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.42rem 0.72rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.74);
    border: 1px solid rgba(92, 72, 49, 0.08);
    color: var(--text);
    font-size: 0.8rem;
    font-weight: 700;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 1.2rem 0 0.9rem;
}

.section-header span {
    font-family: var(--font-serif);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
}

.section-header .line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(26, 123, 116, 0.22), rgba(218, 115, 71, 0.12), transparent);
}

.food-highlight-bar {
    margin: 0.4rem 0 1rem;
    padding: 0.75rem 0.95rem;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(26, 123, 116, 0.08), rgba(255, 250, 244, 0.9));
    border: 1px solid rgba(26, 123, 116, 0.12);
    color: var(--text);
    font-size: 0.92rem;
}

.activity-card,
.meal-card,
.itin-card,
.rec-card,
.feature-block,
.getaway-card {
    position: relative;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(255, 253, 248, 0.96), rgba(255, 248, 239, 0.88)) !important;
    border: 1px solid rgba(92, 72, 49, 0.1) !important;
    border-radius: 24px !important;
    padding: 1.15rem 1.1rem !important;
    margin-bottom: 1rem !important;
    box-shadow: var(--shadow-sm) !important;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer;
}

.activity-card:hover,
.meal-card:hover,
.rec-card:hover,
.getaway-card:hover,
.feature-block:hover {
    transform: translateY(-4px) scale(1.01);
    box-shadow: var(--shadow-md), var(--shadow-glow) !important;
    border-color: rgba(227, 107, 70, 0.2) !important;
}

.activity-card::before,
.meal-card::before,
.rec-card::before,
.getaway-card::before,
.feature-block::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--accent-primary), var(--accent3), var(--accent2), var(--accent4), var(--accent5));
    background-size: 200% 100%;
    animation: gradientShift 6s ease infinite;
}

@keyframes gradientShift {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

.activity-card::after,
.meal-card::after,
.rec-card::after,
.getaway-card::after,
.feature-block::after {
    content: "";
    position: absolute;
    inset: auto -40px -52px auto;
    width: 130px;
    height: 130px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(218, 115, 71, 0.08), rgba(218, 115, 71, 0));
    pointer-events: none;
}

.activity-card .time {
    display: inline-flex;
    margin-bottom: 0.55rem;
    padding: 0.28rem 0.58rem;
    border-radius: 999px;
    background: rgba(26, 123, 116, 0.08);
    color: var(--accent2) !important;
    font-size: 0.78rem;
    font-weight: 800 !important;
    letter-spacing: 0.04em;
}

.activity-card .act {
    font-size: 1.12rem !important;
    font-weight: 800 !important;
    color: var(--text) !important;
    margin-bottom: 0.3rem;
}

.activity-card .meta {
    color: var(--muted) !important;
    font-size: 0.9rem !important;
    line-height: 1.55;
}

.meal-card {
    min-height: 188px;
    background:
        linear-gradient(180deg, rgba(255, 252, 248, 0.98), rgba(245, 252, 250, 0.92)) !important;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.meal-card .cost {
    display: inline-flex;
    margin-top: 0.9rem;
    padding: 0.35rem 0.65rem;
    border-radius: 999px;
    background: linear-gradient(135deg, rgba(218, 115, 71, 0.12), rgba(244, 194, 96, 0.1));
    color: var(--accent-primary);
    font-size: 0.84rem;
    font-weight: 800;
    box-shadow: 0 4px 12px rgba(218, 115, 71, 0.1);
    animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

.meal-label {
    color: var(--accent2);
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.meal-card .place {
    font-family: var(--font-serif);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
    margin-top: 0.6rem;
}

.meal-card .dish {
    margin-top: 0.35rem;
    color: var(--muted);
    font-weight: 600;
}

.nearby-alt {
    padding: 0.8rem 0.95rem;
    border-radius: 16px;
    background: rgba(255, 248, 239, 0.7);
    border: 1px solid rgba(92, 72, 49, 0.08);
    margin-bottom: 0.65rem;
}

.nearby-alt .dist {
    color: var(--accent2);
    font-weight: 700;
}

.day-total-row {
    margin-top: 1rem;
    padding: 0.8rem 0.95rem;
    border-radius: 18px;
    background: rgba(31, 41, 51, 0.04);
    color: var(--muted);
    font-weight: 700;
}

.budget-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.95rem 1rem;
    margin-bottom: 0.7rem;
    border-radius: 18px;
    background: rgba(255, 251, 246, 0.78);
    border: 1px solid rgba(92, 72, 49, 0.08);
}

.budget-row.total {
    background: linear-gradient(135deg, rgba(218, 115, 71, 0.12), rgba(244, 194, 96, 0.14));
    border-color: rgba(218, 115, 71, 0.18);
}

.blabel {
    color: var(--muted);
    font-weight: 700;
}

.bval {
    color: var(--text);
    font-weight: 800;
}

.tip-chip,
.tag,
.place-pill,
.interest-pill {
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.35rem !important;
    border-radius: 999px !important;
    font-weight: 700 !important;
}

.tip-chip {
    margin: 0 0.55rem 0.65rem 0;
    padding: 0.58rem 0.85rem !important;
    background: linear-gradient(135deg, rgba(26, 123, 116, 0.1), rgba(85, 107, 214, 0.08)) !important;
    border: 1px solid rgba(26, 123, 116, 0.12) !important;
    color: var(--accent2) !important;
}

.tag {
    padding: 0.35rem 0.65rem !important;
    background: rgba(218, 115, 71, 0.1) !important;
    border: 1px solid rgba(218, 115, 71, 0.12) !important;
    color: var(--accent-primary) !important;
    font-size: 0.78rem !important;
}

.place-pill {
    width: 100%;
    padding: 0.8rem 0.9rem !important;
    background: rgba(255, 251, 246, 0.82) !important;
    border: 1px solid rgba(92, 72, 49, 0.08) !important;
    color: var(--text) !important;
    justify-content: flex-start !important;
    box-shadow: var(--shadow-sm);
}

.interest-pills {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 0.55rem !important;
    margin: 1rem 0 1.2rem !important;
}

.interest-pill {
    padding: 0.45rem 0.72rem !important;
    background: rgba(26, 123, 116, 0.08) !important;
    border: 1px solid rgba(26, 123, 116, 0.14) !important;
    color: var(--accent2) !important;
    font-size: 0.82rem !important;
}

.getaway-card .dest-name,
.rec-card .dest-name {
    font-family: var(--font-serif);
    font-size: 1.22rem;
    font-weight: 700;
    color: var(--text);
}

.getaway-card.selected {
    border-color: rgba(26, 123, 116, 0.28) !important;
    box-shadow: 0 20px 44px rgba(26, 123, 116, 0.14) !important;
    background: linear-gradient(180deg, rgba(245, 255, 252, 0.98), rgba(255, 249, 240, 0.92)) !important;
}

.rec-card .country {
    margin-top: 0.3rem;
    color: var(--muted);
    font-size: 0.9rem;
}

.rec-card .vibe {
    display: inline-flex;
    margin-top: 0.75rem;
    margin-bottom: 0.8rem;
    padding: 0.34rem 0.65rem;
    border-radius: 999px;
    background: linear-gradient(135deg, rgba(85, 107, 214, 0.1), rgba(182, 90, 122, 0.09));
    color: var(--accent4);
    font-size: 0.8rem;
    font-weight: 800;
}

.rec-card .reason {
    color: var(--muted);
    line-height: 1.55;
    min-height: 3rem;
}

.feature-block {
    text-align: left;
    min-height: 196px;
}

.feature-block.demo-card {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 228px;
    background:
        linear-gradient(180deg, rgba(255, 252, 248, 0.98), rgba(243, 250, 248, 0.92)) !important;
}

.demo-card-top,
.demo-meta-row,
.planner-lens-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
}

.demo-card-top {
    margin-bottom: 0.9rem;
}

.demo-kicker,
.demo-badge,
.demo-meta-pill,
.planner-lens-route {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    font-weight: 700;
}

.demo-kicker {
    padding: 0.34rem 0.7rem;
    background: rgba(26, 123, 116, 0.08);
    border: 1px solid rgba(26, 123, 116, 0.14);
    color: var(--accent2);
    font-size: 0.74rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.demo-badge {
    padding: 0.34rem 0.68rem;
    background: rgba(218, 115, 71, 0.1);
    color: var(--accent-primary);
    font-size: 0.78rem;
}

.demo-route {
    margin-top: 0.95rem;
    padding: 0.8rem 0.92rem;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.55);
    border: 1px solid rgba(92, 72, 49, 0.08);
    color: var(--text);
    font-size: 0.9rem;
    line-height: 1.5;
}

.demo-meta-row {
    margin-top: 0.9rem;
    flex-wrap: wrap;
    justify-content: flex-start;
}

.demo-meta-pill {
    padding: 0.45rem 0.72rem;
    background: rgba(31, 41, 51, 0.05);
    color: var(--muted);
    font-size: 0.78rem;
}

.planner-lens {
    margin: 1rem 0 1.1rem;
    padding: 1.1rem 1.15rem;
    border-radius: 24px;
    background:
        radial-gradient(circle at top right, rgba(85, 107, 214, 0.12), transparent 34%),
        linear-gradient(135deg, rgba(255, 250, 244, 0.98), rgba(244, 251, 249, 0.95));
    border: 1px solid rgba(92, 72, 49, 0.08);
    box-shadow: var(--shadow-sm);
}

.planner-lens-head {
    align-items: flex-start;
    margin-bottom: 1rem;
}

.planner-lens-kicker {
    color: var(--accent-primary);
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.planner-lens-title {
    margin-top: 0.35rem;
    font-family: var(--font-serif);
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text);
}

.planner-lens-route {
    max-width: 48%;
    padding: 0.52rem 0.82rem;
    background: rgba(255, 255, 255, 0.62);
    border: 1px solid rgba(92, 72, 49, 0.08);
    color: var(--accent4);
    font-size: 0.82rem;
    line-height: 1.4;
    text-align: right;
}

.planner-lens-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.8rem;
}

.planner-lens-item {
    padding: 0.82rem 0.9rem;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.56);
    border: 1px solid rgba(92, 72, 49, 0.07);
}

.planner-lens-item strong {
    display: block;
    color: var(--text);
    line-height: 1.45;
}

.planner-lens-label {
    display: block;
    margin-bottom: 0.38rem;
    color: var(--muted);
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.planner-lens-wide {
    grid-column: span 2;
}

.feature-block .icon {
    width: 52px;
    height: 52px;
    display: grid;
    place-items: center;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(218, 115, 71, 0.16), rgba(85, 107, 214, 0.12));
    font-size: 1.45rem;
    margin-bottom: 0.95rem;
}

.feature-block .ftitle {
    font-family: var(--font-serif);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.45rem;
}

.feature-block .fdesc {
    color: var(--muted);
    line-height: 1.6;
}

iframe,
[data-testid="stIFrame"] iframe {
    border-radius: 24px !important;
    box-shadow: var(--shadow-md) !important;
}

.stRadio > div,
.stCheckbox > div {
    gap: 0.75rem !important;
}

.stRadio label,
.stCheckbox label {
    color: var(--text) !important;
    font-weight: 600 !important;
}

.stRadio [role="radiogroup"] {
    gap: 0.55rem !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
}

.stRadio label {
    min-height: 44px !important;
    padding: 0.18rem 0.28rem !important;
    border-radius: 999px !important;
    background: rgba(255, 251, 246, 0.84) !important;
    border: 1px solid rgba(92, 72, 49, 0.08) !important;
    box-shadow: var(--shadow-sm) !important;
}

.stRadio label p {
    font-weight: 700 !important;
}

.stRadio label:has(input:checked) {
    background: var(--gradient-primary) !important;
    border-color: transparent !important;
    box-shadow: 0 14px 28px rgba(218, 115, 71, 0.22) !important;
}

.stRadio label:has(input:checked) p {
    color: #fffaf3 !important;
}

@media (max-width: 1100px) {
    .main .block-container {
        padding-top: 1rem;
    }

    .page-hero {
        padding: 1.6rem;
    }

    .planner-panel-intro {
        margin-top: -0.6rem;
    }
}

@media (max-width: 768px) {
    .main .block-container {
        padding-top: 0.8rem;
        padding-bottom: 3rem;
    }

    .page-hero {
        border-radius: 24px;
        padding: 1.4rem 1.2rem;
    }

    .page-hero.hero-clean {
        min-height: 240px;
    }

    .page-hero.hero-clean h1 {
        max-width: 9ch;
        font-size: clamp(2.7rem, 11vw, 4.25rem) !important;
    }

    .planner-panel-intro {
        margin-top: -0.2rem;
        padding: 1rem;
    }

    .summary-banner {
        padding: 0.95rem;
    }

    .activity-card,
    .meal-card,
    .itin-card,
    .rec-card,
    .feature-block,
    .getaway-card {
        border-radius: 20px !important;
    }

    .demo-card-top,
    .planner-lens-head {
        flex-direction: column;
        align-items: flex-start;
    }

    .planner-lens-route {
        max-width: 100%;
        text-align: left;
    }

    .planner-lens-grid {
        grid-template-columns: 1fr 1fr;
    }

    .planner-lens-wide {
        grid-column: span 2;
    }
}
</style>
"""
