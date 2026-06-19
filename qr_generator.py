import qrcode
import io
import base64
import os
from datetime import datetime
from fpdf import FPDF


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
        f"Age: {booking_data.get('passenger_age', 'N/A')}\n"
        f"Gender: {booking_data.get('passenger_gender', 'N/A')}\n"
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

    # Load logo as base64
    logo_b64 = ""
    for logo_file in ["logo.jpg.jpeg", "logo.jpg", "image.jpg.jpeg"]:
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), logo_file)
        if os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as f:
                    logo_b64 = base64.b64encode(f.read()).decode()
                break
            except Exception:
                pass

    logo_html = ""
    if logo_b64:
        logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" style="width:52px; height:52px; border-radius:12px; object-fit:cover; border:2px solid rgba(255,255,255,0.2);" />'

    source = booking.get('source', 'N/A')
    destination = booking.get('destination', 'N/A')
    fare_val = booking.get('fare', 'N/A')
    departure = booking.get('departure_time', '')
    arrival = booking.get('arrival_time', '')
    bus_no = booking.get('bus_number', '')

    html = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif; max-width:480px; margin:0 auto; background:#0f1319; border-radius:18px; overflow:hidden; border:2px solid rgba(0,212,255,0.25); color:#e8edf4; position:relative;">

        <!-- Top ticket stub perforation -->
        <div style="position:relative; height:14px; background:#0f1319; overflow:visible;">
            <div style="position:absolute; left:-8px; top:0; width:16px; height:16px; background:#0f1319; border-radius:50%; border:2px solid rgba(0,212,255,0.25); box-sizing:border-box;"></div>
            <div style="position:absolute; right:-8px; top:0; width:16px; height:16px; background:#0f1319; border-radius:50%; border:2px solid rgba(0,212,255,0.25); box-sizing:border-box;"></div>
        </div>

        <!-- Header with logo + brand -->
        <div style="background:linear-gradient(135deg,#00d4ff 0%,#6c63ff 50%,#a855f7 100%); padding:18px 20px; display:flex; align-items:center; gap:14px;">
            {logo_html}
            <div>
                <div style="font-size:18px; font-weight:800; letter-spacing:2px; text-transform:uppercase; color:#fff;">TICKETHUB</div>
                <div style="font-size:10px; color:rgba(255,255,255,0.85); letter-spacing:1px; margin-top:2px;">E-TICKET &nbsp;|&nbsp; DIGITAL BOARDING PASS</div>
            </div>
        </div>

        <!-- Route section — live map style -->
        <div style="padding:24px 20px 16px; position:relative;">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <!-- Source -->
                <div style="text-align:center; flex:1;">
                    <div style="width:14px; height:14px; border-radius:50%; background:#00d4ff; margin:0 auto 8px auto; box-shadow:0 0 12px rgba(0,212,255,0.5);"></div>
                    <div style="font-size:20px; font-weight:800; color:#00d4ff; text-transform:uppercase; letter-spacing:0.5px;">{source}</div>
                    <div style="font-size:10px; color:#8899aa; margin-top:3px; letter-spacing:1px;">FROM</div>
                </div>

                <!-- Route line -->
                <div style="flex:0 0 auto; display:flex; align-items:center; padding:0 6px; margin-top:-18px;">
                    <div style="width:6px; height:6px; border-radius:50%; background:#6c63ff;"></div>
                    <div style="width:40px; height:2px; background:linear-gradient(90deg,#6c63ff,#a855f7); margin:0 3px;"></div>
                    <div style="font-size:16px; color:#6c63ff;">&#9654;</div>
                    <div style="width:40px; height:2px; background:linear-gradient(90deg,#a855f7,#00d4ff); margin:0 3px;"></div>
                    <div style="width:6px; height:6px; border-radius:50%; background:#00d4ff;"></div>
                </div>

                <!-- Destination -->
                <div style="text-align:center; flex:1;">
                    <div style="width:14px; height:14px; border-radius:50%; background:#a855f7; margin:0 auto 8px auto; box-shadow:0 0 12px rgba(168,85,247,0.5);"></div>
                    <div style="font-size:20px; font-weight:800; color:#a855f7; text-transform:uppercase; letter-spacing:0.5px;">{destination}</div>
                    <div style="font-size:10px; color:#8899aa; margin-top:3px; letter-spacing:1px;">TO</div>
                </div>
            </div>
        </div>

        <!-- Perforated divider -->
        <div style="position:relative; margin:0 20px;">
            <div style="border-top:2px dashed rgba(0,212,255,0.2);"></div>
            <div style="position:absolute; left:-30px; top:-8px; width:16px; height:16px; background:#0f1319; border-radius:50%;"></div>
            <div style="position:absolute; right:-30px; top:-8px; width:16px; height:16px; background:#0f1319; border-radius:50%;"></div>
        </div>

        <!-- Details grid -->
        <div style="padding:16px 20px;">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px 16px; font-size:12px;">
                <div>
                    <div style="color:#8899aa; font-size:9px; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:2px;">Booking ID</div>
                    <div style="font-weight:700; color:#00d4ff; font-size:13px;">#{booking.get('booking_id', 'N/A')}</div>
                </div>
                <div>
                    <div style="color:#8899aa; font-size:9px; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:2px;">Date</div>
                    <div style="font-weight:700; font-size:13px;">{booking.get('date', 'N/A')}</div>
                </div>
                <div>
                    <div style="color:#8899aa; font-size:9px; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:2px;">Seat</div>
                    <div style="font-weight:700; font-size:13px;">{booking.get('seat', 'N/A')}</div>
                </div>
                <div>
                    <div style="color:#8899aa; font-size:9px; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:2px;">Passenger</div>
                    <div style="font-weight:700; font-size:13px;">{booking.get('passenger_name', 'N/A')}</div>
                </div>
                <div>
                    <div style="color:#8899aa; font-size:9px; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:2px;">Age / Gender</div>
                    <div style="font-weight:700; font-size:13px;">{booking.get('passenger_age', 'N/A')} / {booking.get('passenger_gender', 'N/A')}</div>
                </div>
                <div>
                    <div style="color:#8899aa; font-size:9px; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:2px;">Agency</div>
                    <div style="font-weight:700; font-size:13px;">{agency_name}</div>
                </div>
                <div>
                    <div style="color:#8899aa; font-size:9px; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:2px;">Fare</div>
                    <div style="font-weight:700; color:#00d4ff; font-size:14px;">{'₹' + str(fare_val) if fare_val != 'N/A' else 'N/A'}</div>
                </div>
                <div>
                    <div style="color:#8899aa; font-size:9px; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:2px;">Payment</div>
                    <div style="font-weight:700; color:#10b981; font-size:13px;">PAID</div>
                </div>
                {f'<div><div style="color:#8899aa; font-size:9px; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:2px;">Departure</div><div style="font-weight:700; font-size:13px;">{departure}</div></div>' if departure else ''}
                {f'<div><div style="color:#8899aa; font-size:9px; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:2px;">Arrival</div><div style="font-weight:700; font-size:13px;">{arrival}</div></div>' if arrival else ''}
                {f'<div><div style="color:#8899aa; font-size:9px; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:2px;">Bus No.</div><div style="font-weight:700; font-size:13px;">{bus_no}</div></div>' if bus_no else ''}
            </div>
        </div>

        <!-- Perforated divider -->
        <div style="position:relative; margin:0 20px;">
            <div style="border-top:2px dashed rgba(0,212,255,0.2);"></div>
            <div style="position:absolute; left:-30px; top:-8px; width:16px; height:16px; background:#0f1319; border-radius:50%;"></div>
            <div style="position:absolute; right:-30px; top:-8px; width:16px; height:16px; background:#0f1319; border-radius:50%;"></div>
        </div>

        <!-- QR Code -->
        <div style="padding:18px 20px; text-align:center;">
            <img src="data:image/png;base64,{qr_b64}" style="width:130px; height:130px; border-radius:10px; border:2px solid rgba(0,212,255,0.15);" />
            <div style="font-size:10px; color:#8899aa; margin-top:8px; letter-spacing:0.5px;">Scan to verify ticket</div>
        </div>

        <!-- Footer -->
        <div style="background:rgba(0,212,255,0.05); padding:12px 20px; text-align:center; font-size:9px; color:#556677; border-top:1px solid rgba(0,212,255,0.1);">
            Generated on {booking_date or 'N/A'} &bull; TicketHub Smart Booking
        </div>

        <!-- Bottom ticket stub perforation -->
        <div style="position:relative; height:14px; background:#0f1319; overflow:visible;">
            <div style="position:absolute; left:-8px; top:0; width:16px; height:16px; background:#0f1319; border-radius:50%; border:2px solid rgba(0,212,255,0.25); box-sizing:border-box;"></div>
            <div style="position:absolute; right:-8px; top:0; width:16px; height:16px; background:#0f1319; border-radius:50%; border:2px solid rgba(0,212,255,0.25); box-sizing:border-box;"></div>
        </div>
    </div>
    """
    return html


def generate_ticket_pdf(booking: dict, agency: dict = None, payment: dict = None) -> bytes:
    agency_name = agency.get("agency_name", "Bus Agency") if agency else "Bus Agency"
    booking_date = booking.get("created_at")
    if isinstance(booking_date, datetime):
        booking_date = booking_date.strftime("%d %b %Y, %I:%M %p")

    fare = booking.get("fare", 0)
    payment_status = "PAID"
    transaction_id = ""
    if payment:
        fare = payment.get("fare", fare)
        payment_status = payment.get("payment_status", "SUCCESS")
        transaction_id = payment.get("transaction_id", "")
    elif booking.get("fare"):
        fare = booking.get("fare")

    phone = booking.get("phone_number", "")
    bus_number = booking.get("bus_number", "")
    departure = booking.get("departure_time", "")
    arrival = booking.get("arrival_time", "")
    age = booking.get("passenger_age", "")
    gender = booking.get("passenger_gender", "")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    pw, ph = 210, 297
    margin = 12
    content_w = pw - 2 * margin

    # --- Dark background ---
    pdf.set_fill_color(12, 16, 22)
    pdf.rect(0, 0, pw, ph, "F")

    # --- Outer border (cyan glow) ---
    pdf.set_draw_color(0, 212, 255)
    pdf.set_line_width(0.8)
    pdf.rect(4, 4, pw - 8, ph - 8)

    # --- Inner border (subtle) ---
    pdf.set_draw_color(30, 40, 55)
    pdf.set_line_width(0.3)
    pdf.rect(7, 7, pw - 14, ph - 14)

    # --- Top perforation circles (ticket stub) ---
    pdf.set_fill_color(12, 16, 22)
    pdf.set_draw_color(0, 212, 255)
    pdf.set_line_width(0.3)
    pdf.ellipse(2, 10, 10, 10, "DF")
    pdf.ellipse(pw - 12, 10, 10, 10, "DF")

    # --- Header gradient bar ---
    y_top = 14
    pdf.set_fill_color(0, 212, 255)
    pdf.rect(margin, y_top, 55, 24, "F")
    pdf.set_fill_color(108, 99, 255)
    pdf.rect(67, y_top, 55, 24, "F")
    pdf.set_fill_color(168, 85, 247)
    pdf.rect(129, y_top, content_w - 117, 24, "F")

    # --- Logo top-left (overlapping header) ---
    logo_found = False
    for logo_file in ["logo.jpg.jpeg", "logo.jpg", "image.jpg.jpeg", "image.jpg.png"]:
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), logo_file)
        if os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=14, y=y_top + 2, w=20)
                logo_found = True
                break
            except Exception:
                pass

    # Header title
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(38, y_top + 3)
    pdf.cell(0, 9, "TICKETHUB")
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_xy(38, y_top + 12)
    pdf.cell(0, 6, "E-TICKET  |  DIGITAL BOARDING PASS")

    # --- Route section (map-style) ---
    y_route = y_top + 32
    source = booking.get("source", "N/A")
    dest = booking.get("destination", "N/A")

    # Source dot
    pdf.set_fill_color(0, 212, 255)
    pdf.ellipse(margin + 30, y_route + 4, 5, 5, "F")

    # Source city
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 212, 255)
    pdf.set_xy(margin, y_route + 12)
    pdf.cell(65, 10, source, align="C")

    # FROM label
    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(120, 140, 160)
    pdf.set_xy(margin, y_route + 22)
    pdf.cell(65, 5, "FROM", align="C")

    # Route line with arrow
    y_line = y_route + 6
    pdf.set_draw_color(108, 99, 255)
    pdf.set_line_width(1.0)
    pdf.line(margin + 68, y_line, 100, y_line)
    pdf.set_draw_color(168, 85, 247)
    pdf.line(100, y_line, 132, y_line)

    # Arrow triangle
    pdf.set_fill_color(168, 85, 247)
    pdf.set_draw_color(168, 85, 247)
    pdf.set_line_width(0.3)
    pdf.set_font("ZapfDingbats", "", 10)
    pdf.set_text_color(168, 85, 247)
    pdf.set_xy(100, y_line - 4)
    pdf.cell(10, 8, chr(174))  # right-pointing triangle

    # Dots on route line
    pdf.set_fill_color(108, 99, 255)
    pdf.ellipse(margin + 75, y_line - 1, 3, 3, "F")
    pdf.set_fill_color(168, 85, 247)
    pdf.ellipse(132, y_line - 1, 3, 3, "F")

    # Destination dot
    pdf.set_fill_color(168, 85, 247)
    pdf.ellipse(pw - margin - 35, y_route + 4, 5, 5, "F")

    # Destination city
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(168, 85, 247)
    pdf.set_xy(pw - margin - 65, y_route + 12)
    pdf.cell(65, 10, dest, align="C")

    # TO label
    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(120, 140, 160)
    pdf.set_xy(pw - margin - 65, y_route + 22)
    pdf.cell(65, 5, "TO", align="C")

    # --- Perforated divider with circle cutouts ---
    y_sep1 = y_route + 32
    pdf.set_draw_color(0, 212, 255)
    pdf.set_line_width(0.3)
    pdf.dashed_line(margin + 4, y_sep1, pw - margin - 4, y_sep1, 3, 2)
    # Circle cutouts
    pdf.set_fill_color(12, 16, 22)
    pdf.set_draw_color(0, 212, 255)
    pdf.set_line_width(0.3)
    pdf.ellipse(margin - 2, y_sep1 - 5, 10, 10, "DF")
    pdf.ellipse(pw - margin - 8, y_sep1 - 5, 10, 10, "DF")

    # --- Details grid (2 columns) ---
    y_det = y_sep1 + 8
    col_w = content_w / 2
    row_h = 14

    details = [
        ("BOOKING ID", f"#{booking.get('booking_id', 'N/A')}"),
        ("DATE", booking.get("date", "N/A")),
        ("SEAT", booking.get("seat", "N/A")),
        ("PASSENGER", booking.get("passenger_name", "N/A")),
        ("AGE", str(age) if age else "N/A"),
        ("GENDER", gender if gender else "N/A"),
        ("PHONE", phone if phone else "N/A"),
        ("AGENCY", agency_name),
        ("FARE", f"Rs.{fare}" if fare else "N/A"),
        ("PAYMENT", payment_status.upper()),
    ]
    if departure:
        details.append(("DEPARTURE", departure))
    if arrival:
        details.append(("ARRIVAL", arrival))
    if bus_number:
        details.append(("BUS NO.", bus_number))
    if transaction_id:
        details.append(("TXN ID", f"#{transaction_id}"))

    for i, (label, value) in enumerate(details):
        col = i % 2
        row = i // 2
        x = margin + 4 + (col * col_w)
        cy = y_det + (row * row_h)

        pdf.set_font("Helvetica", "", 5.5)
        pdf.set_text_color(100, 120, 140)
        pdf.set_xy(x, cy)
        pdf.cell(col_w, 4, label)

        pdf.set_font("Helvetica", "B", 8.5)
        if label == "PAYMENT":
            color = (16, 185, 129) if value in ("SUCCESS", "PAID") else (239, 68, 68)
            pdf.set_text_color(*color)
        elif label == "FARE":
            pdf.set_text_color(0, 212, 255)
        else:
            pdf.set_text_color(232, 237, 244)
        pdf.set_xy(x, cy + 4)
        pdf.cell(col_w, 8, str(value))

    # --- Perforated divider with circle cutouts ---
    rows_used = (len(details) + 1) // 2
    y_sep2 = y_det + (rows_used * row_h) + 4
    pdf.set_draw_color(0, 212, 255)
    pdf.set_line_width(0.3)
    pdf.dashed_line(margin + 4, y_sep2, pw - margin - 4, y_sep2, 3, 2)
    pdf.set_fill_color(12, 16, 22)
    pdf.set_draw_color(0, 212, 255)
    pdf.ellipse(margin - 2, y_sep2 - 5, 10, 10, "DF")
    pdf.ellipse(pw - margin - 8, y_sep2 - 5, 10, 10, "DF")

    # --- QR Code centered ---
    y_qr = y_sep2 + 6
    qr_img = io.BytesIO()
    qr = qrcode.QRCode(version=1, box_size=8, border=1)
    qr_content = (
        f"TICKETHUB BOOKING\n"
        f"Booking ID: {booking.get('booking_id', 'N/A')}\n"
        f"Passenger: {booking.get('passenger_name', 'N/A')}\n"
        f"Route: {source} -> {dest}\n"
        f"Date: {booking.get('date', 'N/A')}\n"
        f"Seat: {booking.get('seat', 'N/A')}\n"
        f"Fare: Rs.{fare}\n"
        f"Status: {booking.get('status', 'confirmed').upper()}"
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    qr_img_data = qr.make_image(fill_color="#0a0e14", back_color="#ffffff")
    qr_img_data.save(qr_img, format="PNG")
    qr_img.seek(0)

    qr_path = io.BytesIO(qr_img.read())
    pdf.image(qr_path, x=(pw - 38) / 2, y=y_qr, w=38)

    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(100, 120, 140)
    pdf.set_xy(margin, y_qr + 40)
    pdf.cell(content_w, 5, "Scan to verify ticket", align="C")

    # --- Footer ---
    y_footer = y_qr + 48
    if y_footer > ph - 30:
        y_footer = ph - 30

    pdf.set_fill_color(18, 28, 38)
    pdf.rect(margin, y_footer, content_w, 20, "F")

    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(80, 100, 120)
    pdf.set_xy(margin, y_footer + 2)
    pdf.cell(content_w, 4, f"Generated on {booking_date or 'N/A'}  |  TicketHub Smart Booking", align="C")
    pdf.set_xy(margin, y_footer + 7)
    pdf.cell(content_w, 4, "Please carry a valid ID proof along with this e-ticket.", align="C")
    pdf.set_xy(margin, y_footer + 12)
    pdf.set_font("Helvetica", "B", 6.5)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(content_w, 4, "Thank you for choosing TicketHub!", align="C")

    # --- Bottom perforation circles ---
    pdf.set_fill_color(12, 16, 22)
    pdf.set_draw_color(0, 212, 255)
    pdf.set_line_width(0.3)
    pdf.ellipse(2, ph - 18, 10, 10, "DF")
    pdf.ellipse(pw - 12, ph - 18, 10, 10, "DF")

    pdf_bytes = pdf.output()
    if isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    return pdf_bytes
