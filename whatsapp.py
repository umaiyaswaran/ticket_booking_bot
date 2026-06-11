import requests
import json
import re
import logging
from config import EVOLUTION_API_URL, EVOLUTION_API_KEY
import time

logger = logging.getLogger(__name__)

HEADERS = {
    "apikey": EVOLUTION_API_KEY,
    "Content-Type": "application/json"
}


def validate_api_connection() -> dict:
    """Test Evolution API connectivity and authentication."""
    try:
        resp = requests.get(
            f"{EVOLUTION_API_URL}/instance/fetchInstances",
            headers=HEADERS,
            timeout=10
        )
        if resp.status_code == 200:
            return {"success": True, "message": "API connection successful"}
        elif resp.status_code == 401:
            return {"success": False, "message": "Invalid API key", "status_code": 401}
        elif resp.status_code == 403:
            return {"success": False, "message": "Access denied. Check API key permissions", "status_code": 403}
        else:
            return {"success": False, "message": f"API error: {resp.status_code}", "status_code": resp.status_code}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "Cannot connect to API server. Check URL."}
    except requests.exceptions.Timeout:
        return {"success": False, "message": "API request timeout. Server not responding."}
    except Exception as e:
        return {"success": False, "message": f"Connection error: {str(e)}"}


def create_instance(instance_name: str, phone_number: str = "") -> dict:
    """Create a new Evolution API instance for an agency with enhanced error handling."""
    try:
        # Validate and sanitize instance name
        if not instance_name or len(instance_name) < 3:
            return {"success": False, "message": "Instance name must be at least 3 characters"}
        
        # Sanitize: lowercase, replace underscores/spaces with hyphens, remove invalid chars
        sanitized = instance_name.strip().lower()
        sanitized = re.sub(r'[\s_]+', '-', sanitized)
        sanitized = re.sub(r'[^a-z0-9\-]', '', sanitized)
        sanitized = re.sub(r'-{2,}', '-', sanitized)
        sanitized = sanitized.strip('-')
        
        if len(sanitized) < 3:
            return {"success": False, "message": f"Instance name '{instance_name}' is invalid after sanitization. Use lowercase letters, numbers, and hyphens."}
        
        instance_name = sanitized
        
        # Check if instance already exists
        instances_check = requests.get(
            f"{EVOLUTION_API_URL}/instance/fetchInstances",
            headers=HEADERS,
            timeout=10
        )
        if instances_check.status_code == 200:
            existing = instances_check.json()
            if isinstance(existing, list):
                for inst in existing:
                    if inst.get("name") == instance_name or inst.get("instance_name") == instance_name:
                        return {"success": False, "message": f"Instance '{instance_name}' already exists"}
        
        payload = {
            "instanceName": instance_name,
            "qrcode": True
        }
        
        logger.info(f"Creating instance: {instance_name}")
        logger.info(f"Payload: {json.dumps(payload)}")
        
        resp = requests.post(
            f"{EVOLUTION_API_URL}/instance/create",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        
        logger.info(f"Create instance response: {resp.status_code} - {resp.text[:500]}")
        
        if resp.status_code in [200, 201]:
            data = resp.json()
            logger.info(f"Instance created: {instance_name} -> {data}")
            return {"success": True, "data": data, "instance_name": instance_name, "message": "Instance created successfully"}
        elif resp.status_code == 400:
            error_detail = resp.text[:500] if resp.text else "No details"
            return {"success": False, "message": f"Invalid request (400): {error_detail}", "status_code": 400}
        elif resp.status_code == 401:
            return {"success": False, "message": "Invalid API key", "status_code": 401}
        elif resp.status_code == 409:
            return {"success": False, "message": f"Instance '{instance_name}' already exists", "status_code": 409}
        else:
            error_text = resp.text if resp.text else resp.reason
            return {"success": False, "message": f"API error {resp.status_code}: {error_text[:200]}", "status_code": resp.status_code}
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Create instance connection error: {e}")
        return {"success": False, "message": f"Cannot connect to API server: {str(e)[:100]}"}
    except requests.exceptions.Timeout as e:
        logger.error(f"Create instance timeout: {e}")
        return {"success": False, "message": "API request timeout. Server not responding."}
    except Exception as e:
        logger.error(f"Create instance error: {e}")
        return {"success": False, "message": f"Error: {str(e)[:200]}"}


def get_qr_code(instance_name: str) -> dict:
    """Get QR code for connecting WhatsApp."""
    try:
        resp = requests.get(
            f"{EVOLUTION_API_URL}/instance/connect/{instance_name}",
            headers=HEADERS,
            timeout=30
        )
        logger.info(f"QR response status: {resp.status_code}")
        logger.info(f"QR response: {resp.text[:200]}")
        data = resp.json()
        if isinstance(data, dict):
            # Try multiple field names Evolution API might use
            base64_str = (
                data.get("base64") or
                data.get("qr") or
                data.get("code") or
                (data.get("data", {}) if isinstance(data.get("data"), dict) else {}).get("base64")
            )
            if base64_str:
                return {"success": True, "base64": base64_str}
        return {"success": False, "message": f"No QR in response: {str(data)[:200]}"}
    except Exception as e:
        logger.error(f"Get QR error: {e}")
        return {"success": False, "message": str(e)}


def get_instance_status(instance_name: str) -> dict:
    """Check if an instance is connected."""
    try:
        resp = requests.get(
            f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}",
            headers=HEADERS,
            timeout=15
        )
        data = resp.json()
        state = data.get("state", data.get("connectionStatus", "unknown"))
        return {"success": True, "connected": state in ("open", "connected"), "state": state}
    except Exception as e:
        logger.error(f"Instance status error: {e}")
        return {"success": False, "connected": False, "state": "error"}


