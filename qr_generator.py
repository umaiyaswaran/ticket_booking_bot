import qrcode
import io
import base64
from datetime import datetime


def generate_booking_qr(booking_data: dict) -> str:
    """
    Generate a QR code for a booking and return as base64 string.
    
    Args:
        booking_data: Dict with booking_id, source, destination, date, seat, etc.
    
    Returns:
        Base64 encoded PNG image string
    """
    qr_content = (
        f"TICKETHUB BOOKING\n"
        f"Booking ID: {booking_data.get('booking_id', 'N/A')}\n"
        f"Passenger: {booking_data.get('passenger_name', 'N/A')}\n"
        f"Route: {booking_data.get('source', 'N/A')} → {booking_data.get('destination', 'N/A')}\n"
        f"Date: {booking_data.get('date', 'N/A')}\n"
        f"Seat: {booking_data.get('seat', 'N/A')}\n"
        f"Agency: {booking_data.get('agency_username', 'N/A')}\n"
        f"Status: {booking_data.get('status', 'confirmed').upper()}"
    )

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(qr_content)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0a0e14", back_color="#ffffff")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.read()).decode()
    return img_base64


def generate_ticket_html(booking: dict, agency: dict = None) -> str:
    """Generate a professional HTML ticket for display/download."""
    agency_name = agency.get("agency_name", "Bus Agency") if agency else "Bus Agency"
    qr_b64 = generate_booking_qr(booking)
    booking_date = booking.get("created_at")
    if isinstance(booking_date, datetime):
        booking_date = booking_date.strftime("%d %b %Y, %I:%M %p")

    html = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif; max-width:480px; margin:0 auto; background:#0f1319; border-radius:16px; overflow:hidden; border:1px solid rgba(0,212,255,0.15); color:#e8edf4;">
        <div style="background:linear-gradient(135deg,#00d4ff,#6c63ff,#a855f7); padding:20px; text-align:center;">
            <div style="font-size:14px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#fff;">🎫 TicketHub</div>
            <div style="font-size:11px; color:rgba(255,255,255,0.8); margin-top:4px;">E-TICKET</div>
        </div>
        <div style="padding:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <div>
                    <div style="font-size:22px; font-weight:800; color:#00d4ff;">{booking.get('source', 'N/A')}</div>
                    <div style="font-size:11px; color:#8899aa;">FROM</div>
                </div>
                <div style="font-size:20px; color:#6c63ff;">✈ →</div>
                <div style="text-align:right;">
                    <div style="font-size:22px; font-weight:800; color:#00d4ff;">{booking.get('destination', 'N/A')}</div>
                    <div style="font-size:11px; color:#8899aa;">TO</div>
                </div>
            </div>
            <div style="border-top:1px dashed rgba(255,255,255,0.1); margin:12px 0;"></div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:13px;">
                <div><span style="color:#8899aa;">Booking ID</span><br><strong style="color:#00d4ff;">#{booking.get('booking_id', 'N/A')}</strong></div>
                <div><span style="color:#8899aa;">Date</span><br><strong>{booking.get('date', 'N/A')}</strong></div>
                <div><span style="color:#8899aa;">Seat</span><br><strong>{booking.get('seat', 'N/A')}</strong></div>
                <div><span style="color:#8899aa;">Passenger</span><br><strong>{booking.get('passenger_name', 'N/A')}</strong></div>
                <div><span style="color:#8899aa;">Agency</span><br><strong>{agency_name}</strong></div>
                <div><span style="color:#8899aa;">Status</span><br><strong style="color:{'#10b981' if booking.get('status')=='confirmed' else '#ef4444'};">{booking.get('status', 'confirmed').upper()}</strong></div>
            </div>
            <div style="border-top:1px dashed rgba(255,255,255,0.1); margin:16px 0;"></div>
            <div style="text-align:center;">
                <img src="data:image/png;base64,{qr_b64}" style="width:140px; height:140px; border-radius:8px;" />
                <div style="font-size:10px; color:#8899aa; margin-top:6px;">Scan to verify ticket</div>
            </div>
        </div>
        <div style="background:rgba(0,212,255,0.05); padding:12px; text-align:center; font-size:10px; color:#556677;">
            Generated on {booking_date or 'N/A'} &bull; TicketHub Smart Booking
        </div>
    </div>
    """
    return html
