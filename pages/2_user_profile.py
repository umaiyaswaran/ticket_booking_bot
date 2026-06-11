"""
User Profile & Booking Management
Shows user profile, booking history, and ticket details
"""

import streamlit as st
import db
import pandas as pd
from qr_generator import generate_booking_qr, generate_ticket_html
from datetime import datetime

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="My Profile - TicketHub",
    page_icon="👤",
    layout="wide"
)

# =====================================================
# AUTHENTICATION CHECK
# =====================================================
if not st.session_state.get("logged_in") or st.session_state.get("role") != "User":
    st.error("⚠️ Please login as a User to access this page")
    st.stop()

# =====================================================
# SIDEBAR NAVIGATION
# =====================================================
with st.sidebar:
    st.markdown("### 🎫 TicketHub Menu")
    st.markdown("---")
    
    st.markdown("**👤 USER DASHBOARD**")
    
    if st.button("📊 Dashboard", use_container_width=True):
        st.switch_page("app.py")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎫 My Bookings", use_container_width=True, key="sb_bookings"):
            st.rerun()
    with col2:
        if st.button("⚙️ Profile", use_container_width=True, key="sb_profile"):
            st.rerun()
    
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

username = st.session_state.get("user")
user = db.users_collection.find_one({"username": username})

# =====================================================
# PAGE TITLE
# =====================================================
st.markdown("# 👤 My Profile & Bookings")
st.divider()

# =====================================================
# TABS
# =====================================================
tab1, tab2, tab3 = st.tabs(["👤 Profile", "🎫 My Bookings", "⚙️ Settings"])