def send_text_message(instance_name: str, phone_number: str, message: str) -> dict:
    """Send a text message via WhatsApp."""
    try:
        phone = phone_number.replace("+", "").replace(" ", "")
        if not phone.startswith("91") and len(phone) == 10:
            phone = "91" + phone

        payload = {
            "number": phone,
            "text": message
        }
        resp = requests.post(
            f"{EVOLUTION_API_URL}/message/sendText/{instance_name}",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        data = resp.json()
        success = resp.status_code in [200, 201]
        logger.info(f"Message sent to {phone}: {success}")
        return {"success": success, "data": data}
    except Exception as e:
        logger.error(f"Send message error: {e}")
        return {"success": False, "message": str(e)}


def send_image_message(instance_name: str, phone_number: str, image_url: str, caption: str = "") -> dict:
    """Send an image with caption via WhatsApp."""
    try:
        phone = phone_number.replace("+", "").replace(" ", "")
        if not phone.startswith("91") and len(phone) == 10:
            phone = "91" + phone

        payload = {
            "number": phone,
            "caption": caption,
            "media": image_url
        }
        resp = requests.post(
            f"{EVOLUTION_API_URL}/message/sendImage/{instance_name}",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        data = resp.json()
        success = resp.status_code in [200, 201]
        return {"success": success, "data": data}
    except Exception as e:
        logger.error(f"Send image error: {e}")
        return {"success": False, "message": str(e)}


def disconnect_instance(instance_name: str) -> dict:
    """Logout/close an instance connection without deleting it."""
    try:
        resp = requests.put(
            f"{EVOLUTION_API_URL}/instance/logout/{instance_name}",
            headers=HEADERS,
            timeout=15
        )
        if resp.status_code in [200, 201, 204]:
            return {"success": True}
        # Fallback: try GET logout
        resp2 = requests.get(
            f"{EVOLUTION_API_URL}/instance/logout/{instance_name}",
            headers=HEADERS,
            timeout=15
        )
        return {"success": resp2.status_code in [200, 201, 204]}
    except Exception as e:
        logger.error(f"Disconnect error: {e}")
        return {"success": False, "message": str(e)}


def delete_instance(instance_name: str) -> dict:
    """Permanently delete an instance."""
    try:
        resp = requests.delete(
            f"{EVOLUTION_API_URL}/instance/delete/{instance_name}",
            headers=HEADERS,
            timeout=15
        )
        return {"success": resp.status_code in [200, 204]}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return {"success": False, "message": str(e)}


def instance_exists(instance_name: str) -> bool:
    """Check if instance exists on Evolution API."""
    try:
        resp = requests.get(
            f"{EVOLUTION_API_URL}/instance/fetchInstances",
            headers=HEADERS,
            timeout=10
        )
        if resp.status_code == 200:
            instances = resp.json()
            return any(inst.get("name") == instance_name for inst in instances)
        return False
    except Exception:
        return False
