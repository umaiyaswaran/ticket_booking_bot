"""
TicketHub Payment Module
Razorpay integration for secure bus ticket payments.
Handles UPI, Card, Net Banking, QR payments with full transaction tracking.
"""

import razorpay
import hashlib
import hmac
import uuid
import time
import qrcode
import io
import base64
import os
import logging
from datetime import datetime
from pymongo import DESCENDING
from pathlib import Path
from dotenv import load_dotenv

# Load .env
_project_root = Path(__file__).parent
load_dotenv(_project_root / ".env")

logger = logging.getLogger(__name__)

# =============================================
# RAZORPAY API KEYS (from .env, never exposed)
# =============================================
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_T2CMdaj6ZCwKnU")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "fY8QNMeDZwcnm0F8yVyojQbN")

# Initialize Razorpay client (server-side only, never exposed to frontend)
_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# =============================================
# DATABASE COLLECTION
# =============================================
def _get_payments_collection(db_module):
    """Get or create the payments collection."""
    return db_module.db["payments"]


def _get_next_transaction_id(payments_col):
    """Generate unique auto-incrementing transaction ID."""
    last = payments_col.find_one(sort=[("transaction_id", DESCENDING)])
    if last and "transaction_id" in last:
        return last["transaction_id"] + 1
    return 80001


def _generate_razorpay_order_id():
    """Generate unique Razorpay order ID."""
    return f"order_{uuid.uuid4().hex[:16]}"


# =============================================
# FARE CALCULATION
# =============================================
FARE_PER_KM = 2.5
BASE_FARE = 150

# Route distance estimates (km) - for demo; replace with real API
ROUTE_DISTANCES = {
    ("delhi", "mumbai"): 1400,
    ("mumbai", "delhi"): 1400,
    ("chennai", "mumbai"): 1330,
    ("mumbai", "chennai"): 1330,
    ("delhi", "goa"): 1870,
    ("goa", "delhi"): 1870,
    ("bangalore", "chennai"): 350,
    ("chennai", "bangalore"): 350,
    ("delhi", "bangalore"): 2150,
    ("bangalore", "delhi"): 2150,
    ("mumbai", "goa"): 580,
    ("goa", "mumbai"): 580,
    ("hyderabad", "bangalore"): 570,
    ("bangalore", "hyderabad"): 570,
    ("delhi", "jaipur"): 280,
    ("jaipur", "delhi"): 280,
    ("mumbai", "pune"): 150,
    ("pune", "mumbai"): 150,
    ("kolkata", "delhi"): 1450,
    ("delhi", "kolkata"): 1450,
    ("chennai", "bangalore"): 350,
    ("bangalore", "chennai"): 350,
}


