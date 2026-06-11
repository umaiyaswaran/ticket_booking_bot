import streamlit as st
import os
import db
from chatbot import process_message, active_conversations, BookingConversation, handle_booking_confirmation
from qr_generator import generate_booking_qr, generate_ticket_html
import notifications as notif_manager
import pandas as pd
from datetime import datetime

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

# =====================================================
# CUSTOM CSS
# =====================================================

# =====================================================
# SIDEBAR MENU
# =====================================================

def render_sidebar():
    """Render sidebar with navigation and booking options for Users and Agencies"""
    with st.sidebar:
        st.markdown("### 🎫 TicketHub Menu")
        st.markdown("---")
        
        if not st.session_state.logged_in:
            st.info("👤 Login to access your dashboard")
        
        elif st.session_state.role == "User":
            # USER NAVIGATION
            st.markdown("**👤 USER DASHBOARD**")
            
            if st.button("📊 Dashboard", use_container_width=True):
                st.switch_page("app.py")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎫 My Bookings", use_container_width=True):
                    st.switch_page("pages/2_user_profile.py")
            
            with col2:
                if st.button("⚙️ Profile", use_container_width=True):
                    st.switch_page("pages/2_user_profile.py")
            
            st.divider()
            
            # Booking Mode Selection
            st.markdown("**🤖 Booking Mode**")
            mode_col1, mode_col2 = st.columns(2)
            
            with mode_col1:
                if st.button("🤖 AI Bot", use_container_width=True, key="mode_ai"):
                    st.session_state.booking_mode = "ai_bot"
                    st.rerun()
            
            with mode_col2:
                if st.button("📝 Manual", use_container_width=True, key="mode_manual"):
                    st.session_state.booking_mode = "manual"
                    st.rerun()
            
            # Show active mode indicator
            if st.session_state.booking_mode == "ai_bot":
                st.success("✅ Using AI Bot Mode")
            else:
                st.info("ℹ️ Using Manual Booking Mode")
        
        elif st.session_state.role == "Agency":
            # AGENCY NAVIGATION
            st.markdown("**🏢 AGENCY DASHBOARD**")
            
            if st.button("📊 Dashboard", use_container_width=True):
                st.switch_page("pages/1_agency_dashboard.py")
            
            if st.button("🛣️ Routes", use_container_width=True):
                st.switch_page("pages/3_agency_routes.py")
            
            if st.button("📱 WhatsApp Settings", use_container_width=True):
                st.switch_page("pages/2_agency_whatsapp.py")
            
            if st.button("📢 Broadcast Messages", use_container_width=True):
                st.switch_page("pages/4_agency_broadcast.py")
            
            st.divider()
            st.markdown("**📈 Quick Stats**")
            
            # Quick stats
            agency_bookings = list(db.bookings_collection.find({
                "agency_username": st.session_state.user,
                "status": "confirmed"
            }))
            
            st.metric("Total Bookings", len(agency_bookings))
        
        # Common options for all logged-in users
        if st.session_state.logged_in:
            st.divider()
            st.markdown("**🔧 Account**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏠 Home", use_container_width=True):
                    st.switch_page("app.py")
            
            with col2:
                if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                    st.session_state.logged_in = False
                    st.session_state.user = None
                    st.session_state.role = None
                    st.session_state.chat_history = []
                    st.success("✅ Logged out successfully")
                    st.rerun()


