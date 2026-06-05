import streamlit as st
import db
from chatbot import process_message

db.init_db()

st.set_page_config(page_title="Ticket Booking System", layout="wide", initial_sidebar_state="expanded")

# ==================== CUSTOM CSS ====================
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
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"], 
        [data-testid="stIFrameComponent"] {
            background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0f1419 100%);
            color: var(--text-primary);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(15, 20, 25, 0.95) 0%, rgba(26, 31, 46, 0.95) 100%);
            border-right: 1px solid var(--card-border);
            backdrop-filter: blur(10px);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            padding: 20px 0;
        }

        /* Radio Button Styling */
        [data-testid="stRadio"] {
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding: 20px;
        }

        [data-testid="stRadio"] > label {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 153, 255, 0.05) 100%);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 14px 16px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 500;
            color: var(--text-primary);
        }

        [data-testid="stRadio"] > label:hover {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(0, 153, 255, 0.1) 100%);
            border-color: var(--primary-color);
            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.15);
            transform: translateX(4px);
        }

        [data-testid="stRadio"] > label[data-checked="true"] {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.25) 0%, rgba(0, 153, 255, 0.15) 100%);
            border-color: var(--primary-color);
            box-shadow: 0 12px 40px rgba(0, 212, 255, 0.2);
        }

        /* Main Container */
        [data-testid="stMainBlockContainer"] {
            padding: 40px 60px;
            max-width: 1400px;
            margin: 0 auto;
        }

        /* Headers */
        h1, h2, h3 {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 50%, var(--accent-color) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 3em;
            margin-bottom: 40px;
            text-align: center;
        }

        h2 {
            font-size: 2em;
            margin-bottom: 25px;
        }

        h3 {
            font-size: 1.3em;
            margin-bottom: 15px;
        }

        /* Input Fields */
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        input[type="text"],
        input[type="number"],
        input[type="date"] {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.05) 0%, rgba(0, 153, 255, 0.02) 100%);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            color: var(--text-primary);
            padding: 12px 16px;
            font-size: 1em;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        [data-testid="stTextInput"] input:hover,
        [data-testid="stNumberInput"] input:hover,
        [data-testid="stDateInput"] input:hover,
        input[type="text"]:hover,
        input[type="number"]:hover,
        input[type="date"]:hover {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 153, 255, 0.05) 100%);
            border-color: var(--primary-color);
            box-shadow: 0 8px 24px rgba(0, 212, 255, 0.1);
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stDateInput"] input:focus,
        input[type="text"]:focus,
        input[type="number"]:focus,
        input[type="date"]:focus {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(0, 153, 255, 0.08) 100%);
            border-color: var(--primary-color);
            box-shadow: 0 12px 32px rgba(0, 212, 255, 0.2);
            outline: none;
        }

        /* Buttons */
        [data-testid="stButton"] > button {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border: none;
            border-radius: 10px;
            color: var(--dark-bg);
            padding: 12px 32px;
            font-weight: 700;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 8px 20px rgba(0, 212, 255, 0.3);
            text-transform: uppercase;
            letter-spacing: 1px;
            width: 100%;
        }

        [data-testid="stButton"] > button:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 32px rgba(0, 212, 255, 0.4);
        }

        [data-testid="stButton"] > button:active {
            transform: translateY(-1px);
        }

        /* Cards / Containers */
        [data-testid="stContainer"],
        [data-testid="stColumn"],
        [data-testid="stExpandable"] {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(100, 200, 255, 0.02) 100%);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(20px);
            transition: all 0.3s ease;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        /* Chat Input */
        [data-testid="stChatInput"] input {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(0, 153, 255, 0.03) 100%);
            border: 1.5px solid var(--primary-color);
            border-radius: 12px;
            color: var(--text-primary);
            padding: 14px 18px;
            font-size: 1em;
            backdrop-filter: blur(15px);
        }

        [data-testid="stChatInput"] input::placeholder {
            color: var(--text-secondary);
        }

        [data-testid="stChatInput"] input:focus {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.12) 0%, rgba(0, 153, 255, 0.06) 100%);
            outline: none;
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
        }

        /* Chat Message Styling */
        [data-testid="stChatMessage"] {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(100, 200, 255, 0.03) 100%);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            backdrop-filter: blur(20px);
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Success Message */
        [data-testid="stAlert"] {
            background: linear-gradient(135deg, rgba(0, 200, 100, 0.15) 0%, rgba(0, 150, 100, 0.05) 100%) !important;
            border: 1px solid rgba(0, 200, 100, 0.3) !important;
            border-radius: 12px !important;
            color: #00ff8f !important;
            backdrop-filter: blur(20px);
        }

        /* Error Message */
        [data-testid="stAlert"] > [role="alert"] {
            background: transparent !important;
        }

        /* Columns Layout */
        [data-testid="stColumns"] {
            gap: 24px;
        }

        /* Metric Cards */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 153, 255, 0.05) 100%);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(20px);
            transition: all 0.3s ease;
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 212, 255, 0.2);
            border-color: var(--primary-color);
        }

        [data-testid="stMetric"] > div > label {
            color: var(--text-secondary) !important;
            font-size: 0.9em;
        }

        [data-testid="stMetric"] > div > div {
            color: var(--primary-color) !important;
            font-size: 2.2em;
            font-weight: 700;
        }

        /* Markdown */
        [data-testid="stMarkdown"] {
            color: var(--text-primary);
        }

        /* Label styling */
        label {
            color: var(--text-secondary) !important;
            font-weight: 600;
            font-size: 0.95em;
            margin-bottom: 8px;
        }

        /* Info/Warning boxes */
        [data-testid="stInfo"],
        [data-testid="stWarning"],
        [data-testid="stError"],
        [data-testid="stSuccess"] {
            border-radius: 12px !important;
            backdrop-filter: blur(20px) !important;
        }

        /* Scroll bar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0, 212, 255, 0.05);
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, var(--secondary-color) 0%, var(--accent-color) 100%);
        }

        /* Responsive */
        @media (max-width: 768px) {
            [data-testid="stMainBlockContainer"] {
                padding: 20px;
            }

            h1 {
                font-size: 2em;
            }

            h2 {
                font-size: 1.5em;
            }
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

inject_custom_css()

# ==================== SESSION STATE ====================
if "chat" not in st.session_state:
    st.session_state.chat = []

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid rgba(0, 212, 255, 0.2);">
        <h2 style="margin: 0; font-size: 1.8em;">✈️ BookIT</h2>
        <p style="color: #b0b9c6; font-size: 0.85em; margin-top: 5px;">Smart Booking System</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    menu = st.radio(
        "Navigation",
        ["🤖 AI Assistant", "🎫 Book Ticket", "📄 My Bookings", "🗑️ Cancel Ticket"],
        label_visibility="collapsed"
    )

# ==================== DASHBOARD HEADER ====================
st.markdown("<h1>✈️ Smart Ticket Booking System</h1>", unsafe_allow_html=True)

# ==================== DASHBOARD STATISTICS ====================
col1, col2, col3 = st.columns(3, gap="medium")

data = db.get_bookings()
total_bookings = len(data)
total_passengers = sum(1 for _ in data)

with col1:
    st.metric("Total Bookings", total_bookings, "bookings")

with col2:
    st.metric("Active Passengers", total_passengers, "passengers")

with col3:
    st.metric("Unique Routes", len(set((d[3], d[4]) for d in data)) if data else 0, "routes")

st.markdown("<br>", unsafe_allow_html=True)

# ==================== AI CHAT ASSISTANT PAGE ====================
if menu == "🤖 AI Assistant":
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 153, 255, 0.05) 100%); 
                border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 16px; padding: 20px; margin-bottom: 30px;
                backdrop-filter: blur(20px);">
        <h2 style="margin-top: 0;">💬 AI Chat Assistant</h2>
        <p style="color: #b0b9c6; margin: 0;">Ask me anything about bookings, routes, or travel tips!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat container
    chat_container = st.container()
    with chat_container:
        st.markdown("""
        <style>
            .chat-container {
                display: flex;
                flex-direction: column;
                gap: 12px;
                padding: 20px;
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(100, 200, 255, 0.01) 100%);
                border: 1px solid rgba(0, 212, 255, 0.1);
                border-radius: 16px;
                min-height: 400px;
                max-height: 500px;
                overflow-y: auto;
                backdrop-filter: blur(20px);
            }
            
            .message-user {
                display: flex;
                justify-content: flex-end;
                animation: slideIn 0.3s ease;
            }
            
            .message-bot {
                display: flex;
                justify-content: flex-start;
                animation: slideIn 0.3s ease;
            }
            
            .message-content {
                max-width: 70%;
                padding: 12px 16px;
                border-radius: 12px;
                word-wrap: break-word;
                font-size: 0.95em;
                line-height: 1.5;
            }
            
            .message-user .message-content {
                background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
                color: #0f1419;
                font-weight: 500;
                border-bottom-right-radius: 4px;
            }
            
            .message-bot .message-content {
                background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(0, 153, 255, 0.08) 100%);
                color: #ffffff;
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-bottom-left-radius: 4px;
            }
        </style>
        """, unsafe_allow_html=True)
        
        if st.session_state.chat:
            for role, msg in st.session_state.chat:
                if role == "user":
                    st.markdown(f"""
                    <div class="message-user">
                        <div class="message-content">👤 {msg}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="message-bot">
                        <div class="message-content">🤖 {msg}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; color: #b0b9c6; padding: 40px 20px;">
                <p style="font-size: 1.1em;">👋 Hi! I'm your travel assistant.</p>
                <p>Ask me about bookings, routes, or get travel recommendations!</p>
            </div>
            """, unsafe_allow_html=True)
    
    user_input = st.chat_input("Type your message here...", key="chat_input")
    
    if user_input:
        st.session_state.chat.append(("user", user_input))
        response = process_message(user_input)
        st.session_state.chat.append(("bot", response))
        st.rerun()

