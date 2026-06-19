"""
Agency Dashboard
Shows bookings, revenue, analytics, and passenger management for agencies
"""

import streamlit as st
import db
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Agency Dashboard - TicketHub",
    page_icon="📊",
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

# Get agency info
agency = db.agencies_collection.find_one({"username": agency_username})

# =====================================================
# PAGE TITLE
# =====================================================
st.markdown("# 📊 Agency Dashboard")
st.markdown(f"**Agency**: {agency.get('agency_name', agency_username)} | **Since**: {str(agency.get('created_at', 'Unknown'))[:10]}")
st.divider()

# =====================================================
# FETCH DATA
# =====================================================
# Get all bookings for this agency
all_bookings = list(db.bookings_collection.find({"agency_username": agency_username}))

# Get bookings by status
confirmed_bookings = [b for b in all_bookings if b.get("status") == "confirmed"]
cancelled_bookings = [b for b in all_bookings if b.get("status") == "cancelled"]

# Get today's bookings
today = datetime.now().strftime("%Y-%m-%d")
today_bookings = [b for b in all_bookings if b.get("date") == today and b.get("status") == "confirmed"]

# Calculate revenue from confirmed bookings + tickets collection
total_revenue = 0
today_revenue = 0
try:
    for b in confirmed_bookings:
        ticket_rec = db.tickets_collection.find_one({"booking_id": b.get("booking_id")})
        fare = 0
        if ticket_rec and ticket_rec.get("fare"):
            fare = float(ticket_rec["fare"])
        elif b.get("fare"):
            fare = float(b["fare"])
        total_revenue += fare
        if b.get("date") == today:
            today_revenue += fare
except Exception:
    pass

# =====================================================
# KEY METRICS (TOP ROW)
# =====================================================
st.markdown("## 📈 Key Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Total Bookings",
        value=len(all_bookings),
        delta=len(today_bookings) if today_bookings else "0 today"
    )

with col2:
    st.metric(
        label="Confirmed",
        value=len(confirmed_bookings),
        delta=f"{len(confirmed_bookings) * 100 // len(all_bookings) if all_bookings else 0}%"
    )

with col3:
    st.metric(
        label="Cancelled",
        value=len(cancelled_bookings),
        delta=f"{len(cancelled_bookings) * 100 // len(all_bookings) if all_bookings else 0}%"
    )

with col4:
    st.metric(
        label="Total Revenue",
        value=f"₹{total_revenue:,}",
        delta=f"₹{today_revenue:,} today"
    )

with col5:
    st.metric(
        label="Avg Occupancy",
        value=f"{len(confirmed_bookings) * 100 // (len(confirmed_bookings) + len(cancelled_bookings)) if (len(confirmed_bookings) + len(cancelled_bookings)) > 0 else 0}%"
    )

st.divider()

# =====================================================
# TABS
# =====================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "📋 Bookings", "👥 Passengers", "⚙️ Settings"])

