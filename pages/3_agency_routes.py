"""
Agency Routes Management
Allows agencies to create, edit, and manage bus routes
Routes are stored as a nested array inside the agency document in agencies_collection.
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

# =====================================================
# HELPER: get / update routes for this agency
# =====================================================
def _get_routes():
    agency_doc = db.agencies_collection.find_one({"username": agency_username})
    return agency_doc.get("routes", []) if agency_doc else []

def _push_route(route_data):
    db.agencies_collection.update_one(
        {"username": agency_username},
        {"$push": {"routes": route_data}}
    )

def _pull_route(source, destination):
    db.agencies_collection.update_one(
        {"username": agency_username},
        {"$pull": {"routes": {"source": source, "destination": destination}}}
    )

def _update_route(source, destination, update_fields):
    db.agencies_collection.update_one(
        {"username": agency_username, "routes.source": source, "routes.destination": destination},
        {"$set": {f"routes.$.{k}": v for k, v in update_fields.items()}}
    )

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

    routes = _get_routes()

    if routes:
        st.success(f"✅ You have {len(routes)} route(s)")

        df_routes = pd.DataFrame([
            {
                "Source": r.get("source"),
                "Destination": r.get("destination"),
                "Departure": r.get("departure_time", "N/A"),
                "Arrival": r.get("arrival_time", "N/A"),
                "Total Seats": r.get("total_seats", 0),
                "Available": r.get("available_seats", 0),
                "Fare (₹)": r.get("fare", 0),
                "Bus Type": r.get("bus_type", "Standard")
            }
            for r in routes
        ])

        st.dataframe(df_routes, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("### Route Details")

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

            if st.button("🗑️ Delete This Route", use_container_width=True, type="secondary"):
                _pull_route(selected_route["source"], selected_route["destination"])
                st.success("✅ Route deleted successfully")
                st.rerun()

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
            source = st.text_input("Source City", placeholder="e.g., Chennai")
            destination = st.text_input("Destination City", placeholder="e.g., Madurai")
            departure_time = st.time_input("Departure Time")
            bus_type = st.selectbox("Bus Type", ["AC Volvo", "Non-AC", "Sleeper AC", "Semi-Sleeper", "Luxury"])

        with col2:
            arrival_time = st.time_input("Arrival Time")
            total_seats = st.number_input("Total Seats", min_value=1, max_value=100, value=40)
            fare = st.number_input("Ticket Fare (₹)", min_value=0, step=50, value=500)

        description = st.text_area("Route Description (Optional)", height=80)

        submitted = st.form_submit_button("➕ Add Route", use_container_width=True, type="primary")

        if submitted:
            if not source or not destination:
                st.error("❌ Source and Destination are required")
            elif source.lower() == destination.lower():
                st.error("❌ Source and Destination cannot be the same")
            else:
                route_data = {
                    "source": source.strip().title(),
                    "destination": destination.strip().title(),
                    "departure_time": str(departure_time),
                    "arrival_time": str(arrival_time),
                    "bus_type": bus_type,
                    "total_seats": int(total_seats),
                    "available_seats": int(total_seats),
                    "fare": int(fare),
                    "description": description,
                    "created_at": datetime.now().isoformat()
                }
                _push_route(route_data)
                st.success("✅ Route added successfully!")
                st.rerun()

# =====================================================
# TAB 3: EDIT ROUTE
# =====================================================
with tab3:
    st.markdown("## Edit Route")

    routes = _get_routes()

    if routes:
        route_labels = [f"{r.get('source')} → {r.get('destination')}" for r in routes]
        route_map = {f"{r.get('source')} → {r.get('destination')}": r for r in routes}

        # Persist selected route index across reruns
        prev_idx = st.session_state.get("edit_route_idx", 0)
        if prev_idx >= len(routes):
            prev_idx = 0

        selected_label = st.selectbox("Select Route to Edit", route_labels, index=prev_idx, key="edit_route_select")
        selected_idx = route_labels.index(selected_label)
        st.session_state.edit_route_idx = selected_idx
        route = routes[selected_idx]

        st.markdown(f"### Editing: {route.get('source')} → {route.get('destination')}")

        with st.form(f"edit_route_form_{selected_idx}"):
            col1, col2 = st.columns(2)

            with col1:
                source = st.text_input("Source City", value=route.get("source", ""), disabled=True)
                destination = st.text_input("Destination City", value=route.get("destination", ""), disabled=True)
                try:
                    dep_val = pd.to_datetime(route.get("departure_time", "00:00")).time()
                except Exception:
                    dep_val = datetime.strptime("08:00", "%H:%M").time()
                departure_time = st.time_input("Departure Time", value=dep_val)
                bus_type = st.selectbox("Bus Type", ["AC Volvo", "Non-AC", "Sleeper AC", "Semi-Sleeper", "Luxury"],
                    index=["AC Volvo", "Non-AC", "Sleeper AC", "Semi-Sleeper", "Luxury"].index(route.get("bus_type", "AC Volvo")))

            with col2:
                try:
                    arr_val = pd.to_datetime(route.get("arrival_time", "00:00")).time()
                except Exception:
                    arr_val = datetime.strptime("14:00", "%H:%M").time()
                arrival_time = st.time_input("Arrival Time", value=arr_val)
                total_seats = st.number_input("Total Seats", min_value=1, max_value=100,
                    value=route.get("total_seats", 40), disabled=True)
                fare = st.number_input("Ticket Fare (₹)", min_value=0, step=50, value=route.get("fare", 500))
                available_seats = st.number_input("Available Seats", min_value=0, max_value=total_seats,
                    value=route.get("available_seats", total_seats))

            description = st.text_area("Route Description", value=route.get("description", ""), height=80)

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("💾 Update Route", use_container_width=True, type="primary")
            with col2:
                if st.form_submit_button("🗑️ Delete Route", use_container_width=True, type="secondary"):
                    _pull_route(route["source"], route["destination"])
                    st.session_state.edit_route_idx = 0
                    st.success("✅ Route deleted successfully")
                    st.rerun()

            if submitted:
                _update_route(route["source"], route["destination"], {
                    "departure_time": str(departure_time),
                    "arrival_time": str(arrival_time),
                    "bus_type": bus_type,
                    "fare": int(fare),
                    "available_seats": int(available_seats),
                    "description": description,
                    "updated_at": datetime.now().isoformat()
                })
                st.success("✅ Route updated successfully!")
                st.rerun()

    else:
        st.info("📌 No routes to edit. Create a route first!")

# =====================================================
# FOOTER
# =====================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85em; margin-top: 30px;">
    <p>Routes are associated with your agency and visible to customers</p>
    <p>Departure and Arrival times are displayed to customers during booking</p>
    <p>Fares and seat availability can be updated anytime</p>
</div>
""", unsafe_allow_html=True)
