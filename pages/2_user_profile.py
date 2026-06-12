"""
User Profile & Dashboard
Full profile management, bookings, and account settings
"""

import streamlit as st
import db
import auth
from qr_generator import generate_booking_qr, generate_ticket_html

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="My Profile - TicketHub",
    page_icon="👤",
    layout="wide"
)

# =====================================================
# AUTH CHECK
# =====================================================
if not st.session_state.get("logged_in") or st.session_state.get("role") != "User":
    st.error("Please login as a User to access this page")
    st.stop()

username = st.session_state.get("user")
user = db.users_collection.find_one({"username": username})

if not user:
    st.error("User not found")
    st.stop()

# =====================================================
# CSS
# =====================================================
st.markdown("""
<style>
    .profile-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 30px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .profile-card h2 { margin: 0; color: white; }
    .profile-card p { color: rgba(255,255,255,0.8); margin: 5px 0 0 0; }
    .stat-box {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .stat-box h3 { margin: 0; color: #667eea; }
    .stat-box p { margin: 5px 0 0 0; color: #666; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.markdown("### Menu")
    if st.button("Back to Chat", use_container_width=True):
        st.switch_page("app.py")
    if st.button("Logout", use_container_width=True, type="secondary"):
        for key in ["logged_in", "user", "role", "chat_history", "booking_mode", "quick_action"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# =====================================================
# HEADER
# =====================================================
full_name = user.get("full_name", username)
st.markdown(f"""
<div class="profile-card">
    <h2>{full_name}</h2>
    <p>@{username}</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# TABS
# =====================================================
tab1, tab2, tab3 = st.tabs(["Profile", "My Bookings", "Settings"])

# =====================================================
# TAB 1: PROFILE
# =====================================================
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    total_bookings = db.bookings_collection.count_documents({"username": username})
    active_bookings = db.bookings_collection.count_documents({"username": username, "status": "confirmed"})
    cancelled = db.bookings_collection.count_documents({"username": username, "status": "cancelled"})

    with col1:
        st.markdown('<div class="stat-box"><h3>{}</h3><p>Total Bookings</p></div>'.format(total_bookings), unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stat-box"><h3>{}</h3><p>Active</p></div>'.format(active_bookings), unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="stat-box"><h3>{}</h3><p>Cancelled</p></div>'.format(cancelled), unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="stat-box"><h3>{}</h3><p>Phone</p></div>'.format(user.get("phone", "N/A")), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Edit Profile")

    with st.form("edit_profile"):
        col1, col2 = st.columns(2)

        with col1:
            new_full_name = st.text_input("Full Name", value=user.get("full_name", ""))
            new_phone = st.text_input("Phone Number", value=user.get("phone", ""), help="10-digit mobile number")

        with col2:
            new_gender = st.selectbox("Gender", ["Not specified", "Male", "Female", "Other"],
                                       index=["Not specified", "Male", "Female", "Other"].index(user.get("gender", "Not specified")))
            new_age = st.number_input("Age", min_value=1, max_value=120, value=user.get("age", 25) or 25)

        if st.form_submit_button("Save Changes", use_container_width=True, type="primary"):
            update = {"full_name": new_full_name, "gender": new_gender, "age": new_age}
            if new_phone and len(new_phone) == 10 and new_phone.isdigit():
                update["phone"] = new_phone
            elif new_phone:
                st.error("Invalid phone number. Enter 10 digits.")
                st.stop()

            db.users_collection.update_one({"username": username}, {"$set": update})
            st.success("Profile updated!")
            st.rerun()

# =====================================================
# TAB 2: MY BOOKINGS
# =====================================================
with tab2:
    st.markdown("### My Bookings")

    bookings = list(db.bookings_collection.find({"username": username}).sort("date", -1))

    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter", ["All", "Confirmed", "Cancelled"], key="booking_filter")
    with col2:
        sort_order = st.radio("Sort", ["Latest", "Oldest"], horizontal=True, key="booking_sort")

    filtered = bookings
    if status_filter != "All":
        filtered = [b for b in filtered if b.get("status") == status_filter.lower()]
    if sort_order == "Oldest":
        filtered = filtered[::-1]

    if filtered:
        for booking in filtered:
            status_icon = "🟢" if booking.get("status") == "confirmed" else "🔴"
            with st.expander(f"{status_icon} #{booking.get('booking_id')} - {booking.get('source')} to {booking.get('destination')} ({booking.get('date')})"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"**Route:** {booking.get('source')} to {booking.get('destination')}")
                    st.markdown(f"**Date:** {booking.get('date')}")
                    st.markdown(f"**Seat:** {booking.get('seat')}")
                with c2:
                    st.markdown(f"**Passenger:** {booking.get('passenger_name')}")
                    st.markdown(f"**Age:** {booking.get('passenger_age')}")
                    st.markdown(f"**Gender:** {booking.get('passenger_gender', 'N/A')}")
                with c3:
                    st.markdown(f"**Status:** {booking.get('status', 'unknown').upper()}")
                    st.markdown(f"**Agency:** {booking.get('agency_username')}")

                st.divider()

                try:
                    qr = generate_booking_qr(booking)
                    st.image(f"data:image/png;base64,{qr}", width=150)
                except:
                    pass

                if booking.get("status") != "cancelled":
                    if st.button("Cancel Booking", key=f"cancel_{booking.get('booking_id')}"):
                        result = db.cancel_booking(booking.get("booking_id"))
                        if result.get("success"):
                            st.success("Booking cancelled!")
                            st.rerun()
    else:
        st.info("No bookings found")

# =====================================================
# TAB 3: SETTINGS
# =====================================================
with tab3:
    st.markdown("### Account Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Change Password")
        current_pwd = st.text_input("Current Password", type="password", key="cur_pwd")
        new_pwd = st.text_input("New Password", type="password", key="new_pwd")
        confirm_pwd = st.text_input("Confirm Password", type="password", key="conf_pwd")

        if st.button("Update Password", use_container_width=True):
            if not current_pwd or not new_pwd or not confirm_pwd:
                st.error("All fields required")
            elif new_pwd != confirm_pwd:
                st.error("Passwords don't match")
            elif len(new_pwd) < 6:
                st.error("Password must be at least 6 characters")
            elif not auth.verify_password(current_pwd, user.get("password", "")):
                st.error("Current password is incorrect")
            else:
                hashed = auth.hash_password(new_pwd)
                db.users_collection.update_one({"username": username}, {"$set": {"password": hashed}})
                st.success("Password updated!")

    with col2:
        st.markdown("#### Notifications")
        notif_enabled = st.checkbox("WhatsApp Notifications", value=user.get("notifications_enabled", True))
        if st.button("Save Preferences", use_container_width=True):
            db.users_collection.update_one({"username": username}, {"$set": {"notifications_enabled": notif_enabled}})
            st.success("Settings saved!")

    st.divider()

    st.markdown("#### Danger Zone")
    if st.button("Delete My Account", type="secondary"):
        st.warning("This will permanently delete your account and all data.")
        if st.button("Confirm Delete", key="confirm_del"):
            db.users_collection.delete_one({"username": username})
            db.bookings_collection.delete_many({"username": username})
            for key in ["logged_in", "user", "role", "chat_history"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Account deleted!")
            st.rerun()

    st.divider()

    if st.button("Logout", use_container_width=True, type="primary"):
        for key in ["logged_in", "user", "role", "chat_history", "booking_mode", "quick_action"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
