import streamlit as st
import os
import logging
import db
from chatbot import process_message, active_conversations, BookingConversation, handle_booking_confirmation
from qr_generator import generate_booking_qr, generate_ticket_html
import notifications as notif_manager
from voice_component import voice_input
import payment_page
from payments import init_payment_indexes
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Initialize database
try:
    db.init_db()
except:
    pass

def init_session_state():
    """Initialize session state - MUST be called AFTER set_page_config"""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "quick_action" not in st.session_state:
        st.session_state.quick_action = None
    if "last_message" not in st.session_state:
        st.session_state.last_message = None
    if "booking_mode" not in st.session_state:
        st.session_state.booking_mode = "ai_bot"
    if "voice_input" not in st.session_state:
        st.session_state.voice_input = ""

# =====================================================
# CUSTOM CSS
# =====================================================

# =====================================================
# SIDEBAR MENU — delegated to shared sidebar module
# =====================================================
from agency_sidebar import render_user_sidebar, render_agency_sidebar

def render_sidebar():
    """Render sidebar based on user role."""
    role = st.session_state.get("role")
    if role == "User":
        render_user_sidebar()
    elif role in ("Agency", "Travel Agency"):
        render_agency_sidebar()


def inject_custom_css():
    st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">', unsafe_allow_html=True)
    custom_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        /* ============================================================
           HIDE DEFAULT STREAMLIT ELEMENTS
           ============================================================ */
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

        /* ============================================================
           DESIGN TOKENS (Uber-inspired)
           ============================================================ */
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
            --link: #0000ee;
            --on-dark: #ffffff;
            --black-elevated: #282828;

            --text-primary: #000000;
            --text-secondary: #5e5e5e;
            --text-muted: #afafaf;

            --success: #10b981;
            --success-soft: rgba(16, 185, 129, 0.12);
            --warning: #f59e0b;
            --warning-soft: rgba(245, 158, 11, 0.12);
            --error: #ef4444;
            --error-soft: rgba(239, 68, 68, 0.12);
            --info: #3b82f6;
            --info-soft: rgba(59, 130, 246, 0.12);

            --r-none: 0px;
            --r-md: 8px;
            --r-lg: 12px;
            --r-xl: 16px;
            --r-pill: 999px;
            --r-pill-tab: 36px;
            --r-full: 9999px;

            --spacing-xxs: 4px;
            --spacing-xs: 6px;
            --spacing-sm: 8px;
            --spacing-md: 12px;
            --spacing-lg: 16px;
            --spacing-xl: 20px;
            --spacing-2xl: 24px;
            --spacing-3xl: 32px;

            --r-xs: 8px;
            --r-sm: 12px;

            --shadow-sm: 0 2px 8px rgba(0,0,0,0.08);
            --shadow-md: 0 4px 16px rgba(0,0,0,0.12);
            --shadow-lg: 0 8px 40px rgba(0,0,0,0.16);
            --shadow-pill: 0 2px 8px rgba(0,0,0,0.16);
            --shadow-elevated: 0 4px 16px rgba(0,0,0,0.12);
            --shadow-card: 0 4px 16px rgba(0,0,0,0.16);

            --ease: cubic-bezier(0.4, 0, 0.2, 1);
            --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        /* ============================================================
           GLOBAL RESET & BACKGROUND
           ============================================================ */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; }

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

        [data-testid="stAppViewContainer"]::before,
        [data-testid="stAppViewContainer"]::after {
            display: none !important;
        }

        /* ============================================================
           HEADINGS - Sentence-case, black, weight 700
           ============================================================ */
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

        /* ============================================================
           CARDS - Flat white with rounded.xl (16px)
           ============================================================ */
        .card, .glass-card {
            background: var(--canvas);
            border: 1px solid var(--surface-pressed);
            border-radius: var(--r-xl);
            padding: var(--spacing-2xl);
            position: relative;
            overflow: hidden;
            transition: all 0.25s var(--ease);
        }

        .card::before, .glass-card::before { display: none; }

        .card:hover, .glass-card:hover {
            border-color: var(--hairline-mid);
            box-shadow: var(--shadow-elevated);
        }

        .glass-card {
            background: var(--canvas);
            backdrop-filter: none;
            -webkit-backdrop-filter: none;
        }

        /* ============================================================
           BUTTONS - Pill-shaped (999px), black primary
           ============================================================ */
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

        /* Secondary button */
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

        /* ============================================================
           TEXT INPUTS - canvas-soft background
           ============================================================ */
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

        /* ============================================================
           SELECTBOX
           ============================================================ */
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

        /* ============================================================
           TABS - Pill-tab style (36px radius)
           ============================================================ */
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

        /* ============================================================
           SIDEBAR - White background, black text
           ============================================================ */
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

        [data-testid="stSidebar"] [data-testid="stMetric"] {
            background: var(--canvas-soft) !important;
            border: none !important;
            border-radius: var(--r-xl) !important;
            padding: var(--spacing-2xl) !important;
        }

        [data-testid="stSidebar"] [data-testid="stMetricValue"] {
            color: var(--ink) !important;
        }

        /* ============================================================
           DIVIDERS
           ============================================================ */
        hr, [data-testid="stHorizontalBlock"] hr {
            border: none !important;
            border-top: 1px solid var(--surface-pressed) !important;
            margin: 20px 0 !important;
        }

        /* ============================================================
           EXPANDER
           ============================================================ */
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

        /* ============================================================
           METRICS
           ============================================================ */
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

        /* ============================================================
           DATAFRAME / TABLES
           ============================================================ */
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

        .dataframe tbody tr:hover {
            background: var(--canvas-soft) !important;
        }

        .dataframe tbody td {
            color: var(--ink) !important;
            padding: 12px 16px !important;
        }

        /* ============================================================
           ALERTS / NOTIFICATIONS
           ============================================================ */
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

        /* ============================================================
           CHAT MESSAGES - Flat design
           ============================================================ */
        .bot-message {
            background: var(--canvas-soft) !important;
            border-left: 3px solid var(--ink) !important;
            padding: var(--spacing-lg) var(--spacing-2xl) !important;
            border-radius: 4px var(--r-xl) var(--r-xl) 4px !important;
            margin: 14px 0 !important;
            max-width: 82% !important;
            word-wrap: break-word !important;
            color: var(--ink) !important;
            line-height: 1.7 !important;
            font-size: 0.93em !important;
            box-shadow: none !important;
        }

        .user-message {
            background: var(--ink) !important;
            border-left: 3px solid var(--ink) !important;
            padding: var(--spacing-lg) var(--spacing-2xl) !important;
            border-radius: 4px var(--r-xl) var(--r-xl) 4px !important;
            margin: 14px 0 14px auto !important;
            max-width: 82% !important;
            word-wrap: break-word !important;
            color: var(--on-dark) !important;
            line-height: 1.7 !important;
            font-size: 0.93em !important;
            box-shadow: none !important;
        }

        @keyframes msgSlideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .success-box {
            background: var(--success-soft) !important;
            border-left: 4px solid var(--success) !important;
            padding: var(--spacing-lg) var(--spacing-2xl) !important;
            border-radius: 4px var(--r-xl) var(--r-xl) 4px !important;
            margin: 12px 0 !important;
        }

        .error-box {
            background: var(--error-soft) !important;
            border-left: 4px solid var(--error) !important;
            padding: var(--spacing-lg) var(--spacing-2xl) !important;
            border-radius: 4px var(--r-xl) var(--r-xl) 4px !important;
            margin: 12px 0 !important;
        }

        .stats-card {
            background: var(--canvas) !important;
            border: 1px solid var(--surface-pressed) !important;
            border-radius: var(--r-xl) !important;
            padding: var(--spacing-2xl) !important;
            margin: 10px 0 !important;
            transition: all 0.25s var(--ease) !important;
        }

        .stats-card:hover {
            border-color: var(--hairline-mid) !important;
            box-shadow: var(--shadow-elevated) !important;
        }

        /* ============================================================
           COLUMNS / LAYOUT
           ============================================================ */
        [data-testid="stHorizontalBlock"] { gap: 16px !important; }
        [data-testid="stColumn"] { padding: 5px !important; }

        /* ============================================================
           FORMS
           ============================================================ */
        [data-testid="stForm"] {
            background: var(--canvas) !important;
            border: 1px solid var(--surface-pressed) !important;
            border-radius: var(--r-xl) !important;
            padding: var(--spacing-2xl) !important;
            box-shadow: none !important;
        }

        /* ============================================================
           CHECKBOX / RADIO
           ============================================================ */
        [data-testid="stCheckbox"] label span { color: var(--ink) !important; }
        [data-testid="stRadio"] label span { color: var(--ink) !important; }

        /* ============================================================
           DATE INPUT
           ============================================================ */
        [data-testid="stDateInput"] > div > div {
            background: var(--canvas-soft) !important;
            border: none !important;
            border-radius: var(--r-none) !important;
            color: var(--ink) !important;
        }

        /* ============================================================
           PROGRESS BAR
           ============================================================ */
        [data-testid="stProgress"] > div > div {
            background: var(--ink) !important;
            border-radius: var(--r-full) !important;
        }

        [data-testid="stProgress"] > div {
            background: var(--canvas-soft) !important;
            border-radius: var(--r-full) !important;
        }

        /* ============================================================
           SCROLLBAR
           ============================================================ */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--surface-pressed); border-radius: 12px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--hairline-mid); }

        /* ============================================================
           LOADING / SPINNER
           ============================================================ */
        [data-testid="stSpinner"] > div { border-top-color: var(--ink) !important; }

        /* ============================================================
           MOBILE LAYOUT
           ============================================================ */
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
        }

        @media (max-width: 480px) {
            h1, [data-testid="stMarkdownContainer"] h1 { font-size: 1.4em !important; }
        }

        /* ============================================================
           TOUCH-FRIENDLY
           ============================================================ */
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

        /* ============================================================
           FOCUS VISIBLE (Accessibility)
           ============================================================ */
        :focus-visible {
            outline: 2px solid var(--ink);
            outline-offset: 3px;
        }

        /* ============================================================
           SELECTION
           ============================================================ */
        ::selection {
            background: rgba(0, 0, 0, 0.15);
            color: var(--ink);
        }

        /* ============================================================
           ANIMATIONS
           ============================================================ */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .stMarkdown { animation: fadeIn 0.3s var(--ease) both; }

        /* ============================================================
           LOGIN PAGE - Clean, Uber-inspired
           ============================================================ */
        @keyframes loginFadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes loginSlideUp {
            from { opacity: 0; transform: translateY(40px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .login-fade-in {
            animation: loginFadeIn 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        .login-slide-up {
            animation: loginSlideUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) 0.2s forwards;
        }

        .login-hero {
            text-align: left;
            padding: 0;
            margin-bottom: 32px;
        }

        .login-hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 18px;
            background: var(--ink) !important;
            border: none !important;
            border-radius: var(--r-pill) !important;
            font-size: 0.72em;
            font-weight: 500;
            color: var(--on-dark) !important;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 20px;
        }

        .login-hero h1 {
            font-family: 'Inter', sans-serif;
            font-size: 2.4em !important;
            font-weight: 800;
            margin-bottom: 8px !important;
            line-height: 1.1 !important;
            color: var(--ink) !important;
            letter-spacing: -0.04em;
            background: none !important;
            -webkit-text-fill-color: var(--ink) !important;
        }

        .login-hero p {
            color: var(--body) !important;
            font-size: 0.95em !important;
            margin: 0 !important;
            line-height: 1.6 !important;
        }

        .login-card-noir {
            background: #f3f3f3 !important;
            border: none !important;
            border-radius: var(--r-xl) !important;
            padding: var(--spacing-2xl) !important;
            box-shadow: none !important;
            position: relative;
            overflow: hidden;
        }

        .login-noir-btn {
            background: var(--primary) !important;
            color: var(--on-primary) !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            font-size: 1em !important;
            border: none !important;
            border-radius: var(--r-pill) !important;
            padding: 0 !important;
            height: 48px !important;
            width: 100% !important;
            cursor: pointer !important;
            position: relative;
            overflow: hidden;
            transition: all 0.2s ease !important;
        }
        .login-noir-btn:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        }
        .login-noir-btn:active {
            transform: translateY(0) !important;
        }
        .login-noir-btn::after { display: none; }

        .login-neon-text { text-shadow: none !important; }

        /* Tab overrides */
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
            font-size: 0.88em !important;
            padding: 12px 20px !important;
            transition: all 0.2s ease !important;
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

        /* Button overrides */
        [data-testid="stButton"] > button[kind="primary"],
        [data-testid="stButton"] > button[data-testid="stBaseButton-primary"] {
            background: var(--primary) !important;
            color: var(--on-primary) !important;
            border: none !important;
            border-radius: var(--r-pill) !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            height: 50px !important;
            box-shadow: none !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stButton"] > button[kind="primary"]:hover {
            box-shadow: var(--shadow-pill) !important;
        }

        /* Input overrides */
        [data-testid="stTextInput"] input,
        [data-testid="stTextInput"] input:focus {
            background: var(--canvas) !important;
            border: 1px solid var(--surface-pressed) !important;
            border-radius: var(--r-none) !important;
            color: var(--ink) !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stTextInput"] input:focus {
            outline: 2px solid var(--ink) !important;
            outline-offset: -2px !important;
            box-shadow: none !important;
            border-color: var(--ink) !important;
            background: var(--canvas) !important;
        }
        [data-testid="stTextInput"] label {
            font-family: 'Inter', sans-serif !important;
            font-size: 1em !important;
            font-weight: 400 !important;
            letter-spacing: 0 !important;
            text-transform: none !important;
            color: var(--ink) !important;
        }

        /* ============================================================
           NOTIFICATION CARD
           ============================================================ */
        .notif-card {
            border-radius: var(--r-xl) !important;
            padding: var(--spacing-lg) var(--spacing-2xl) !important;
            margin: 10px 0 !important;
            transition: all 0.2s var(--ease) !important;
            background: var(--canvas) !important;
            border: 1px solid var(--surface-pressed) !important;
        }

        .notif-card:hover { transform: translateX(3px); border-color: var(--hairline-mid); }

        /* ============================================================
           STATUS BADGES - Pill-shaped
           ============================================================ */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 5px 12px;
            border-radius: var(--r-pill);
            font-size: 0.75em;
            font-weight: 500;
            text-transform: none;
            letter-spacing: 0;
        }

        .status-confirmed {
            background: var(--success-soft);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.25);
        }

        .status-cancelled {
            background: var(--error-soft);
            color: var(--error);
            border: 1px solid rgba(239, 68, 68, 0.25);
        }

        /* ============================================================
           BOOKING CARD - Flat white with left indicator
           ============================================================ */
        .booking-card {
            background: var(--canvas) !important;
            border: 1px solid var(--surface-pressed) !important;
            border-radius: var(--r-xl) !important;
            padding: var(--spacing-2xl) !important;
            margin: 14px 0 !important;
            transition: all 0.25s var(--ease) !important;
            position: relative;
            overflow: hidden;
        }

        .booking-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            width: 4px;
            background: var(--ink);
        }

        .booking-card:hover {
            border-color: var(--hairline-mid) !important;
            box-shadow: var(--shadow-elevated) !important;
        }

        /* ============================================================
           BLOCK CONTAINER
           ============================================================ */
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
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def render_custom_header():
    """Render a premium custom header bar"""
    user = st.session_state.get("user", "")
    role = st.session_state.get("role", "")
    initial = user[0].upper() if user else ""
    role_label = "Agency" if role == "Travel Agency" else "User"

    nav_html = ""
    if user:
        nav_html = f'''
        <div class="header-nav">
            <span class="header-nav-link active">Dashboard</span>
        </div>
        <div class="header-user">
            <div class="header-user-avatar">{initial}</div>
            <div class="header-user-info">
                <span class="header-user-name">{user}</span>
                <span class="header-user-role">{role_label}</span>
            </div>
        </div>
        '''

    header_html = f'''
    <div class="custom-header">
        <div class="header-logo">
            <div class="header-logo-icon">🎫</div>
            <span class="header-logo-text">TicketHub</span>
        </div>
        {nav_html}
    </div>
    '''
    st.markdown(header_html, unsafe_allow_html=True)

