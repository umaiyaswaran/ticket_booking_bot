"""
Shared sidebar navigation for User and Agency.
Import and call render_user_sidebar() or render_agency_sidebar() as needed.
"""
import streamlit as st


def _inject_white_theme_css():
    """Inject Uber-inspired white theme CSS for agency pages."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    :root {
        --primary: #000000;
        --on-primary: #ffffff;
        --ink: #000000;
        --body: #5e5e5e;
        --mute: #afafaf;
        --hairline-mid: #4b4b4b;
        --canvas: #ffffff;
        --canvas-soft: #efefef;
        --canvas-softer: #f3f3f3;
        --surface-pressed: #e2e2e2;
        --on-dark: #ffffff;
        --r-none: 0px;
        --r-md: 8px;
        --r-lg: 12px;
        --r-xl: 16px;
        --r-pill: 999px;
        --r-pill-tab: 36px;
        --r-full: 9999px;
        --spacing-sm: 8px;
        --spacing-md: 12px;
        --spacing-lg: 16px;
        --spacing-xl: 20px;
        --spacing-2xl: 24px;
        --spacing-3xl: 32px;
        --shadow-sm: 0 2px 8px rgba(0,0,0,0.08);
        --shadow-md: 0 4px 16px rgba(0,0,0,0.12);
        --shadow-pill: 0 2px 8px rgba(0,0,0,0.16);
        --shadow-elevated: 0 4px 16px rgba(0,0,0,0.12);
        --ease: cubic-bezier(0.4, 0, 0.2, 1);
        --success: #10b981;
        --success-soft: rgba(16, 185, 129, 0.12);
        --warning: #f59e0b;
        --warning-soft: rgba(245, 158, 11, 0.12);
        --error: #ef4444;
        --error-soft: rgba(239, 68, 68, 0.12);
        --info: #3b82f6;
        --info-soft: rgba(59, 130, 246, 0.12);
    }

    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"],
    .main .block-container {
        background: var(--canvas) !important;
        color: var(--ink);
        font-family: 'Inter', -apple-system, sans-serif;
        overflow-x: hidden;
        -webkit-font-smoothing: antialiased;
    }

    #MainMenu, footer,
    button[title="View fullscreen"],
    [data-testid="stSidebarNav"],
    [data-testid="stDecoration"],
    .stDeployButton,
    div[data-testid="stToolbar"],
    div[data-testid="stStatusWidget"],
    div[data-testid="stBottomBlockContainer"] > div:last-child {
        display: none !important;
    }

    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
    }

    button[data-testid="stSidebarCollapseControl"] {
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        z-index: 99999 !important;
        display: flex !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        background: #ffffff !important;
        border: 1px solid #e2e2e2 !important;
        border-radius: 999px !important;
        width: 42px !important;
        height: 42px !important;
        transition: all 0.2s ease !important;
    }

    button[data-testid="stSidebarCollapseControl"]:hover {
        background: #efefef !important;
        border-color: #afafaf !important;
    }

    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.25;
        background: none !important;
    }

    h1, [data-testid="stMarkdownContainer"] h1 {
        font-size: 2.6em !important;
        margin-bottom: 8px !important;
    }
    h2, [data-testid="stMarkdownContainer"] h2 {
        font-size: 1.8em !important;
        margin-bottom: 6px !important;
    }
    h3, [data-testid="stMarkdownContainer"] h3 {
        font-size: 1.3em !important;
        margin-bottom: 4px !important;
    }

    .card, .glass-card {
        background: var(--canvas);
        border: 1px solid var(--surface-pressed);
        border-radius: var(--r-xl);
        padding: var(--spacing-2xl);
        position: relative;
        overflow: hidden;
        transition: all 0.25s var(--ease);
    }
    .card:hover, .glass-card:hover {
        border-color: var(--hairline-mid);
        box-shadow: var(--shadow-elevated);
    }
    .card::before, .glass-card::before { display: none; }
    .glass-card {
        background: var(--canvas);
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
    }

    [data-testid="stButton"] > button,
    [data-testid="stFormSubmitButton"] > button {
        background: var(--primary) !important;
        border: none !important;
        border-radius: var(--r-pill) !important;
        color: var(--on-primary) !important;
        padding: var(--spacing-md) var(--spacing-md) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.9em !important;
        cursor: pointer !important;
        width: 100% !important;
        letter-spacing: 0 !important;
        transition: all 0.2s var(--ease) !important;
        box-shadow: none !important;
        min-height: 46px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    [data-testid="stButton"] > button::after,
    [data-testid="stFormSubmitButton"] > button::after { display: none; }

    [data-testid="stButton"] > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        box-shadow: var(--shadow-pill) !important;
        transform: translateY(-1px) !important;
    }

    [data-testid="stButton"] > button:active,
    [data-testid="stFormSubmitButton"] > button:active {
        transform: translateY(0) !important;
        background: var(--surface-pressed) !important;
        color: var(--ink) !important;
    }

    [data-testid="stButton"] > button[kind="secondary"],
    [data-testid="stButton"] > button:not([kind="primary"]):not([kind="secondary"]) {
        background: var(--canvas) !important;
        color: var(--ink) !important;
        border: 1px solid var(--surface-pressed) !important;
    }
    [data-testid="stButton"] > button[kind="secondary"]:hover,
    [data-testid="stButton"] > button:not([kind="primary"]):not([kind="secondary"]):hover {
        background: var(--canvas-soft) !important;
        border-color: var(--hairline-mid) !important;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea,
    input[type="text"],
    input[type="password"],
    textarea {
        background: var(--canvas-soft) !important;
        border: none !important;
        border-radius: var(--r-none) !important;
        color: var(--ink) !important;
        padding: var(--spacing-lg) !important;
        font-size: 1em !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s var(--ease) !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus,
    input[type="text"]:focus,
    input[type="password"]:focus,
    textarea:focus {
        border-color: var(--ink) !important;
        box-shadow: none !important;
        outline: 2px solid var(--ink) !important;
        outline-offset: -2px !important;
        background: var(--canvas-soft) !important;
    }

    [data-testid="stTextInput"] label,
    [data-testid="stNumberInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stSelectbox"] label {
        color: var(--ink) !important;
        font-size: 1em !important;
        font-weight: 400 !important;
        letter-spacing: 0 !important;
        text-transform: none !important;
    }

    ::placeholder { color: var(--mute) !important; opacity: 1 !important; }

    [data-testid="stSelectbox"] > div > div {
        background: var(--canvas-soft) !important;
        border: none !important;
        border-radius: var(--r-none) !important;
        color: var(--ink) !important;
        transition: all 0.2s var(--ease) !important;
    }
    [data-testid="stSelectbox"] > div > div:hover { border-color: var(--hairline-mid) !important; }
    [data-testid="stSelectbox"] > div > div:focus-within {
        outline: 2px solid var(--ink) !important;
        outline-offset: -2px !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: var(--canvas-soft) !important;
        gap: 2px !important;
        border-bottom: none !important;
        border-radius: var(--r-pill-tab) !important;
        padding: 4px !important;
    }
    [data-testid="stTabs"] button {
        background: transparent !important;
        border: none !important;
        border-bottom: none !important;
        color: var(--ink) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.9em !important;
        padding: 10px 20px !important;
        transition: all 0.2s var(--ease) !important;
        border-radius: var(--r-pill-tab) !important;
    }
    [data-testid="stTabs"] button:hover {
        color: var(--ink) !important;
        background: rgba(0, 0, 0, 0.04) !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--ink) !important;
        border-bottom-color: transparent !important;
        background: var(--canvas) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        background-color: transparent !important;
        border-radius: var(--r-pill-tab) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

    [data-testid="stSidebar"] {
        background: var(--canvas) !important;
        border-right: 1px solid var(--surface-pressed) !important;
        box-shadow: none !important;
        display: block !important;
        visibility: visible !important;
        transform: translateX(0) !important;
        transition: none !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        display: block !important;
        visibility: visible !important;
        transform: translateX(0) !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        background: none !important;
        font-size: 1.1em !important;
        margin-bottom: 14px !important;
        padding-bottom: 10px !important;
        border-bottom: 1px solid var(--surface-pressed) !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: var(--surface-pressed) !important;
        margin: 14px 0 !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] li {
        color: var(--body) !important;
        font-size: 0.88em !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdown"] strong {
        color: var(--ink) !important;
        font-size: 0.78em !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] > button {
        border-radius: var(--r-pill) !important;
        font-size: 0.9em !important;
        font-family: 'Inter', sans-serif !important;
        padding: 11px 18px !important;
        margin-bottom: 6px !important;
        text-align: left !important;
        transition: all 0.2s var(--ease) !important;
        background: var(--canvas-soft) !important;
        border: none !important;
        color: var(--ink) !important;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
        background: var(--surface-pressed) !important;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"],
    [data-testid="stSidebar"] [data-testid="stButton"] > button[data-testid="stBaseButton-primary"] {
        background: var(--primary) !important;
        border: none !important;
        color: var(--on-primary) !important;
    }

    hr, [data-testid="stHorizontalBlock"] hr {
        border: none !important;
        border-top: 1px solid var(--surface-pressed) !important;
        margin: 20px 0 !important;
    }

    [data-testid="stExpander"] {
        background: var(--canvas) !important;
        border: 1px solid var(--surface-pressed) !important;
        border-radius: var(--r-xl) !important;
        margin: 10px 0 !important;
        transition: all 0.2s var(--ease) !important;
    }
    [data-testid="stExpander"]:hover { border-color: var(--hairline-mid) !important; }
    [data-testid="stExpander"] summary {
        color: var(--ink) !important;
        font-weight: 500 !important;
        font-size: 0.92em !important;
    }

    [data-testid="stMetric"] {
        background: var(--canvas) !important;
        border: 1px solid var(--surface-pressed) !important;
        border-radius: var(--r-xl) !important;
        padding: var(--spacing-2xl) !important;
        transition: all 0.25s var(--ease) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    [data-testid="stMetric"]::before { display: none; }
    [data-testid="stMetric"]:hover {
        border-color: var(--hairline-mid) !important;
        box-shadow: var(--shadow-elevated) !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--ink) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.8em !important;
        letter-spacing: -0.02em !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--body) !important;
        font-weight: 400 !important;
        font-size: 0.85em !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
    }

    .dataframe {
        border: 1px solid var(--surface-pressed) !important;
        border-radius: var(--r-xl) !important;
        overflow: hidden !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85em !important;
        background: var(--canvas) !important;
    }
    .dataframe thead tr th {
        background: var(--canvas-soft) !important;
        color: var(--ink) !important;
        font-weight: 500 !important;
        border-bottom: 1px solid var(--surface-pressed) !important;
        padding: 12px 16px !important;
        font-size: 0.85em !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
    }
    .dataframe tbody tr {
        border-bottom: 1px solid var(--surface-pressed) !important;
        transition: background 0.15s var(--ease) !important;
    }
    .dataframe tbody tr:hover { background: var(--canvas-soft) !important; }
    .dataframe tbody td {
        color: var(--ink) !important;
        padding: 12px 16px !important;
    }

    [data-testid="stAlert"],
    [data-testid="stNotification"] {
        border-radius: var(--r-xl) !important;
        border-left: 4px solid var(--ink) !important;
        padding: var(--spacing-lg) var(--spacing-2xl) !important;
        font-size: 0.9em !important;
    }
    [data-testid="stAlert"][kind="success"],
    div[data-baseweb="notification"][kind="positive"] {
        background: var(--success-soft) !important;
        border-left-color: var(--success) !important;
    }
    [data-testid="stAlert"][kind="warning"],
    div[data-baseweb="notification"][kind="warning"] {
        background: var(--warning-soft) !important;
        border-left-color: var(--warning) !important;
    }
    [data-testid="stAlert"][kind="error"],
    div[data-baseweb="notification"][kind="error"] {
        background: var(--error-soft) !important;
        border-left-color: var(--error) !important;
    }
    [data-testid="stAlert"][kind="info"],
    div[data-baseweb="notification"][kind="info"] {
        background: var(--info-soft) !important;
        border-left-color: var(--info) !important;
    }

    [data-testid="stForm"] {
        background: var(--canvas) !important;
        border: 1px solid var(--surface-pressed) !important;
        border-radius: var(--r-xl) !important;
        padding: var(--spacing-2xl) !important;
        box-shadow: none !important;
    }

    [data-testid="stCheckbox"] label span { color: var(--ink) !important; }
    [data-testid="stRadio"] label span { color: var(--ink) !important; }

    [data-testid="stDateInput"] > div > div {
        background: var(--canvas-soft) !important;
        border: none !important;
        border-radius: var(--r-none) !important;
        color: var(--ink) !important;
    }

    [data-testid="stProgress"] > div > div {
        background: var(--ink) !important;
        border-radius: var(--r-full) !important;
    }
    [data-testid="stProgress"] > div {
        background: var(--canvas-soft) !important;
        border-radius: var(--r-full) !important;
    }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--surface-pressed); border-radius: 12px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--hairline-mid); }

    [data-testid="stSpinner"] > div { border-top-color: var(--ink) !important; }

    [data-testid="stHorizontalBlock"] { gap: 16px !important; }
    [data-testid="stColumn"] { padding: 5px !important; }

    .block-container {
        padding-top: 10px !important;
        padding-bottom: 0 !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    [data-testid="stMainBlockContainer"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }

    @media (max-width: 767px) {
        header[data-testid="stHeader"] { display: none !important; }
        .block-container {
            padding-top: 10px !important;
            padding-left: 14px !important;
            padding-right: 14px !important;
        }
        h1, [data-testid="stMarkdownContainer"] h1 { font-size: 1.6em !important; }
        h2, [data-testid="stMarkdownContainer"] h2 { font-size: 1.3em !important; }
        [data-testid="stButton"] > button {
            min-height: 50px !important;
            font-size: 0.95em !important;
        }
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 8px !important;
        }
        [data-testid="stColumn"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
        .dataframe { font-size: 0.75em !important; }
        [data-testid="stMetric"] { padding: 14px !important; }
        [data-testid="stMetricValue"] { font-size: 1.4em !important; }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }
        [data-testid="stTabs"] button {
            padding: 8px 14px !important;
            font-size: 0.82em !important;
            white-space: nowrap !important;
        }
    }

    @media (min-width: 768px) and (max-width: 1023px) {
        .block-container {
            padding-left: 16px !important;
            padding-right: 16px !important;
        }
        [data-testid="stHorizontalBlock"] { gap: 10px !important; }
    }

    @media (hover: none) and (pointer: coarse) {
        [data-testid="stButton"] > button {
            min-height: 50px !important;
            padding: 14px 18px !important;
        }
        input, select, textarea {
            min-height: 50px !important;
            font-size: 16px !important;
        }
    }

    :focus-visible {
        outline: 2px solid var(--ink);
        outline-offset: 3px;
    }

    ::selection {
        background: rgba(0, 0, 0, 0.15);
        color: var(--ink);
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stMarkdown { animation: fadeIn 0.3s var(--ease) both; }
    </style>
    """, unsafe_allow_html=True)