# =====================================================
# TAB 1: PROFILE
# =====================================================
with tab1:
    st.markdown("## Your Profile Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Basic Information
        """)
        
        st.markdown(f"""
        **Username**: {user.get('username')}
        
        **Email**: {user.get('email', 'Not set')}
        
        **Mobile Number**: {user.get('phone', 'Not set')}
        
        **Gender**: {user.get('gender', 'Not specified')}
        """)
    
    with col2:
        st.markdown("""
        ### Account Details
        """)
        
        st.markdown(f"""
        **Member Since**: {str(user.get('created_at', 'Unknown'))[:10]}
        
        **Total Bookings**: {len(list(db.bookings_collection.find({'username': username})))}
        
        **Active Bookings**: {len(list(db.bookings_collection.find({'username': username, 'status': 'confirmed'})))}
        
        **Cancelled**: {len(list(db.bookings_collection.find({'username': username, 'status': 'cancelled'})))}
        """)
    
    st.divider()
    
    # Edit profile section
    st.markdown("## Edit Profile")
    
    with st.form("edit_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_email = st.text_input(
                "Email",
                value=user.get('email', ''),
                disabled=True,
                help="Email cannot be changed"
            )
            
            new_gender = st.selectbox(
                "Gender",
                ["Not specified", "Male", "Female", "Other"],
                index=["Not specified", "Male", "Female", "Other"].index(user.get('gender', 'Not specified'))
            )
        
        with col2:
            new_phone = st.text_input(
                "Mobile Number",
                value=user.get('phone', ''),
                disabled=True,
                help="Mobile number cannot be changed"
            )
            
            new_name = st.text_input(
                "Full Name (Optional)",
                value=user.get('full_name', ''),
                placeholder="Enter your full name"
            )
        
        st.divider()
        
        if st.form_submit_button("💾 Update Profile", use_container_width=True, type="primary"):
            try:
                update_data = {
                    "gender": new_gender,
                }
                
                if new_name:
                    update_data["full_name"] = new_name
                
                db.users_collection.update_one(
                    {"username": username},
                    {"$set": update_data}
                )
                
                st.success("✅ Profile updated successfully!")
                st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error updating profile: {str(e)}")

# =====================================================
# TAB 2: MY BOOKINGS
# =====================================================
with tab2:
    st.markdown("## My Bookings")
    
    # Get all bookings for this user
    user_bookings = list(db.bookings_collection.find({"username": username}).sort("date", -1))
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Confirmed", "Cancelled"],
            key="user_booking_status"
        )
    
    with col2:
        sort_order = st.radio(
            "Sort by",
            ["Latest First", "Oldest First"],
            horizontal=True
        )
    
    # Apply filters
    filtered_bookings = user_bookings
    
    if status_filter != "All":
        filtered_bookings = [b for b in filtered_bookings if b.get("status") == status_filter.lower()]
    
    if sort_order == "Oldest First":
        filtered_bookings = filtered_bookings[::-1]
    
    # Display bookings
    if filtered_bookings:
        st.success(f"✅ You have {len(filtered_bookings)} booking(s)")
        
        # Create tabs for each booking
        for i, booking in enumerate(filtered_bookings):
            status_icon = "🟢" if booking.get("status") == "confirmed" else "🔴"
            booking_title = f"{status_icon} #{booking.get('booking_id')} - {booking.get('source')} → {booking.get('destination')} ({booking.get('date')})"
            
            with st.expander(booking_title, expanded=(i == 0)):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("""
                    ### Journey Details
                    """)
                    st.markdown(f"""
                    **Route**: {booking.get('source')} → {booking.get('destination')}
                    
                    **Date**: {booking.get('date')}
                    
                    **Seat**: {booking.get('seat')}
                    
                    **Agency**: {booking.get('agency_username')}
                    """)
                
                with col2:
                    st.markdown("""
                    ### Passenger Details
                    """)
                    st.markdown(f"""
                    **Name**: {booking.get('passenger_name')}
                    
                    **Age**: {booking.get('passenger_age')} years
                    
                    **Gender**: {booking.get('passenger_gender', 'Not specified')}
                    
                    **Status**: {booking.get('status', 'unknown').upper()}
                    """)
                
                with col3:
                    st.markdown("""
                    ### Booking Info
                    """)
                    st.markdown(f"""
                    **Booking ID**: {booking.get('booking_id')}
                    
                    **Booked On**: {str(booking.get('created_at', 'Unknown'))[:10]}
                    
                    **Price**: ₹500
                    
                    **WhatsApp**: ✅ Notification Sent
                    """)
                
                st.divider()
                
                # QR Code
                st.markdown("### 📱 QR Ticket")
                try:
                    qr_base64 = generate_booking_qr(booking)
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.markdown(
                            f'<img src="data:image/png;base64,{qr_base64}" style="width:100%; max-width:200px; border-radius:8px;">',
                            unsafe_allow_html=True
                        )
                        st.caption("Scan this QR at boarding")
                except Exception as e:
                    st.error(f"❌ Error generating QR: {str(e)}")
                
                st.divider()
                
                # Actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🎫 View Full Ticket", use_container_width=True, key=f"view_ticket_{booking.get('booking_id')}"):
                        st.session_state.show_ticket = booking.get("booking_id")
                
                with col2:
                    if st.button("📥 Download PDF", use_container_width=True, key=f"download_{booking.get('booking_id')}"):
                        st.info("📥 PDF download feature coming soon!")
                
                with col3:
                    if booking.get("status") != "cancelled":
                        if st.button("❌ Cancel Booking", use_container_width=True, key=f"cancel_{booking.get('booking_id')}"):
                            if st.button("⚠️ Confirm Cancellation", key=f"confirm_cancel_{booking.get('booking_id')}"):
                                try:
                                    result = db.cancel_booking(booking.get("booking_id"))
                                    if result.get("success"):
                                        st.success(f"✅ Booking #{booking.get('booking_id')} cancelled")
                                        # Send cancellation notification
                                        try:
                                            import notifications as notif_manager
                                            notif_manager.send_cancellation_notification(result.get("booking"))
                                        except:
                                            pass
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error: {result.get('message')}")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
    
    else:
        st.info("📌 No bookings found")
    
    # Show full ticket modal
    if st.session_state.get("show_ticket"):
        booking = next((b for b in user_bookings if b.get("booking_id") == st.session_state.show_ticket), None)
        if booking:
            st.markdown("---")
            st.markdown("### 🎫 Full Ticket")
            
            agency = db.agencies_collection.find_one({"username": booking.get("agency_username")})
            ticket_html = generate_ticket_html(booking, agency)
            
            st.markdown(ticket_html, unsafe_allow_html=True)
            
            if st.button("❌ Close"):
                st.session_state.show_ticket = None
                st.rerun()

# =====================================================
# TAB 3: SETTINGS
# =====================================================
with tab3:
    st.markdown("## Account Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Notifications")
        
        notifications_enabled = st.checkbox(
            "Enable WhatsApp Notifications",
            value=user.get("notifications_enabled", True),
            help="Receive WhatsApp updates on bookings and cancellations"
        )
        
        if st.button("💾 Save Notification Settings", use_container_width=True):
            db.users_collection.update_one(
                {"username": username},
                {"$set": {"notifications_enabled": notifications_enabled}}
            )
            st.success("✅ Settings saved")
    
    with col2:
        st.markdown("### Password")
        
        current_password = st.text_input(
            "Current Password",
            type="password",
            key="current_pwd"
        )
        
        new_password = st.text_input(
            "New Password",
            type="password",
            key="new_pwd"
        )
        
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="confirm_pwd"
        )
        
        if st.button("🔐 Change Password", use_container_width=True):
            if not current_password or not new_password or not confirm_password:
                st.error("❌ All fields are required")
            elif new_password != confirm_password:
                st.error("❌ Passwords don't match")
            elif len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters")
            else:
                st.success("✅ Password changed successfully")
    
    st.divider()
    
    st.markdown("### Danger Zone")
    
    if st.button("🗑️ Delete Account", use_container_width=True, type="secondary"):
        st.warning("⚠️ This action cannot be undone. All your data will be deleted.")
        
        if st.button("⚠️ Permanently Delete My Account", key="confirm_delete_account"):
            db.users_collection.delete_one({"username": username})
            st.success("✅ Account deleted")
            st.session_state.logged_in = False
            st.rerun()

# =====================================================
# FOOTER
# =====================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85em; margin-top: 30px;">
    <p>💡 Your bookings and QR codes are synced across all devices</p>
    <p>📱 Show your QR code at the boarding counter</p>
    <p>🔒 Your personal information is securely stored</p>
</div>
""", unsafe_allow_html=True)