def inject_custom_css():
    st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">', unsafe_allow_html=True)
    custom_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        /* ============================================================
           HIDE ALL DEFAULT STREAMLIT ELEMENTS
           ============================================================ */
        #MainMenu, footer, header[data-testid="stHeader"],
        button[title="View fullscreen"],
        [data-testid="stSidebarNav"],
        [data-testid="stDecoration"],
        .stDeployButton,
        div[data-testid="stToolbar"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stBottomBlockContainer"] > div:last-child {
            display: none !important;
        }

        .block-container {
            padding-top: 0 !important;
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

        /* ============================================================
           DESIGN TOKENS
           ============================================================ */
        :root {
            --primary: #00d4ff;
            --primary-soft: rgba(0, 212, 255, 0.15);
            --primary-glow: rgba(0, 212, 255, 0.4);
            --secondary: #6c63ff;
            --accent: #a855f7;
            --accent-soft: rgba(168, 85, 247, 0.15);
            --gradient-brand: linear-gradient(135deg, #00d4ff 0%, #6c63ff 50%, #a855f7 100%);
            --gradient-card: linear-gradient(145deg, rgba(17, 24, 34, 0.9) 0%, rgba(15, 20, 30, 0.95) 100%);
            --gradient-glass: linear-gradient(145deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
            --bg-body: #06080d;
            --bg-card: #0f1319;
            --bg-card-elevated: #141a23;
            --bg-surface: rgba(255, 255, 255, 0.025);
            --border: rgba(255, 255, 255, 0.06);
            --border-hover: rgba(0, 212, 255, 0.25);
            --border-active: rgba(0, 212, 255, 0.5);
            --text-primary: #f0f4f8;
            --text-secondary: #8b9ab5;
            --text-muted: #4a5568;
            --success: #10b981;
            --success-soft: rgba(16, 185, 129, 0.12);
            --warning: #f59e0b;
            --warning-soft: rgba(245, 158, 11, 0.12);
            --error: #ef4444;
            --error-soft: rgba(239, 68, 68, 0.12);
            --info: #3b82f6;
            --info-soft: rgba(59, 130, 246, 0.12);
            --r-xs: 6px;
            --r-sm: 10px;
            --r-md: 14px;
            --r-lg: 20px;
            --r-xl: 24px;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
            --shadow-md: 0 4px 16px rgba(0,0,0,0.35);
            --shadow-lg: 0 8px 32px rgba(0,0,0,0.4);
            --shadow-glow: 0 0 30px rgba(0, 212, 255, 0.08);
            --shadow-glow-lg: 0 0 60px rgba(0, 212, 255, 0.12);
            --glass-bg: rgba(15, 19, 25, 0.8);
            --glass-border: rgba(255, 255, 255, 0.06);
            --ease: cubic-bezier(0.4, 0, 0.2, 1);
            --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        /* ============================================================
           GLOBAL RESET & BACKGROUND
           ============================================================ */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html {
            scroll-behavior: smooth;
        }

        html, body,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"],
        .main .block-container {
            background: var(--bg-body) !important;
            color: var(--text-primary);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* Animated mesh gradient background */
        [data-testid="stAppViewContainer"]::before {
            content: '';
            position: fixed;
            inset: 0;
            background:
                radial-gradient(ellipse 80% 60% at 10% 10%, rgba(0, 212, 255, 0.07) 0%, transparent 60%),
                radial-gradient(ellipse 60% 80% at 90% 90%, rgba(108, 99, 255, 0.06) 0%, transparent 60%),
                radial-gradient(ellipse 50% 50% at 50% 50%, rgba(168, 85, 247, 0.04) 0%, transparent 70%);
            z-index: -2;
            pointer-events: none;
            animation: meshFloat 20s ease-in-out infinite alternate;
        }

        @keyframes meshFloat {
            0% { opacity: 0.8; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.05); }
            100% { opacity: 0.8; transform: scale(1); }
        }

        /* Floating orbs */
        [data-testid="stAppViewContainer"]::after {
            content: '';
            position: fixed;
            top: -200px;
            right: -200px;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(0, 212, 255, 0.05) 0%, transparent 70%);
            border-radius: 50%;
            z-index: -1;
            pointer-events: none;
            animation: orbFloat 15s ease-in-out infinite alternate;
        }

        @keyframes orbFloat {
            0% { transform: translate(0, 0); }
            100% { transform: translate(-100px, 100px); }
        }

        /* ============================================================
           CUSTOM HEADER
           ============================================================ */
        .custom-header {
            position: sticky;
            top: 0;
            z-index: 9998;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 28px;
            height: 60px;
            background: rgba(6, 8, 13, 0.85);
            backdrop-filter: blur(24px) saturate(1.8);
            -webkit-backdrop-filter: blur(24px) saturate(1.8);
            border-bottom: 1px solid var(--glass-border);
        }

        .custom-header::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: var(--gradient-brand);
            opacity: 0.3;
        }

        .header-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            cursor: pointer;
        }

        .header-logo-icon {
            width: 36px;
            height: 36px;
            background: var(--gradient-brand);
            border-radius: var(--r-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            box-shadow: 0 2px 12px rgba(0, 212, 255, 0.3);
            position: relative;
            overflow: hidden;
        }

        .header-logo-icon::after {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, transparent 50%);
            border-radius: inherit;
        }

        .header-logo-text {
            font-size: 1.15em;
            font-weight: 800;
            background: var(--gradient-brand);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.03em;
        }

        .header-nav {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .header-nav-link {
            padding: 6px 14px;
            border-radius: var(--r-sm);
            color: var(--text-secondary);
            font-size: 0.85em;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.2s var(--ease);
            cursor: pointer;
        }

        .header-nav-link:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.05);
        }

        .header-nav-link.active {
            color: var(--primary);
            background: var(--primary-soft);
        }

        .header-user {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-user-avatar {
            width: 34px;
            height: 34px;
            background: var(--gradient-brand);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 700;
            color: #fff;
            box-shadow: 0 2px 8px rgba(0, 212, 255, 0.25);
        }

        .header-user-info {
            display: flex;
            flex-direction: column;
            line-height: 1.2;
        }

        .header-user-name {
            font-size: 0.85em;
            font-weight: 600;
            color: var(--text-primary);
        }

        .header-user-role {
            font-size: 0.7em;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 600;
        }

        /* ============================================================
           CUSTOM FOOTER
           ============================================================ */
        .custom-footer {
            text-align: center;
            padding: 28px 20px;
            margin-top: 40px;
            border-top: 1px solid var(--border);
            position: relative;
        }

        .custom-footer::before {
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 120px;
            height: 1px;
            background: var(--gradient-brand);
            opacity: 0.5;
        }

        .footer-brand {
            font-size: 0.85em;
            font-weight: 700;
            background: var(--gradient-brand);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
        }

        .footer-copy {
            font-size: 0.75em;
            color: var(--text-muted);
            margin-top: 6px;
        }

        /* ============================================================
           HEADINGS
           ============================================================ */
        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
            background: var(--gradient-brand);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1.2;
        }

        h1, [data-testid="stMarkdownContainer"] h1 {
            font-size: 2.2em !important;
            margin-bottom: 6px !important;
        }

        h2, [data-testid="stMarkdownContainer"] h2 {
            font-size: 1.6em !important;
            margin-bottom: 4px !important;
        }

        h3, [data-testid="stMarkdownContainer"] h3 {
            font-size: 1.25em !important;
            margin-bottom: 4px !important;
        }

        /* ============================================================
           CARDS
           ============================================================ */
        .card, .glass-card {
            background: var(--gradient-card);
            border: 1px solid var(--border);
            border-radius: var(--r-md);
            padding: 24px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s var(--ease);
        }

        .card::before, .glass-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: var(--gradient-brand);
            opacity: 0;
            transition: opacity 0.3s var(--ease);
        }

        .card:hover, .glass-card:hover {
            border-color: var(--border-hover);
            box-shadow: var(--shadow-glow);
            transform: translateY(-2px);
        }

        .card:hover::before, .glass-card:hover::before {
            opacity: 0.5;
        }

        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }

        /* ============================================================
           BUTTONS
           ============================================================ */
        [data-testid="stButton"] > button,
        [data-testid="stFormSubmitButton"] > button {
            background: var(--gradient-brand) !important;
            border: none !important;
            border-radius: var(--r-sm) !important;
            color: #fff !important;
            padding: 11px 28px !important;
            font-weight: 700 !important;
            font-size: 0.88em !important;
            cursor: pointer !important;
            width: 100% !important;
            letter-spacing: 0.01em !important;
            transition: all 0.3s var(--ease) !important;
            box-shadow: 0 2px 12px rgba(0, 212, 255, 0.2), inset 0 1px 0 rgba(255,255,255,0.15) !important;
            min-height: 44px !important;
            position: relative !important;
            overflow: hidden !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
        }

        [data-testid="stButton"] > button::after,
        [data-testid="stFormSubmitButton"] > button::after {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, transparent 50%);
            pointer-events: none;
        }

        [data-testid="stButton"] > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            box-shadow: 0 4px 24px rgba(0, 212, 255, 0.35), inset 0 1px 0 rgba(255,255,255,0.2) !important;
            transform: translateY(-2px) !important;
        }

        [data-testid="stButton"] > button:active,
        [data-testid="stFormSubmitButton"] > button:active {
            transform: translateY(0) !important;
            box-shadow: 0 1px 6px rgba(0, 212, 255, 0.2) !important;
        }

        [data-testid="stButton"] > button:focus-visible {
            outline: 2px solid var(--primary);
            outline-offset: 2px;
        }

        /* ============================================================
           TEXT INPUTS / TEXTAREA
           ============================================================ */
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea,
        input[type="text"],
        input[type="password"],
        textarea {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--r-sm) !important;
            color: var(--text-primary) !important;
            padding: 12px 16px !important;
            font-size: 0.9em !important;
            width: 100% !important;
            transition: all 0.25s var(--ease) !important;
            font-family: 'Inter', sans-serif !important;
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus,
        input[type="text"]:focus,
        input[type="password"]:focus,
        textarea:focus {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1), 0 0 20px rgba(0, 212, 255, 0.05) !important;
            outline: none !important;
            background: rgba(255, 255, 255, 0.04) !important;
        }

        [data-testid="stTextInput"] label,
        [data-testid="stNumberInput"] label,
        [data-testid="stTextArea"] label,
        [data-testid="stSelectbox"] label {
            color: var(--text-secondary) !important;
            font-size: 0.82em !important;
            font-weight: 600 !important;
            letter-spacing: 0.04em !important;
            text-transform: uppercase !important;
        }

        ::placeholder {
            color: var(--text-muted) !important;
            opacity: 1 !important;
        }

        /* ============================================================
           SELECTBOX / DROPDOWN
           ============================================================ */
        [data-testid="stSelectbox"] > div > div {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--r-sm) !important;
            color: var(--text-primary) !important;
            transition: all 0.25s var(--ease) !important;
        }

        [data-testid="stSelectbox"] > div > div:hover {
            border-color: var(--border-hover) !important;
        }

        [data-testid="stSelectbox"] > div > div:focus-within {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1) !important;
        }

        /* ============================================================
           TABS
           ============================================================ */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            background: rgba(255, 255, 255, 0.02) !important;
            gap: 2px !important;
            border-bottom: 1px solid var(--border) !important;
            border-radius: var(--r-sm) var(--r-sm) 0 0 !important;
            padding: 4px 4px 0 4px !important;
        }

        [data-testid="stTabs"] button {
            background: transparent !important;
            border: none !important;
            border-bottom: 2px solid transparent !important;
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            font-size: 0.88em !important;
            padding: 12px 20px !important;
            transition: all 0.25s var(--ease) !important;
            border-radius: var(--r-xs) var(--r-xs) 0 0 !important;
            letter-spacing: 0.01em !important;
        }

        [data-testid="stTabs"] button:hover {
            color: var(--text-primary) !important;
            background: rgba(0, 212, 255, 0.04) !important;
        }

        [data-testid="stTabs"] button[aria-selected="true"],
        [data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--primary) !important;
            border-bottom-color: var(--primary) !important;
            background: rgba(0, 212, 255, 0.06) !important;
        }

        [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            background-color: var(--primary) !important;
            border-radius: 2px !important;
        }

        [data-testid="stTabs"] [data-baseweb="tab-border"] {
            display: none !important;
        }

        /* ============================================================
           SIDEBAR
           ============================================================ */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #080b12 0%, #0d1117 100%) !important;
            border-right: 1px solid var(--border) !important;
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3) !important;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
            font-size: 1.05em !important;
            margin-bottom: 14px !important;
            padding-bottom: 10px !important;
            border-bottom: 1px solid var(--border) !important;
        }

        [data-testid="stSidebar"] hr {
            border-color: var(--border) !important;
            margin: 14px 0 !important;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdown"] li {
            color: var(--text-secondary) !important;
            font-size: 0.88em !important;
        }

        /* ============================================================
           DIVIDERS
           ============================================================ */
        hr, [data-testid="stHorizontalBlock"] hr {
            border: none !important;
            border-top: 1px solid var(--border) !important;
            margin: 18px 0 !important;
        }

        [data-testid="stDivider"] {
            border-color: var(--border) !important;
        }

        /* ============================================================
           EXPANDER
           ============================================================ */
        [data-testid="stExpander"] {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--r-md) !important;
            margin: 10px 0 !important;
            transition: all 0.25s var(--ease) !important;
        }

        [data-testid="stExpander"]:hover {
            border-color: var(--border-hover) !important;
        }

        [data-testid="stExpander"] summary {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            font-size: 0.92em !important;
        }

        /* ============================================================
           METRICS
           ============================================================ */
        [data-testid="stMetric"] {
            background: var(--gradient-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--r-md) !important;
            padding: 20px !important;
            transition: all 0.3s var(--ease) !important;
            position: relative !important;
            overflow: hidden !important;
        }

        [data-testid="stMetric"]::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--gradient-brand);
            opacity: 0.6;
        }

        [data-testid="stMetric"]:hover {
            border-color: var(--border-hover) !important;
            box-shadow: var(--shadow-glow) !important;
            transform: translateY(-2px) !important;
        }

        [data-testid="stMetricValue"] {
            color: var(--primary) !important;
            font-weight: 800 !important;
            font-size: 1.8em !important;
            letter-spacing: -0.03em !important;
        }

        [data-testid="stMetricLabel"] {
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            font-size: 0.82em !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
        }

        [data-testid="stMetricDelta"] > div {
            font-weight: 600 !important;
        }

        /* ============================================================
           DATAFRAME / TABLES
           ============================================================ */
        .dataframe {
            border: 1px solid var(--border) !important;
            border-radius: var(--r-md) !important;
            overflow: hidden !important;
            font-size: 0.86em !important;
            background: var(--bg-card) !important;
        }

        .dataframe thead tr th {
            background: rgba(0, 212, 255, 0.06) !important;
            color: var(--primary) !important;
            font-weight: 700 !important;
            border-bottom: 1px solid var(--border) !important;
            padding: 12px 14px !important;
            font-size: 0.9em !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }

        .dataframe tbody tr {
            border-bottom: 1px solid rgba(255, 255, 255, 0.03) !important;
            transition: background 0.2s var(--ease) !important;
        }

        .dataframe tbody tr:hover {
            background: rgba(0, 212, 255, 0.04) !important;
        }

        .dataframe tbody td {
            color: var(--text-primary) !important;
            padding: 11px 14px !important;
        }

        /* ============================================================
           ALERTS / NOTIFICATIONS
           ============================================================ */
        [data-testid="stAlert"],
        [data-testid="stNotification"] {
            border-radius: var(--r-sm) !important;
            border-left: 4px solid var(--primary) !important;
            padding: 14px 18px !important;
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
           CHAT MESSAGES
           ============================================================ */
        .bot-message {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.06) 0%, rgba(108, 99, 255, 0.04) 100%) !important;
            border-left: 3px solid var(--primary) !important;
            padding: 16px 18px !important;
            border-radius: 2px var(--r-sm) var(--r-sm) 2px !important;
            margin: 12px 0 !important;
            max-width: 82% !important;
            word-wrap: break-word !important;
            color: var(--text-primary) !important;
            line-height: 1.65 !important;
            font-size: 0.92em !important;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15) !important;
            animation: msgSlideIn 0.3s var(--ease-spring) !important;
        }

        .user-message {
            background: linear-gradient(135deg, rgba(108, 99, 255, 0.12) 0%, rgba(168, 85, 247, 0.08) 100%) !important;
            border-left: 3px solid var(--secondary) !important;
            padding: 16px 18px !important;
            border-radius: 2px var(--r-sm) var(--r-sm) 2px !important;
            margin: 12px 0 12px auto !important;
            max-width: 82% !important;
            word-wrap: break-word !important;
            color: var(--text-primary) !important;
            line-height: 1.65 !important;
            font-size: 0.92em !important;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15) !important;
            animation: msgSlideIn 0.3s var(--ease-spring) !important;
        }

        @keyframes msgSlideIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .success-box {
            background: var(--success-soft) !important;
            border-left: 4px solid var(--success) !important;
            padding: 14px 18px !important;
            border-radius: 2px var(--r-sm) var(--r-sm) 2px !important;
            margin: 10px 0 !important;
        }

        .error-box {
            background: var(--error-soft) !important;
            border-left: 4px solid var(--error) !important;
            padding: 14px 18px !important;
            border-radius: 2px var(--r-sm) var(--r-sm) 2px !important;
            margin: 10px 0 !important;
        }

        .stats-card {
            background: var(--gradient-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--r-md) !important;
            padding: 22px !important;
            margin: 8px 0 !important;
            transition: all 0.3s var(--ease) !important;
        }

        .stats-card:hover {
            border-color: var(--border-hover) !important;
            box-shadow: var(--shadow-glow) !important;
            transform: translateY(-2px) !important;
        }

        /* ============================================================
           COLUMNS / LAYOUT
           ============================================================ */
        [data-testid="stHorizontalBlock"] {
            gap: 14px !important;
        }

        [data-testid="stColumn"] {
            padding: 4px !important;
        }

        /* ============================================================
           FORMS
           ============================================================ */
        [data-testid="stForm"] {
            background: var(--gradient-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--r-md) !important;
            padding: 24px !important;
            box-shadow: var(--shadow-md) !important;
        }

        [data-testid="stFormSubmitButton"] > button {
            background: var(--gradient-brand) !important;
        }

        /* ============================================================
           CHECKBOX / RADIO
           ============================================================ */
        [data-testid="stCheckbox"] label span {
            color: var(--text-primary) !important;
        }

        [data-testid="stRadio"] label span {
            color: var(--text-primary) !important;
        }

        /* ============================================================
           DATE INPUT
           ============================================================ */
        [data-testid="stDateInput"] > div > div {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--r-sm) !important;
            color: var(--text-primary) !important;
        }

        /* ============================================================
           PROGRESS BAR
           ============================================================ */
        [data-testid="stProgress"] > div > div {
            background: var(--gradient-brand) !important;
            border-radius: 10px !important;
        }

        [data-testid="stProgress"] > div {
            background: rgba(255, 255, 255, 0.06) !important;
            border-radius: 10px !important;
        }

        /* ============================================================
           SCROLLBAR
           ============================================================ */
        ::-webkit-scrollbar {
            width: 5px;
            height: 5px;
        }

        ::-webkit-scrollbar-track {
            background: transparent;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(0, 212, 255, 0.15);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 212, 255, 0.3);
        }

        /* ============================================================
           LOADING / SPINNER
           ============================================================ */
        [data-testid="stSpinner"] > div {
            border-top-color: var(--primary) !important;
        }

        /* ============================================================
           MOBILE LAYOUT
           ============================================================ */
        @media (max-width: 767px) {
            header[data-testid="stHeader"] {
                display: none !important;
            }

            .block-container {
                padding-top: 0 !important;
                padding-left: 12px !important;
                padding-right: 12px !important;
            }

            .custom-header {
                padding: 0 14px;
                height: 50px;
            }

            .header-logo-text {
                font-size: 1em;
            }

            .header-nav {
                display: none;
            }

            h1, [data-testid="stMarkdownContainer"] h1 {
                font-size: 1.5em !important;
            }

            h2, [data-testid="stMarkdownContainer"] h2 {
                font-size: 1.2em !important;
            }

            [data-testid="stButton"] > button {
                min-height: 48px !important;
                font-size: 0.92em !important;
            }
        }

        @media (max-width: 480px) {
            h1, [data-testid="stMarkdownContainer"] h1 {
                font-size: 1.3em !important;
            }
        }

        /* ============================================================
           TOUCH-FRIENDLY
           ============================================================ */
        @media (hover: none) and (pointer: coarse) {
            [data-testid="stButton"] > button {
                min-height: 48px !important;
                padding: 12px 16px !important;
            }

            input, select, textarea {
                min-height: 48px !important;
                font-size: 16px !important;
            }
        }

        /* ============================================================
           FOCUS VISIBLE (Accessibility)
           ============================================================ */
        :focus-visible {
            outline: 2px solid var(--primary);
            outline-offset: 2px;
        }

        /* ============================================================
           SELECTION
           ============================================================ */
        ::selection {
            background: rgba(0, 212, 255, 0.25);
            color: #fff;
        }

        /* ============================================================
           ANIMATIONS
           ============================================================ */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .stMarkdown {
            animation: fadeIn 0.4s var(--ease) both;
        }

        /* ============================================================
           LOGIN PAGE HERO
           ============================================================ */
        .login-hero {
            text-align: center;
            padding: 20px 0 10px;
        }

        .login-hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 16px;
            background: var(--primary-soft);
            border: 1px solid rgba(0, 212, 255, 0.15);
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
            color: var(--primary);
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 16px;
        }

        .login-hero h1 {
            font-size: 2.8em !important;
            margin-bottom: 10px !important;
            line-height: 1.1 !important;
        }

        .login-hero p {
            color: var(--text-secondary) !important;
            font-size: 1.05em !important;
            max-width: 400px;
            margin: 0 auto !important;
            line-height: 1.6 !important;
        }

        .login-card {
            background: var(--gradient-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--r-lg) !important;
            padding: 32px !important;
            box-shadow: var(--shadow-lg), var(--shadow-glow) !important;
            position: relative;
            overflow: hidden;
        }

        .login-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--gradient-brand);
        }

        /* ============================================================
           NOTIFICATION CARD (custom)
           ============================================================ */
        .notif-card {
            border-radius: var(--r-sm) !important;
            padding: 16px 18px !important;
            margin: 10px 0 !important;
            transition: all 0.25s var(--ease) !important;
        }

        .notif-card:hover {
            transform: translateX(4px);
        }

        /* ============================================================
           STATUS BADGES
           ============================================================ */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .status-confirmed {
            background: var(--success-soft);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.2);
        }

        .status-cancelled {
            background: var(--error-soft);
            color: var(--error);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }

        /* ============================================================
           BOOKING CARD
           ============================================================ */
        .booking-card {
            background: var(--gradient-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--r-md) !important;
            padding: 20px !important;
            margin: 12px 0 !important;
            transition: all 0.3s var(--ease) !important;
            position: relative;
            overflow: hidden;
        }

        .booking-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            width: 3px;
            background: var(--gradient-brand);
        }

        .booking-card:hover {
            border-color: var(--border-hover) !important;
            box-shadow: var(--shadow-glow) !important;
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
    st.set_page_config(
        page_title="Ticket Booking - Login", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    init_session_state()
    inject_custom_css()
    render_custom_header()
    
    # Hero section
    hero_html = '''
    <div class="login-hero">
        <div class="login-hero-badge">🎫 Online Bus Booking</div>
        <h1>Book Your Journey</h1>
        <p>Travel smarter with seamless bus ticket booking. Choose your route, pick your seat, and you're ready to go.</p>
    </div>
    '''
    st.markdown(hero_html, unsafe_allow_html=True)
    
    # Login card centered
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # Tab selection
        tab1, tab2 = st.tabs(["👤 User Login", "🏢 Agency Login"])
        
        with tab1:
            st.subheader("User Login")
            
            username = st.text_input("Username", key="user_username")
            password = st.text_input("Password", type="password", key="user_password")
            
            col_login, col_signup = st.columns(2)
            
            with col_login:
                if st.button("🔓 Login", use_container_width=True):
                    if username and password:
                        result = db.login_user(username, password)
                        if result['success']:
                            st.session_state.user = username
                            st.session_state.role = "User"
                            st.session_state.logged_in = True
                            # Fetch and store user gender from profile
                            profile = db.get_user_profile(username)
                            if profile:
                                st.session_state.user_gender = profile.get('gender', 'Male')
                            # Ensure a fresh conversation object for this user
                            conv = BookingConversation(username)
                            if profile:
                                conv.passenger_gender = profile.get('gender')
                            active_conversations[username] = conv
                            st.success("✅ Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error(f"❌ {result['message']}")
                    else:
                        st.warning("⚠️ Please enter username and password")
            
            with col_signup:
                if st.button("📝 Sign Up", use_container_width=True):
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
                
                if st.button("✅ Create Account", use_container_width=True):
                    if new_username and new_password and full_name:
                        # Validate phone
                        from auth import validate_phone, validate_password_strength
                        phone_valid = validate_phone(new_phone)
                        pw_valid = validate_password_strength(new_password)
                        
                        if not phone_valid["valid"]:
                            st.error(f"❌ {phone_valid['message']}")
                        elif not pw_valid["valid"]:
                            st.error(f"❌ {pw_valid['message']}")
                        elif new_password == confirm_password:
                            result = db.create_user(new_username, new_password, "User", gender_option=signup_gender, full_name=full_name, age=int(age), phone=phone_valid["formatted"])
                            if result['success']:
                                st.success("✅ Account created! Please login now.")
                                st.session_state.show_signup = False
                                st.rerun()
                            else:
                                st.error(f"❌ {result['message']}")
                        else:
                            st.error("❌ Passwords don't match!")
                    else:
                        st.warning("⚠️ Please fill in all fields")
        
        with tab2:
            st.subheader("Agency Login")
            
            agency_username = st.text_input("Agency Username", key="agency_username")
            agency_password = st.text_input("Agency Password", type="password", key="agency_password")
            
            col_login, col_signup = st.columns(2)
            
            with col_login:
                if st.button("🔓 Login", use_container_width=True, key="agency_login"):
                    if agency_username and agency_password:
                        result = db.login_user(agency_username, agency_password)
                        if result['success'] and result['role'] == "Travel Agency":
                            st.session_state.user = agency_username
                            st.session_state.role = "Agency"
                            # Ensure fresh conversation for agency user
                            active_conversations[agency_username] = BookingConversation(agency_username)
                            st.session_state.logged_in = True
                            st.success("✅ Agency login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error(f"❌ {result.get('message', 'Invalid credentials')}")
                    else:
                        st.warning("⚠️ Please enter username and password")
            
            with col_signup:
                if st.button("📝 Register", use_container_width=True):
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
                
                if st.button("✅ Register Agency", use_container_width=True):
                    if new_agency_username and new_agency_password and agency_name:
                        from auth import validate_phone, validate_password_strength
                        phone_valid = validate_phone(agency_phone)
                        pw_valid = validate_password_strength(new_agency_password)
                        
                        if not phone_valid["valid"]:
                            st.error(f"❌ {phone_valid['message']}")
                        elif not pw_valid["valid"]:
                            st.error(f"❌ {pw_valid['message']}")
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
                                st.success("✅ Agency registered! Please login now.")
                                st.session_state.show_agency_signup = False
                                st.rerun()
                            else:
                                st.error(f"❌ {result['message']}")
                        else:
                            st.error("❌ Passwords don't match!")
                    else:
                        st.warning("⚠️ Please fill in all required fields")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    render_custom_footer()

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
    
    render_custom_header()
    
    # Page header with gradient
    header_html = f'''
    <div style="padding: 16px 0 8px; margin-bottom: 8px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <h1 style="margin-bottom:4px !important; font-size:1.8em !important;">Booking Assistant</h1>
                <p style="color:var(--text-secondary); font-size:0.9em; margin:0;">Welcome back, <strong style="color:var(--primary);">{st.session_state.user}</strong></p>
            </div>
        </div>
    </div>
    '''
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Logout button (top right)
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.chat_history = []
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
                st.write(f"👤 **You**: {msg['content']}")
            else:
                # Check if message contains HTML (seat map)
                if '<div' in msg['content'] or '<button' in msg['content']:
                    st.markdown(msg['content'], unsafe_allow_html=True)
                else:
                    st.write(f"🤖 **Bot**: {msg['content']}")

        # If bot is awaiting confirmation, show Confirm/Cancel buttons
        conv = active_conversations.get(st.session_state.user) if st.session_state.user else None
        if conv and conv.stage == "confirmation":
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Confirm Booking", key="bot_confirm"):
                    bot_response = handle_booking_confirmation(conv, "yes", st.session_state.user)
                    st.session_state.chat_history.append({'role': 'bot', 'content': bot_response})
                    st.rerun()
            with col_no:
                if st.button("❌ Cancel Booking", key="bot_cancel"):
                    bot_response = handle_booking_confirmation(conv, "no", st.session_state.user)
                    st.session_state.chat_history.append({'role': 'bot', 'content': bot_response})
                    st.rerun()

        # Input area
        # Input area
        user_input = st.text_input("You: ", placeholder="Type your message or request...", key="chat_input_" + str(len(st.session_state.chat_history)))
        
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
            
            # Add user message to history
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input
            })
            
            # Get bot response
            bot_response = process_message(user_input, username=st.session_state.user)
            
            # Add bot response to history
            st.session_state.chat_history.append({
                'role': 'bot',
                'content': bot_response
            })
            
            st.rerun()

        # ── Notifications Panel ──────────────────────────────────────────
        if st.session_state.get("quick_action") == "notifications":
            st.markdown("---")
            st.markdown("### 🔔 Your Notifications")

            notifications = db.get_user_notifications(st.session_state.user)
            # Mark all as read now that user opened the panel
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
                        <div style="
                            background: {bg_color};
                            border-left: 4px solid {border_color};
                            border-radius: 8px;
                            padding: 14px 16px;
                            margin: 10px 0;
                        ">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                                <span style="font-weight:700; color:#00d4ff; font-size:0.95em;">
                                    {unread_badge}🏢 {notif.get('agency_name', notif.get('agency_username', 'Agency'))}
                                </span>
                                <span style="font-size:0.78em; color:#b0b9c6;">🎫 Booking #{notif.get('booking_id')} &nbsp;|&nbsp; 🕐 {time_str}</span>
                            </div>
                            <p style="margin:0; font-size:0.92em; color:#e0e8f0; line-height:1.5;">{notif.get('message', '')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            if st.button("✖ Close Notifications", key="close_notif"):
                st.session_state.quick_action = None
                st.rerun()
            st.markdown("---")

    else:
        # MANUAL BOOKING MODE
        st.markdown("### 📝 Manual Booking Mode")
        st.markdown("---")
        
        # Determine which action to show based on quick_action from sidebar
        action = st.session_state.get("quick_action")
        
        if action == "manual_book":
            # MANUAL BOOK INTERFACE
            st.markdown("### ✅ Book a Ticket")
            
            # Responsive layout: stack on mobile, columns on desktop
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### 📍 Route Information")
                source = st.text_input("From (Source City)", placeholder="e.g., Chennai", key="manual_source")
                destination = st.text_input("To (Destination City)", placeholder="e.g., Mumbai", key="manual_dest")
                travel_date = st.date_input("📅 Travel Date", key="manual_date")
            
            with col2:
                st.markdown("#### 🚌 Select Agency & Seat")
                if source and destination:
                    # Get agencies for this route
                    agencies = db.get_agencies_by_route(source, destination)
                    if agencies:
                        agency_option = st.selectbox(
                            "Select Agency",
                            [a['agency_name'] for a in agencies],
                            key="manual_agency"
                        )
                        
                        # Get available seats
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
                    else:
                        st.warning("❌ No agencies found for this route")
                        seat = None
                else:
                    st.info("📝 Enter route details to see available agencies")
                    seat = None
            
            st.markdown("---")
            st.markdown("#### 👤 Passenger Details")
            
            # Use single column for passenger details on all devices
            passenger_name = st.text_input("Full Name", placeholder="e.g., John Doe", key="manual_name")
            passenger_age = st.number_input("Age", min_value=1, max_value=120, value=25, key="manual_age")
            
            st.markdown("---")
            
            if st.button("🎫 Confirm Booking", use_container_width=True, key="manual_confirm"):
                if source and destination and passenger_name and seat:
                    # Create booking
                    from datetime import datetime
                    booking_result = db.create_booking(
                        username=st.session_state.user,
                        agency_username=selected_agency['agency_username'],
                        source=source,
                        destination=destination,
                        date=travel_date.strftime('%Y-%m-%d'),
                        seat=seat,
                        passenger_name=passenger_name,
                        passenger_age=int(passenger_age)
                    )
                    
                    if booking_result['success']:
                        st.success(f"✅ Booking Confirmed! Booking ID: {booking_result['booking_id']}")
                        st.session_state.quick_action = None
                        st.rerun()
                    else:
                        st.error(f"❌ Booking failed: {booking_result['message']}")
                else:
                    st.error("❌ Please fill all required fields")
        
        elif action == "manual_view":
            # VIEW BOOKINGS INTERFACE
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
                                # Generate and display QR code
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
            # CANCEL BOOKING INTERFACE
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
            # DEFAULT VIEW
            st.info("📌 **Select an action from the left sidebar:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### ✅ Book a Ticket")
                st.markdown("Create a new booking by providing your route and seat preference")
            
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
    st.set_page_config(
        page_title="My Profile", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
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
            
            st.markdown("---")
            st.markdown("### ✏️ Edit Profile")
            
            new_full_name = st.text_input("Full Name", value=profile['full_name'], key="edit_fullname")
            new_age = st.number_input("Age", min_value=1, max_value=120, value=profile['age'] or 25, key="edit_age")
            new_gender = st.selectbox("Gender", ["Male", "Female"], index=0 if profile['gender'] == "Male" else 1, key="edit_gender")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Changes", use_container_width=True):
                    result = db.update_user_profile(st.session_state.user, full_name=new_full_name, age=new_age, gender=new_gender)
                    if result['success']:
                        st.success("✅ Profile updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Update failed: {result['message']}")
            
            with col2:
                if st.button("🔙 Back to Booking", use_container_width=True):
                    st.session_state.quick_action = None
                    st.rerun()

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

        # CASE 3: No instance → Create form
        else:
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
        if st.session_state.role == "User":
            user_chatbot_page()
        elif st.session_state.role == "Agency":
            agency_dashboard()

if __name__ == "__main__":
    main()
