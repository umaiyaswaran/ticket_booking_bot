import logging
import db
import whatsapp
from qr_generator import generate_booking_qr
import base64
import io
from PIL import Image

logger = logging.getLogger(__name__)


def get_user_phone(username: str) -> str:
    """Get user's phone number from profile."""
    try:
        user = db.users_collection.find_one({"username": username})
        if user:
            return user.get("phone", "")
        return ""
    except Exception as e:
        logger.error(f"Get user phone error: {e}")
        return ""


def get_agency_phone(agency_username: str) -> str:
    """Get agency's phone number from profile."""
    try:
        agency = db.agencies_collection.find_one({"username": agency_username})
        if agency:
            return agency.get("phone", "")
        return ""
    except Exception as e:
        logger.error(f"Get agency phone error: {e}")
        return ""


def get_agency_whatsapp_instance(agency_username: str) -> str:
    """Get the WhatsApp instance name for an agency."""
    try:
        instance = db.whatsapp_instances_collection.find_one({"agency_username": agency_username})
        if instance:
            return instance.get("instance_name", "")
        return ""
    except Exception as e:
        logger.error(f"Get WhatsApp instance error: {e}")
        return ""


def send_booking_confirmation(booking: dict) -> dict:
    """
    Send WhatsApp booking confirmation to customer and agency with QR code.
    
    Args:
        booking: Full booking dict from database
    
    Returns:
        {"customer_sent": bool, "agency_sent": bool, "qr_sent": bool}
    """
    result = {"customer_sent": False, "agency_sent": False, "qr_sent": False}

    try:
        customer_phone = get_user_phone(booking.get("username", ""))
        agency_phone = get_agency_phone(booking.get("agency_username", ""))
        instance = get_agency_whatsapp_instance(booking.get("agency_username", ""))

        if not instance:
            logger.warning("No WhatsApp instance for agency, skipping WhatsApp notifications")
            return result

        agency = db.agencies_collection.find_one({"username": booking.get("agency_username")})
        agency_name = agency.get("agency_name", "Bus Agency") if agency else "Bus Agency"

        customer_msg = (
            f"🎫 *TicketHub - Booking Confirmed!*\n\n"
            f"Booking ID: #{booking.get('booking_id')}\n"
            f"Passenger: {booking.get('passenger_name', 'N/A')}\n"
            f"Route: {booking.get('source')} → {booking.get('destination')}\n"
            f"Date: {booking.get('date')}\n"
            f"Seat: {booking.get('seat')}\n"
            f"Agency: {agency_name}\n\n"
            f"Status: ✅ CONFIRMED\n"
            f"Show this message or QR code at boarding."
        )

        agency_msg = (
            f"📋 *New Booking Received!*\n\n"
            f"Booking ID: #{booking.get('booking_id')}\n"
            f"Passenger: {booking.get('passenger_name', 'N/A')} (Age: {booking.get('passenger_age', 'N/A')})\n"
            f"Route: {booking.get('source')} → {booking.get('destination')}\n"
            f"Date: {booking.get('date')}\n"
            f"Seat: {booking.get('seat')}\n"
            f"Booked by: {booking.get('username')}"
        )

        # Send customer messages
        if customer_phone:
            resp = whatsapp.send_text_message(instance, customer_phone, customer_msg)
            result["customer_sent"] = resp.get("success", False)
            
            # Send QR code image to customer
            try:
                qr_base64 = generate_booking_qr(booking)
                # Create proper image URL for WhatsApp
                qr_image_url = f"data:image/png;base64,{qr_base64}"
                qr_resp = whatsapp.send_image_message(
                    instance, 
                    customer_phone, 
                    qr_image_url,
                    caption="🎫 Your Booking QR Code - Show this at boarding"
                )
                result["qr_sent"] = qr_resp.get("success", False)
            except Exception as qr_error:
                logger.error(f"QR code sending error: {qr_error}")
                # Continue even if QR fails
                pass

        # Send agency messages
        if agency_phone:
            resp = whatsapp.send_text_message(instance, agency_phone, agency_msg)
            result["agency_sent"] = resp.get("success", False)

        # Store in-app notification for customer
        db.send_notification(
            booking.get("agency_username"),
            booking.get("username"),
            booking.get("booking_id"),
            f"Booking #{booking.get('booking_id')} confirmed! {booking.get('source')} → {booking.get('destination')} on {booking.get('date')}, Seat: {booking.get('seat')}"
        )

        return result

    except Exception as e:
        logger.error(f"Send booking confirmation error: {e}")
        return result


def send_cancellation_notification(booking: dict) -> dict:
    """
    Send WhatsApp cancellation notification to customer and agency.
    
    Args:
        booking: Full booking dict from database
    
    Returns:
        {"customer_sent": bool, "agency_sent": bool}
    """
    result = {"customer_sent": False, "agency_sent": False}

    try:
        customer_phone = get_user_phone(booking.get("username", ""))
        agency_phone = get_agency_phone(booking.get("agency_username", ""))
        instance = get_agency_whatsapp_instance(booking.get("agency_username", ""))

        if not instance:
            return result

        agency = db.agencies_collection.find_one({"username": booking.get("agency_username")})
        agency_name = agency.get("agency_name", "Bus Agency") if agency else "Bus Agency"

        customer_msg = (
            f"🎫 *TicketHub - Booking Cancelled*\n\n"
            f"Booking ID: #{booking.get('booking_id')}\n"
            f"Route: {booking.get('source')} → {booking.get('destination')}\n"
            f"Date: {booking.get('date')}\n"
            f"Seat: {booking.get('seat')}\n"
            f"Agency: {agency_name}\n\n"
            f"Status: ❌ CANCELLED\n"
            f"Seat has been released and is now available."
        )

        agency_msg = (
            f"📋 *Booking Cancelled!*\n\n"
            f"Booking ID: #{booking.get('booking_id')}\n"
            f"Passenger: {booking.get('passenger_name', 'N/A')}\n"
            f"Route: {booking.get('source')} → {booking.get('destination')}\n"
            f"Date: {booking.get('date')}\n"
            f"Seat: {booking.get('seat')} (now available)\n"
            f"Cancelled by: {booking.get('username')}"
        )

        if customer_phone:
            resp = whatsapp.send_text_message(instance, customer_phone, customer_msg)
            result["customer_sent"] = resp.get("success", False)

        if agency_phone:
            resp = whatsapp.send_text_message(instance, agency_phone, agency_msg)
            result["agency_sent"] = resp.get("success", False)

        # Store cancellation record
        db.cancellations_collection.insert_one({
            "booking_id": booking.get("booking_id"),
            "username": booking.get("username"),
            "agency_username": booking.get("agency_username"),
            "source": booking.get("source"),
            "destination": booking.get("destination"),
            "date": booking.get("date"),
            "seat": booking.get("seat"),
            "cancelled_at": db.datetime.now(),
            "whatsapp_customer": result["customer_sent"],
            "whatsapp_agency": result["agency_sent"]
        })

        return result

    except Exception as e:
        logger.error(f"Send cancellation notification error: {e}")
        return result
