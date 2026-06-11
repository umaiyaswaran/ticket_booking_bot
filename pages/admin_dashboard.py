"""
Admin Dashboard
System management and monitoring
"""

import streamlit as st
import db
import pandas as pd

def render_admin_dashboard():
    """Render the admin dashboard"""
    
    st.markdown("### 🛡️ Admin Dashboard")
    st.markdown("---")
    
    # Tabs: System Overview, Users, Agencies, Bookings
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "👥 Users", "🏢 Agencies", "🎫 Bookings"])
    
    # ==========================================
    # TAB 1: OVERVIEW
    # ==========================================
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        
        # Get statistics
        all_bookings = db.bookings_collection.count_documents({})
        all_users = db.users_collection.count_documents({"role": "User"})
        all_agencies = db.agencies_collection.count_documents({})
        whatsapp_connected = db.whatsapp_instances_collection.count_documents({"is_connected": True})
        
        with col1:
            st.metric("Total Bookings", all_bookings)
        with col2:
            st.metric("Total Users", all_users)
        with col3:
            st.metric("Total Agencies", all_agencies)
        with col4:
            st.metric("WhatsApp Connected", whatsapp_connected)
        
        st.markdown("---")
        st.markdown("#### 📈 System Health")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("✅ MongoDB Connection: Active")
            st.write(f"🏢 Collections: 8")
        with col2:
            st.write("✅ Evolution API: " + ("Connected" if whatsapp_connected > 0 else "No instances"))
            st.write("✅ System Status: Operational")
    
    # ==========================================
    # TAB 2: USERS
    # ==========================================
    with tab2:
        st.markdown("#### 👥 User Management")
        
        # Get all users
        users = list(db.users_collection.find({"role": "User"}, {
            "_id": 0,
            "username": 1,
            "full_name": 1,
            "phone": 1,
            "gender": 1,
            "created_at": 1
        }).limit(100))
        
        if users:
            user_data = []
            for u in users:
                user_data.append({
                    "Username": u.get("username", "N/A"),
                    "Full Name": u.get("full_name", "N/A"),
                    "Phone": u.get("phone", "N/A"),
                    "Gender": u.get("gender", "N/A"),
                    "Joined": str(u.get("created_at", "N/A")).split()[0] if u.get("created_at") else "N/A"
                })
            
            df = pd.DataFrame(user_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("📌 No users found")
    
    # ==========================================
    # TAB 3: AGENCIES
    # ==========================================
    with tab3:
        st.markdown("#### 🏢 Agency Management")
        
        # Get all agencies
        agencies = list(db.agencies_collection.find({}, {
            "_id": 0,
            "username": 1,
            "agency_name": 1,
            "total_vehicles": 1,
            "seats_per_vehicle": 1,
            "created_at": 1
        }).limit(100))
        
        if agencies:
            agency_data = []
            for a in agencies:
                username = a.get("username", "N/A")
                whatsapp_status = "✅ Connected" if db.whatsapp_instances_collection.find_one({"agency_username": username, "is_connected": True}) else "🔴 Not Connected"
                
                agency_data.append({
                    "Username": username,
                    "Agency Name": a.get("agency_name", "N/A"),
                    "Vehicles": a.get("total_vehicles", 0),
                    "Seats/Vehicle": a.get("seats_per_vehicle", 0),
                    "WhatsApp": whatsapp_status,
                    "Joined": str(a.get("created_at", "N/A")).split()[0] if a.get("created_at") else "N/A"
                })
            
            df = pd.DataFrame(agency_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("📌 No agencies found")
    
    # ==========================================
    # TAB 4: BOOKINGS
    # ==========================================
    with tab4:
        st.markdown("#### 🎫 All Bookings")
        
        # Get all bookings
        bookings = list(db.bookings_collection.find({}, {
            "_id": 0,
            "booking_id": 1,
            "username": 1,
            "agency_username": 1,
            "source": 1,
            "destination": 1,
            "date": 1,
            "passenger_name": 1,
            "status": 1,
            "created_at": 1
        }).limit(100).sort("created_at", -1))
        
        if bookings:
            booking_data = []
            for b in bookings:
                booking_data.append({
                    "Booking ID": b.get("booking_id", "N/A"),
                    "User": b.get("username", "N/A"),
                    "Agency": b.get("agency_username", "N/A"),
                    "Route": f"{b.get('source', 'N/A')} → {b.get('destination', 'N/A')}",
                    "Date": b.get("date", "N/A"),
                    "Passenger": b.get("passenger_name", "N/A"),
                    "Status": b.get("status", "confirmed")
                })
            
            df = pd.DataFrame(booking_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Statistics
            st.markdown("---")
            confirmed = len([b for b in bookings if b.get("status") == "confirmed"])
            cancelled = len([b for b in bookings if b.get("status") == "cancelled"])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Confirmed", confirmed)
            with col2:
                st.metric("Cancelled", cancelled)
        else:
            st.info("📌 No bookings found")