# =====================================================
# TAB 1: ANALYTICS
# =====================================================
with tab1:
    st.markdown("## Booking Analytics")
    
    # Booking trend chart
    if all_bookings:
        # Group bookings by date
        bookings_by_date = {}
        for booking in all_bookings:
            date = booking.get("date", "Unknown")
            bookings_by_date[date] = bookings_by_date.get(date, 0) + 1
        
        df_trend = pd.DataFrame(
            list(bookings_by_date.items()),
            columns=["Date", "Bookings"]
        ).sort_values("Date")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_trend = px.line(
                df_trend,
                x="Date",
                y="Bookings",
                title="Bookings Over Time",
                markers=True,
                line_shape="spline"
            )
            fig_trend.update_layout(
                height=400,
                xaxis_title="Date",
                yaxis_title="Number of Bookings",
                template="plotly_white"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        
        with col2:
            # Status pie chart
            status_data = {
                "Confirmed": len(confirmed_bookings),
                "Cancelled": len(cancelled_bookings)
            }
            
            fig_pie = px.pie(
                values=list(status_data.values()),
                names=list(status_data.keys()),
                title="Booking Status Distribution",
                color_discrete_map={"Confirmed": "#10b981", "Cancelled": "#ef4444"}
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Revenue chart — from confirmed bookings + tickets collection
        st.markdown("### Revenue Analytics")
        
        revenue_by_date = {}
        for b in confirmed_bookings:
            date = b.get("date", "Unknown")
            fare = 0
            try:
                ticket_rec = db.tickets_collection.find_one({"booking_id": b.get("booking_id")})
                if ticket_rec and ticket_rec.get("fare"):
                    fare = float(ticket_rec["fare"])
                elif b.get("fare"):
                    fare = float(b["fare"])
            except Exception:
                pass
            revenue_by_date[date] = revenue_by_date.get(date, 0) + fare
        
        df_revenue = pd.DataFrame(
            list(revenue_by_date.items()),
            columns=["Date", "Revenue"]
        ).sort_values("Date")
        
        fig_revenue = px.bar(
            df_revenue,
            x="Date",
            y="Revenue",
            title="Daily Revenue",
            text="Revenue",
            color="Revenue",
            color_continuous_scale="Greens"
        )
        fig_revenue.update_layout(
            height=400,
            xaxis_title="Date",
            yaxis_title="Revenue (₹)"
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    else:
        st.info("📌 No bookings yet. Bookings analytics will appear here.")

# =====================================================
# TAB 2: BOOKINGS
# =====================================================
with tab2:
    st.markdown("## All Bookings")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Confirmed", "Cancelled"],
            key="booking_status_filter"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Date (Newest)", "Date (Oldest)", "Booking ID"],
            key="booking_sort"
        )
    
    with col3:
        search_term = st.text_input(
            "Search Booking ID or Passenger",
            placeholder="e.g., 1001 or John"
        )
    
    # Filter bookings
    filtered_bookings = all_bookings
    
    if status_filter != "All":
        filtered_bookings = [b for b in filtered_bookings if b.get("status") == status_filter.lower()]
    
    if search_term:
        filtered_bookings = [
            b for b in filtered_bookings
            if str(b.get("booking_id")) in search_term or
               (b.get("passenger_name", "").lower().find(search_term.lower()) >= 0)
        ]
    
    # Sort bookings
    if sort_by == "Date (Newest)":
        filtered_bookings = sorted(filtered_bookings, key=lambda x: x.get("date", ""), reverse=True)
    elif sort_by == "Date (Oldest)":
        filtered_bookings = sorted(filtered_bookings, key=lambda x: x.get("date", ""))
    else:
        filtered_bookings = sorted(filtered_bookings, key=lambda x: x.get("booking_id", 0), reverse=True)
    
    # Display bookings
    if filtered_bookings:
        for booking in filtered_bookings[:50]:  # Show first 50
            status_color = "🟢" if booking.get("status") == "confirmed" else "🔴"
            
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**#{booking.get('booking_id')}**")
                    st.caption(status_color + " " + booking.get("status", "unknown").upper())
                
                with col2:
                    st.markdown(f"📍 {booking.get('source')} → {booking.get('destination')}")
                    st.caption(f"👤 {booking.get('passenger_name')} ({booking.get('passenger_age')} yrs)")
                
                with col3:
                    st.markdown(f"📅 {booking.get('date')}")
                    st.caption(f"💺 Seat: {booking.get('seat')}")
                
                with col4:
                    # Get real fare from tickets collection
                    real_fare = "—"
                    try:
                        ticket_rec = db.tickets_collection.find_one({"booking_id": booking.get("booking_id")})
                        if ticket_rec and ticket_rec.get("fare"):
                            real_fare = f"₹{ticket_rec['fare']}"
                    except Exception:
                        pass
                    st.markdown(f"**{real_fare}**")
                    if st.button("👁️ View", key=f"view_{booking.get('booking_id')}"):
                        st.session_state.selected_booking = booking
                        st.rerun()
            
            st.divider()

    # Show selected booking detail popup
    if "selected_booking" in st.session_state and st.session_state.selected_booking:
        sb = st.session_state.selected_booking
        st.divider()
        st.markdown("## Booking Details")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Booking ID:** #{sb.get('booking_id')}")
            st.markdown(f"**Status:** {sb.get('status', 'N/A').upper()}")
            st.markdown(f"**Route:** {sb.get('source', 'N/A')} → {sb.get('destination', 'N/A')}")
            st.markdown(f"**Date:** {sb.get('date', 'N/A')}")
            st.markdown(f"**Seat:** {sb.get('seat', 'N/A')}")
        with c2:
            st.markdown(f"**Passenger:** {sb.get('passenger_name', 'N/A')}")
            st.markdown(f"**Age:** {sb.get('passenger_age', 'N/A')}")
            st.markdown(f"**Gender:** {sb.get('passenger_gender', 'N/A')}")
            st.markdown(f"**Phone:** {sb.get('phone_number', 'N/A')}")
            try:
                ticket_rec = db.tickets_collection.find_one({"booking_id": sb.get("booking_id")})
                fare_val = ticket_rec.get("fare", "N/A") if ticket_rec else "N/A"
            except Exception:
                fare_val = "N/A"
            st.markdown(f"**Fare:** ₹{fare_val}")

        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            if st.button("🗑️ Delete Booking", type="primary", key="delete_booking_detail"):
                st.session_state.delete_booking = sb
        with bc3:
            if st.button("❌ Close", key="close_booking_detail"):
                st.session_state.selected_booking = None
                st.rerun()

    # Handle booking delete confirmation
    if "delete_booking" in st.session_state and st.session_state.delete_booking:
        db_entry = st.session_state.delete_booking
        st.warning(f"⚠️ Are you sure you want to delete booking **#{db_entry.get('booking_id')}** for **{db_entry.get('passenger_name')}**?")
        dc1, dc2 = st.columns(2)
        with dc1:
            if st.button("✅ Yes, Delete", type="primary", key="confirm_delete_booking"):
                try:
                    # Cancel booking
                    db.bookings_collection.update_one(
                        {"booking_id": db_entry.get("booking_id")},
                        {"$set": {"status": "cancelled"}}
                    )
                    # Remove ticket record
                    db.tickets_collection.delete_one({"booking_id": db_entry.get("booking_id")})
                    # Remove revenue record
                    db.revenue_collection.delete_one({"booking_id": db_entry.get("booking_id")})
                    # Remove notification records
                    db.notifications_collection.delete_many({"booking_id": db_entry.get("booking_id")})
                    st.success(f"✅ Booking #{db_entry.get('booking_id')} deleted successfully!")
                    st.session_state.delete_booking = None
                    st.session_state.selected_booking = None
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Delete failed: {e}")
        with dc2:
            if st.button("❌ Cancel", key="cancel_delete_booking"):
                st.session_state.delete_booking = None
                st.rerun()
    
    else:
        st.info("📌 No bookings match your filters")

# =====================================================
# TAB 3: PASSENGERS
# =====================================================
with tab3:
    st.markdown("## Passenger Management")
    
    if confirmed_bookings:
        # Get unique passengers (by username)
        passengers = {}
        for booking in confirmed_bookings:
            uname = booking.get("username", "Unknown")
            if uname not in passengers:
                passengers[uname] = {
                    "name": booking.get("passenger_name", "N/A"),
                    "age": booking.get("passenger_age", "N/A"),
                    "gender": booking.get("passenger_gender", "N/A"),
                    "bookings": 0,
                    "last_booking": booking.get("date", ""),
                    "total_spent": 0
                }
            passengers[uname]["bookings"] += 1
            try:
                ticket_rec = db.tickets_collection.find_one({"booking_id": booking.get("booking_id")})
                real_fare = ticket_rec.get("fare", 0) if ticket_rec else 0
            except Exception:
                real_fare = 0
            passengers[uname]["total_spent"] += real_fare
            passengers[uname]["last_booking"] = max(passengers[uname]["last_booking"], booking.get("date", ""))

        sorted_passengers = sorted(passengers.items(), key=lambda x: x[1]["bookings"], reverse=True)

        st.markdown(f"### 👥 {len(sorted_passengers)} Passenger(s)")

        for uname, data in sorted_passengers:
            with st.container():
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(f"**{data['name']}** | Age: {data['age']} | {data['gender']} | Bookings: {data['bookings']} | Spent: ₹{data['total_spent']:,}")
                with c2:
                    if st.button("👁️ View", key=f"dash_view_pass_{uname}"):
                        st.session_state.dash_view_passenger = {"username": uname, **data}
                with c3:
                    if st.button("🗑️ Delete", key=f"dash_del_pass_{uname}"):
                        st.session_state.dash_del_passenger = {"username": uname, **data}
                st.divider()

        # Show passenger detail
        if "dash_view_passenger" in st.session_state and st.session_state.dash_view_passenger:
            vp = st.session_state.dash_view_passenger
            st.markdown("### 👤 Passenger Details")
            vc1, vc2 = st.columns(2)
            with vc1:
                st.markdown(f"**Username:** {vp.get('username')}")
                st.markdown(f"**Name:** {vp.get('name')}")
                st.markdown(f"**Age:** {vp.get('age')}")
                st.markdown(f"**Gender:** {vp.get('gender')}")
            with vc2:
                st.markdown(f"**Total Bookings:** {vp.get('bookings')}")
                st.markdown(f"**Total Spent:** ₹{vp.get('total_spent', 0):,}")
                st.markdown(f"**Last Booking:** {vp.get('last_booking')}")
            if st.button("❌ Close", key="close_dash_pass_view"):
                st.session_state.dash_view_passenger = None
                st.rerun()

        # Handle delete confirmation
        if "dash_del_passenger" in st.session_state and st.session_state.dash_del_passenger:
            dp = st.session_state.dash_del_passenger
            st.warning(f"⚠️ Are you sure you want to cancel ALL bookings for **{dp.get('name')}** ({dp.get('username')})?")
            dc1, dc2 = st.columns(2)
            with dc1:
                if st.button("✅ Yes, Cancel All", type="primary", key="confirm_dash_del_pass"):
                    try:
                        # Cancel all confirmed bookings for this passenger
                        result = db.bookings_collection.update_many(
                            {"agency_username": agency_username, "username": dp.get("username"), "status": "confirmed"},
                            {"$set": {"status": "cancelled"}}
                        )
                        # Remove ticket records
                        db.tickets_collection.delete_many({"agency_username": agency_username, "username": dp.get("username")})
                        # Remove revenue records
                        db.revenue_collection.delete_many({"agency_username": agency_username, "username": dp.get("username")})
                        st.success(f"✅ Cancelled {result.modified_count} booking(s) for {dp.get('name')}!")
                        st.session_state.dash_del_passenger = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Delete failed: {e}")
            with dc2:
                if st.button("❌ Cancel", key="cancel_dash_del_pass"):
                    st.session_state.dash_del_passenger = None
                    st.rerun()
    
    else:
        st.info("📌 No passenger data yet")

# =====================================================
# TAB 4: SETTINGS
# =====================================================
with tab4:
    st.markdown("## Agency Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Basic Information")
        
        new_agency_name = st.text_input("Agency Name", value=agency.get('agency_name', ''), key="set_agency_name")
        st.markdown(f"**Username**: {agency_username}")
        new_email = st.text_input("Email", value=agency.get('email', ''), key="set_email")
        new_phone = st.text_input("Phone", value=agency.get('phone', ''), key="set_phone")
        st.markdown(f"**Created**: {str(agency.get('created_at', 'Unknown'))[:10]}")
        
        if st.button("💾 Update Profile", type="primary", use_container_width=True, key="set_update_profile"):
            updates = {}
            if new_agency_name != agency.get('agency_name', ''):
                updates["agency_name"] = new_agency_name
            if new_email != agency.get('email', ''):
                updates["email"] = new_email
            if new_phone != agency.get('phone', ''):
                updates["phone"] = new_phone
            if updates:
                db.agencies_collection.update_one(
                    {"username": agency_username},
                    {"$set": updates}
                )
                st.success("✅ Profile updated successfully!")
                st.rerun()
            else:
                st.info("No changes to update")
    
    with col2:
        st.markdown("### Pricing Settings")
        ticket_price = agency.get("ticket_price", 0)
        
        new_ticket_price = st.number_input(
            "Ticket Price (₹)",
            value=ticket_price,
            min_value=0,
            step=100
        )
        
        if new_ticket_price != ticket_price:
            if st.button("💾 Update Ticket Price", use_container_width=True):
                db.agencies_collection.update_one(
                    {"username": agency_username},
                    {"$set": {"ticket_price": new_ticket_price}}
                )
                st.success(f"✅ Ticket price updated to ₹{new_ticket_price}")
                st.rerun()
    
    st.divider()
    st.markdown("### Quick Links")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📱 WhatsApp Settings", use_container_width=True):
            st.switch_page("pages/2_agency_whatsapp.py")
    
    with col2:
        if st.button("🛣️ Manage Routes", use_container_width=True):
            st.switch_page("pages/3_agency_routes.py")

# =====================================================
# FOOTER
# =====================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85em; margin-top: 30px;">
    <p>💡 Dashboard data updates in real-time as bookings are made</p>
    <p>📊 All metrics are calculated from confirmed bookings only</p>
</div>
""", unsafe_allow_html=True)