# ==================== BOOK TICKET PAGE ====================
elif menu == "🎫 Book Ticket":
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 153, 255, 0.05) 100%); 
                border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 16px; padding: 20px; margin-bottom: 30px;
                backdrop-filter: blur(20px);">
        <h2 style="margin-top: 0;">🎫 Book Your Ticket</h2>
        <p style="color: #b0b9c6; margin: 0;">Fill in your details to reserve your seat</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("**Passenger Information**", help="")
        name = st.text_input("Full Name", placeholder="Enter your full name", key="name_input")
        age = st.number_input("Age", min_value=1, max_value=100, value=25, key="age_input")
    
    with col2:
        st.markdown("**Travel Details**", help="")
        source = st.text_input("Source", placeholder="From", key="source_input")
        destination = st.text_input("Destination", placeholder="To", key="dest_input")
    
    col3, col4 = st.columns(2, gap="large")
    
    with col3:
        date = st.date_input("Travel Date", key="date_input")
    
    with col4:
        seat = st.text_input("Seat Number", placeholder="e.g., A1, B2", key="seat_input")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Form validation
    if st.button("✈️ Complete Booking", use_container_width=True):
        if not name or not source or not destination or not seat:
            st.error("⚠️ Please fill in all fields")
        else:
            db.add_booking(name, age, source, destination, str(date), seat)
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(0, 200, 100, 0.15) 0%, rgba(0, 150, 100, 0.05) 100%); 
                        border: 1px solid rgba(0, 200, 100, 0.3); border-radius: 12px; padding: 20px; text-align: center;
                        backdrop-filter: blur(20px);">
                <h3 style="margin-top: 0; color: #00ff8f;">✅ Ticket Booked Successfully!</h3>
                <p style="color: #b0b9c6; margin: 10px 0;">Booking confirmed. Have a great trip!</p>
            </div>
            """, unsafe_allow_html=True)

# ==================== VIEW TICKETS PAGE ====================
elif menu == "📄 My Bookings":
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 153, 255, 0.05) 100%); 
                border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 16px; padding: 20px; margin-bottom: 30px;
                backdrop-filter: blur(20px);">
        <h2 style="margin-top: 0;">📄 Your Bookings</h2>
        <p style="color: #b0b9c6; margin: 0;">View all your active ticket reservations</p>
    </div>
    """, unsafe_allow_html=True)
    
    data = db.get_bookings()
    
    if len(data) == 0:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(0, 153, 255, 0.03) 100%); 
                    border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 16px; padding: 40px; text-align: center;
                    backdrop-filter: blur(20px);">
            <h3 style="color: #b0b9c6; margin-top: 0;">No bookings found</h3>
            <p style="color: #7a8a99;">Start by booking your first ticket!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Create columns for tickets
        cols_per_row = 2
        for i in range(0, len(data), cols_per_row):
            cols = st.columns(cols_per_row, gap="large")
            
            for j, col in enumerate(cols):
                if i + j < len(data):
                    row = data[i + j]
                    booking_id, passenger_name, passenger_age, source, travel_date, seat, destination = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
                    
                    with col:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.12) 0%, rgba(0, 153, 255, 0.06) 100%); 
                                    border: 1px solid rgba(0, 212, 255, 0.25); border-radius: 16px; padding: 24px; 
                                    backdrop-filter: blur(20px); transition: all 0.3s ease; height: 100%;
                                    box-shadow: 0 8px 32px rgba(0, 212, 255, 0.08);">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                                <div>
                                    <p style="color: #b0b9c6; margin: 0 0 6px 0; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px;">Booking ID</p>
                                    <h3 style="background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 700; font-size: 1.4em; margin: 0;">#{booking_id}</h3>
                                </div>
                                <span style="font-size: 2.5em;">✈️</span>
                            </div>
                            <div style="margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid rgba(0, 212, 255, 0.1);">
                                <p style="color: #b0b9c6; margin: 0 0 4px 0; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px;">Passenger</p>
                                <h4 style="margin: 0; color: #ffffff; font-size: 1.2em;">{passenger_name}</h4>
                            </div>
                            <div style="background: linear-gradient(135deg, rgba(0, 0, 0, 0.3) 0%, rgba(0, 212, 255, 0.05) 100%); padding: 16px; border-radius: 12px; margin: 16px 0; border: 1px solid rgba(0, 212, 255, 0.1);">
                                <p style="color: #b0b9c6; margin: 0 0 12px 0; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px;">Journey Details</p>
                                <div style="display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 12px; align-items: center; margin-bottom: 12px;">
                                    <div style="text-align: center;">
                                        <p style="color: #b0b9c6; margin: 0; font-size: 0.75em;">FROM</p>
                                        <p style="color: #00d4ff; margin: 4px 0; font-weight: 700; font-size: 1em;">{source}</p>
                                    </div>
                                    <div style="text-align: center; padding: 0 8px;">
                                        <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                                            <div style="flex: 1; height: 2px; background: linear-gradient(90deg, transparent, #00d4ff, transparent);"></div>
                                            <span style="font-size: 1.2em; color: #00d4ff;">→</span>
                                            <div style="flex: 1; height: 2px; background: linear-gradient(90deg, transparent, #00d4ff, transparent);"></div>
                                        </div>
                                    </div>
                                    <div style="text-align: center;">
                                        <p style="color: #b0b9c6; margin: 0; font-size: 0.75em;">TO</p>
                                        <p style="color: #00d4ff; margin: 4px 0; font-weight: 700; font-size: 1em;">{destination}</p>
                                    </div>
                                </div>
                                <div style="height: 1px; background: rgba(0, 212, 255, 0.1); margin: 8px 0;"></div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
                                    <div style="background: rgba(0, 212, 255, 0.08); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.15);">
                                        <p style="color: #b0b9c6; margin: 0; font-size: 0.7em; text-transform: uppercase; font-weight: 600;">📅 Date</p>
                                        <p style="color: #ffffff; margin: 4px 0; font-weight: 600; font-size: 0.95em;">{travel_date}</p>
                                    </div>
                                    <div style="background: rgba(0, 212, 255, 0.08); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.15);">
                                        <p style="color: #b0b9c6; margin: 0; font-size: 0.7em; text-transform: uppercase; font-weight: 600;">🪑 Seat</p>
                                        <p style="color: #ffffff; margin: 4px 0; font-weight: 600; font-size: 0.95em;">{seat}</p>
                                    </div>
                                    <div style="background: rgba(0, 212, 255, 0.08); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.15);">
                                        <p style="color: #b0b9c6; margin: 0; font-size: 0.7em; text-transform: uppercase; font-weight: 600;">👤 Age</p>
                                        <p style="color: #ffffff; margin: 4px 0; font-weight: 600; font-size: 0.95em;">{passenger_age} years</p>
                                    </div>
                                </div>
                            </div>
                            <div style="background: linear-gradient(135deg, rgba(0, 200, 100, 0.1) 0%, rgba(0, 150, 100, 0.05) 100%); border: 1px solid rgba(0, 200, 100, 0.2); border-radius: 8px; padding: 12px; text-align: center; margin-top: 16px;">
                                <p style="color: #00ff8f; margin: 0; font-size: 0.85em; font-weight: 700;">✅ BOOKING CONFIRMED</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