def calculate_fare(source, destination, seats=1, agency_username=None):
    """
    Get fare for a route. First checks agency-set fares in DB,
    falls back to auto-calculation if no fare is set.
    Returns fare in INR (integer).
    """
    # 1. Try to get agency-set fare from DB
    if agency_username:
        try:
            import db as _db
            db_fare = _db.get_route_fare(agency_username, source, destination)
            print(f"[CALC FARE] agency={agency_username}, src={source}, dest={destination}, db_fare={db_fare}")
            if db_fare:
                return int(db_fare) * seats
        except Exception as e:
            print(f"[CALC FARE ERROR] {e}")

    # 2. Fallback: auto-calculate from distance
    key = (source.strip().lower(), destination.strip().lower())
    distance = ROUTE_DISTANCES.get(key, 500)
    raw_fare = BASE_FARE + (distance * FARE_PER_KM)
    fare = int(((raw_fare * seats) + 9) // 10 * 10)
    print(f"[CALC FARE] fallback auto-calc: key={key}, distance={distance}, fare={fare}")
    return max(fare, 199)


# =============================================
# PAYMENT INITIATION
# =============================================
def initiate_payment(db, username, source, destination, travel_date,
                     agency_username, seat, passenger_name, fare,
                     payment_method, phone_number=""):
    """
    Create a pending payment record and REAL Razorpay order.
    
    Returns:
        {
            "success": bool,
            "transaction_id": int,
            "razorpay_order_id": str,
            "razorpay_key_id": str,   # Public key for frontend (safe to expose)
            "amount": int,            # Amount in paise
            "fare": int,              # Fare in INR
            "message": str
        }
    """
    try:
        payments_col = _get_payments_collection(db)

        # Duplicate prevention: check if same user+seat+date already has a pending payment
        existing = payments_col.find_one({
            "user_name": username,
            "seat_numbers": seat,
            "travel_date": travel_date,
            "source": {"$regex": f"^{source}$", "$options": "i"},
            "destination": {"$regex": f"^{destination}$", "$options": "i"},
            "payment_status": {"$in": ["PENDING", "SUCCESS"]}
        })
        if existing:
            return {
                "success": False,
                "message": "A payment for this seat is already in progress or completed.",
                "transaction_id": existing.get("transaction_id")
            }

        transaction_id = _get_next_transaction_id(payments_col)
        amount_paise = fare * 100  # Razorpay expects amount in paise

        # Create REAL Razorpay order
        try:
            razorpay_order = _client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"txn_{transaction_id}",
                "notes": {
                    "username": username,
                    "route": f"{source} to {destination}",
                    "seat": seat
                }
            })
            razorpay_order_id = razorpay_order.get("id", "")
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {e}")
            return {"success": False, "message": f"Payment gateway error: {str(e)[:100]}"}

        payment_record = {
            "transaction_id": transaction_id,
            "razorpay_order_id": razorpay_order_id,
            "user_name": username,
            "phone_number": phone_number,
            "source": source,
            "destination": destination,
            "travel_date": travel_date,
            "bus_name": agency_username,
            "seat_numbers": seat,
            "fare": fare,
            "amount": amount_paise,
            "payment_method": payment_method,
            "payment_status": "PENDING",
            "razorpay_payment_id": None,
            "razorpay_signature": None,
            "created_at": datetime.now(),
            "expires_at": datetime.now(),
            "updated_at": datetime.now()
        }

        payments_col.insert_one(payment_record)
        logger.info(f"Payment initiated: TXN#{transaction_id} | Order: {razorpay_order_id} | User: {username} | Fare: ₹{fare}")

        return {
            "success": True,
            "transaction_id": transaction_id,
            "razorpay_order_id": razorpay_order_id,
            "razorpay_key_id": RAZORPAY_KEY_ID,  # Public key - safe to send to frontend
            "amount": amount_paise,
            "fare": fare,
            "message": "Payment order created successfully"
        }

    except Exception as e:
        logger.error(f"Initiate payment error: {e}")
        return {"success": False, "message": f"Payment initiation failed: {str(e)[:100]}"}


# =============================================
# PAYMENT VERIFICATION
# =============================================
def verify_payment(db, transaction_id, razorpay_payment_id, razorpay_order_id, razorpay_signature):
    """
    Verify Razorpay payment signature using HMAC-SHA256.
    Also handles direct UPI manual verification.
    
    Returns:
        {"success": bool, "message": str, "payment_record": dict}
    """
    try:
        payments_col = _get_payments_collection(db)

        # Fetch the payment record
        payment = payments_col.find_one({"transaction_id": int(transaction_id)})
        if not payment:
            return {"success": False, "message": "Payment record not found"}

        # Prevent duplicate verification
        if payment.get("payment_status") == "SUCCESS":
            return {
                "success": True,
                "message": "Payment already verified",
                "payment_record": payment
            }

        # Direct UPI manual verification (skip HMAC check)
        if razorpay_signature == "UPI_MANUAL_VERIFIED":
            payments_col.update_one(
                {"transaction_id": int(transaction_id)},
                {"$set": {
                    "payment_status": "SUCCESS",
                    "razorpay_payment_id": "UPI_DIRECT",
                    "razorpay_signature": "UPI_MANUAL_VERIFIED",
                    "verified_at": datetime.now(),
                    "updated_at": datetime.now()
                }}
            )
            payment = payments_col.find_one({"transaction_id": int(transaction_id)})
            logger.info(f"Payment verified (UPI Direct): TXN#{transaction_id}")
            return {
                "success": True,
                "message": "Payment verified",
                "payment_record": payment
            }

        # HMAC-SHA256 signature verification
        payload = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, razorpay_signature):
            # Signature mismatch - potential tampering
            payments_col.update_one(
                {"transaction_id": int(transaction_id)},
                {"$set": {
                    "payment_status": "FAILED",
                    "failure_reason": "Signature verification failed",
                    "updated_at": datetime.now()
                }}
            )
            logger.warning(f"Payment signature mismatch: TXN#{transaction_id}")
            return {"success": False, "message": "Payment verification failed - invalid signature"}

        # Signature valid - mark as SUCCESS
        payments_col.update_one(
            {"transaction_id": int(transaction_id)},
            {"$set": {
                "payment_status": "SUCCESS",
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
                "verified_at": datetime.now(),
                "updated_at": datetime.now()
            }}
        )

        # Refresh record
        payment = payments_col.find_one({"transaction_id": int(transaction_id)})
        logger.info(f"Payment verified: TXN#{transaction_id} | Razorpay ID: {razorpay_payment_id}")

        return {
            "success": True,
            "message": "Payment verified successfully",
            "payment_record": payment
        }

    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        return {"success": False, "message": f"Verification failed: {str(e)[:100]}"}


