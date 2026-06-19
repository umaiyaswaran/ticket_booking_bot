"""
TicketHub - Agency Payment Setup
Agencies configure payment details (bank/UPI/QR) and set route fares with bus timing.
"""

import streamlit as st
import db
from datetime import datetime

st.set_page_config(page_title="Agency Payment Setup", layout="wide", initial_sidebar_state="expanded")

# ── Custom CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

.agency-setup-container {
    font-family: 'Inter', sans-serif;
    max-width: 800px;
    margin: 0 auto;
}

.setup-header {
    text-align: center;
    padding: 28px 20px 20px;
    background: #ffffff;
    border: 1px solid #e2e2e2;
    border-radius: 16px 16px 0 0;
}
.setup-header h1 {
    font-family: 'Inter', sans-serif;
    font-size: 1.6em;
    font-weight: 700;
    color: #000000;
    margin: 0 0 6px 0;
}
.setup-header p {
    color: #5e5e5e;
    font-size: 0.85em;
    margin: 0;
}

.config-card {
    background: #ffffff;
    border: 1px solid #e2e2e2;
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
}
.config-card::before { display: none; }

.section-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.1em;
    font-weight: 700;
    color: #000000;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.fare-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px;
    background: #f3f3f3;
    border: none;
    border-radius: 8px;
    margin: 8px 0;
    transition: all 0.2s ease;
}
.fare-row:hover {
    background: #efefef;
}

.route-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #efefef;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 500;
    color: #000000;
    font-size: 0.88em;
}

.success-msg {
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.25);
    border-radius: 12px;
    padding: 14px 18px;
    color: #10b981;
    font-weight: 500;
    margin: 12px 0;
}

.secure-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #efefef;
    border: none;
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 0.72em;
    color: #5e5e5e;
    font-weight: 500;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)


def render_header():
    st.markdown("""
    <div class="setup-header">
        <h1>Agency Payment Setup</h1>
        <p>Configure payment details and set route fares for your agency</p>
    </div>
    """, unsafe_allow_html=True)


def render_payment_config(agency_username, agency_name):
    """Render payment configuration form."""
    st.markdown('<div class="section-title">🏦 Payment Configuration</div>', unsafe_allow_html=True)
    
    existing = db.get_agency_payment_config(agency_username)
    
    with st.form("payment_config_form"):
        col1, col2 = st.columns(2)
        with col1:
            account_holder = st.text_input(
                "Account Holder Name",
                value=existing.get("account_holder_name", "") if existing else "",
                placeholder="e.g., Travel Agency Pvt Ltd"
            )
            account_number = st.text_input(
                "Bank Account Number",
                value=existing.get("account_number", "") if existing else "",
                placeholder="e.g., 12345678901234"
            )
        with col2:
            ifsc_code = st.text_input(
                "IFSC Code",
                value=existing.get("ifsc_code", "") if existing else "",
                placeholder="e.g., SBIN0001234"
            )
            upi_id = st.text_input(
                "UPI ID",
                value=existing.get("upi_id", "") if existing else "",
                placeholder="e.g., agency@upi"
            )
        
        qr_image = st.file_uploader(
            "Upload QR Code Image (optional)",
            type=["png", "jpg", "jpeg"],
            help="Upload your UPI QR code for customers to scan"
        )
        
        submitted = st.form_submit_button("💾 Save Payment Config", use_container_width=True)
        
        if submitted:
            qr_data = None
            if qr_image:
                import base64
                qr_data = base64.b64encode(qr_image.read()).decode()
            
            result = db.save_agency_payment_config(
                agency_username=agency_username,
                agency_name=agency_name,
                account_holder=account_holder,
                account_number=account_number,
                ifsc_code=ifsc_code,
                upi_id=upi_id,
                qr_image=qr_data
            )
            
            if result["success"]:
                st.markdown('<div class="success-msg">✅ Payment configuration saved successfully!</div>', unsafe_allow_html=True)
                st.rerun()
            else:
                st.error(f"❌ {result['message']}")
    
    # Show existing config summary
    if existing:
        st.markdown("---")
        st.markdown("#### Current Configuration")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Account Holder:** {existing.get('account_holder_name', 'Not set')}")
            st.markdown(f"**Account:** ****{existing.get('account_number', '')[-4:] if existing.get('account_number') else 'XXXX'}")
        with col2:
            st.markdown(f"**IFSC:** {existing.get('ifsc_code', 'Not set')}")
            st.markdown(f"**UPI:** {existing.get('upi_id', 'Not set')}")
        
        if existing.get("qr_image"):
            import base64
            st.markdown("**QR Code:**")
            st.image(base64.b64decode(existing["qr_image"]), width=150)