# ==================== CANCEL TICKET PAGE ====================
elif menu == "🗑️ Cancel Ticket":
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(255, 100, 100, 0.1) 0%, rgba(255, 150, 100, 0.05) 100%); 
                border: 1px solid rgba(255, 100, 100, 0.2); border-radius: 16px; padding: 20px; margin-bottom: 30px;
                backdrop-filter: blur(20px);">
        <h2 style="margin-top: 0;">🗑️ Cancel Booking</h2>
        <p style="color: #b0b9c6; margin: 0;">This action cannot be undone. Please be careful.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("**Cancel Single Booking**")
        booking_id = st.number_input("Enter Booking ID", min_value=1, key="cancel_id_input")
        
        if st.button("❌ Cancel This Booking", use_container_width=True, key="cancel_single"):
            existing_bookings = [b[0] for b in db.get_bookings()]
            if booking_id in existing_bookings:
                db.cancel_booking(booking_id)
                st.markdown("""
                <div style="background: linear-gradient(135deg, rgba(0, 200, 100, 0.15) 0%, rgba(0, 150, 100, 0.05) 100%); 
                            border: 1px solid rgba(0, 200, 100, 0.3); border-radius: 12px; padding: 20px; text-align: center;
                            backdrop-filter: blur(20px);">
                    <h3 style="margin-top: 0; color: #00ff8f;">✅ Booking Cancelled</h3>
                    <p style="color: #b0b9c6; margin: 0;">Your booking has been successfully removed.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("❌ Booking ID not found!")
    
    with col2:
        st.markdown("**Cancel Multiple Bookings**")
        range_start = st.number_input("Starting ID", min_value=1, value=1, key="range_start_input")
        range_end = st.number_input("Ending ID", min_value=1, value=10, key="range_end_input")
        
        if st.button("❌ Cancel Range", use_container_width=True, key="cancel_range"):
            if range_start > range_end:
                st.error("⚠️ Starting ID cannot be greater than Ending ID")
            else:
                cancelled_count = 0
                for i in range(range_start, range_end + 1):
                    try:
                        db.cancel_booking(i)
                        cancelled_count += 1
                    except:
                        pass
                
                if cancelled_count > 0:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, rgba(0, 200, 100, 0.15) 0%, rgba(0, 150, 100, 0.05) 100%); 
                                border: 1px solid rgba(0, 200, 100, 0.3); border-radius: 12px; padding: 20px; text-align: center;
                                backdrop-filter: blur(20px);">
                        <h3 style="margin-top: 0; color: #00ff8f;">✅ {cancelled_count} Bookings Cancelled</h3>
                        <p style="color: #b0b9c6; margin: 0;">Selected range has been cleared.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("ℹ️ No bookings found in the selected range.")

    