def render_custom_footer():
    """Render a premium custom footer"""
    st.markdown('''
    <div class="custom-footer">
        <div class="footer-brand">TicketHub</div>
        <div class="footer-copy">Your trusted partner for bus travel &mdash; Book anywhere, anytime &copy; 2026</div>
    </div>
    ''', unsafe_allow_html=True)

# =====================================================
# LOGIN PAGE
# =====================================================

def login_page():
    """User and Agency Login Page"""
    import base64, os
    st.set_page_config(
        page_title="Ticket Booking - Login", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    init_session_state()
    inject_custom_css()
    
    # Load and encode background image, inject via <style> tag targeting Streamlit containers
    img_path = os.path.join(os.path.dirname(__file__), "image.jpg.jpeg")
    logo_path = os.path.join(os.path.dirname(__file__), "logo.jpg.jpeg")
    img_b64 = ""
    logo_b64 = ""
    if os.path.exists(img_path):
        with open(img_path, "rb") as img_file:
            img_b64 = base64.b64encode(img_file.read()).decode()
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as logo_file:
            logo_b64 = base64.b64encode(logo_file.read()).decode()
        bg_css = f"""
        <style>
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"],
        .main .block-container {{
            background: #ffffff !important;
            min-height: 100vh !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        section[data-testid="stSidebar"] {{
            display: none !important;
        }}
        .stHorizontalBlock {{
            gap: 0 !important;
        }}
        .login-image-panel {{
            width: 100% !important;
            height: 100vh !important;
            position: relative !important;
            overflow: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        .login-image-panel img {{
            width: 100% !important;
            height: 100% !important;
            object-fit: cover !important;
            display: block !important;
        }}
        .login-image-overlay {{
            position: absolute !important;
            top: 0 !important;
            right: 0 !important;
            background: transparent !important;
            display: none !important;
        }}
        .login-image-text {{
            display: none !important;
        }}
        </style>
        """
        st.markdown(bg_css, unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 1], gap=None)

    with right_col:
        if img_b64:
            st.markdown(f'''
            <div class="login-image-panel">
                <img src="data:image/png;base64,{img_b64}" />
            </div>
            ''', unsafe_allow_html=True)

    with left_col:

        logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" style="height: 55px; width: auto; vertical-align: middle; margin-right: 14px;" />' if logo_b64 else ''
        hero_html = f'''
        <div style="text-align: left; margin-bottom: 24px; display: flex; align-items: center;">
            {logo_html}
            <h1 style="color: #e50914; -webkit-text-fill-color: #e50914; font-size: 2.8em; font-weight: 800; letter-spacing: -0.04em; margin: 0;">TICKETHUB</h1>
        </div>
        <div style="margin-bottom: 32px; text-align: left;">
            <h2 style="color: #000000 !important; -webkit-text-fill-color: #000000 !important; font-weight: 800; font-size: 1.6em; letter-spacing: -0.03em; margin: 0 0 8px 0;">BOOK YOUR TICKETS HERE</h2>
            <p style="color: #5e5e5e; font-size: 0.85em; margin: 0; font-weight: 400;">Fast, secure, and hassle-free bus booking</p>
        </div>
        '''
        st.markdown(hero_html, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["User Login", "Agency Login"])

        with tab1:
            st.subheader("User Login")
            
            username = st.text_input("Username", key="user_username")
            password = st.text_input("Password", type="password", key="user_password")
            
            col_login, col_signup = st.columns(2)
            
            with col_login:
                if st.button("Login", use_container_width=True):
                    if username and password:
                        result = db.login_user(username, password)
                        if result['success']:
                            st.session_state.user = username
                            st.session_state.role = "User"
                            st.session_state.logged_in = True
                            profile = db.get_user_profile(username)
                            if profile:
                                st.session_state.user_gender = profile.get('gender', 'Male')
                            conv = BookingConversation(username)
                            if profile:
                                conv.passenger_gender = profile.get('gender')
                            active_conversations[username] = conv
                            st.success("Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error(f"{result['message']}")
                    else:
                        st.warning("Please enter username and password")
            
            with col_signup:
                if st.button("Sign Up", use_container_width=True):
                    st.session_state.show_signup = True
            
            if st.session_state.get("show_signup"):
                st.markdown("---")
                st.subheader("Create New Account")
                new_username = st.text_input("New Username", key="new_user_username")
                new_password = st.text_input("New Password", type="password", key="new_user_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
                new_phone = st.text_input("Mobile Number", placeholder="e.g., 9876543210", key="new_user_phone")
                signup_gender = st.selectbox("Gender", ["Male", "Female"], key="signup_gender")
                full_name = st.text_input("Full Name", key="signup_fullname")
                age = st.number_input("Age", min_value=1, max_value=120, value=25, key="signup_age")
                
                if st.button("Create Account", use_container_width=True):
                    if new_username and new_password and full_name:
                        from auth import validate_phone, validate_password_strength
                        phone_valid = validate_phone(new_phone)
                        pw_valid = validate_password_strength(new_password)
                        
                        if not phone_valid["valid"]:
                            st.error(f"{phone_valid['message']}")
                        elif not pw_valid["valid"]:
                            st.error(f"{pw_valid['message']}")
                        elif new_password == confirm_password:
                            result = db.create_user(new_username, new_password, "User", gender_option=signup_gender, full_name=full_name, age=int(age), phone=phone_valid["formatted"])
                            if result['success']:
                                st.success("Account created! Please login now.")
                                st.session_state.show_signup = False
                                st.rerun()
                            else:
                                st.error(f"{result['message']}")
                        else:
                            st.error("Passwords don't match!")
                    else:
                        st.warning("Please fill in all fields")

        with tab2:
            st.subheader("Agency Login")
            
            agency_username = st.text_input("Agency Username", key="agency_username")
            agency_password = st.text_input("Agency Password", type="password", key="agency_password")
            
            col_login, col_signup = st.columns(2)
            
            with col_login:
                if st.button("Login", use_container_width=True, key="agency_login"):
                    if agency_username and agency_password:
                        result = db.login_user(agency_username, agency_password)
                        if result['success'] and result['role'] == "Travel Agency":
                            st.session_state.user = agency_username
                            st.session_state.role = "Agency"
                            active_conversations[agency_username] = BookingConversation(agency_username)
                            st.session_state.logged_in = True
                            st.success("Agency login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error(f"{result.get('message', 'Invalid credentials')}")
                    else:
                        st.warning("Please enter username and password")
            
            with col_signup:
                if st.button("Register", use_container_width=True):
                    st.session_state.show_agency_signup = True
            
            if st.session_state.get("show_agency_signup"):
                st.markdown("---")
                st.subheader("Register Agency")
                agency_name = st.text_input("Agency Name")
                new_agency_username = st.text_input("Username", key="new_agency_username")
                new_agency_password = st.text_input("Password", type="password", key="new_agency_password")
                confirm_agency_password = st.text_input("Confirm Password", type="password", key="confirm_agency_password")
                agency_phone = st.text_input("Mobile Number", placeholder="e.g., 9876543210", key="agency_phone")
                
                total_vehicles = st.number_input("Total Vehicles", min_value=1, value=5)
                seats_per_vehicle = st.number_input("Seats Per Vehicle", min_value=1, value=50)
                bus_type = st.selectbox("Bus Model / Type", ["Standard (2x2)", "Luxury (2x1)", "Sleeper (1x2)"])
                
                routes_text = st.text_area("Routes (comma-separated, format: City1-City2)", 
                                          placeholder="Delhi-Mumbai, Mumbai-Bangalore, Delhi-Goa")
                
                if st.button("Register Agency", use_container_width=True):
                    if new_agency_username and new_agency_password and agency_name:
                        from auth import validate_phone, validate_password_strength
                        phone_valid = validate_phone(agency_phone)
                        pw_valid = validate_password_strength(new_agency_password)
                        
                        if not phone_valid["valid"]:
                            st.error(f"{phone_valid['message']}")
                        elif not pw_valid["valid"]:
                            st.error(f"{pw_valid['message']}")
                        elif new_agency_password == confirm_agency_password:
                            routes = [r.strip() for r in routes_text.split(',') if '-' in r]
                            routes_list = [{"source": r.split('-')[0].strip(), 
                                          "destination": r.split('-')[1].strip()} for r in routes]
                            
                            agency_details = {
                                "agency_name": agency_name,
                                "routes": routes_list,
                                "total_vehicles": int(total_vehicles),
                                "seats_per_vehicle": int(seats_per_vehicle),
                                "bus_type": bus_type
                            }
                            
                            result = db.create_user(new_agency_username, new_agency_password, 
                                                  "Travel Agency", agency_details, phone=phone_valid["formatted"])
                            if result['success']:
                                st.success("Agency registered! Please login now.")
                                st.session_state.show_agency_signup = False
                                st.rerun()
                            else:
                                st.error(f"{result['message']}")
                        else:
                            st.error("Passwords don't match!")
                    else:
                        st.warning("Please fill in all required fields")

        footer_html = '''
        <div style="margin-top: 32px; padding-top: 20px; border-top: 1px solid #e2e2e2;">
            <p style="font-size: 0.85em; color: #afafaf; margin: 0;">
                Don't have an account? 
                <span style="color: #000000; font-weight: 500; cursor: pointer;">Register Citizen</span>
            </p>
            <div style="margin-top: 16px;">
                <span style="font-family: 'Inter', sans-serif; font-size: 10px; color: #afafaf; letter-spacing: 0.15em; text-transform: uppercase;">TICKETHUB SYSTEMS v2.0</span>
            </div>
        </div>
        '''
        st.markdown(footer_html, unsafe_allow_html=True)

# =====================================================
# USER CHATBOT PAGE
# =====================================================

def user_chatbot_page():
    """Main chatbot interface for users"""
    st.set_page_config(
        page_title="Ticket Booking Chatbot", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    inject_custom_css()
    render_sidebar()
    
    # Check if user is accessing profile settings
    if st.session_state.get("quick_action") == "profile_settings":
        user_profile_page()
        return
    
    # Check if user is accessing payment page
    if st.session_state.get("quick_action") == "payments":
        payment_page.render_payment_page()
        return

    # Route manual booking actions (from sidebar) regardless of booking_mode
    qa = st.session_state.get("quick_action")
    if qa in ("manual_view", "manual_book", "manual_cancel"):
        _render_manual_section()
        return

    # Route notifications from sidebar regardless of booking_mode
    if qa == "notifications":
        _render_notifications_panel()
        return
    
    # Page header with user actions
    header_col1, header_col2, header_col3 = st.columns([4, 1, 1])
    with header_col1:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:4px;">
            <div style="width:44px; height:44px; border-radius:999px; background:#000000;
                        display:flex; align-items:center; justify-content:center; font-size:18px;
                        font-weight:700; color:#ffffff;
                        flex-shrink:0;">{st.session_state.user[0].upper() if st.session_state.user else '?'}</div>
            <div>
                <div style="font-family:'Inter',sans-serif; font-weight:700; font-size:1.4em;
                            color:#000000;
                            letter-spacing:-0.02em;">Welcome back, {st.session_state.user}</div>
                <div style="font-family:'Inter',sans-serif; font-size:0.78em; color:#5e5e5e;
                            font-weight:400;">Your Dashboard</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with header_col2:
        if st.button("👤  Profile", use_container_width=True, key="main_profile"):
            st.session_state.quick_action = "profile_settings"
            st.rerun()
    with header_col3:
        if st.button("🚪  Logout", use_container_width=True, key="main_logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.chat_history = []
            st.session_state.quick_action = None
            st.session_state.booking_mode = "ai_bot"
            st.rerun()
    
    st.markdown("---")
    
    if st.session_state.booking_mode == "ai_bot":
        # AI BOT MODE
        st.markdown("### 🤖 AI Bot Mode")
        st.markdown("*Chat with our intelligent booking assistant - simply describe what you need!*")
        st.markdown("")
        
        # Quick action buttons
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("📝 Book", use_container_width=True, key="quick_book"):
                st.session_state.quick_action = "book"
                st.rerun()
        
        with col2:
            if st.button("📋 Bookings", use_container_width=True, key="quick_bookings"):
                st.session_state.quick_action = "view"
                st.rerun()
        
        with col3:
            if st.button("🛣️ Routes", use_container_width=True, key="quick_routes"):
                st.session_state.quick_action = "routes"
                st.rerun()
        
        with col4:
            if st.button("❓ Help", use_container_width=True, key="quick_help"):
                st.session_state.quick_action = "help"
                st.rerun()

        with col5:
            unread_count = db.get_unread_notification_count(st.session_state.user)
            notif_label = f"🔔 Alerts ({unread_count})" if unread_count > 0 else "🔔 Alerts"
            if st.button(notif_label, use_container_width=True, key="quick_notifications"):
                st.session_state.quick_action = "notifications"
                st.rerun()
        
        st.markdown("---")
        
        # Chat area
        st.markdown("### 💬 Chat with Bot")
        
        # Display chat history
        for i, msg in enumerate(st.session_state.chat_history):
            if msg['role'] == 'user':
                voice_tag = ' 🎤' if msg.get('is_voice') else ''
                st.write(f"👤 **You{voice_tag}**: {msg['content']}")
            else:
                # Check if message contains HTML (seat map)
                if '<div' in msg['content'] or '<button' in msg['content']:
                    st.markdown(msg['content'], unsafe_allow_html=True)
                else:
                    st.write(f"🤖 **Bot**: {msg['content']}")
                    # Add voice output button for bot messages
                    safe_text = msg['content'].replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ").replace('"', "&quot;")
                    # Use base64 encoding to safely pass text with emojis/special chars
                    import base64 as b64
                    encoded_text = b64.b64encode(msg['content'].encode('utf-8')).decode('ascii')
                    speak_btn_html = f'''
                    <button onclick="try {{ var s=window.speechSynthesis; s.cancel(); var decoded=atob('{encoded_text}'); var u=new SpeechSynthesisUtterance(decoded); u.rate=0.9; u.pitch=1.0; u.volume=1.0; s.speak(u); }} catch(e) {{ console.error(e); }}" 
                        style="display:inline-flex; align-items:center; gap:4px; padding:4px 10px; 
                        background:#efefef; border:none; 
                        border-radius:999px; color:#5e5e5e; font-size:0.75em; cursor:pointer; 
                        transition:all 0.2s ease; margin-top:4px; font-weight:500;"
                        onmouseover="this.style.background='#e2e2e2'; this.style.color='#000000'"
                        onmouseout="this.style.background='#efefef'; this.style.color='#5e5e5e'">
                        Listen
                    </button>
                    '''
                    st.markdown(speak_btn_html, unsafe_allow_html=True)

        # If bot is awaiting confirmation, show Confirm/Cancel buttons
        conv = active_conversations.get(st.session_state.user) if st.session_state.user else None
        if conv and conv.stage == "confirmation":
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Confirm & Pay", key="bot_confirm"):
                    bot_response = handle_booking_confirmation(conv, "yes", st.session_state.user)
                    st.session_state.chat_history.append({'role': 'bot', 'content': bot_response})
                    st.rerun()
            with col_no:
                if st.button("❌ Cancel Booking", key="bot_cancel"):
                    bot_response = handle_booking_confirmation(conv, "no", st.session_state.user)
                    st.session_state.chat_history.append({'role': 'bot', 'content': bot_response})
                    st.rerun()

        # Input area with voice
        user_input = st.text_input("You: ", placeholder="Type your message or use voice input...", key="chat_input_" + str(len(st.session_state.chat_history)))
        
        # Voice input (records audio and transcribes)
        voice_text = voice_input(key="voice_btn")
        if voice_text:
            user_input = voice_text
        
        # Handle quick actions first (before checking user_input) - ONLY FOR AI BOT MODE
        if st.session_state.get("quick_action"):
            if st.session_state.quick_action == "book":
                user_input = "I want to book a ticket"
                st.session_state.quick_action = None
            elif st.session_state.quick_action == "view":
                user_input = "show my bookings"
                st.session_state.quick_action = None
            elif st.session_state.quick_action == "routes":
                user_input = "what routes are available"
                st.session_state.quick_action = None
            elif st.session_state.quick_action == "help":
                user_input = "help"
                st.session_state.quick_action = None
            elif st.session_state.quick_action == "notifications":
                # handled below as a panel, not a chat message
                pass
        
        if user_input and user_input != st.session_state.last_message:
            # Mark this message as processed
            st.session_state.last_message = user_input
            
            # Check if input came from voice
            is_voice = bool(st.session_state.get("voice_input")) and st.session_state.get("voice_input") == user_input
            
            # Add user message to history
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input,
                'is_voice': is_voice
            })
            
            # Get bot response
            bot_response = process_message(user_input, username=st.session_state.user, is_voice=is_voice)
            
            # Add bot response to history
            st.session_state.chat_history.append({
                'role': 'bot',
                'content': bot_response
            })
            
            st.rerun()

        # ── Notifications Panel ──────────────────────────────────────────
        if st.session_state.get("quick_action") == "notifications":
            _render_notifications_panel()

    else:
        _render_manual_section()


def _render_notifications_panel():
    """Render notifications panel for users."""
    st.markdown("### 🔔 Your Notifications")

    notifications = db.get_user_notifications(st.session_state.user)
    db.mark_notifications_read(st.session_state.user)

    if not notifications:
        st.info("📭 You have no notifications yet. Agencies will send you messages about your bookings here.")
    else:
        for notif in notifications:
            is_unread = not notif.get("is_read", True)
            border_color = "#00d4ff" if is_unread else "rgba(255,255,255,0.15)"
            bg_color = "rgba(0,212,255,0.08)" if is_unread else "rgba(255,255,255,0.03)"
            unread_badge = "🆕 " if is_unread else ""

            created_at = notif.get("created_at")
            time_str = created_at.strftime("%d %b %Y, %I:%M %p") if created_at else "Unknown time"

            st.markdown(
                f"""
                <div style="background:{bg_color}; border-left:4px solid {border_color};
                    border-radius:8px; padding:14px 16px; margin:10px 0;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <span style="font-weight:700; color:#00d4ff; font-size:0.95em;">
                            {unread_badge}🏢 {notif.get('agency_name', notif.get('agency_username', 'Agency'))}
                        </span>
                        <span style="font-size:0.78em; color:#b0b9c6;">
                            🎫 Booking #{notif.get('booking_id')} | 🕐 {time_str}
                        </span>
                    </div>
                    <p style="margin:0; font-size:0.92em; color:#e0e8f0; line-height:1.5;">
                        {notif.get('message', '')}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    if st.button("✖ Close", key="close_notif"):
        st.session_state.quick_action = None
        st.rerun()


def _render_manual_section():
    """Render the manual booking mode UI (book, view bookings, cancel)."""
    st.markdown("### 📝 Manual Booking Mode")
    st.markdown("---")

    action = st.session_state.get("quick_action")

    if action == "manual_book":
        st.markdown("### ✅ Book a Ticket")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("#### 📍 Route Information")
            source = st.text_input("From (Source City)", placeholder="e.g., Chennai", key="manual_source")
            destination = st.text_input("To (Destination City)", placeholder="e.g., Mumbai", key="manual_dest")
            travel_date = st.date_input("📅 Travel Date", key="manual_date")

        with col2:
            st.markdown("#### 🚌 Select Agency & Seat")
            fare = 0
            selected_agency = None
            seat = None
            if source and destination:
                agencies = db.get_agencies_by_route(source, destination)
                if agencies:
                    agency_option = st.selectbox(
                        "Select Agency",
                        [a['agency_name'] for a in agencies],
                        key="manual_agency"
                    )
                    selected_agency = next(a for a in agencies if a['agency_name'] == agency_option)
                    available_seats = db.get_available_seats(
                        selected_agency['agency_username'],
                        source,
                        destination,
                        travel_date.strftime('%Y-%m-%d')
                    )
                    if available_seats:
                        seat = st.selectbox("Select Seat", available_seats, key="manual_seat")
                    else:
                        st.warning("❌ No seats available for this date")
                        seat = None

                    fare_doc = db.get_route_fare_with_timing(
                        selected_agency['agency_username'], source, destination
                    )
                    if fare_doc and fare_doc.get("fare"):
                        fare = fare_doc["fare"]
                else:
                    st.warning("❌ No agencies found for this route")
            else:
                st.info("📝 Enter route details to see available agencies")

        st.markdown("---")
        st.markdown("#### 👤 Passenger Details")

        passenger_name = st.text_input("Full Name", placeholder="e.g., John Doe", key="manual_name")
        passenger_age = st.number_input("Age", min_value=1, max_value=120, value=25, key="manual_age")
        passenger_gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="manual_gender")

        st.markdown("---")

        if fare and seat and selected_agency:
            st.markdown(f"""
            <div style="background:rgba(0,212,255,0.05); border:1px solid rgba(0,212,255,0.15); border-radius:12px; padding:16px 20px; margin:8px 0;">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:#8899aa; font-size:13px;">Route</span>
                    <span style="color:#00d4ff; font-weight:700; font-size:13px;">{source} → {destination}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:#8899aa; font-size:13px;">Agency</span>
                    <span style="color:#e8edf4; font-weight:600; font-size:13px;">{selected_agency['agency_name']}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:#8899aa; font-size:13px;">Seat</span>
                    <span style="color:#e8edf4; font-weight:600; font-size:13px;">{seat}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:#8899aa; font-size:13px;">Date</span>
                    <span style="color:#e8edf4; font-weight:600; font-size:13px;">{travel_date.strftime('%d %b %Y')}</span>
                </div>
                <div style="border-top:1px dashed rgba(255,255,255,0.08); padding-top:8px; margin-top:4px;">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:#8899aa; font-size:13px;">Total Fare</span>
                        <span style="color:#00d4ff; font-weight:800; font-size:18px;">₹{fare}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🎫 Confirm Booking", use_container_width=True, key="manual_confirm", type="primary"):
            if source and destination and passenger_name and seat and selected_agency:
                booking_result = db.create_booking(
                    username=st.session_state.user,
                    agency_username=selected_agency['agency_username'],
                    source=source,
                    destination=destination,
                    date=travel_date.strftime('%Y-%m-%d'),
                    seat=seat,
                    passenger_name=passenger_name,
                    passenger_age=int(passenger_age),
                    passenger_gender=passenger_gender
                )
                if booking_result['success']:
                    booking_id = booking_result['booking_id']

                    try:
                        db.tickets_collection.insert_one({
                            "booking_id": booking_id,
                            "username": st.session_state.user,
                            "agency_username": selected_agency['agency_username'],
                            "source": source,
                            "destination": destination,
                            "date": travel_date.strftime('%Y-%m-%d'),
                            "seat": seat,
                            "passenger_name": passenger_name,
                            "passenger_age": int(passenger_age),
                            "passenger_gender": passenger_gender,
                            "fare": fare,
                            "status": "confirmed",
                            "payment_method": "manual",
                            "created_at": datetime.datetime.now()
                        })
                    except Exception:
                        pass

                    try:
                        db.revenue_collection.insert_one({
                            "agency_username": selected_agency['agency_username'],
                            "booking_id": booking_id,
                            "fare": fare,
                            "date": travel_date.strftime('%Y-%m-%d'),
                            "source": source,
                            "destination": destination,
                            "created_at": datetime.datetime.now()
                        })
                    except Exception:
                        pass

                    try:
                        import notifications as nm
                        bus_timing = db.get_route_fare_with_timing(
                            selected_agency['agency_username'], source, destination
                        )
                        booking_data = {
                            "booking_id": booking_id,
                            "username": st.session_state.user,
                            "agency_username": selected_agency['agency_username'],
                            "source": source,
                            "destination": destination,
                            "date": travel_date.strftime('%Y-%m-%d'),
                            "seat": seat,
                            "passenger_name": passenger_name,
                            "passenger_age": int(passenger_age),
                            "passenger_gender": passenger_gender,
                            "fare": fare,
                            "status": "confirmed",
                            "phone_number": "",
                            "departure_time": bus_timing.get("departure_time", "") if bus_timing else "",
                            "arrival_time": bus_timing.get("arrival_time", "") if bus_timing else "",
                            "bus_number": bus_timing.get("bus_number", "") if bus_timing else "",
                        }
                        nm.send_booking_confirmation(booking_data)
                    except Exception:
                        pass

                    st.success(f"✅ Booking #{booking_id} Confirmed! Fare: ₹{fare}")
                    st.session_state.quick_action = None
                    st.rerun()
                else:
                    st.error(f"❌ Booking failed: {booking_result['message']}")
            else:
                st.error("❌ Please fill all required fields")

    elif action == "manual_view":
        st.markdown("### 📋 My Bookings")
        st.markdown("---")

        bookings = db.get_user_bookings(st.session_state.user)

        if bookings:
            st.success(f"✅ You have {len(bookings)} booking(s)")

            for booking in bookings:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.markdown(f"""
                        🎫 **Booking #{booking['booking_id']}**
                        - 📍 Route: {booking['source']} → {booking['destination']}
                        - 📅 Date: {booking['date']}
                        - 💺 Seat: {booking['seat']}
                        - 👤 Passenger: {booking['passenger_name']} ({booking['passenger_age']} yrs)
                        - 🏢 Agency: {booking['agency_username']}
                        - Status: {booking['status'].upper()}
                        """)

                    with col2:
                        if booking['status'] != 'cancelled':
                            try:
                                import qr_generator
                                qr_base64 = qr_generator.generate_booking_qr(booking)
                                st.markdown(
                                    f'<img src="data:image/png;base64,{qr_base64}" style="width:120px; border-radius:8px;">',
                                    unsafe_allow_html=True
                                )
                                st.caption("📱 Scan QR Code")
                            except Exception:
                                pass

                    with col3:
                        if booking['status'] != 'cancelled':
                            try:
                                import qr_generator
                                ticket_record = db.get_ticket_by_booking(booking['booking_id'])
                                agency_info = db.get_agency(booking.get('agency_username'))
                                payment_record = None
                                if ticket_record and ticket_record.get('transaction_id'):
                                    payment_record = db.get_payment_by_transaction(ticket_record['transaction_id'])
                                pdf_data = qr_generator.generate_ticket_pdf(booking, agency_info, payment_record)
                                if isinstance(pdf_data, bytearray):
                                    pdf_data = bytes(pdf_data)
                                st.download_button(
                                    label="📥 Download Ticket",
                                    data=pdf_data,
                                    file_name=f"Ticket_{booking['booking_id']}.pdf",
                                    mime="application/pdf",
                                    key=f"pdf_{booking['booking_id']}",
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.warning("PDF not available")

                            if st.button("❌ Cancel", key=f"cancel_{booking['booking_id']}", use_container_width=True):
                                result = db.cancel_booking(booking['booking_id'])
                                if result['success']:
                                    try:
                                        import notifications as notif_manager
                                        notif_manager.send_cancellation_notification(result['booking'])
                                    except Exception:
                                        pass
                                st.success(f"Booking #{booking['booking_id']} cancelled")
                                st.rerun()

                    st.divider()
        else:
            st.info("📌 You have no bookings yet")

    elif action == "manual_cancel":
        st.markdown("### ❌ Cancel Booking")
        st.markdown("---")

        bookings = db.get_user_bookings(st.session_state.user)
        active_bookings = [b for b in bookings if b['status'] != 'cancelled']

        if active_bookings:
            booking_options = {
                f"Booking #{b['booking_id']} - {b['source']} to {b['destination']} ({b['date']})": b['booking_id']
                for b in active_bookings
            }
            selected = st.selectbox("Select a booking to cancel", list(booking_options.keys()))
            booking_id = booking_options[selected]
            st.warning(f"⚠️ Are you sure you want to cancel booking #{booking_id}?")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Cancel it", use_container_width=True):
                    result = db.cancel_booking(booking_id)
                    if result['success']:
                        try:
                            import notifications as notif_manager
                            notif_manager.send_cancellation_notification(result['booking'])
                        except Exception:
                            pass
                    st.success(f"✅ Booking #{booking_id} has been cancelled")
                    st.session_state.quick_action = None
                    st.rerun()
            with col2:
                if st.button("❌ No, Keep it", use_container_width=True):
                    st.session_state.quick_action = None
                    st.rerun()
        else:
            st.info("📌 You have no active bookings to cancel")

    else:
        # Default view — show manual mode home with action buttons
        st.info("📌 **Select an action from the sidebar or below:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### ✅ Book a Ticket")
            st.markdown("Create a new booking by providing your route and seat preference")
            if st.button("📝 Book Now", use_container_width=True, key="home_book"):
                st.session_state.quick_action = "manual_book"
                st.rerun()

        with col2:
            st.markdown("### 📋 My Bookings")
            st.markdown("View and manage all your bookings in one place")
            if st.button("📋 View Bookings", use_container_width=True, key="home_view"):
                st.session_state.quick_action = "manual_view"
                st.rerun()

        with col3:
            st.markdown("### ❌ Cancel Booking")
            st.markdown("Cancel an existing booking if your plans changed")
            if st.button("❌ Cancel Booking", use_container_width=True, key="home_cancel"):
                st.session_state.quick_action = "manual_cancel"
                st.rerun()
            
            with col2:
                st.markdown("### 📋 View Bookings")
                st.markdown("View all your existing bookings and their details")
            
            with col3:
                st.markdown("### ❌ Cancel Booking")
                st.markdown("Cancel any of your existing bookings")
    
    render_custom_footer()

# =====================================================
# USER PROFILE SETTINGS PAGE
# =====================================================

def user_profile_page():
    """User profile settings and management"""
    # Responsive layout: centered content
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 👤 My Profile")
        st.markdown("---")
        
        # Fetch current profile
        profile = db.get_user_profile(st.session_state.user)
        
        if profile:
            st.markdown("### 📋 Profile Information")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Username:** {profile['username']}")
                st.markdown(f"**Full Name:** {profile['full_name']}")
            
            with col2:
                st.markdown(f"**Gender:** {profile['gender']}")
                st.markdown(f"**Age:** {profile['age']}")
            
            if profile.get('phone'):
                st.markdown(f"**Phone:** {profile['phone']}")
            
            st.markdown("---")
            st.markdown("### ✏️ Edit Profile")
            
            new_full_name = st.text_input("Full Name", value=profile['full_name'], key="edit_fullname")
            new_age = st.number_input("Age", min_value=1, max_value=120, value=profile['age'] or 25, key="edit_age")
            new_gender = st.selectbox("Gender", ["Male", "Female"], index=0 if profile['gender'] == "Male" else 1, key="edit_gender")
            new_phone = st.text_input("Phone Number", value=profile.get('phone', ''), placeholder="e.g., 9876543210", key="edit_phone")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Changes", use_container_width=True):
                    result = db.update_user_profile(st.session_state.user, full_name=new_full_name, age=new_age, gender=new_gender)
                    if new_phone and new_phone != profile.get('phone', ''):
                        db.update_user_phone(st.session_state.user, new_phone)
                    if result['success']:
                        st.success("✅ Profile updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Update failed: {result['message']}")
            
            with col2:
                if st.button("🔙 Back to Dashboard", use_container_width=True):
                    st.session_state.quick_action = None
                    st.rerun()
        
        else:
            st.warning("⚠️ Profile not found. Please contact support.")

# =====================================================
# AGENCY DASHBOARD
# =====================================================

def agency_dashboard():
    """Agency dashboard for viewing bookings and statistics"""
    st.set_page_config(
        page_title="Agency Dashboard", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    inject_custom_css()
    render_sidebar()
    
    # Responsive header layout
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown("# 🏢 Agency Dashboard")
    with col3:
        if st.button("🚪 Logout", key="agency_logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()
    
    agency_username = st.session_state.user
    st.markdown(f"**Agency: {agency_username}**")
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Statistics", "📋 Bookings", "🛣️ Routes", "⚙️ Settings", "📢 Send Notification", "📱 WhatsApp"])
    
    with tab1:
        st.subheader("📊 Booking Statistics")
        
        bookings = db.get_bookings_by_agency(agency_username)
        agency_info = db.get_agency(agency_username)
        
        if agency_info:
            # Responsive stats cards (2 cols on mobile, 4 on desktop)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Bookings", len(bookings))
            
            with col2:
                st.metric("Total Vehicles", agency_info.get('total_vehicles', 0))
            
            with col3:
                st.metric("Seats/Vehicle", agency_info.get('seats_per_vehicle', 0))
            
            with col4:
                total_capacity = (agency_info.get('total_vehicles', 0) * 
                                 agency_info.get('seats_per_vehicle', 0))
                st.metric("Total Capacity", total_capacity)
            
            st.markdown("---")
            
            # Recent bookings chart
            if bookings:
                dates = [b.get('date') for b in bookings]
                date_counts = pd.Series(dates).value_counts().sort_index()
                
                st.markdown("### 📈 Bookings by Date")
                st.bar_chart(date_counts)
                
                # Route stats
                st.markdown("### 🛣️ Bookings by Route")
                routes = [f"{b.get('source', '')} → {b.get('destination', '')}" for b in bookings]
                route_counts = pd.Series(routes).value_counts()
                st.bar_chart(route_counts)
                
                # Status breakdown
                st.markdown("### 📊 Booking Status")
                statuses = [b.get('status', 'confirmed') for b in bookings]
                status_counts = pd.Series(statuses).value_counts()
                st.bar_chart(status_counts)
                
                # Revenue estimate
                st.markdown("### 💰 Revenue Summary")
                confirmed = [b for b in bookings if b.get('status') == 'confirmed']
                st.metric("Confirmed Bookings", len(confirmed))
                st.metric("Cancelled Bookings", len(bookings) - len(confirmed))
                cancel_rate = ((len(bookings) - len(confirmed)) / len(bookings) * 100) if bookings else 0
                st.metric("Cancellation Rate", f"{cancel_rate:.1f}%")
    
    with tab2:
        st.subheader("📋 All Bookings")
        
        bookings = db.get_bookings_by_agency(agency_username)
        
        if bookings:
            # Create DataFrame
            data = []
            for b in bookings:
                data.append({
                    'Booking ID': b.get('booking_id'),
                    'Passenger': b.get('passenger_name', 'N/A'),
                    'Age': b.get('passenger_age', 'N/A'),
                    'From': b.get('source'),
                    'To': b.get('destination'),
                    'Date': b.get('date'),
                    'Seat': b.get('seat'),
                    'Status': b.get('status', 'confirmed')
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # Summary stats
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Bookings", len(bookings))
            with col2:
                confirmed = sum(1 for b in bookings if b.get('status') == 'confirmed')
                st.metric("Confirmed", confirmed)
            with col3:
                cancelled = sum(1 for b in bookings if b.get('status') == 'cancelled')
                st.metric("Cancelled", cancelled)
        else:
            st.info("📭 No bookings yet")
    
    with tab3:
        st.subheader("🛣️ Available Routes")
        
        agency_info = db.get_agency(agency_username)
        
        if agency_info:
            routes = agency_info.get('routes', [])
            
            if routes:
                for i, route in enumerate(routes, 1):
                    st.markdown(f"**{i}. {route['source']} → {route['destination']}**")
            else:
                st.info("📭 No routes configured")
    
    with tab4:
        st.subheader("⚙️ Agency Settings")
        
        agency_info = db.get_agency(agency_username)
        
        if agency_info:
            st.markdown("### 🛠️ Edit Configuration")
            with st.form("agency_settings_form"):
                new_agency_name = st.text_input(
                    "Agency Name",
                    value=agency_info.get("agency_name", "")
                )
                new_total_vehicles = st.number_input(
                    "Total Vehicles",
                    min_value=1,
                    max_value=1000,
                    value=int(agency_info.get("total_vehicles", 0))
                )
                new_seats_per_vehicle = st.number_input(
                    "Seats per Vehicle",
                    min_value=1,
                    max_value=100,
                    value=int(agency_info.get("seats_per_vehicle", 0))
                )
                
                # Retrieve current bus type index
                bus_options = ["Standard (2x2)", "Luxury (2x1)", "Sleeper (1x2)"]
                current_bus_type = agency_info.get("bus_type", "Standard (2x2)")
                try:
                    bus_index = bus_options.index(current_bus_type)
                except ValueError:
                    bus_index = 0
                    
                new_bus_type = st.selectbox(
                    "Bus Model / Type",
                    bus_options,
                    index=bus_index
                )
                
                submitted = st.form_submit_button("💾 Save Settings", use_container_width=True)
                if submitted:
                    if not new_agency_name.strip():
                        st.error("⚠️ Agency Name cannot be empty.")
                    else:
                        agency_details = {
                            "agency_name": new_agency_name.strip(),
                            "total_vehicles": int(new_total_vehicles),
                            "seats_per_vehicle": int(new_seats_per_vehicle),
                            "bus_type": new_bus_type,
                            "routes": agency_info.get("routes", [])
                        }
                        res = db.update_agency(agency_username, agency_details)
                        if res and res.get("success"):
                            st.success("✅ Settings updated successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to update settings: {res.get('message') if res else 'Unknown error'}")

            st.markdown("---")
            st.markdown("### 💰 Route Fare Management")
            st.markdown("*Set ticket fare for each route. This amount will be charged to passengers during payment.*")

            routes = agency_info.get('routes', [])
            existing_fares = {f"{f['source'].lower()}-{f['destination'].lower()}": f['fare']
                              for f in db.get_all_agency_fares(agency_username)}

            if routes:
                fare_cols = st.columns([3, 2, 2, 1])
                with fare_cols[0]:
                    st.markdown("**Route**")
                with fare_cols[1]:
                    st.markdown("**Fare (₹)**")
                with fare_cols[2]:
                    st.markdown("**Status**")
                with fare_cols[3]:
                    st.markdown("**Action**")

                for route in routes:
                    src = route['source']
                    dst = route['destination']
                    key = f"{src.lower()}-{dst.lower()}"
                    current_fare = existing_fares.get(key, "")

                    r_cols = st.columns([3, 2, 2, 1])
                    with r_cols[0]:
                        st.markdown(f"**{src} → {dst}**")
                    with r_cols[1]:
                        fare_val = st.number_input(
                            "Fare",
                            min_value=50,
                            max_value=50000,
                            value=int(current_fare) if current_fare else 200,
                            step=10,
                            key=f"fare_{key}",
                            label_visibility="collapsed"
                        )
                    with r_cols[2]:
                        if current_fare:
                            st.success(f"₹{current_fare}")
                        else:
                            st.warning("Not set")
                    with r_cols[3]:
                        if st.button("💾", key=f"save_fare_{key}", help="Save fare"):
                            result = db.set_route_fare(agency_username, src, dst, fare_val)
                            if result["success"]:
                                st.success(f"✅ {result['message']}")
                                st.rerun()
                            else:
                                st.error(f"❌ {result['message']}")

                st.markdown("---")
                st.info("💡 **Tip:** Set fares for all your routes before users start booking. The fare shown here will be charged during payment.")
            else:
                st.info("📭 No routes configured. Add routes first to set fares.")

    with tab5:
        st.subheader("📢 Send Notification to Passengers")
        st.markdown("*Select one or more passengers below and send a message directly to their notification panel.*")
        st.markdown("---")

        bookings = db.get_bookings_by_agency(agency_username)

        if not bookings:
            st.info("📭 No bookings found. Notifications can only be sent to passengers who have booked with you.")
        else:
            # Date filter
            available_dates = sorted(list(set(b.get('date') for b in bookings if b.get('date'))))
            
            def reset_checkbox_selections():
                st.session_state["notif_select_all"] = False
                for key in list(st.session_state.keys()):
                    if key.startswith("notif_chk_"):
                        st.session_state[key] = False
            
            if available_dates:
                selected_date = st.selectbox(
                    "📅 Filter by Travel Date",
                    ["-- All Dates --"] + available_dates,
                    key="notif_date_filter",
                    on_change=reset_checkbox_selections
                )
                if selected_date != "-- All Dates --":
                    bookings = [b for b in bookings if b.get('date') == selected_date]

            # ── Passenger multi-select list ──────────────────────────────
            st.markdown("#### 🧑‍🤝‍🧑 Select Passengers")

            # Build a list of (label, booking) tuples
            booking_list = []
            for b in bookings:
                label = (
                    f"#{b.get('booking_id')}  |  "
                    f"{b.get('passenger_name', 'N/A')}  |  "
                    f"{b.get('source')} → {b.get('destination')}  |  "
                    f"{b.get('date')}  |  Seat: {b.get('seat')}"
                )
                booking_list.append((label, b))

            all_labels = [lbl for lbl, _ in booking_list]

            def toggle_select_all():
                select_all_val = st.session_state.get("notif_select_all", False)
                for idx in range(len(booking_list)):
                    st.session_state[f"notif_chk_{idx}"] = select_all_val

            # "Select All" toggle
            select_all = st.checkbox(
                "✅ Select All Passengers",
                value=False,
                key="notif_select_all",
                on_change=toggle_select_all
            )

            # Individual checkboxes
            st.markdown("---")
            checked_bookings = []
            for idx, (label, booking) in enumerate(booking_list):
                checked = st.checkbox(
                    label, 
                    value=st.session_state.get(f"notif_chk_{idx}", select_all), 
                    key=f"notif_chk_{idx}"
                )
                if checked:
                    checked_bookings.append(booking)

            # Summary of selection
            st.markdown("---")
            if checked_bookings:
                st.success(f"✅ **{len(checked_bookings)}** passenger(s) selected")
            else:
                st.info("☝️ Select at least one passenger to send a notification.")

            # ── Message composer ─────────────────────────────────────────
            st.markdown("#### 💬 Message")
            template = st.selectbox(
                "📝 Quick Templates (optional)",
                [
                    "-- Select a template or write your own --",
                    "Your bus departure has been rescheduled. Please check the updated time.",
                    "Your bus is running on time. Please arrive 15 minutes early.",
                    "There is a platform change for your journey. Please check with our staff.",
                    "Your booking has been confirmed. Have a safe journey! 🚌",
                    "Due to unforeseen circumstances, this trip has been cancelled. Please contact us for a refund.",
                ],
                key="notif_template"
            )

            prefill = "" if template.startswith("--") else template
            notif_message = st.text_area(
                "Write your message",
                value=prefill,
                height=130,
                placeholder="e.g. Your bus is delayed by 30 minutes due to heavy traffic. We apologise for the inconvenience.",
                key="notif_message_input"
            )

            # ── Send button ──────────────────────────────────────────────
            send_col, _ = st.columns([1, 2])
            with send_col:
                if st.button("📤 Send Notification", use_container_width=True, key="send_notif_btn"):
                    if not checked_bookings:
                        st.warning("⚠️ Please select at least one passenger.")
                    elif not notif_message.strip():
                        st.warning("⚠️ Please enter a message before sending.")
                    else:
                        sent_ok = 0
                        sent_fail = 0
                        for booking in checked_bookings:
                            result = db.send_notification(
                                agency_username=agency_username,
                                to_username=booking.get("username"),
                                booking_id=booking.get("booking_id"),
                                message=notif_message.strip()
                            )
                            if result["success"]:
                                sent_ok += 1
                            else:
                                sent_fail += 1

                        if sent_ok:
                            st.success(
                                f"✅ Notification sent to **{sent_ok}** passenger(s) successfully!"
                            )
                        if sent_fail:
                            st.error(f"❌ Failed to send to {sent_fail} passenger(s).")

    with tab6:
        st.subheader("📱 WhatsApp Integration")
        st.markdown("*Connect your WhatsApp Business API to send booking confirmations and notifications.*")
        st.markdown("---")

        import whatsapp as wa
        import time

        # Check DB record
        existing = db.get_whatsapp_instance(agency_username)

        # Check Evolution API live status
        live_exists = False
        live_state = "unknown"
        inst_name_db = existing.get("instance_name") if existing else None

        if inst_name_db:
            live_exists = wa.instance_exists(inst_name_db)
            if live_exists:
                try:
                    live_data = wa.get_instance_status(inst_name_db)
                    live_state = live_data.get("state", "unknown")
                except:
                    pass

        # CASE 1: DB has record but Evolution API doesn't → clean DB, show create
        if existing and not live_exists:
            db.delete_whatsapp_instance(agency_username)
            existing = None
            st.warning("Previous instance was removed from server. Please create a new one.")

        # CASE 2: Instance exists on Evolution API
        if existing and live_exists:
            st.success(f"✅ WhatsApp instance: `{inst_name_db}`")

            if live_state in ("open", "connected"):
                st.badge("🟢 Connected", color="green")
            elif live_state in ("disconnected", "close"):
                st.badge("🔴 Disconnected", color="red")
            else:
                st.badge(f"🟡 {live_state}", color="orange")

            # --- Action buttons ---
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🔄 Refresh Status", use_container_width=True):
                    try:
                        status_data = wa.get_instance_status(inst_name_db)
                        state = status_data.get("state", "unknown")
                        is_connected = status_data.get("connected", False)
                        db.update_whatsapp_status(agency_username, is_connected)
                        from pymongo import MongoClient
                        db_client = MongoClient(os.getenv("MONGO_URI", ""), serverSelectionTimeoutMS=3000)
                        db_client["ticket_booking"]["whatsapp_instances"].update_one(
                            {"agency_username": agency_username},
                            {"$set": {"status": state}}
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            with col2:
                if st.button("🔗 Get QR Code", use_container_width=True):
                    try:
                        # If currently connected, logout first to get fresh QR
                        if live_state in ("open", "connected"):
                            with st.spinner("Disconnecting to generate new QR..."):
                                wa.disconnect_instance(inst_name_db)
                                time.sleep(4)

                        with st.spinner("Fetching QR code..."):
                            qr_data = wa.get_qr_code(inst_name_db)

                        if qr_data and qr_data.get("success") and qr_data.get("base64"):
                            b64 = qr_data["base64"]
                            if not b64.startswith("data:"):
                                b64 = f"data:image/png;base64,{b64}"
                            st.image(b64, width=300)
                            st.caption("Scan with WhatsApp → Settings → Linked Devices → Link a Device")
                        else:
                            msg = qr_data.get("message", "Unknown error") if qr_data else "No response"
                            st.warning(f"Could not get QR: {msg}")
                    except Exception as e:
                        st.error(f"Error: {e}")

            with col3:
                if st.button("❌ Delete Instance", type="primary", use_container_width=True):
                    try:
                        wa.delete_instance(inst_name_db)
                        db.delete_whatsapp_instance(agency_username)
                        st.success("Instance deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        # CASE 3: No instance → Auto-create then show form
        else:
            auto_name = f"{agency_username}-whatsapp"
            sanitized_auto = "".join(c if c.isalnum() or c == "_" else "_" for c in auto_name.strip()).lower()
            if len(sanitized_auto) >= 3:
                with st.spinner(f"Auto-creating WhatsApp instance '{sanitized_auto}'..."):
                    auto_result = wa.create_instance(sanitized_auto)
                    if auto_result.get("success"):
                        db.save_whatsapp_instance(agency_username, sanitized_auto, auto_result)
                        st.success(f"✅ Instance auto-created: {sanitized_auto}")
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.warning(f"Auto-create skipped: {auto_result.get('message', 'Unknown error')}")

            st.markdown("#### Create WhatsApp Instance")
            instance_name = st.text_input(
                "Instance Name",
                value=f"{agency_username}-whatsapp",
                help="A unique name for your WhatsApp connection (lowercase letters, numbers, and hyphens only)"
            )

            if st.button("📱 Create Instance", use_container_width=True):
                if instance_name:
                    try:
                        with st.spinner("Creating WhatsApp instance..."):
                            result = wa.create_instance(instance_name)

                        if result and result.get("success"):
                            sanitized_name = result.get("instance_name", instance_name)
                            db.save_whatsapp_instance(agency_username, sanitized_name, result)

                            with st.spinner("Waiting for instance to initialize..."):
                                time.sleep(5)

                            with st.spinner("Fetching QR code..."):
                                qr_data = wa.get_qr_code(sanitized_name)

                            if qr_data and qr_data.get("success") and qr_data.get("base64"):
                                st.success("Instance created! Scan the QR below:")
                                b64 = qr_data["base64"]
                                if not b64.startswith("data:"):
                                    b64 = f"data:image/png;base64,{b64}"
                                st.image(b64, width=300)
                                st.caption("Scan with WhatsApp → Settings → Linked Devices → Link a Device")
                            else:
                                st.success("Instance created! Click 'Get QR Code' to scan.")
                            st.rerun()
                        else:
                            error_msg = result.get("message", "Unknown error") if result else "No response"
                            st.error(f"Failed to create: {error_msg}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please enter an instance name")

        st.markdown("---")
        st.markdown("#### ℹ️ How it works")
        st.markdown("""
        1. **Create Instance** — Generates a WhatsApp connection linked to your agency
        2. **Scan QR Code** — Open WhatsApp on your phone → Settings → Linked Devices → Link a Device
        3. **Automatically** — Booking confirmations and cancellation notices are sent via WhatsApp
        """)


# =====================================================
# MAIN APP
# =====================================================

def main():
    init_session_state()
    if not st.session_state.logged_in:
        login_page()
    else:
        user_chatbot_page()

if __name__ == "__main__":
    main()
