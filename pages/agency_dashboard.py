"""
Agency Dashboard
Analytics and management interface for travel agencies
"""

import streamlit as st
import db
import pandas as pd
from datetime import datetime, timedelta

def render_agency_dashboard():
    """Render the agency dashboard"""
    
    st.markdown("### 📊 Agency Dashboard")
    st.markdown("---")
    
    agency_username = st.session_state.get("user")
    if not agency_username:
        st.error("❌ Please login first")
        return
    
    # Get agency details
    agency = db.get_agency(agency_username)
    if not agency:
        st.error("❌ Agency not found")
        return
    
    # Tabs: Overview, Bookings, Analytics, Routes, Settings
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🎫 Bookings", "📊 Analytics", "🛣️ Routes"])
    
    # ==========================================
    # TAB 1: OVERVIEW
    # ==========================================
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        
        # Get statistics
        all_bookings = db.get_bookings_by_agency(agency_username)
        total_bookings = len(all_bookings)
        confirmed_bookings = len([b for b in all_bookings if b.get("status") == "confirmed"])
        total_revenue = confirmed_bookings * 500  # Placeholder calculation
        
        with col1:
            st.metric("Total Bookings", total_bookings)
        with col2:
            st.metric("Confirmed", confirmed_bookings)
        with col3:
            st.metric("Revenue", f"₹{total_revenue:,}")
        with col4:
            st.metric("Vehicles", agency.get("total_vehicles", 0))
        
        st.markdown("---")
        
        # Agency Information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏢 Agency Information")
            st.write(f"**Name:** {agency.get('agency_name', 'N/A')}")
            st.write(f"**Vehicles:** {agency.get('total_vehicles', 0)}")
            st.write(f"**Seats/Vehicle:** {agency.get('seats_per_vehicle', 0)}")
            st.write(f"**Bus Type:** {agency.get('bus_type', 'Standard')}")
        
        with col2:
            st.markdown("#### 📱 WhatsApp Status")
            instance = db.get_whatsapp_instance(agency_username)
            if instance and instance.get("is_connected"):
                st.success(f"✅ Connected\n{instance.get('instance_name')}\n{instance.get('phone_number', 'N/A')}")
            elif instance:
                st.warning(f"🟡 Pending: {instance.get('status')}")
            else:
                st.info("🔴 Not configured")
    
    # ==========================================
    # TAB 2: BOOKINGS
    # ==========================================
    with tab2:
        st.markdown("#### 🎫 Recent Bookings")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            filter_status = st.selectbox("Filter by Status", ["All", "confirmed", "cancelled"])
        with col2:
            filter_date = st.date_input("Filter by Date", value=datetime.now().date())
        
        # Get and filter bookings
        bookings = db.get_bookings_by_agency(agency_username)
        
        if filter_status != "All":
            bookings = [b for b in bookings if b.get("status") == filter_status]
        
        if bookings:
            # Display as table
            booking_data = []
            for b in bookings[:20]:  # Show last 20
                booking_data.append({
                    "Booking ID": b.get("booking_id"),
                    "Route": f"{b.get('source')} → {b.get('destination')}",
                    "Date": b.get("date"),
                    "Seat": b.get("seat"),
                    "Passenger": b.get("passenger_name", "N/A"),
                    "Status": b.get("status", "confirmed")
                })
            
            df = pd.DataFrame(booking_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Export option
            if st.button("📥 Export to CSV", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"bookings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("📌 No bookings found")
    
    # ==========================================
    # TAB 3: ANALYTICS
    # ==========================================
    with tab3:
        st.markdown("#### 📊 Booking Analytics")
        
        bookings = db.get_bookings_by_agency(agency_username)
        
        if bookings:
            # Route statistics
            route_stats = {}
            for b in bookings:
                if b.get("status") == "confirmed":
                    route_key = f"{b.get('source')} → {b.get('destination')}"
                    route_stats[route_key] = route_stats.get(route_key, 0) + 1
            
            if route_stats:
                st.markdown("**Most Popular Routes:**")
                route_df = pd.DataFrame(list(route_stats.items()), columns=["Route", "Bookings"])
                route_df = route_df.sort_values("Bookings", ascending=False)
                st.bar_chart(route_df.set_index("Route"))
            
            # Gender distribution
            gender_stats = {"Male": 0, "Female": 0, "Neutral": 0}
            for b in bookings:
                if b.get("status") == "confirmed":
                    gender = b.get("passenger_gender", "Neutral")
                    if gender in gender_stats:
                        gender_stats[gender] += 1
            
            if sum(gender_stats.values()) > 0:
                st.markdown("**Passenger Gender Distribution:**")
                gender_df = pd.DataFrame(list(gender_stats.items()), columns=["Gender", "Count"])
                st.pie_chart(gender_df.set_index("Gender"))
        else:
            st.info("📌 No bookings data available for analytics")
    
    # ==========================================
    # TAB 4: ROUTES
    # ==========================================
    with tab4:
        st.markdown("#### 🛣️ Manage Routes")
        
        routes = agency.get("routes", [])
        
        if routes:
            st.markdown("**Current Routes:**")
            route_cols = st.columns(2)
            for idx, route in enumerate(routes):
                with route_cols[idx % 2]:
                    st.info(f"{route.get('source')} → {route.get('destination')}")
        else:
            st.warning("⚠️ No routes configured")
        
        st.markdown("---")
        st.markdown("**Add New Route:**")
        
        col1, col2 = st.columns(2)
        with col1:
            source = st.text_input("Source City", placeholder="e.g., Delhi")
        with col2:
            destination = st.text_input("Destination City", placeholder="e.g., Mumbai")
        
        if st.button("➕ Add Route", use_container_width=True):
            if source and destination:
                new_routes = routes + [{"source": source, "destination": destination}]
                result = db.update_agency(agency_username, {
                    "agency_name": agency.get("agency_name"),
                    "routes": new_routes,
                    "total_vehicles": agency.get("total_vehicles"),
                    "seats_per_vehicle": agency.get("seats_per_vehicle"),
                    "bus_type": agency.get("bus_type", "Standard (2x2)")
                })
                if result.get("success"):
                    st.success("✅ Route added successfully")
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('message')}")
            else:
                st.error("❌ Please enter both source and destination")
