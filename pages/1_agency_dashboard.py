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

# Calculate revenue (assuming ticket price from agency settings)
ticket_price = agency.get("ticket_price", 500)
total_revenue = len(confirmed_bookings) * ticket_price
today_revenue = len(today_bookings) * ticket_price

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
        
        # Revenue chart
        st.markdown("### Revenue Analytics")
        
        revenue_by_date = {}
        for booking in confirmed_bookings:
            date = booking.get("date", "Unknown")
            revenue_by_date[date] = (revenue_by_date.get(date, 0) or 0) + ticket_price
        
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
                    st.markdown(f"₹{ticket_price}")
                    if st.button("👁️ View", key=f"view_{booking.get('booking_id')}"):
                        st.session_state.selected_booking = booking
                        st.rerun()
            
            st.divider()
    
    else:
        st.info("📌 No bookings match your filters")

# =====================================================
# TAB 3: PASSENGERS
# =====================================================
with tab3:
    st.markdown("## Passenger Management")
    
    if confirmed_bookings:
        # Get unique passengers
        passengers = {}
        for booking in confirmed_bookings:
            phone = booking.get("username", "Unknown")
            if phone not in passengers:
                passengers[phone] = {
                    "name": booking.get("passenger_name", "N/A"),
                    "bookings": 0,
                    "last_booking": booking.get("date"),
                    "total_spent": 0
                }
            passengers[phone]["bookings"] += 1
            passengers[phone]["total_spent"] += ticket_price
            passengers[phone]["last_booking"] = max(passengers[phone]["last_booking"], booking.get("date", ""))
        
        # Convert to dataframe
        df_passengers = pd.DataFrame([
            {
                "Username": username,
                "Passenger Name": data["name"],
                "Bookings": data["bookings"],
                "Total Spent": f"₹{data['total_spent']:,}",
                "Last Booking": data["last_booking"]
            }
            for username, data in sorted(passengers.items(), key=lambda x: x[1]["bookings"], reverse=True)
        ])
        
        # Display with pagination
        page_size = 10
        total_pages = (len(df_passengers) + page_size - 1) // page_size
        page = st.selectbox("Page", range(1, total_pages + 1), key="passenger_page")
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        st.dataframe(
            df_passengers.iloc[start_idx:end_idx],
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"Showing {start_idx + 1}-{min(end_idx, len(df_passengers))} of {len(df_passengers)} passengers")
    
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
        st.markdown(f"""
        **Agency Name**: {agency.get('agency_name')}
        
        **Username**: {agency_username}
        
        **Email**: {agency.get('email', 'N/A')}
        
        **Phone**: {agency.get('phone', 'N/A')}
        
        **Created**: {str(agency.get('created_at', 'Unknown'))[:10]}
        """)
    
    with col2:
        st.markdown("### Pricing Settings")
        
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