# =============================================
# PAYMENT STATUS
# =============================================
def get_payment_status(db, transaction_id):
    """Get current payment status."""
    try:
        payments_col = _get_payments_collection(db)
        payment = payments_col.find_one({"transaction_id": int(transaction_id)})
        if payment:
            return {
                "success": True,
                "status": payment.get("payment_status", "PENDING"),
                "payment": payment
            }
        return {"success": False, "status": "NOT_FOUND"}
    except Exception as e:
        return {"success": False, "status": "ERROR"}


def check_razorpay_order_status(razorpay_order_id):
    """
    Poll Razorpay API to check if an order has been paid.
    Returns: {"paid": bool, "status": str, "payment_id": str|None}
    """
    try:
        order = _client.order.fetch(razorpay_order_id)
        status = order.get("status", "")
        if status == "paid":
            payments = order.get("payments", [])
            payment_id = payments[0]["id"] if payments else None
            return {"paid": True, "status": "PAID", "payment_id": payment_id}
        elif status == "expired":
            return {"paid": False, "status": "EXPIRED", "payment_id": None}
        else:
            return {"paid": False, "status": status.upper(), "payment_id": None}
    except Exception as e:
        logger.error(f"Razorpay order status check error: {e}")
        return {"paid": False, "status": "ERROR", "payment_id": None}


def mark_payment_failed(db, transaction_id, reason="User cancelled or timeout"):
    """Mark a payment as failed."""
    try:
        payments_col = _get_payments_collection(db)
        payments_col.update_one(
            {"transaction_id": int(transaction_id)},
            {"$set": {
                "payment_status": "FAILED",
                "failure_reason": reason,
                "updated_at": datetime.now()
            }}
        )
        return {"success": True}
    except Exception:
        return {"success": False}


# =============================================
# QR CODE GENERATION FOR UPI PAYMENT
# =============================================
def generate_upi_qr(amount, upi_id="ticketbooking@upi", merchant_name="TicketHub"):
    """
    Generate a UPI QR code for manual payment.
    Returns base64 encoded PNG image.
    """
    upi_string = f"upi://pay?pa={upi_id}&pn={merchant_name}&am={amount}&cu=INR&tn=Bus%20Ticket%20Payment"

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(upi_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0a0e14", back_color="#ffffff")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode()


# =============================================
# PAYMENT HISTORY
# =============================================
def get_user_payments(db, username, limit=20):
    """Get payment history for a user."""
    try:
        payments_col = _get_payments_collection(db)
        payments = list(payments_col.find(
            {"user_name": username}
        ).sort("created_at", DESCENDING).limit(limit))
        return payments
    except Exception:
        return []


def get_payment_by_transaction(db, transaction_id):
    """Get a specific payment record."""
    try:
        payments_col = _get_payments_collection(db)
        return payments_col.find_one({"transaction_id": int(transaction_id)})
    except Exception:
        return None


# =============================================
# INIT INDEXES
# =============================================
def init_payment_indexes(db):
    """Create database indexes for payments collection."""
    try:
        payments_col = _get_payments_collection(db)
        payments_col.create_index("transaction_id", unique=True)
        payments_col.create_index("razorpay_order_id")
        payments_col.create_index("razorpay_payment_id")
        payments_col.create_index([("user_name", 1), ("created_at", -1)])
        payments_col.create_index("payment_status")
        payments_col.create_index([("user_name", 1), ("seat_numbers", 1), ("travel_date", 1)])
    except Exception as e:
        logger.error(f"Payment index creation error: {e}")
