import re
import hashlib
import secrets
from datetime import datetime


def hash_password(password: str) -> str:
    """Hash password with SHA-256 + salt for storage."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash."""
    if "$" not in stored_hash:
        return password == stored_hash
    salt, hashed = stored_hash.split("$", 1)
    return hashlib.sha256((salt + password).encode()).hexdigest() == hashed


def validate_phone(phone: str) -> dict:
    """
    Validate phone number format.
    Accepts: +91XXXXXXXXXX, 0XXXXXXXXXX, 10-digit numbers.
    Returns: {"valid": bool, "message": str, "formatted": str}
    """
    if not phone:
        return {"valid": False, "message": "Phone number is required", "formatted": ""}

    cleaned = re.sub(r'[\s\-\(\)]', '', phone.strip())

    if cleaned.startswith('+91') and len(cleaned) == 13:
        formatted = cleaned
    elif cleaned.startswith('91') and len(cleaned) == 12:
        formatted = '+' + cleaned
    elif cleaned.startswith('0') and len(cleaned) == 11:
        formatted = '+91' + cleaned[1:]
    elif len(cleaned) == 10 and cleaned.isdigit():
        formatted = '+91' + cleaned
    else:
        return {"valid": False, "message": "Invalid phone number format. Use 10-digit Indian number.", "formatted": ""}

    if not re.match(r'^\+91[6-9]\d{9}$', formatted):
        return {"valid": False, "message": "Invalid Indian mobile number. Must start with 6-9.", "formatted": ""}

    return {"valid": True, "message": "Valid phone number", "formatted": formatted}


def validate_password_strength(password: str) -> dict:
    """Validate password meets minimum requirements."""
    if len(password) < 6:
        return {"valid": False, "message": "Password must be at least 6 characters"}
    if not re.search(r'[A-Za-z]', password):
        return {"valid": False, "message": "Password must contain at least one letter"}
    if not re.search(r'\d', password):
        return {"valid": False, "message": "Password must contain at least one number"}
    return {"valid": True, "message": "Strong password"}
