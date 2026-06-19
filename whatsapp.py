import requests
import json
import re
import logging
import io
import base64
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
            "integration": "WHATSAPP-BAILEYS",
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
        logger.info(f"Status response: {resp.status_code} - {resp.text[:300]}")

        if resp.status_code not in [200, 201]:
            return {"success": False, "connected": False, "state": "error", "message": f"API returned {resp.status_code}"}

        data = resp.json()
        # Handle multiple possible response formats from Evolution API
        state = (
            data.get("state") or
            data.get("connectionStatus") or
            data.get("status") or
            (data.get("data", {}) if isinstance(data.get("data"), dict) else {}).get("state") or
            (data.get("instance", {}) if isinstance(data.get("instance"), dict) else {}).get("state") or
            (data.get("instance", {}) if isinstance(data.get("instance"), dict) else {}).get("status") or
            "unknown"
        )
        state_lower = str(state).lower().strip()
        connected = state_lower in ("open", "connected", "open", "connecting")
        return {"success": True, "connected": connected, "state": state}
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
    """Send an image with caption via WhatsApp using /message/sendMedia/."""
    try:
        phone = phone_number.replace("+", "").replace(" ", "")
        if not phone.startswith("91") and len(phone) == 10:
            phone = "91" + phone

        # Extract raw base64 if data URI
        if image_url.startswith("data:"):
            raw_b64 = image_url.split(",", 1)[1] if "," in image_url else image_url
        else:
            raw_b64 = image_url

        payload = {
            "number": phone,
            "mediatype": "image",
            "media": raw_b64,
            "caption": caption
        }
        resp = requests.post(
            f"{EVOLUTION_API_URL}/message/sendMedia/{instance_name}",
            headers=HEADERS,
            json=payload,
            timeout=60
        )
        data = resp.json()
        success = resp.status_code in [200, 201]
        if not success:
            logger.error(f"Image send failed: {resp.status_code} - {data}")
        return {"success": success, "data": data}
    except Exception as e:
        logger.error(f"Send image error: {e}")
        return {"success": False, "message": str(e)}


def send_document_message(instance_name: str, phone_number: str, document_base64: str, filename: str = "document.pdf", caption: str = "") -> dict:
    """Send a document (PDF) via WhatsApp. Converts PDF to image and sends via /message/sendMedia/."""
    try:
        phone = phone_number.replace("+", "").replace(" ", "")
        if not phone.startswith("91") and len(phone) == 10:
            phone = "91" + phone

        # Decode PDF bytes
        if document_base64.startswith("data:"):
            raw_b64 = document_base64.split(",", 1)[1] if "," in document_base64 else document_base64
        else:
            raw_b64 = document_base64
        pdf_bytes = base64.b64decode(raw_b64)

        # Convert PDF first page to PNG image
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            img_buf = io.BytesIO(pix.tobytes("png"))
            img_b64 = base64.b64encode(img_buf.read()).decode()
            doc.close()
            logger.info(f"PDF converted to image via PyMuPDF ({len(img_b64)} chars base64)")
        except Exception as fitz_err:
            logger.error(f"PDF to image conversion failed: {fitz_err}")
            return {"success": False, "message": f"PDF conversion failed: {fitz_err}"}

        # Send via /message/sendMedia/ (Evolution API v2 correct endpoint)
        payload = {
            "number": phone,
            "mediatype": "image",
            "media": img_b64,
            "caption": caption
        }
        logger.info(f"Sending PDF-as-image to {phone} via {instance_name} (base64={len(img_b64)} chars)")
        resp = requests.post(
            f"{EVOLUTION_API_URL}/message/sendMedia/{instance_name}",
            headers=HEADERS,
            json=payload,
            timeout=120
        )
        data = resp.json()
        success = resp.status_code in [200, 201]
        if success:
            logger.info(f"PDF image sent successfully to {phone}")
        else:
            logger.error(f"PDF image send failed: {resp.status_code} - {data}")
        return {"success": success, "data": data}

    except Exception as e:
        logger.error(f"Send document error: {e}", exc_info=True)
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
            if isinstance(instances, list):
                for inst in instances:
                    inst_name = inst.get("name") or inst.get("instance_name") or ""
                    if inst_name == instance_name:
                        return True
                    # Also check nested data
                    if isinstance(inst.get("data"), dict):
                        inst_name = inst["data"].get("name") or inst["data"].get("instance_name") or ""
                        if inst_name == instance_name:
                            return True
        return False
    except Exception:
        return False
