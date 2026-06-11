"""
Agency Broadcast Messages
Allows agencies to send bulk WhatsApp messages to passengers
"""

import streamlit as st
import db
import whatsapp
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Broadcast Messages - TicketHub Agency",
    page_icon="📢",
    layout="wide"
)

# =====================================================
# AUTHENTICATION CHECK
# =====================================================
if not st.session_state.get("logged_in"):
    st.error("⚠️ Please login first")
    st.stop()

if st.session_state.get("role") not in ["Agency", "Travel Agency"]:
    st.error("⚠️ Please login as an Agency to access this page")
    st.stop()

agency_username = st.session_state.get("user")

# Check if WhatsApp is connected
whatsapp_instance = db.get_whatsapp_instance(agency_username)

# =====================================================
# PAGE TITLE
# =====================================================
st.markdown("# 📢 Broadcast Messages")
st.markdown(f"**Agency**: {agency_username}")

if not whatsapp_instance or not whatsapp_instance.get("is_connected"):
    st.error("⚠️ WhatsApp is not connected. Go to WhatsApp Settings to connect first.")
    st.info("Once connected, you can send bulk messages to your passengers.")
    if st.button("🔗 Go to WhatsApp Settings"):
        st.switch_page("pages/2_agency_whatsapp.py")
    st.stop()

st.divider()

# =====================================================
# TABS
# =====================================================
tab1, tab2 = st.tabs(["📤 Send Message", "📜 Message History"])