def render_fare_management(agency_username):
    """Render fare management section."""
    st.markdown('<div class="section-title">💰 Route Fare Management</div>', unsafe_allow_html=True)
    st.markdown("*Set ticket fare, departure/arrival time, and bus number for each route.*")
    
    # Get agency routes
    agency = db.get_agency(agency_username)
    if not agency:
        st.error("Agency profile not found.")
        return
    
    routes = agency.get("routes", [])
    if not routes:
        st.warning("No routes configured. Please add routes in Agency Settings first.")
        return
    
    # Add new fare form
    with st.expander("➕ Add / Update Route Fare", expanded=True):
        with st.form("add_fare_form"):
            route_options = [f"{r['source']} → {r['destination']}" for r in routes]
            selected_route = st.selectbox("Select Route", route_options)
            
            parts = selected_route.split(" → ")
            source, destination = parts[0], parts[1]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                fare = st.number_input("Fare (₹)", min_value=1, max_value=99999, value=650, step=10)
            with col2:
                departure = st.text_input("Departure Time", placeholder="e.g., 08:00 AM")
            with col3:
                arrival = st.text_input("Arrival Time", placeholder="e.g., 02:00 PM")
            
            bus_number = st.text_input("Bus Number", placeholder="e.g., TN-01-AB-1234")
            
            if st.form_submit_button("✅ Save Fare", use_container_width=True):
                result = db.set_route_fare_with_timing(
                    agency_username, source, destination, fare,
                    departure_time=departure, arrival_time=arrival, bus_number=bus_number
                )
                if result["success"]:
                    st.success(f"✅ {result['message']}")
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")
    
    # Show existing fares
    fares = db.get_all_agency_fares(agency_username)
    if fares:
        st.markdown("#### Current Route Fares")
        for fare_item in fares:
            route_key = f"{fare_item['source']} → {fare_item['destination']}"
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 0.5])
            with col1:
                st.markdown(f"**{route_key}**")
            with col2:
                st.markdown(f"₹{fare_item.get('fare', 0)}")
            with col3:
                st.markdown(f"🕐 {fare_item.get('departure_time', '-')}")
            with col4:
                st.markdown(f"🕐 {fare_item.get('arrival_time', '-')}")
            with col5:
                if fare_item.get("bus_number"):
                    st.markdown(f"🚌 {fare_item['bus_number']}")
            
            if st.button("🗑️", key=f"del_fare_{fare_item['source']}_{fare_item['destination']}"):
                db.delete_route_fare(agency_username, fare_item["source"], fare_item["destination"])
                st.rerun()
            
            st.markdown("---")
    else:
        st.info("No fares configured yet. Add your first route fare above.")


def main():
    render_header()
    
    # Check if user is logged in as agency
    if "user" not in st.session_state or not st.session_state.get("logged_in"):
        st.error("🔒 Please login as an agency to access this page.")
        return
    
    if st.session_state.get("role") != "Agency":
        st.error("🔒 Only agencies can access this page.")
        return
    
    agency_username = st.session_state.user

    from agency_sidebar import render_agency_sidebar
    render_agency_sidebar()
    
    # Get agency info
    agency = db.get_agency(agency_username)
    if not agency:
        st.error("Agency profile not found.")
        return
    
    agency_name = agency.get("agency_name", agency_username)
    
    st.markdown(f"**Agency:** {agency_name}")
    st.markdown("---")
    
    # Tabs
    tab1, tab2 = st.tabs(["🏦 Payment Setup", "💰 Fare Management"])
    
    with tab1:
        render_payment_config(agency_username, agency_name)
    
    with tab2:
        render_fare_management(agency_username)
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding:16px;">
        <div class="secure-badge">🔒 All payment data is encrypted and stored securely</div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
else:
    main()