def _inject_sidebar_css():
    """Inject responsive sidebar CSS — hamburger menu on mobile, expanded on desktop."""
    st.markdown("""
    <style>
    /* Hide default Streamlit elements */
    [data-testid="stSidebarNav"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu, footer, button[title="View fullscreen"], .stDeployButton,
    div[data-testid="stToolbar"], div[data-testid="stStatusWidget"],
    div[data-testid="stBottomBlockContainer"] > div:last-child {
        display: none !important;
    }

    /* Hamburger menu button — always visible, top-left */
    button[data-testid="stSidebarCollapseControl"] {
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        z-index: 99999 !important;
        display: flex !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        background: #ffffff !important;
        border: 1px solid #e2e2e2 !important;
        border-radius: 999px !important;
        width: 42px !important;
        height: 42px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    button[data-testid="stSidebarCollapseControl"]:hover {
        background: #efefef !important;
        border-color: #afafaf !important;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e2e2e2 !important;
        transition: transform 0.2s ease !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 60px !important;
    }

    /* ===== DESKTOP (≥1024px) — sidebar always open ===== */
    @media (min-width: 1024px) {
        section[data-testid="stSidebar"] {
            transform: translateX(0) !important;
            min-width: 280px !important;
            max-width: 280px !important;
            width: 280px !important;
            visibility: visible !important;
            display: block !important;
        }
        section[data-testid="stSidebar"][aria-expanded="false"] {
            transform: translateX(0) !important;
            visibility: visible !important;
            display: block !important;
        }
        button[data-testid="stSidebarCollapseControl"] {
            display: none !important;
        }
        .main .block-container,
        [data-testid="stAppBlockContainer"] {
            margin-left: 280px !important;
            padding-left: 20px !important;
            padding-right: 20px !important;
        }
    }

    /* ===== TABLET (768px–1023px) — sidebar toggleable ===== */
    @media (min-width: 768px) and (max-width: 1023px) {
        section[data-testid="stSidebar"] {
            min-width: 260px !important;
            max-width: 260px !important;
            width: 260px !important;
        }
        button[data-testid="stSidebarCollapseControl"] {
            display: flex !important;
        }
    }

    /* ===== MOBILE (<768px) — sidebar hidden, hamburger only ===== */
    @media (max-width: 767px) {
        section[data-testid="stSidebar"] {
            min-width: 280px !important;
            max-width: 280px !important;
            width: 280px !important;
            box-shadow: 4px 0 20px rgba(0,0,0,0.15) !important;
        }
        section[data-testid="stSidebar"][aria-expanded="false"] {
            transform: translateX(-100%) !important;
            visibility: hidden !important;
            display: none !important;
        }
        section[data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0) !important;
            visibility: visible !important;
            display: block !important;
        }
        button[data-testid="stSidebarCollapseControl"] {
            display: flex !important;
            position: fixed !important;
            top: 10px !important;
            left: 10px !important;
            z-index: 99999 !important;
        }
        .main .block-container,
        [data-testid="stAppBlockContainer"] {
            margin-left: 0 !important;
            padding-left: 14px !important;
            padding-right: 14px !important;
            padding-top: 50px !important;
        }
    }

    /* Mobile overlay backdrop when sidebar is open */
    @media (max-width: 767px) {
        section[data-testid="stSidebar"][aria-expanded="true"]::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0,0,0,0.4);
            z-index: -1;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # JavaScript to auto-expand sidebar on desktop only
    st.markdown("""
    <script>
    (function() {
        function isDesktop() { return window.innerWidth >= 1024; }

        function expandSidebarOnDesktop() {
            if (!isDesktop()) return;
            try {
                var sidebar = document.querySelector('section[data-testid="stSidebar"]');
                if (!sidebar) return;
                if (sidebar.getAttribute('aria-expanded') === 'false') {
                    var btn = document.querySelector('button[data-testid="stSidebarCollapseControl"]');
                    if (btn) btn.click();
                }
            } catch(e) {}
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', expandSidebarOnDesktop);
        } else {
            expandSidebarOnDesktop();
        }

        var observer = new MutationObserver(function() { expandSidebarOnDesktop(); });
        observer.observe(document.body, { childList: true, subtree: true });

        var attempts = 0;
        var timer = setInterval(function() {
            expandSidebarOnDesktop();
            attempts++;
            if (attempts > 25) clearInterval(timer);
        }, 200);
    })();
    </script>
    """, unsafe_allow_html=True)


def render_user_sidebar():
    """Render sidebar for logged-in Users. Shows user-specific navigation only."""
    _inject_sidebar_css()
    _inject_white_theme_css()

    username = st.session_state.get("user", "User")
    initial = username[0].upper() if username else "U"

    with st.sidebar:
        # User info card
        st.markdown(f"""
        <div style="background: #efefef;
                    border: none; border-radius: 16px;
                    padding: 22px; margin-bottom: 22px; text-align: center;">
            <div style="width:58px; height:58px; border-radius:999px; background: #000000;
                        display:flex; align-items:center; justify-content:center; font-size:24px;
                        font-weight:700; color:#ffffff; margin:0 auto 12px auto;">{initial}</div>
            <div style="font-family:'Inter',sans-serif; font-weight:700; font-size:1.05em; color:#000000; margin-bottom:3px;">{username}</div>
            <div style="font-size:0.7em; color:#5e5e5e; font-weight:400;">User Account</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<p style="font-family:\'Inter\',sans-serif; font-size:0.72em; font-weight:500; color:#5e5e5e; margin-bottom:10px;">Navigation</p>', unsafe_allow_html=True)

        if st.button("🏠 Dashboard", use_container_width=True, key="usb_dashboard"):
            st.session_state.quick_action = None
            st.session_state.chat_history = []
            st.rerun()

        if st.button("📋 My Bookings", use_container_width=True, key="usb_my_bookings"):
            st.session_state.quick_action = "manual_view"
            st.rerun()

        if st.button("🔔 Notifications", use_container_width=True, key="usb_notifications"):
            st.session_state.quick_action = "notifications"
            st.rerun()

        if st.button("💳 Payments", use_container_width=True, key="usb_payments"):
            st.session_state.quick_action = "payments"
            st.rerun()

        st.markdown('<hr style="border:none; border-top:1px solid #e2e2e2; margin:18px 0;">', unsafe_allow_html=True)

        st.markdown('<p style="font-family:\'Inter\',sans-serif; font-size:0.72em; font-weight:500; color:#5e5e5e; margin-bottom:10px;">Booking Mode</p>', unsafe_allow_html=True)

        mode_col1, mode_col2 = st.columns(2)
        with mode_col1:
            ai_active = st.session_state.get("booking_mode") == "ai_bot"
            if st.button("🤖 AI Bot", use_container_width=True, key="usb_mode_ai",
                         type="primary" if ai_active else "secondary"):
                st.session_state.booking_mode = "ai_bot"
                st.rerun()
        with mode_col2:
            manual_active = st.session_state.get("booking_mode") == "manual"
            if st.button("📝 Manual", use_container_width=True, key="usb_mode_manual",
                         type="primary" if manual_active else "secondary"):
                st.session_state.booking_mode = "manual"
                st.rerun()

        st.markdown('<hr style="border:none; border-top:1px solid #e2e2e2; margin:18px 0;">', unsafe_allow_html=True)

        st.markdown('<p style="font-family:\'Inter\',sans-serif; font-size:0.72em; font-weight:500; color:#5e5e5e; margin-bottom:10px;">Account</p>', unsafe_allow_html=True)

        if st.button("👤 Profile Settings", use_container_width=True, key="usb_profile"):
            st.session_state.quick_action = "profile_settings"
            st.rerun()

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True, key="usb_logout"):
            for k in ["logged_in", "user", "role", "chat_history", "booking_mode", "quick_action"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()


def render_agency_sidebar():
    """Render sidebar for logged-in Agencies. Shows agency-specific navigation only."""
    _inject_sidebar_css()
    _inject_white_theme_css()

    agency_username = st.session_state.get("user", "Agency")
    initial = agency_username[0].upper() if agency_username else "A"

    with st.sidebar:
        # Agency info card
        st.markdown(f"""
        <div style="background: #efefef;
                    border: none; border-radius: 16px;
                    padding: 22px; margin-bottom: 22px; text-align: center;">
            <div style="width:58px; height:58px; border-radius:999px; background: #000000;
                        display:flex; align-items:center; justify-content:center; font-size:24px;
                        font-weight:700; color:#ffffff; margin:0 auto 12px auto;">{initial}</div>
            <div style="font-family:'Inter',sans-serif; font-weight:700; font-size:1.05em; color:#000000; margin-bottom:3px;">{agency_username}</div>
            <div style="font-size:0.7em; color:#5e5e5e; font-weight:400;">Travel Agency</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<p style="font-family:\'Inter\',sans-serif; font-size:0.72em; font-weight:500; color:#5e5e5e; margin-bottom:10px;">Navigation</p>', unsafe_allow_html=True)

        if st.button("📊 Dashboard", use_container_width=True, key="asb_dash"):
            st.switch_page("pages/1_agency_dashboard.py")

        if st.button("🛣️ Routes", use_container_width=True, key="asb_routes"):
            st.switch_page("pages/3_agency_routes.py")

        if st.button("📱 WhatsApp", use_container_width=True, key="asb_whatsapp"):
            st.switch_page("pages/2_agency_whatsapp.py")

        if st.button("📢 Broadcast", use_container_width=True, key="asb_broadcast"):
            st.switch_page("pages/4_agency_broadcast.py")

        if st.button("💰 Payment Setup", use_container_width=True, key="asb_payment"):
            st.switch_page("pages/5_agency_payment_setup.py")

        st.markdown('<hr style="border:none; border-top:1px solid #e2e2e2; margin:18px 0;">', unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True, key="asb_logout"):
            for k in ["logged_in", "user", "role", "chat_history", "booking_mode", "quick_action"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.switch_page("app.py")
