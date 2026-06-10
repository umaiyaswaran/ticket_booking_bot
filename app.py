import streamlit as st
import db
from chatbot import process_message, active_conversations, BookingConversation, handle_booking_confirmation
import pandas as pd
from datetime import datetime

# =====================================================
# VIEWPORT & RESPONSIVE SETTINGS
# =====================================================
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
""", unsafe_allow_html=True)

# Initialize database
try:
    db.init_db()
except:
    pass

# =====================================================
# SESSION STATE INITIALIZATION
# =====================================================

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
    st.session_state.booking_mode = "ai_bot"  # "ai_bot" or "manual"

# =====================================================
# CUSTOM CSS
# =====================================================

# =====================================================
# SIDEBAR MENU
# =====================================================

def render_sidebar():
    """Render sidebar with navigation and booking options"""
    with st.sidebar:
        st.markdown("### 🎫 Menu")
        st.markdown("---")
        
        if st.session_state.logged_in and st.session_state.role == "User":
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
            
            st.markdown("---")
            
            if st.session_state.booking_mode == "manual":
                # Manual Booking Section
                st.markdown("**📝 Manual Booking Options**")
                if st.button("✅ Book a Ticket", use_container_width=True, key="manual_book"):
                    st.session_state.quick_action = "manual_book"
                    st.rerun()
                if st.button("📋 View My Bookings", use_container_width=True, key="manual_view"):
                    st.session_state.quick_action = "manual_view"
                    st.rerun()
                if st.button("❌ Cancel Booking", use_container_width=True, key="manual_cancel"):
                    st.session_state.quick_action = "manual_cancel"
                    st.rerun()
            else:
                # AI Bot Section
                st.markdown("**💬 Chat with AI Bot**")
                st.markdown("Quick commands:")
                st.markdown("- 'book a ticket'")
                st.markdown("- 'show my bookings'")
                st.markdown("- 'cancel booking'")
                st.markdown("- 'available routes'")
            
            st.markdown("---")
            st.markdown("**⚙️ Settings**")
            if st.button("👤 My Profile", use_container_width=True, key="profile_settings"):
                st.session_state.quick_action = "profile_settings"
                st.rerun()

def inject_custom_css():
    custom_css = """
    <style>
        :root {
            --primary-color: #00d4ff;
            --secondary-color: #0099ff;
            --accent-color: #667eea;
            --dark-bg: #0f1419;
            --card-bg: rgba(255, 255, 255, 0.05);
            --card-border: rgba(0, 212, 255, 0.1);
            --text-primary: #ffffff;
            --text-secondary: #b0b9c6;
            --success-color: #2ecc71;
            --warning-color: #f39c12;
            --error-color: #e74c3c;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
            background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0f1419 100%);
            color: var(--text-primary);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            width: 100%;
            overflow-x: hidden;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(15, 20, 25, 0.95) 0%, rgba(26, 31, 46, 0.95) 100%);
            border-right: 1px solid var(--card-border);
        }

        h1, h2, h3 {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 50%, var(--accent-color) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            margin-bottom: 20px;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        input[type="text"],
        input[type="password"],
        textarea {
            background: rgba(0, 212, 255, 0.05);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            color: var(--text-primary);
            padding: 10px 12px;
            font-size: 0.9em;
            width: 100%;
        }

        [data-testid="stButton"] > button {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border: none;
            border-radius: 8px;
            color: var(--dark-bg);
            padding: 10px 24px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
        }

        [data-testid="stSelectbox"] {
            background: rgba(0, 212, 255, 0.05);
            border: 1px solid var(--card-border);
        }

        .message-container {
            display: flex;
            margin: 10px 0;
            gap: 10px;
            flex-wrap: wrap;
        }

        .bot-message {
            background: rgba(0, 212, 255, 0.1);
            border-left: 3px solid var(--primary-color);
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
            max-width: 85%;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }

        .user-message {
            background: rgba(102, 126, 234, 0.2);
            border-left: 3px solid var(--accent-color);
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0 10px auto;
            max-width: 85%;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }

        .success-box {
            background: rgba(46, 204, 113, 0.1);
            border-left: 4px solid var(--success-color);
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
        }

        .error-box {
            background: rgba(231, 76, 60, 0.1);
            border-left: 4px solid var(--error-color);
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
        }

        .stats-card {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 153, 255, 0.05) 100%);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 16px;
            margin: 10px 0;
        }

        /* ==================== DESKTOP LAYOUT (1200px+) ==================== */
        @media (min-width: 1200px) {
            h1 { font-size: 2.5em; }
            h2 { font-size: 1.8em; }
            h3 { font-size: 1.4em; }
            p { font-size: 1em; }
            
            [data-testid="stButton"] > button {
                padding: 12px 28px;
                font-size: 1em;
            }
            
            .bot-message, .user-message {
                max-width: 85%;
                padding: 14px 16px;
                font-size: 0.95em;
            }
        }

        /* ==================== TABLET LAYOUT (768px - 1199px) ==================== */
        @media (min-width: 768px) and (max-width: 1199px) {
            h1 { font-size: 2em; }
            h2 { font-size: 1.5em; }
            h3 { font-size: 1.2em; }
            p { font-size: 0.95em; }
            
            [data-testid="stButton"] > button {
                padding: 10px 22px;
                font-size: 0.95em;
            }
            
            [data-testid="stTextInput"] input,
            [data-testid="stNumberInput"] input,
            input[type="text"],
            input[type="password"] {
                padding: 10px 14px;
                font-size: 0.9em;
            }
            
            .bot-message, .user-message {
                max-width: 90%;
                padding: 12px 14px;
                font-size: 0.9em;
            }
            
            [data-testid="stSidebar"] {
                width: 200px !important;
            }
        }

        /* ==================== MOBILE LAYOUT (480px - 767px) ==================== */
        @media (min-width: 480px) and (max-width: 767px) {
            h1 { font-size: 1.6em; margin-bottom: 12px; }
            h2 { font-size: 1.2em; margin-bottom: 10px; }
            h3 { font-size: 1em; margin-bottom: 8px; }
            p { font-size: 0.85em; }
            
            [data-testid="stButton"] > button {
                padding: 8px 16px;
                font-size: 0.85em;
                min-height: 40px;
            }
            
            [data-testid="stTextInput"] input,
            [data-testid="stNumberInput"] input,
            input[type="text"],
            input[type="password"] {
                padding: 8px 12px;
                font-size: 0.8em;
                height: 40px;
            }
            
            .bot-message, .user-message {
                max-width: 95%;
                padding: 10px 12px;
                font-size: 0.8em;
                margin: 8px 0;
            }
            
            [data-testid="stSidebar"] {
                width: 80px !important;
            }
            
            [data-testid="stSidebar"] h3 {
                font-size: 0.8em;
                display: none;
            }
        }

        /* ==================== SMALL MOBILE LAYOUT (< 480px) ==================== */
        @media (max-width: 479px) {
            html, body {
                font-size: 14px;
            }
            
            h1 { font-size: 1.4em; margin-bottom: 10px; }
            h2 { font-size: 1em; margin-bottom: 8px; }
            h3 { font-size: 0.9em; margin-bottom: 6px; }
            p { font-size: 0.8em; }
            
            [data-testid="stButton"] > button {
                padding: 6px 12px;
                font-size: 0.75em;
                min-height: 36px;
                width: 100%;
            }
            
            [data-testid="stTextInput"] input,
            [data-testid="stNumberInput"] input,
            input[type="text"],
            input[type="password"],
            textarea {
                padding: 6px 10px;
                font-size: 0.75em;
                height: 36px;
                width: 100% !important;
            }
            
            [data-testid="stSelectbox"] select {
                font-size: 0.75em;
            }
            
            .bot-message, .user-message {
                max-width: 98%;
                padding: 8px 10px;
                font-size: 0.75em;
                margin: 6px 0;
                border-left-width: 2px;
            }
            
            [data-testid="stSidebar"] {
                width: 0 !important;
            }
            
            [data-testid="stTabs"] {
                margin: 8px 0;
            }
            
            .stats-card {
                padding: 12px;
                margin: 8px 0;
            }
            
            /* Hide text labels in mobile, show only icons */
            [data-testid="stSidebar"] > div:first-child {
                width: 50px;
            }
        }

        /* ==================== GENERAL RESPONSIVE FIXES ==================== */
        [data-testid="stColumn"] {
            padding: 4px;
        }

        [data-testid="stExpander"] {
            margin: 8px 0;
        }

        /* Responsive table styling */
        .dataframe {
            font-size: inherit;
            width: 100%;
            overflow-x: auto;
        }

        /* Responsive iframe */
        iframe {
            max-width: 100%;
            height: auto;
        }

        /* Touch-friendly tap targets */
        @media (hover: none) and (pointer: coarse) {
            [data-testid="stButton"] > button {
                min-height: 48px;
                padding: 12px 16px;
            }
            
            input, select, textarea {
                min-height: 48px;
                font-size: 16px;
            }
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

inject_custom_css()

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
    
    # Responsive layout: full width on mobile, centered on desktop
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 🎫 Smart Ticket Booking")
        st.markdown("---")
        
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
                signup_gender = st.selectbox("Gender", ["Male", "Female"], key="signup_gender")
                full_name = st.text_input("Full Name", key="signup_fullname")
                age = st.number_input("Age", min_value=1, max_value=120, value=25, key="signup_age")
                
                if st.button("✅ Create Account", use_container_width=True):
                    if new_username and new_password and full_name:
                        if new_password == confirm_password:
                            result = db.create_user(new_username, new_password, "User", gender_option=signup_gender, full_name=full_name, age=int(age))
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
                            st.session_state.role = "Travel Agency"
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
                
                total_vehicles = st.number_input("Total Vehicles", min_value=1, value=5)
                seats_per_vehicle = st.number_input("Seats Per Vehicle", min_value=1, value=50)
                bus_type = st.selectbox("Bus Model / Type", ["Standard (2x2)", "Luxury (2x1)", "Sleeper (1x2)"])
                
                routes_text = st.text_area("Routes (comma-separated, format: City1-City2)", 
                                          placeholder="Delhi-Mumbai, Mumbai-Bangalore, Delhi-Goa")
                
                if st.button("✅ Register Agency", use_container_width=True):
                    if new_agency_username and new_agency_password and agency_name:
                        if new_agency_password == confirm_agency_password:
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
                                                  "Travel Agency", agency_details)
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