# =====================================================
# TAB 1: SEND MESSAGE
# =====================================================
with tab1:
    st.markdown("## Send Bulk WhatsApp Message")
    
    st.markdown("""
    <div style="background: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; border-radius: 4px; margin: 15px 0;">
    <strong>📌 Quick Message Templates:</strong>
    <ul>
    <li>Bus Delayed: "Dear passenger, your bus is delayed by [X] minutes. Updated departure time: [TIME]"</li>
    <li>Bus Cancelled: "We regret to inform that your bus on [ROUTE] has been cancelled. Refund will be processed within 24 hours."</li>
    <li>Route Changed: "Your route has been changed. New boarding point: [LOCATION]. Contact our support for more details."</li>
    <li>Boarding Time: "Your bus boards in [X] minutes at [LOCATION]. Please be ready."</li>
    <li>Emergency: "Important: [YOUR MESSAGE]"</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Get all confirmed bookings for this agency
    all_bookings = list(db.bookings_collection.find({
        "agency_username": agency_username,
        "status": "confirmed"
    }))
    
    # Get all routes for filtering
    routes = list(db.buses_collection.find({"agency_username": agency_username}))
    
    with st.form("broadcast_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Select target audience
            target_type = st.radio(
                "Send message to:",
                ["All Passengers", "Specific Route", "Specific Date"],
                horizontal=True
            )
        
        with col2:
            st.write("")  # Spacing
        
        # Filter based on selection
        if target_type == "Specific Route":
            if routes:
                selected_route = st.selectbox(
                    "Select Route",
                    [f"{r.get('source')} → {r.get('destination')}" for r in routes]
                )
                filtered_bookings = [
                    b for b in all_bookings
                    if b.get("source") in selected_route and b.get("destination") in selected_route
                ]
            else:
                st.warning("No routes found")
                filtered_bookings = []
        
        elif target_type == "Specific Date":
            selected_date = st.date_input("Select Date")
            filtered_bookings = [
                b for b in all_bookings
                if b.get("date") == str(selected_date)
            ]
        
        else:  # All Passengers
            filtered_bookings = all_bookings
        
        st.divider()
        
        # Message composition
        st.markdown("### 📝 Compose Message")
        
        # Preset templates
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚌 Bus Delayed Template"):
                st.session_state.message_template = "Dear passenger, your bus is delayed by [X] minutes. Updated departure time: [TIME]. We apologize for the inconvenience."
        
        with col2:
            if st.button("❌ Bus Cancelled Template"):
                st.session_state.message_template = "We regret to inform that your bus has been cancelled. Refund will be processed within 24 hours to your original payment method."
        
        with col3:
            if st.button("📍 Route Changed Template"):
                st.session_state.message_template = "Your route has been changed. New boarding point: [LOCATION]. Contact our support at [NUMBER] for more details."
        
        message = st.text_area(
            "Message",
            value=st.session_state.get("message_template", ""),
            placeholder="Type your message here (up to 500 characters)...",
            height=120,
            max_chars=500,
            help="Use [X], [TIME], [LOCATION], [NUMBER] as placeholders"
        )
        
        st.divider()
        
        # Show recipient count
        recipient_count = len(filtered_bookings)
        if recipient_count > 0:
            st.info(f"📤 This message will be sent to **{recipient_count}** passenger(s)")
        else:
            st.warning("⚠️ No passengers found matching your filters")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button(
                "📤 Send Message",
                use_container_width=True,
                type="primary",
                disabled=(not message or recipient_count == 0)
            )
        
        with col2:
            if st.form_submit_button("📋 Preview", use_container_width=True):
                st.session_state.show_preview = True
        
        if submitted:
            # Send messages
            if not message or recipient_count == 0:
                st.error("❌ Cannot send. Message is empty or no recipients.")
            else:
                # Confirm before sending
                st.warning(f"⚠️ Are you sure? This will send {recipient_count} messages.")
                
                if st.button("✅ Confirm and Send", use_container_width=True, key="confirm_send"):
                    progress_bar = st.progress(0)
                    success_count = 0
                    failed_count = 0
                    
                    instance_name = whatsapp_instance.get("instance_name")
                    
                    for i, booking in enumerate(filtered_bookings):
                        try:
                            passenger_phone = booking.get("username")  # Assuming username is phone
                            passenger_name = booking.get("passenger_name")
                            
                            # Personalize message
                            personal_message = f"Hi {passenger_name},\n\n{message}"
                            
                            # Send via WhatsApp
                            result = whatsapp.send_text_message(
                                instance_name,
                                passenger_phone,
                                personal_message
                            )
                            
                            if result.get("success"):
                                success_count += 1
                            else:
                                failed_count += 1
                        
                        except Exception as e:
                            logger.error(f"Error sending message: {e}")
                            failed_count += 1
                        
                        # Update progress
                        progress_bar.progress((i + 1) / recipient_count)
                    
                    st.divider()
                    
                    if success_count > 0:
                        st.success(f"✅ Successfully sent {success_count} message(s)")
                    
                    if failed_count > 0:
                        st.warning(f"⚠️ Failed to send {failed_count} message(s)")
                    
                    # Log to database
                    broadcast_log = {
                        "agency_username": agency_username,
                        "message": message,
                        "target_type": target_type,
                        "recipient_count": recipient_count,
                        "success_count": success_count,
                        "failed_count": failed_count,
                        "sent_at": datetime.now()
                    }
                    
                    try:
                        db.notifications_collection.insert_one(broadcast_log)
                    except:
                        pass

# =====================================================
# TAB 2: MESSAGE HISTORY
# =====================================================
with tab2:
    st.markdown("## Message History")
    
    # Get broadcast history
    broadcasts = list(db.notifications_collection.find({
        "agency_username": agency_username,
        "sent_at": {"$exists": True}
    }).sort("sent_at", -1).limit(50))
    
    if broadcasts:
        for broadcast in broadcasts:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    **📝 {broadcast.get('target_type', 'Unknown')}**
                    
                    Message: {broadcast.get('message', 'N/A')[:100]}...
                    """)
                
                with col2:
                    st.markdown(f"""
                    ✅ Success: {broadcast.get('success_count', 0)}
                    
                    ❌ Failed: {broadcast.get('failed_count', 0)}
                    """)
                
                with col3:
                    st.caption(f"📅 {str(broadcast.get('sent_at', 'Unknown'))[:19]}")
                
                st.divider()
    
    else:
        st.info("📌 No message history yet")

# =====================================================
# FOOTER
# =====================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85em; margin-top: 30px;">
    <p>💡 Messages are personalized with passenger names</p>
    <p>📊 View delivery status for each broadcast in Message History</p>
    <p>⏰ Messages are sent immediately through WhatsApp</p>
</div>
""", unsafe_allow_html=True)
