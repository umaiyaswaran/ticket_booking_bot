"""
Agency Routes Management
Allows agencies to create, edit, and manage bus routes
"""

import streamlit as st
import db
import pandas as pd
from datetime import datetime

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Routes Management - TicketHub Agency",
    page_icon="🛣️",
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

# =====================================================
# PAGE TITLE
# =====================================================
st.markdown("# 🛣️ Routes Management")
st.markdown(f"**Agency**: {agency_username}")
st.divider()

# =====================================================
# TABS
# =====================================================
tab1, tab2, tab3 = st.tabs(["📋 View Routes", "➕ Add Route", "✏️ Edit Route"])

# =====================================================
# TAB 1: VIEW ROUTES
# =====================================================
with tab1:
    st.markdown("## Your Routes")
    
    # Get all routes for this agency
    routes = list(db.buses_collection.find({"agency_username": agency_username}))
    
    if routes:
        st.success(f"✅ You have {len(routes)} route(s)")
        
        # Create dataframe
        df_routes = pd.DataFrame([
            {
                "ID": route.get("_id"),
                "Source": route.get("source"),
                "Destination": route.get("destination"),
                "Departure": route.get("departure_time", "N/A"),
                "Arrival": route.get("arrival_time", "N/A"),
                "Total Seats": route.get("total_seats", 0),
                "Available": route.get("available_seats", 0),
                "Fare (₹)": route.get("fare", 0),
                "Bus Type": route.get("bus_type", "Standard")
            }
            for route in routes
        ])
        
        st.dataframe(df_routes, use_container_width=True, hide_index=True)
        
        st.divider()
        st.markdown("### Route Details")
        
        # Select route to view details
        selected_route_name = st.selectbox(
            "Select a route to view details",
            [f"{r.get('source')} → {r.get('destination')}" for r in routes]
        )
        
        selected_route = next(
            (r for r in routes if f"{r.get('source')} → {r.get('destination')}" == selected_route_name),
            None
        )
        
        if selected_route:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                **Source**: {selected_route.get('source')}
                
                **Destination**: {selected_route.get('destination')}
                
                **Bus Type**: {selected_route.get('bus_type', 'Standard')}
                """)
            
            with col2:
                st.markdown(f"""
                **Departure**: {selected_route.get('departure_time', 'N/A')}
                
                **Arrival**: {selected_route.get('arrival_time', 'N/A')}
                
                **Fare**: ₹{selected_route.get('fare', 0)}
                """)
            
            with col3:
                st.markdown(f"""
                **Total Seats**: {selected_route.get('total_seats', 0)}
                
                **Available Seats**: {selected_route.get('available_seats', 0)}
                
                **Booked**: {selected_route.get('total_seats', 0) - selected_route.get('available_seats', 0)}
                """)
            
            st.divider()
            
            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✏️ Edit This Route", use_container_width=True):
                    st.session_state.edit_route_id = str(selected_route.get("_id"))
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Delete This Route", use_container_width=True, type="secondary"):
                    if st.button("⚠️ Confirm Delete", key="confirm_delete"):
                        try:
                            db.buses_collection.delete_one({"_id": selected_route.get("_id")})
                            st.success("✅ Route deleted successfully")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
    
    else:
        st.info("📌 No routes added yet. Create your first route!")

# =====================================================
# TAB 2: ADD ROUTE
# =====================================================
with tab2:
    st.markdown("## Add New Route")
    
    with st.form("add_route_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            source = st.text_input(
                "Source City",
                placeholder="e.g., Chennai",
                help="Starting point of the route"
            )
            destination = st.text_input(
                "Destination City",
                placeholder="e.g., Madurai",
                help="Ending point of the route"
            )
            departure_time = st.time_input(
                "Departure Time",
                help="When the bus departs"
            )
            bus_type = st.selectbox(
                "Bus Type",
                ["AC Volvo", "Non-AC", "Sleeper AC", "Semi-Sleeper", "Luxury"],
                help="Type of bus for this route"
            )
        
        with col2:
            arrival_time = st.time_input(
                "Arrival Time",
                help="When the bus arrives at destination"
            )
            total_seats = st.number_input(
                "Total Seats",
                min_value=1,
                max_value=100,
                value=40,
                help="Total number of seats in the bus"
            )
            fare = st.number_input(
                "Ticket Fare (₹)",
                min_value=0,
                step=50,
                value=500,
                help="Price per ticket"
            )
        
        st.divider()
        st.markdown("**Route Description** (Optional)")
        description = st.text_area(
            "Add any additional information about this route",
            placeholder="e.g., Route includes AC facility, Water provided, etc.",
            height=80
        )
        
        st.divider()
        
        submitted = st.form_submit_button("➕ Add Route", use_container_width=True, type="primary")
        
        if submitted:
            # Validation
            if not source or not destination:
                st.error("❌ Source and Destination are required")
            elif source.lower() == destination.lower():
                st.error("❌ Source and Destination cannot be the same")
            elif not fare or fare <= 0:
                st.error("❌ Fare must be greater than 0")
            else:
                try:
                    route_data = {
                        "agency_username": agency_username,
                        "source": source.title(),
                        "destination": destination.title(),
                        "departure_time": str(departure_time),
                        "arrival_time": str(arrival_time),
                        "bus_type": bus_type,
                        "total_seats": int(total_seats),
                        "available_seats": int(total_seats),
                        "fare": int(fare),
                        "description": description,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                    
                    result = db.buses_collection.insert_one(route_data)
                    
                    st.success(f"✅ Route added successfully!")
                    st.markdown(f"**Route ID**: `{result.inserted_id}`")
                    st.info("You can now create bookings for this route")
                    
                    # Reset form
                    st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error adding route: {str(e)}")

# =====================================================
# TAB 3: EDIT ROUTE
# =====================================================
with tab3:
    st.markdown("## Edit Route")
    
    # Get all routes
    routes = list(db.buses_collection.find({"agency_username": agency_username}))
    
    if routes:
        # Select route to edit
        route_options = {f"{r.get('source')} → {r.get('destination')} ({str(r.get('_id'))[:8]})": r for r in routes}
        selected = st.selectbox("Select Route to Edit", list(route_options.keys()))
        
        route = route_options[selected]
        
        st.markdown(f"### Editing: {route.get('source')} → {route.get('destination')}")
        
        with st.form("edit_route_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                source = st.text_input(
                    "Source City",
                    value=route.get("source", ""),
                    disabled=True
                )
                destination = st.text_input(
                    "Destination City",
                    value=route.get("destination", ""),
                    disabled=True
                )
                departure_time = st.time_input(
                    "Departure Time",
                    value=pd.to_datetime(route.get("departure_time", "00:00")).time()
                )
                bus_type = st.selectbox(
                    "Bus Type",
                    ["AC Volvo", "Non-AC", "Sleeper AC", "Semi-Sleeper", "Luxury"],
                    index=["AC Volvo", "Non-AC", "Sleeper AC", "Semi-Sleeper", "Luxury"].index(route.get("bus_type", "AC Volvo"))
                )
            
            with col2:
                arrival_time = st.time_input(
                    "Arrival Time",
                    value=pd.to_datetime(route.get("arrival_time", "00:00")).time()
                )
                total_seats = st.number_input(
                    "Total Seats",
                    min_value=1,
                    max_value=100,
                    value=route.get("total_seats", 40),
                    disabled=True,
                    help="Cannot change total seats for existing route"
                )
                fare = st.number_input(
                    "Ticket Fare (₹)",
                    min_value=0,
                    step=50,
                    value=route.get("fare", 500)
                )
                available_seats = st.number_input(
                    "Available Seats",
                    min_value=0,
                    max_value=total_seats,
                    value=route.get("available_seats", total_seats)
                )
            
            st.divider()
            st.markdown("**Route Description**")
            description = st.text_area(
                "Route information",
                value=route.get("description", ""),
                height=80
            )
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button("💾 Update Route", use_container_width=True, type="primary")
            
            with col2:
                if st.form_submit_button("🗑️ Delete Route", use_container_width=True, type="secondary"):
                    try:
                        db.buses_collection.delete_one({"_id": route.get("_id")})
                        st.success("✅ Route deleted successfully")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            if submitted:
                try:
                    update_data = {
                        "departure_time": str(departure_time),
                        "arrival_time": str(arrival_time),
                        "bus_type": bus_type,
                        "fare": int(fare),
                        "available_seats": int(available_seats),
                        "description": description,
                        "updated_at": datetime.now()
                    }
                    
                    db.buses_collection.update_one(
                        {"_id": route.get("_id")},
                        {"$set": update_data}
                    )
                    
                    st.success(f"✅ Route updated successfully!")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error updating route: {str(e)}")
    
    else:
        st.info("📌 No routes to edit. Create a route first!")

# =====================================================
# FOOTER
# =====================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85em; margin-top: 30px;">
    <p>💡 Routes are associated with your agency and visible to customers</p>
    <p>📅 Departure and Arrival times are displayed to customers during booking</p>
    <p>💰 Fares and seat availability can be updated anytime</p>
</div>
""", unsafe_allow_html=True)