# =====================================================
# USER CHATBOT PAGE
# =====================================================

def user_chatbot_page():
    """Main chatbot interface for users"""
    st.set_page_config(
        page_title="Ticket Booking Chatbot", 
        layout="wide",
        initial_sidebar_state="auto"
    )
    
    # Check if user is accessing profile settings
    if st.session_state.get("quick_action") == "profile_settings":
        user_profile_page()
        return
    
    # Render sidebar
    render_sidebar()
    
    # Header
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown("# 🤖 Booking Assistant")
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.chat_history = []
            st.rerun()
    
    st.markdown(f"**Welcome, {st.session_state.user}!** 👋")
    st.markdown("---")
    
    if st.session_state.booking_mode == "ai_bot":
        # AI BOT MODE
        st.markdown("### 🤖 AI Bot Mode")
        st.markdown("*Chat with our intelligent booking assistant - simply describe what you need!*")
        st.markdown("")
        
        # Quick action buttons - responsive layout (2 cols on mobile, 5 on desktop)
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
                st.markdown(f"<div class='user-message'>👤 You: {msg['content']}</div>", 
                           unsafe_allow_html=True)
            else:
                # Check if message contains HTML (seat map)
                if '<div' in msg['content'] or '<button' in msg['content']:
                    st.markdown(msg['content'], unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='bot-message'>🤖 Bot:\n\n{msg['content']}</div>", 
                               unsafe_allow_html=True)

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
                        
                        with col3:
                            if booking['status'] != 'cancelled':
                                if st.button("❌ Cancel", key=f"cancel_{booking['booking_id']}", use_container_width=True):
                                    db.cancel_booking(booking['booking_id'])
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
                        db.cancel_booking(booking_id)
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
        initial_sidebar_state="auto"
    )
    
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Statistics", "📋 Bookings", "🛣️ Routes", "⚙️ Settings", "📢 Send Notification"])
    
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


# =====================================================
# MAIN APP
# =====================================================

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        if st.session_state.role == "User":
            user_chatbot_page()
        elif st.session_state.role == "Travel Agency":
            agency_dashboard()

if __name__ == "__main__":
    main()
