"""
Agency Broadcast Messages
Allows agencies to send bulk WhatsApp messages to passengers
"""

import streamlit as st
import db
import whatsapp
import notifications
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Broadcast Messages - TicketHub Agency",
    page_icon="📢",
    layout="wide",
    initial_sidebar_state="expanded"
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

from agency_sidebar import render_agency_sidebar
render_agency_sidebar()

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
tab1, tab2, tab3 = st.tabs(["📤 Send Message", "👥 Send to Passengers", "📜 Message History"])

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
    
    # Get all bookings for this agency (for messaging)
    all_bookings = list(db.bookings_collection.find({
        "agency_username": agency_username
    }))
    
    # Message templates (outside form)
    st.markdown("### 📝 Quick Templates")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚌 Bus Delayed Template", key="tmpl_delay"):
            st.session_state.message_template = "Dear passenger, your bus is delayed by [X] minutes. Updated departure time: [TIME]. We apologize for the inconvenience."
    with col2:
        if st.button("❌ Bus Cancelled Template", key="tmpl_cancel"):
            st.session_state.message_template = "We regret to inform that your bus has been cancelled. Refund will be processed within 24 hours to your original payment method."
    with col3:
        if st.button("📍 Route Changed Template", key="tmpl_route"):
            st.session_state.message_template = "Your route has been changed. New boarding point: [LOCATION]. Contact our support at [NUMBER] for more details."

    # Get all bookings for this agency (for messaging)
    all_bookings = list(db.bookings_collection.find({
        "agency_username": agency_username
    }))

    # Get unique routes and dates from bookings
    booking_routes = sorted(set(f"{b.get('source', '')} → {b.get('destination', '')}" for b in all_bookings if b.get('source') and b.get('destination')))
    booking_dates = sorted(set(b.get('date', '') for b in all_bookings if b.get('date')), reverse=True)

    # Filters — OUTSIDE the form so they update immediately on selection
    selected_route = None
    selected_date = None

    col1, col2 = st.columns(2)
    with col1:
        target_type = st.radio(
            "Send message to:",
            ["All Passengers", "Specific Route", "Specific Date"],
            horizontal=True,
            key="broadcast_target"
        )
    with col2:
        if target_type == "Specific Route" and booking_routes:
            selected_route = st.selectbox("Select Route", booking_routes, key="broadcast_route")
        elif target_type == "Specific Date" and booking_dates:
            selected_date = st.selectbox("Select Date", booking_dates, key="broadcast_date")
        else:
            st.write("")

    # Filter bookings based on selection
    if target_type == "Specific Route" and selected_route:
        src, dst = selected_route.split(" → ")
        filtered_bookings = [
            b for b in all_bookings
            if b.get("source", "").strip() == src.strip() and b.get("destination", "").strip() == dst.strip()
        ]
    elif target_type == "Specific Date" and selected_date:
        filtered_bookings = [
            b for b in all_bookings
            if b.get("date") == selected_date
        ]
    else:
        filtered_bookings = all_bookings

    st.divider()

    # Show recipient list
    st.markdown(f"### 📋 Recipients ({len(filtered_bookings)})")
    if filtered_bookings:
        for idx, b in enumerate(filtered_bookings[:20]):
            phone = notifications.get_user_phone(b.get("username", ""))
            status_icon = "🟢" if b.get("status") == "confirmed" else "🔴"
            st.markdown(f"{status_icon} **{b.get('passenger_name', 'N/A')}** | 📅 {b.get('date', '')} | 📍 {b.get('source', '')} → {b.get('destination', '')} | 💺 {b.get('seat', 'N/A')} | 📱 {phone or 'No phone'}")
        if len(filtered_bookings) > 20:
            st.caption(f"...and {len(filtered_bookings) - 20} more")
    else:
        st.info("No passengers found for selected filter")

    st.divider()

    # Message composition — inside form only for send
    st.markdown("### 📝 Compose Message")

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
        if st.button("📤 Send Message", use_container_width=True, type="primary", key="broadcast_send_btn",
                      disabled=(not message or recipient_count == 0)):
            # Send messages
            if not message or recipient_count == 0:
                st.error("❌ Cannot send. Message is empty or no recipients.")
            else:
                progress_bar = st.progress(0)
                success_count = 0
                failed_count = 0
                
                instance_name = whatsapp_instance.get("instance_name")
                
                for i, booking in enumerate(filtered_bookings):
                    try:
                        passenger_username = booking.get("username", "")
                        passenger_phone = notifications.get_user_phone(passenger_username)
                        passenger_name = booking.get("passenger_name", "Passenger")

                        if not passenger_phone:
                            failed_count += 1
                            progress_bar.progress((i + 1) / recipient_count)
                            continue

                        personal_message = f"Hi {passenger_name},\n\n{message}"
                        
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
                    
                    progress_bar.progress((i + 1) / recipient_count)
                
                st.divider()
                
                if success_count > 0:
                    st.success(f"✅ Successfully sent {success_count} message(s)")
                
                if failed_count > 0:
                    st.warning(f"⚠️ Failed to send {failed_count} message(s)")
                
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
# TAB 2: SEND TO PASSENGERS (Route-wise + Date-wise)
# =====================================================
with tab2:
    st.markdown("## 👥 Send Notification to Passengers")
    st.markdown("Filter by route or date, select passengers, and send a WhatsApp message.")

    # Get all bookings for this agency
    all_passenger_bookings = list(db.bookings_collection.find({
        "agency_username": agency_username
    }).sort("date", -1))

    if not all_passenger_bookings:
        st.info("📌 No bookings found. Passengers will appear here after bookings are made.")
    else:
        # Get unique routes and dates from bookings
        booking_routes = sorted(set(f"{b.get('source', '')} → {b.get('destination', '')}" for b in all_passenger_bookings if b.get('source') and b.get('destination')))
        booking_dates = sorted(set(b.get('date', '') for b in all_passenger_bookings if b.get('date')), reverse=True)

        # Filter section
        st.markdown("### 🔍 Filter Passengers")
        fc1, fc2 = st.columns(2)
        with fc1:
            filter_type = st.radio("Filter by:", ["All Passengers", "Route", "Date"], horizontal=True, key="pass_filter_type")
        with fc2:
            if filter_type == "Route":
                selected_route = st.selectbox("Select Route", booking_routes, key="pass_route_filter")
                src, dst = selected_route.split(" → ")
                filtered = [b for b in all_passenger_bookings if b.get("source", "").strip() == src.strip() and b.get("destination", "").strip() == dst.strip()]
            elif filter_type == "Date":
                selected_date = st.selectbox("Select Date", booking_dates, key="pass_date_filter")
                filtered = [b for b in all_passenger_bookings if b.get("date") == selected_date]
            else:
                filtered = all_passenger_bookings

        st.markdown("---")

        # Deduplicate by username (keep latest booking per passenger)
        seen = {}
        for b in filtered:
            uname = b.get("username", "")
            if uname not in seen:
                seen[uname] = b
        unique_passengers = list(seen.values())

        # Select All checkbox
        select_all = st.checkbox(f"✅ Select All ({len(unique_passengers)} passengers)", key="pass_select_all")

        # Show passenger list with checkboxes
        selected_passengers = []
        if unique_passengers:
            st.markdown(f"### 📋 Passengers ({len(unique_passengers)})")

            for idx, booking in enumerate(unique_passengers):
                phone = notifications.get_user_phone(booking.get("username", ""))
                phone_display = phone if phone else "No phone"
                status_icon = "🟢" if booking.get("status") == "confirmed" else "🔴"

                col1, col2, col3 = st.columns([5, 1, 1])
                with col1:
                    checked = st.checkbox(
                        f"{status_icon} 👤 {booking.get('passenger_name', 'N/A')} | 📅 {booking.get('date', '')} | 📍 {booking.get('source', '')} → {booking.get('destination', '')} | 💺 {booking.get('seat', 'N/A')} | 📱 {phone_display}",
                        value=select_all,
                        key=f"pass_check_{idx}"
                    )
                    if checked:
                        selected_passengers.append(booking)

                with col2:
                    if st.button("👁️", key=f"view_pass_{idx}", help="View Details"):
                        st.session_state.view_passenger = booking

                with col3:
                    if st.button("🗑️", key=f"del_pass_{idx}", help="Delete Booking"):
                        st.session_state.del_passenger = booking
        else:
            st.info("No passengers found for selected filter")

        # Show passenger detail view
        if "view_passenger" in st.session_state and st.session_state.view_passenger:
            vp = st.session_state.view_passenger
            phone = notifications.get_user_phone(vp.get("username", ""))
            st.divider()
            st.markdown("### 👤 Passenger Details")
            vc1, vc2 = st.columns(2)
            with vc1:
                st.markdown(f"**Booking ID:** #{vp.get('booking_id', 'N/A')}")
                st.markdown(f"**Passenger:** {vp.get('passenger_name', 'N/A')}")
                st.markdown(f"**Age:** {vp.get('passenger_age', 'N/A')}")
                st.markdown(f"**Gender:** {vp.get('passenger_gender', 'N/A')}")
                st.markdown(f"**Phone:** {phone or 'N/A'}")
            with vc2:
                st.markdown(f"**Route:** {vp.get('source', 'N/A')} → {vp.get('destination', 'N/A')}")
                st.markdown(f"**Date:** {vp.get('date', 'N/A')}")
                st.markdown(f"**Seat:** {vp.get('seat', 'N/A')}")
                st.markdown(f"**Status:** {vp.get('status', 'N/A').upper()}")
            if st.button("❌ Close", key="close_pass_view"):
                st.session_state.view_passenger = None
                st.rerun()

        # Handle delete confirmation
        if "del_passenger" in st.session_state and st.session_state.del_passenger:
            dp = st.session_state.del_passenger
            st.divider()
            st.warning(f"⚠️ Are you sure you want to delete booking **#{dp.get('booking_id')}** for **{dp.get('passenger_name')}**?")
            dc1, dc2 = st.columns(2)
            with dc1:
                if st.button("✅ Yes, Delete", type="primary", key="confirm_del_pass"):
                    try:
                        db.bookings_collection.update_one(
                            {"booking_id": dp.get("booking_id")},
                            {"$set": {"status": "cancelled"}}
                        )
                        db.tickets_collection.delete_one({"booking_id": dp.get("booking_id")})
                        db.revenue_collection.delete_one({"booking_id": dp.get("booking_id")})
                        st.success(f"✅ Booking #{dp.get('booking_id')} deleted successfully!")
                        st.session_state.del_passenger = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Delete failed: {e}")
            with dc2:
                if st.button("❌ Cancel", key="cancel_del_pass"):
                    st.session_state.del_passenger = None
                    st.rerun()

        # Handle delete confirmation
        if "del_passenger" in st.session_state and st.session_state.del_passenger:
            dp = st.session_state.del_passenger
            st.divider()
            st.warning(f"⚠️ Are you sure you want to delete booking **#{dp.get('booking_id')}** for **{dp.get('passenger_name')}**?")
            dc1, dc2 = st.columns(2)
            with dc1:
                if st.button("✅ Yes, Delete", type="primary", key="confirm_del_pass"):
                    try:
                        # Update booking status to cancelled in bookings collection
                        db.bookings_collection.update_one(
                            {"booking_id": dp.get("booking_id")},
                            {"$set": {"status": "cancelled"}}
                        )
                        # Remove ticket record
                        db.tickets_collection.delete_one({"booking_id": dp.get("booking_id")})
                        # Remove revenue record
                        db.revenue_collection.delete_one({"booking_id": dp.get("booking_id")})
                        st.success(f"✅ Booking #{dp.get('booking_id')} deleted successfully!")
                        st.session_state.del_passenger = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Delete failed: {e}")
            with dc2:
                if st.button("❌ Cancel", key="cancel_del_pass"):
                    st.session_state.del_passenger = None
                    st.rerun()

        st.markdown("---")

        # Message composer
        st.markdown("### 📝 Compose Message")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("👋 Greeting Template", key="pass_tmpl_greet"):
                st.session_state.pass_message = "Dear passenger, thank you for traveling with us! We hope you had a pleasant journey."
        with col2:
            if st.button("🔔 Reminder Template", key="pass_tmpl_remind"):
                st.session_state.pass_message = "Reminder: Your bus departs soon. Please be at the boarding point at least 15 minutes before departure."
        with col3:
            if st.button("⭐ Feedback Template", key="pass_tmpl_feedback"):
                st.session_state.pass_message = "Thank you for choosing us! We'd love your feedback. Rate your experience and help us serve you better."

        pass_message = st.text_area(
            "Message",
            value=st.session_state.get("pass_message", ""),
            placeholder="Type your message here... Use {name}, {route}, {date} for personalization",
            height=120,
            key="pass_msg_input"
        )

        # Show selected count
        if selected_passengers:
            st.info(f"📤 Message will be sent to **{len(selected_passengers)}** passenger(s)")
        else:
            st.warning("⚠️ Select at least one passenger to send a message.")

        # Send button
        if st.button("📤 Send to Selected Passengers", type="primary", use_container_width=True,
                      disabled=(not pass_message or not selected_passengers)):
            instance_name = whatsapp_instance.get("instance_name")
            progress = st.progress(0)
            success_count = 0
            failed_count = 0

            for i, booking in enumerate(selected_passengers):
                try:
                    passenger_username = booking.get("username", "")
                    passenger_phone = notifications.get_user_phone(passenger_username)
                    passenger_name = booking.get("passenger_name", "Passenger")

                    if not passenger_phone:
                        failed_count += 1
                        progress.progress((i + 1) / len(selected_passengers))
                        continue

                    # Personalize message
                    personalized = pass_message.replace("{name}", passenger_name)
                    personalized = personalized.replace("{route}", f"{booking.get('source', '')} → {booking.get('destination', '')}")
                    personalized = personalized.replace("{date}", booking.get("date", ""))

                    result = whatsapp.send_text_message(instance_name, passenger_phone, personalized)

                    if result.get("success"):
                        success_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Send error: {e}")
                    failed_count += 1

                progress.progress((i + 1) / len(selected_passengers))

            st.divider()
            if success_count > 0:
                st.success(f"✅ Sent to {success_count} passenger(s) successfully!")
            if failed_count > 0:
                st.warning(f"⚠️ Failed for {failed_count} passenger(s) (no phone or send error)")

            # Log broadcast
            try:
                db.notifications_collection.insert_one({
                    "agency_username": agency_username,
                    "message": pass_message,
                    "target_type": f"Passengers ({date_filter})",
                    "recipient_count": len(selected_passengers),
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "sent_at": datetime.now()
                })
            except Exception:
                pass

# =====================================================
# TAB 3: MESSAGE HISTORY
# =====================================================
with tab3:
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
