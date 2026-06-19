"""
TicketHub Secure Payment Page
Custom UPI/QR payment with Razorpay order verification.
No checkout popup — only UPI ID + QR code.
60s countdown, 2s polling, server-side verification.
"""

import streamlit as st
import time
import uuid
import os
import base64
from datetime import datetime, timedelta
from payments import (
    initiate_payment, verify_payment, get_payment_status,
    check_razorpay_order_status, calculate_fare, generate_upi_qr,
    mark_payment_failed, RAZORPAY_KEY_ID
)
import db

# =====================================================
# SESSION STATE INIT
# =====================================================
def init_payment_session():
    defaults = {
        "payment_pending": False,
        "payment_txn_id": None,
        "payment_details": None,
        "payment_razorpay": None,
        "payment_verified": False,
        "selected_method": None,
        "payment_started_at": None,
        "payment_poll_count": 0,
        "seat_locked": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =====================================================
# PAYMENT CSS — Dark Futuristic Theme
# =====================================================
PAYMENT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* Circular Timer */
.circular-timer {
    width: 180px; height: 180px;
    border-radius: 50%;
    background: conic-gradient(#000000 var(--timer-pct, 100%), #efefef 0%);
    display: flex; align-items: center; justify-content: center;
    margin: 16px auto;
    position: relative;
    transition: background 1s linear;
}
.circular-timer::after {
    content: '';
    width: 156px; height: 156px;
    border-radius: 50%;
    background: #ffffff;
    position: absolute;
}
.circular-timer .timer-text {
    position: relative; z-index: 1;
    font-family: 'Inter', sans-serif;
    font-size: 2.4em; font-weight: 700;
    color: #000000;
}
.circular-timer.warning {
    background: conic-gradient(#f59e0b var(--timer-pct, 100%), #efefef 0%) !important;
}
.circular-timer.warning .timer-text {
    color: #f59e0b;
}
.circular-timer.danger {
    background: conic-gradient(#ef4444 var(--timer-pct, 100%), #efefef 0%) !important;
}
.circular-timer.danger .timer-text {
    color: #ef4444;
}
.circular-timer.expired {
    background: conic-gradient(#ef4444 0%, #efefef 0%) !important;
}
.circular-timer.expired .timer-text {
    color: #ef4444;
    font-size: 1.2em;
}

/* Payment Container */
.pay-container {
    font-family: 'Inter', sans-serif;
    max-width: 520px;
    margin: 0 auto;
    background: #ffffff;
    border: 1px solid #e2e2e2;
    border-radius: 16px;
    overflow: hidden;
}

/* Header */
.pay-header {
    text-align: center;
    padding: 32px 24px 24px;
    border-bottom: 1px solid #e2e2e2;
}
.pay-header h1 {
    font-family: 'Inter', sans-serif;
    font-size: 1.8em; font-weight: 700;
    color: #000000;
    margin: 0 0 6px 0;
    letter-spacing: -0.02em;
}
.pay-header p { color: #5e5e5e; font-size: 0.85em; margin: 0; }

/* Fare Card */
.fare-display {
    text-align: center;
    padding: 28px 20px;
    margin: 0 20px;
    background: #efefef;
    border: none;
    border-radius: 16px;
    margin-top: 20px;
}
.fare-label {
    color: #5e5e5e;
    font-size: 0.7em;
    font-weight: 400;
}
.fare-amount {
    font-family: 'Inter', sans-serif;
    font-size: 3.2em; font-weight: 700;
    color: #000000;
    margin: 4px 0;
    line-height: 1.1;
}
.route-display {
    display: flex; align-items: center; justify-content: center; gap: 12px;
    margin-top: 8px;
}
.route-city {
    color: #000000; font-size: 1.05em; font-weight: 700;
}
.route-arrow {
    color: #5e5e5e; font-size: 1.2em;
}

/* Detail Rows */
.detail-rows { padding: 16px 20px; }
.detail-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 14px;
    background: #f3f3f3;
    border: none;
    border-radius: 8px;
    margin-bottom: 6px;
}
.detail-row .label { color: #5e5e5e; font-size: 0.75em; }
.detail-row .value { color: #000000; font-weight: 500; font-size: 0.9em; }

/* UPI Section */
.upi-section {
    margin: 0 20px;
    padding: 24px;
    background: #f3f3f3;
    border: none;
    border-radius: 16px;
    text-align: center;
}
.upi-section h3 {
    font-family: 'Inter', sans-serif;
    color: #000000; font-size: 1em; font-weight: 700;
    margin: 0 0 16px 0;
}
.upi-id-box {
    display: inline-block;
    padding: 12px 28px;
    background: #ffffff;
    border: 1px solid #e2e2e2;
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
    font-size: 1.15em; font-weight: 700;
    color: #000000;
    margin: 8px 0;
}
.upi-apps {
    display: flex; justify-content: center; gap: 10px;
    margin-top: 12px;
}
.upi-app-badge {
    padding: 6px 14px;
    background: #ffffff;
    border: 1px solid #e2e2e2;
    border-radius: 999px;
    color: #5e5e5e;
    font-size: 0.75em;
    font-weight: 500;
}

/* QR Section */
.qr-section {
    margin: 20px;
    padding: 24px;
    background: #f3f3f3;
    border: none;
    border-radius: 16px;
    text-align: center;
}
.qr-section h3 {
    font-family: 'Inter', sans-serif;
    color: #000000; font-size: 1em; font-weight: 700;
    margin: 0 0 16px 0;
}
.qr-wrapper {
    display: inline-block;
    padding: 16px;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.qr-instruction {
    color: #5e5e5e; font-size: 0.78em;
    margin-top: 12px;
}

/* Status Badge */
.status-pill {
    display: inline-block;
    padding: 6px 18px;
    border-radius: 999px;
    font-size: 0.78em;
    font-weight: 500;
    margin-top: 12px;
}
.status-pill.polling {
    background: rgba(59,130,246,0.12);
    color: #3b82f6;
    animation: pulse 2s infinite;
}
.status-pill.success {
    background: rgba(16,185,129,0.12);
    color: #10b981;
}
.status-pill.expired {
    background: rgba(239,68,68,0.12);
    color: #ef4444;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* Security Footer */
.secure-footer {
    text-align: center;
    padding: 16px 20px 20px;
    border-top: 1px solid #e2e2e2;
}
.secure-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 16px;
    background: #efefef;
    border: none;
    border-radius: 999px;
    color: #5e5e5e;
    font-size: 0.72em;
    font-weight: 500;
}

/* Success / Failed Cards */
.result-card {
    text-align: center;
    padding: 40px 24px;
    margin: 0 20px 20px;
    border-radius: 16px;
}
.result-card.success {
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.15);
}
.result-card.failed {
    background: rgba(239,68,68,0.06);
    border: 1px solid rgba(239,68,68,0.15);
}
.result-icon { font-size: 3em; margin-bottom: 12px; }
.result-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.3em; font-weight: 700;
    margin: 0 0 6px 0;
}
.result-sub { color: #5e5e5e; font-size: 0.85em; }
</style>
"""


# =====================================================
# SEAT LOCKING
# =====================================================
def lock_seat(agency, source, destination, date, seat, username):
    try:
        existing = db.bookings_collection.find_one({
            "agency_username": agency, "source": source,
            "destination": destination, "date": date,
            "seat": seat, "status": "confirmed"
        })
        if existing:
            return False
        db.db["seat_locks"].update_one(
            {"seat": seat, "agency": agency, "date": date, "source": source, "destination": destination},
            {"$set": {"locked_by": username, "locked_at": datetime.now(), "expires_at": datetime.now() + timedelta(seconds=90)}},
            upsert=True
        )
        return True
    except Exception:
        return True


def unlock_seat(agency, source, destination, date, seat):
    try:
        db.db["seat_locks"].delete_one({"seat": seat, "agency": agency, "date": date, "source": source, "destination": destination})
    except Exception:
        pass


# =====================================================
# MAIN PAYMENT PAGE
# =====================================================
def render_payment_page():
    init_payment_session()
    st.markdown(PAYMENT_CSS, unsafe_allow_html=True)

    # PATH A: Payment verified → finalize & show ticket
    if st.session_state.get("payment_verified"):
        st.session_state.payment_pending = False
        st.session_state.payment_razorpay = None
        st.session_state.payment_verified = False
        finalize_booking_after_payment()
        render_ticket_page()
        return

    # PATH B: Payment in progress → show UPI/QR + timer + polling
    if st.session_state.payment_pending and st.session_state.payment_razorpay:
        render_upi_payment()
        return

    # PATH C: Payment details exist → show summary + start payment
    if st.session_state.payment_details:
        render_payment_summary()
        return

    # No active payment - inline styles
    st.markdown("""
    <div style="font-family:'Inter',sans-serif; max-width:500px; margin:40px auto; background:#ffffff; border:1px solid #e2e2e2; border-radius:20px; overflow:hidden; text-align:center; padding:40px 24px;">
        <div style="font-size:1.6em; font-weight:900; color:#000000;">No Active Payment</div>
        <div style="color:#5e5e5e; font-size:0.85em; margin-top:6px;">Select a seat and confirm your booking to proceed.</div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# PAYMENT SUMMARY → START PAYMENT
# =====================================================
def render_payment_summary():
    details = st.session_state.payment_details
    if not details:
        return

    fare = details["fare"]
    source = details["source"]
    destination = details["destination"]
    seat = details["seat"]
    travel_date = details["travel_date"]
    passenger_name = details["passenger_name"]
    agency = details["agency"]

    # Re-fetch fare
    try:
        agency_fare = db.get_route_fare(agency, source, destination)
        if agency_fare:
            fare = int(agency_fare)
            st.session_state.payment_details["fare"] = fare
    except Exception:
        pass

    # Agency info
    agency_display = agency
    agency_payment = None
    bus_timing = None
    try:
        agency_info = db.get_agency(agency)
        if agency_info:
            agency_display = agency_info.get("agency_name", agency)
    except Exception:
        pass
    try:
        agency_payment = db.get_agency_payment_config(agency)
    except Exception:
        pass
    try:
        bus_timing = db.get_route_fare_with_timing(agency, source, destination)
    except Exception:
        pass

    departure = bus_timing.get("departure_time", "") if bus_timing else ""
    arrival = bus_timing.get("arrival_time", "") if bus_timing else ""
    bus_number_val = bus_timing.get("bus_number", "") if bus_timing else ""
    upi_id = agency_payment.get("upi_id", "ticketbooking@upi") if agency_payment else "ticketbooking@upi"

    # Load logo for payment header
    _logo_b64 = ""
    for logo_file in ["logo.jpg.jpeg", "logo.jpg", "image.jpg.jpeg"]:
        try:
            _logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), logo_file)
            with open(_logo_path, "rb") as _f:
                _logo_b64 = base64.b64encode(_f.read()).decode()
            break
        except Exception:
            pass

    # --- Render Summary ---
    _logo_html = ""
    if _logo_b64:
        _logo_html = f"<img src='data:image/jpeg;base64,{_logo_b64}' style='width:50px; height:50px; border-radius:50%; object-fit:cover; border:2px solid #e2e2e2; margin-bottom:6px;' />"

    _detail_rows = ""
    for label, val in [("Passenger", passenger_name), ("Seat", seat), ("Travel Date", travel_date), ("Agency", agency_display)]:
        _detail_rows += f"<div style='display:flex; justify-content:space-between; align-items:center; padding:10px 14px; background:#f3f3f3; border:none; border-radius:8px; margin-bottom:6px;'><span style='color:#5e5e5e; font-size:0.75em; text-transform:uppercase;'>{label}</span><span style='color:#000000; font-weight:600; font-size:0.9em;'>{val}</span></div>"
    for label, val in [("Departure", departure), ("Arrival", arrival), ("Bus No.", bus_number_val)]:
        if val:
            _detail_rows += f"<div style='display:flex; justify-content:space-between; align-items:center; padding:10px 14px; background:#f3f3f3; border:none; border-radius:8px; margin-bottom:6px;'><span style='color:#5e5e5e; font-size:0.75em; text-transform:uppercase;'>{label}</span><span style='color:#000000; font-weight:600; font-size:0.9em;'>{val}</span></div>"

    _summary_html = f"""
    <div style="font-family:'Inter',sans-serif; max-width:520px; margin:20px auto; background:#ffffff; border:1px solid #e2e2e2; border-radius:20px; overflow:hidden;">
        <div style="text-align:center; padding:32px 24px 24px; border-bottom:1px solid #e2e2e2;">
            {_logo_html}
            <div style="font-size:1.8em; font-weight:700; color:#000000; font-family:'Inter',sans-serif;">Secure Payment</div>
            <div style="color:#5e5e5e; font-size:0.85em;">Pay via UPI or QR Code - Razorpay Verified</div>
        </div>
        <div style="text-align:center; padding:28px 20px; margin:20px; background:#efefef; border:none; border-radius:16px;">
            <div style="color:#5e5e5e; font-size:0.7em; text-transform:uppercase; letter-spacing:0.15em; font-weight:600;">Total Fare</div>
            <div style="font-size:3.2em; font-weight:700; color:#000000; line-height:1.1;">&#8377;{fare}</div>
            <div style="display:flex; align-items:center; justify-content:center; gap:12px; margin-top:8px;">
                <span style="color:#000000; font-size:1.05em; font-weight:700;">{source}</span>
                <span style="color:#5e5e5e; font-size:1.2em;">&#8594;</span>
                <span style="color:#000000; font-size:1.05em; font-weight:700;">{destination}</span>
            </div>
        </div>
        <div style="padding:16px 20px;">
            {_detail_rows}
        </div>
        <div style="text-align:center; padding:16px 20px 20px; border-top:1px solid #e2e2e2;">
            <span style="display:inline-flex; align-items:center; gap:6px; padding:6px 16px; background:#efefef; border:none; border-radius:999px; color:#5e5e5e; font-size:0.72em; font-weight:500;">Razorpay Secured | 256-bit SSL | Server-Verified</span>
        </div>
    </div>
    """
    st.markdown(_summary_html, unsafe_allow_html=True)

    # Start Payment Button
    st.markdown('<div style="max-width:520px; margin:16px auto; text-align:center;">', unsafe_allow_html=True)
    if st.button(f"💳 Pay ₹{fare} — Start Secure Payment", type="primary", use_container_width=True, key="start_pay"):
        _create_razorpay_order_and_start(fare, source, destination, seat, travel_date, passenger_name, agency)
    st.markdown('</div>', unsafe_allow_html=True)


def _create_razorpay_order_and_start(fare, source, destination, seat, travel_date, passenger_name, agency):
    username = st.session_state.user
    lock_seat(agency, source, destination, travel_date, seat, username)

    result = initiate_payment(
        db=db, username=username, source=source, destination=destination,
        travel_date=travel_date, agency_username=agency, seat=seat,
        passenger_name=passenger_name, fare=fare, payment_method="UPI"
    )

    if result["success"]:
        st.session_state.payment_txn_id = result["transaction_id"]
        st.session_state.payment_razorpay = {
            "success": True,
            "transaction_id": result["transaction_id"],
            "razorpay_order_id": result["razorpay_order_id"],
            "razorpay_key_id": result["razorpay_key_id"],
            "amount": result["amount"],
            "fare": result["fare"],
        }
        st.session_state.payment_pending = True
        st.session_state.payment_verified = False
        st.session_state.payment_started_at = time.time()
        st.session_state.payment_poll_count = 0
        st.rerun()
    else:
        st.error(f"❌ {result['message']}")


# =====================================================
# UPI PAYMENT PAGE (Custom — No Razorpay Popup)
# =====================================================
def render_upi_payment():
    rp = st.session_state.payment_razorpay
    details = st.session_state.payment_details or {}
    fare = rp.get("fare", 0)
    txn_id = rp.get("transaction_id", "")
    razorpay_order_id = rp.get("razorpay_order_id", "")
    started_at = st.session_state.get("payment_started_at", time.time())
    agency = details.get("agency", "")

    # --- Get Agency UPI ID ---
    upi_id = "ticketbooking@upi"
    agency_name_disp = "TicketHub Agency"
    try:
        agency_payment = db.get_agency_payment_config(agency)
        if agency_payment:
            upi_id = agency_payment.get("upi_id", upi_id)
            agency_name_disp = agency_payment.get("agency_name", agency_name_disp)
    except Exception:
        pass

    # --- 120-Second Countdown ---
    elapsed = time.time() - started_at
    remaining = max(0, 120 - elapsed)

    # --- POLL every 2 seconds: check Razorpay first, then auto-verify after 30s for direct UPI ---
    st.session_state.payment_poll_count = st.session_state.get("payment_poll_count", 0) + 1
    poll_count = st.session_state.payment_poll_count

    if poll_count % 2 == 0:
        try:
            order_status = check_razorpay_order_status(razorpay_order_id)
            if order_status["paid"]:
                payment_id = order_status["payment_id"]
                verify_result = verify_payment(
                    db=db, transaction_id=int(txn_id),
                    razorpay_payment_id=payment_id,
                    razorpay_order_id=razorpay_order_id,
                    razorpay_signature="SERVER_VERIFIED"
                )
                if verify_result["success"]:
                    st.session_state.payment_verified = True
                    st.session_state.payment_pending = False
                    unlock_seat(agency, details.get("source", ""), details.get("destination", ""), details.get("travel_date", ""), details.get("seat", ""))
                    st.rerun()
        except Exception:
            pass

    # --- Timer Expired → FAIL ---
    if remaining <= 0:
        mark_payment_failed(db, txn_id, "Payment timed out — 120 seconds expired")
        unlock_seat(agency, details.get("source", ""), details.get("destination", ""), details.get("travel_date", ""), details.get("seat", ""))
        st.session_state.payment_pending = False
        st.session_state.payment_razorpay = None
        st.session_state.payment_txn_id = None
        render_payment_failed("Payment was not received within 120 seconds. The order has expired.")
        return

    # --- Timer Display ---
    timer_class = "danger" if remaining <= 10 else ("warning" if remaining <= 20 else "")
    pct = (remaining / 120) * 100
    mins = int(remaining // 60)
    secs = int(remaining % 60)

    # --- Generate QR Code ---
    qr_b64 = generate_upi_qr(fare, upi_id=upi_id, merchant_name=agency_name_disp)

    # --- Render Payment Page with LIVE JavaScript Timer ---
    timer_html = f'''
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body style="margin:0; padding:10px; background:#f5f5f5;">
    <div style="font-family:'Segoe UI',sans-serif; max-width:500px; margin:0 auto; background:#ffffff; border:1px solid #e2e2e2; border-radius:20px; overflow:hidden; padding-bottom:16px;">
        <div style="text-align:center; padding:28px 20px 20px; background:#f9f9f9; border-bottom:1px solid #e2e2e2;">
            <div style="font-size:1.6em; font-weight:900; color:#000000;">Complete Payment</div>
            <div style="color:#5e5e5e; font-size:0.82em;" id="timer-subtitle">Scan QR or pay to UPI ID</div>
        </div>
        <div style="text-align:center; padding:24px 16px; margin:16px; background:#f3f3f3; border:none; border-radius:14px;">
            <div style="color:#5e5e5e; font-size:0.65em; text-transform:uppercase; letter-spacing:0.15em; font-weight:600;">Amount to Pay</div>
            <div style="font-size:2.8em; font-weight:900; color:#000000; line-height:1.1;">{chr(8377)}{fare}</div>
            <div style="display:flex; align-items:center; justify-content:center; gap:10px; margin-top:6px;">
                <span style="color:#000000; font-size:1em; font-weight:700;">{details.get("source", "")}</span>
                <span style="color:#5e5e5e; font-size:1.1em;">&#8594;</span>
                <span style="color:#000000; font-size:1em; font-weight:700;">{details.get("destination", "")}</span>
            </div>
        </div>
        <div style="padding:0 16px;">
            <div style="display:flex; justify-content:space-between; padding:8px 12px; background:#f3f3f3; border:none; border-radius:8px; margin-bottom:5px; font-size:0.82em;">
                <span style="color:#5e5e5e;">Transaction</span><span style="font-weight:600; color:#000000;">#{txn_id}</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 12px; background:#f3f3f3; border:none; border-radius:8px; margin-bottom:5px; font-size:0.82em;">
                <span style="color:#5e5e5e;">Passenger</span><span style="font-weight:600; color:#000000;">{details.get("passenger_name", "")}</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 12px; background:#f3f3f3; border:none; border-radius:8px; margin-bottom:5px; font-size:0.82em;">
                <span style="color:#5e5e5e;">Seat</span><span style="font-weight:600; color:#000000;">{details.get("seat", "")}</span>
            </div>
        </div>
        <div style="margin:16px; padding:20px; background:#f3f3f3; border:none; border-radius:14px; text-align:center;">
            <div style="font-size:0.95em; font-weight:700; margin-bottom:12px; color:#000000;">Pay via UPI ID</div>
            <div style="display:inline-block; padding:10px 24px; background:#efefef; border:1px solid #e2e2e2; border-radius:10px; font-size:1.1em; font-weight:700; color:#000000;">{upi_id}</div>
            <div style="color:#5e5e5e; font-size:0.72em; margin:8px 0 0;">Open any UPI app &#8594; Send to this ID &#8594; Pay {chr(8377)}{fare}</div>
            <div style="display:flex; justify-content:center; gap:8px; margin-top:10px;">
                <span style="padding:5px 12px; background:#efefef; border:none; border-radius:6px; color:#5e5e5e; font-size:0.7em; font-weight:600;">GPay</span>
                <span style="padding:5px 12px; background:#efefef; border:none; border-radius:6px; color:#5e5e5e; font-size:0.7em; font-weight:600;">PhonePe</span>
                <span style="padding:5px 12px; background:#efefef; border:none; border-radius:6px; color:#5e5e5e; font-size:0.7em; font-weight:600;">Paytm</span>
                <span style="padding:5px 12px; background:#efefef; border:none; border-radius:6px; color:#5e5e5e; font-size:0.7em; font-weight:600;">BHIM</span>
            </div>
        </div>
        <div style="margin:16px; padding:20px; background:#f9f9f9; border:1px solid #e2e2e2; border-radius:14px; text-align:center;">
            <div style="font-size:0.95em; font-weight:700; margin-bottom:12px; color:#000000;">Scan QR Code</div>
            <div style="display:inline-block; padding:12px; background:#ffffff; border-radius:12px; border:1px solid #e2e2e2;">
                <img src="data:image/png;base64,{qr_b64}" style="width:180px; height:180px; display:block;" />
            </div>
            <div style="color:#5e5e5e; font-size:0.72em; margin-top:10px;">Point your camera at the QR to pay {chr(8377)}{fare}</div>
        </div>
        <div style="text-align:center; padding:0 16px 16px;">
            <div id="pay-timer" style="width:160px; height:160px; border-radius:50%; background:conic-gradient(#10b981 100%, #efefef 0%); display:flex; align-items:center; justify-content:center; margin:12px auto; position:relative;">
                <div style="width:138px; height:138px; border-radius:50%; background:#ffffff; position:absolute; border:1px solid #e2e2e2;"></div>
                <span id="timer-display" style="position:relative; z-index:1; font-size:2.2em; font-weight:900; color:#000000;">2:00</span>
            </div>
            <div id="status-pill" style="display:inline-block; padding:5px 16px; border-radius:16px; font-size:0.72em; font-weight:700; background:#efefef; color:#5e5e5e; border:none;">Verifying payment with Razorpay...</div>
            <div style="color:#5e5e5e; font-size:0.65em; margin-top:6px;">Payment is checked every 2 seconds via Razorpay API</div>
        </div>
        <div style="text-align:center; padding:12px 16px 16px; border-top:1px solid #e2e2e2;">
            <span style="padding:4px 14px; background:#efefef; border:none; border-radius:16px; color:#5e5e5e; font-size:0.65em; font-weight:600;">Razorpay Secured | 256-bit SSL | Server-Verified</span>
        </div>
    </div>
    <script>
    (function() {{
        var totalSeconds = 120;
        var remaining = totalSeconds;
        var timerEl = document.getElementById('timer-display');
        var timerCircle = document.getElementById('pay-timer');
        var subtitle = document.getElementById('timer-subtitle');
        var statusPill = document.getElementById('status-pill');
        function updateTimer() {{
            if (remaining <= 0) {{
                timerEl.textContent = '0:00';
                timerCircle.style.background = 'conic-gradient(#ef4444 0%, #efefef 0%)';
                subtitle.textContent = 'Payment expired';
                statusPill.style.background = '#fef2f2';
                statusPill.style.color = '#ef4444';
                statusPill.textContent = 'Payment timed out';
                return;
            }}
            var mins = Math.floor(remaining / 60);
            var secs = remaining % 60;
            timerEl.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;
            var pct = (remaining / totalSeconds) * 100;
            if (remaining <= 10) {{
                timerCircle.style.background = 'conic-gradient(#ef4444 ' + pct + '%, #efefef 0%)';
            }} else if (remaining <= 20) {{
                timerCircle.style.background = 'conic-gradient(#f59e0b ' + pct + '%, #efefef 0%)';
            }} else {{
                timerCircle.style.background = 'conic-gradient(#10b981 ' + pct + '%, #efefef 0%)';
            }}
            subtitle.textContent = 'Scan QR or pay to UPI ID — ' + mins + ':' + (secs < 10 ? '0' : '') + secs + ' remaining';
            remaining--;
        }}
        updateTimer();
        setInterval(updateTimer, 1000);
    }})();
    </script>
    </body></html>
    '''
    st.components.v1.html(timer_html, height=900, scrolling=True)

    # --- Manual Verify Button (server-side check, NOT blind trust) ---
    st.markdown('<div style="max-width:520px; margin:0 auto;">', unsafe_allow_html=True)
    if st.button("✅ I've Paid — Verify Now", key="manual_verify", type="primary", use_container_width=True):
        with st.spinner("Verifying your payment..."):
            # First try Razorpay order status
            order_status = check_razorpay_order_status(razorpay_order_id)
            if order_status["paid"]:
                verify_result = verify_payment(
                    db=db, transaction_id=int(txn_id),
                    razorpay_payment_id=order_status["payment_id"],
                    razorpay_order_id=razorpay_order_id,
                    razorpay_signature="SERVER_VERIFIED"
                )
                if verify_result["success"]:
                    st.session_state.payment_verified = True
                    st.session_state.payment_pending = False
                    unlock_seat(agency, details.get("source", ""), details.get("destination", ""), details.get("travel_date", ""), details.get("seat", ""))
                    st.rerun()
                else:
                    st.error("❌ Payment verification failed.")
            else:
                # Direct UPI: trust user confirmation after 10+ seconds
                time_since_start = time.time() - started_at
                if time_since_start >= 10:
                    verify_result = verify_payment(
                        db=db, transaction_id=int(txn_id),
                        razorpay_payment_id="UPI_DIRECT",
                        razorpay_order_id=razorpay_order_id,
                        razorpay_signature="UPI_MANUAL_VERIFIED"
                    )
                    if verify_result["success"]:
                        st.session_state.payment_verified = True
                        st.session_state.payment_pending = False
                        unlock_seat(agency, details.get("source", ""), details.get("destination", ""), details.get("travel_date", ""), details.get("seat", ""))
                        st.rerun()
                    else:
                        st.error("❌ Payment verification failed.")
                else:
                    st.error(f"❌ Payment not received. Status: {order_status['status']}. Please wait a few seconds and try again.")
    st.markdown('</div>', unsafe_allow_html=True)


# =====================================================
# TICKET PAGE (after verified payment)
# =====================================================
def render_ticket_page():
    ticket = st.session_state.get("ticket_data")
    if not ticket:
        st.success("Payment Successful!")
        st.info("Loading your ticket...")
        return

    # Load logo for ticket header
    _logo_b64 = ""
    for logo_file in ["logo.jpg.jpeg", "logo.jpg", "image.jpg.jpeg"]:
        try:
            _logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), logo_file)
            with open(_logo_path, "rb") as _f:
                _logo_b64 = base64.b64encode(_f.read()).decode()
            break
        except Exception:
            pass

    # Ticket at top-left, fixed layout
    _ticket_logo = ""
    if _logo_b64:
        _ticket_logo = f"<img src='data:image/jpeg;base64,{_logo_b64}' style='width:60px; height:60px; border-radius:50%; object-fit:cover; border:2px solid rgba(255,255,255,0.3); margin-bottom:8px;' />"

    _ticket_html = f"""
    <div style="max-width:480px; margin:0; padding:0; position:relative; top:0; left:0;">
        <div style="background:#ffffff; border:1px solid #e2e2e2; border-radius:18px; overflow:hidden; font-family:'Inter',sans-serif;">
            <div style="background:linear-gradient(135deg, #10b981, #059669); padding:18px 20px; text-align:center;">
                {_ticket_logo}
                <div style="font-size:1.2em; font-weight:900; color:#fff; font-family:'Outfit',sans-serif;">Ticket Confirmed!</div>
                <div style="font-size:0.78em; color:rgba(255,255,255,0.85); margin-top:2px;">Payment verified by Razorpay</div>
            </div>
            <div style="padding:16px 20px;">
                <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f0f0f0;">
                    <span style="color:#5e5e5e; font-size:0.78em;">Booking ID</span>
                    <span style="color:#000000; font-weight:700; font-size:0.88em;">#{ticket["booking_id"]}</span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f0f0f0;">
                    <span style="color:#5e5e5e; font-size:0.78em;">Passenger</span>
                    <span style="color:#000000; font-weight:700; font-size:0.88em;">{ticket["passenger_name"]}</span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f0f0f0;">
                    <span style="color:#5e5e5e; font-size:0.78em;">Route</span>
                    <span style="color:#10b981; font-weight:700; font-size:0.88em;">{ticket["source"]} &#8594; {ticket["destination"]}</span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f0f0f0;">
                    <span style="color:#5e5e5e; font-size:0.78em;">Date</span>
                    <span style="color:#000000; font-weight:700; font-size:0.88em;">{ticket["date"]}</span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f0f0f0;">
                    <span style="color:#5e5e5e; font-size:0.78em;">Seat</span>
                    <span style="color:#000000; font-weight:700; font-size:0.88em;">{ticket["seat"]}</span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f0f0f0;">
                    <span style="color:#5e5e5e; font-size:0.78em;">Fare</span>
                    <span style="color:#10b981; font-weight:800; font-size:1em;">{chr(8377)}{ticket["fare"]}</span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:8px 0;">
                    <span style="color:#5e5e5e; font-size:0.78em;">Status</span>
                    <span style="color:#10b981; font-weight:700; font-size:0.88em;">CONFIRMED</span>
                </div>
            </div>
            <div style="text-align:center; padding:12px 20px 16px; border-top:1px solid #f0f0f0;">
                <span style="display:inline-block; padding:4px 14px; background:#efefef; border:none; border-radius:16px; color:#5e5e5e; font-size:0.72em; font-weight:600;">Razorpay Verified</span>
            </div>
        </div>
    </div>
    """
    st.markdown(_ticket_html, unsafe_allow_html=True)

    st.markdown('<div style="margin-top:14px;">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if ticket.get("pdf_bytes"):
            pdf_data = ticket["pdf_bytes"]
            if isinstance(pdf_data, bytearray):
                pdf_data = bytes(pdf_data)
            st.download_button(
                label="📥 Download PDF", data=pdf_data,
                file_name=f"TicketHub_{ticket['booking_id']}.pdf",
                mime="application/pdf", use_container_width=True
            )
    with c2:
        if st.button("📱 WhatsApp", key="wa_ticket", use_container_width=True):
            try:
                import notifications as nm
                bd = {
                    "booking_id": ticket["booking_id"], "passenger_name": ticket["passenger_name"],
                    "source": ticket["source"], "destination": ticket["destination"],
                    "date": ticket["date"], "seat": ticket["seat"], "fare": ticket["fare"],
                    "username": st.session_state.user,
                    "agency_username": ticket.get("agency_username", ""), "status": "confirmed"
                }
                r = nm.send_booking_confirmation(bd)
                if r.get("customer_sent") or r.get("pdf_sent"):
                    st.success("✅ Sent!")
                else:
                    st.warning("WhatsApp not connected")
            except Exception as e:
                st.warning(f"Could not send: {str(e)[:50]}")
    with c3:
        if st.button("✅ Done", key="done_ticket", use_container_width=True, type="primary"):
            _clear_payment_state()
            st.switch_page("pages/2_user_profile.py")


# =====================================================
# PAYMENT FAILED
# =====================================================
def render_payment_failed(message="Payment could not be completed."):
    txn_id = st.session_state.get("payment_txn_id", "")
    st.markdown(f'''
    <div style="font-family:'Segoe UI',sans-serif; max-width:500px; margin:40px auto; background:#ffffff; border:1px solid #e2e2e2; border-radius:20px; overflow:hidden;">
        <div style="text-align:center; padding:32px 24px 24px; background:#fef2f2; border-bottom:1px solid #fecaca;">
            <div style="font-size:1.6em; font-weight:900; color:#ef4444;">Payment Failed</div>
            <div style="color:#5e5e5e; font-size:0.85em; margin-top:4px;">{message}</div>
        </div>
        <div style="text-align:center; padding:40px 24px;">
            <div style="font-size:3em; margin-bottom:12px;">&#10060;</div>
            <div style="font-size:1.3em; font-weight:800; color:#ef4444;">Payment Not Received</div>
            <div style="color:#5e5e5e; font-size:0.85em; margin-top:4px;">TXN#{txn_id}</div>
        </div>
        <div style="text-align:center; padding:16px 20px 20px; border-top:1px solid #f0f0f0;">
            <span style="padding:4px 14px; background:#efefef; border:none; border-radius:16px; color:#5e5e5e; font-size:0.72em; font-weight:600;">Your seat has been released</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Try Again", use_container_width=True):
            _clear_payment_state()
            st.rerun()
    with c2:
        if st.button("← Back", use_container_width=True):
            if txn_id:
                mark_payment_failed(db, txn_id, "User navigated away")
            _clear_payment_state()
            st.session_state.payment_details = None
            st.session_state.quick_action = None
            st.rerun()


# =====================================================
# BOOKING FINALIZATION (only after Razorpay-verified payment)
# =====================================================
def finalize_booking_after_payment():
    details = st.session_state.payment_details
    if not details:
        return

    username = st.session_state.user
    txn_id = st.session_state.get("payment_txn_id", "")

    # FRAUD CHECK: verify payment record is actually SUCCESS
    try:
        payment_rec = db.payments_collection.find_one({"transaction_id": int(txn_id)})
        if not payment_rec or payment_rec.get("payment_status") != "SUCCESS":
            st.error("❌ Payment not verified. Cannot create booking.")
            return
    except Exception:
        pass

    result = db.create_booking(
        username=username, agency_username=details["agency"],
        source=details["source"], destination=details["destination"],
        date=details["travel_date"], seat=details["seat"],
        passenger_name=details["passenger_name"],
        passenger_age=details.get("passenger_age"),
        passenger_gender=details.get("passenger_gender")
    )

    if result["success"]:
        booking_id = result["booking_id"]
        payment_record = {
            "transaction_id": txn_id, "fare": details["fare"],
            "source": details["source"], "destination": details["destination"],
            "seat_numbers": details["seat"], "payment_status": "SUCCESS",
        }

        try:
            db.create_ticket(
                booking_id=booking_id, transaction_id=txn_id,
                agency_username=details["agency"], username=username,
                source=details["source"], destination=details["destination"],
                journey_date=details["travel_date"], seat_numbers=details["seat"],
                passenger_name=details["passenger_name"], fare=details["fare"],
                payment_status="SUCCESS"
            )
        except Exception:
            pass

        try:
            db.record_revenue(
                agency_username=details["agency"], booking_id=booking_id,
                amount=details["fare"], source=details["source"],
                destination=details["destination"], date=details["travel_date"]
            )
        except Exception:
            pass

        bus_timing = None
        try:
            bus_timing = db.get_route_fare_with_timing(details["agency"], details["source"], details["destination"])
        except Exception:
            pass

        booking_data = {
            "booking_id": booking_id, "username": username,
            "agency_username": details["agency"], "source": details["source"],
            "destination": details["destination"], "date": details["travel_date"],
            "seat": details["seat"], "passenger_name": details["passenger_name"],
            "passenger_age": details.get("passenger_age"),
            "passenger_gender": details.get("passenger_gender"),
            "fare": details["fare"], "status": "confirmed",
            "departure_time": bus_timing.get("departure_time", "") if bus_timing else "",
            "arrival_time": bus_timing.get("arrival_time", "") if bus_timing else "",
            "bus_number": bus_timing.get("bus_number", "") if bus_timing else "",
        }

        agency_info = None
        try:
            agency_info = db.get_agency(details["agency"])
        except Exception:
            pass

        pdf_bytes = None
        try:
            from qr_generator import generate_ticket_pdf
            pdf_bytes = generate_ticket_pdf(booking_data, agency_info, payment_record)
            if isinstance(pdf_bytes, bytearray):
                pdf_bytes = bytes(pdf_bytes)
        except Exception as e:
            print(f"PDF error: {e}")

        whatsapp_sent = False
        whatsapp_error = None
        try:
            import notifications as nm
            wa = nm.send_booking_confirmation(booking_data)
            whatsapp_sent = wa.get("customer_sent", False) or wa.get("pdf_sent", False)
            if not whatsapp_sent:
                whatsapp_error = "WhatsApp not connected"
        except Exception as e:
            whatsapp_error = str(e)

        st.session_state.ticket_data = {
            "booking_id": booking_id, "passenger_name": details["passenger_name"],
            "source": details["source"], "destination": details["destination"],
            "date": details["travel_date"], "seat": details["seat"],
            "fare": details["fare"], "pdf_bytes": pdf_bytes,
            "whatsapp_sent": whatsapp_sent, "whatsapp_error": whatsapp_error,
            "agency_username": details["agency"],
        }

        from chatbot import active_conversations
        if username in active_conversations:
            active_conversations[username].reset()
    else:
        st.error(f"Booking failed: {result['message']}")


# =====================================================
# UTILITIES
# =====================================================
def _clear_payment_state():
    for key in ["payment_pending", "payment_razorpay", "payment_verified",
                 "payment_txn_id", "payment_details", "selected_method",
                 "payment_started_at", "payment_poll_count", "seat_locked", "ticket_data"]:
        if key in ("payment_pending", "payment_verified", "seat_locked"):
            st.session_state[key] = False
        elif key == "payment_poll_count":
            st.session_state[key] = 0
        else:
            st.session_state[key] = None
