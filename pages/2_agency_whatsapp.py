"""
WhatsApp Settings Page for Agencies
Allows agencies to connect and manage their WhatsApp instance via Evolution API
"""

import streamlit as st
import db
import whatsapp
import logging
import time
import re

logger = logging.getLogger(__name__)

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="WhatsApp Settings - TicketHub Agency",
    page_icon="📱",
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
# CUSTOM CSS
# =====================================================
st.markdown("""
<style>
    .status-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 999px;
        font-weight: 500;
        font-size: 0.9em;
    }
    .status-connected {
        background-color: rgba(16,185,129,0.12);
        color: #10b981;
    }
    .status-pending {
        background-color: rgba(245,158,11,0.12);
        color: #f59e0b;
    }
    .status-error {
        background-color: rgba(239,68,68,0.12);
        color: #ef4444;
    }
    .qr-container {
        text-align: center;
        padding: 30px;
        background: #f3f3f3;
        border-radius: 16px;
        border: 2px dashed #e2e2e2;
        color: #000000;
    }
    .info-box {
        background: rgba(59,130,246,0.08);
        border-left: 4px solid #3b82f6;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# PAGE TITLE
# =====================================================
st.markdown("# 📱 WhatsApp Settings")
st.markdown(f"**Agency**: {agency_username}")
st.divider()

# =====================================================
# CHECK CURRENT INSTANCE
# =====================================================
current_instance = db.get_whatsapp_instance(agency_username)

# =====================================================
# CHECK FOR STALE INSTANCE (DB has record but Evolution API doesn't)
# =====================================================
if current_instance and current_instance.get("instance_name"):
    try:
        live_exists = whatsapp.instance_exists(current_instance["instance_name"])
        if not live_exists:
            st.warning(f"Instance '{current_instance['instance_name']}' not found on server. You may need to recreate it.")
    except Exception:
        pass

# =====================================================
# MAIN TABS
# =====================================================
tab1, tab2, tab3 = st.tabs(["📲 Connection Status", "🔗 Connect WhatsApp", "⚙️ Settings"])

# =====================================================
# TAB 1: CONNECTION STATUS
# =====================================================
with tab1:
    st.markdown("## Current Connection Status")
    
    if current_instance:
        inst_name = current_instance.get("instance_name")
        
        # Check live status from Evolution API
        live_state = "unknown"
        live_connected = False
        api_raw = {}
        try:
            status_data = whatsapp.get_instance_status(inst_name)
            live_state = status_data.get("state", "unknown")
            live_connected = status_data.get("connected", False)
            api_raw = status_data
            print(f"[WA STATUS] instance={inst_name}, state={live_state}, connected={live_connected}, raw={status_data}")
        except Exception as e:
            print(f"[WA STATUS ERROR] {e}")
            live_state = current_instance.get("status", "unknown")
            live_connected = current_instance.get("is_connected", False)
        
        # Also check DB status
        db_connected = current_instance.get("is_connected", False)
        
        # Use whichever says connected (case-insensitive check)
        state_lower = str(live_state).lower().strip()
        is_connected = live_connected or db_connected or state_lower in ("open", "connected")
        
        # Update DB with live status
        if is_connected and not db_connected:
            db.mark_whatsapp_connected(agency_username)
            db.update_whatsapp_status(agency_username, True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if is_connected:
                st.markdown("""
                <div class="status-badge status-connected">
                    CONNECTED
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                **Instance Name**: {inst_name}
                
                **Phone Number**: {current_instance.get('phone_number', 'Not set')}
                
                **Live Status**: {live_state.upper()}
                
                **Connected Since**: {str(current_instance.get('created_at', 'Unknown'))[:10]}
                """)
            
            elif live_state in ("disconnected", "close", "connecting"):
                st.markdown("""
                <div class="status-badge status-pending">
                    DISCONNECTED - NEEDS RECONNECT
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                **Instance Name**: {inst_name}
                
                **Live Status**: {live_state.upper()}
                
                **Created**: {str(current_instance.get('created_at', 'Unknown'))[:10]}
                """)
            
            else:
                st.markdown("""
                <div class="status-badge status-error">
                    NOT CONNECTED
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"**Instance Name**: {inst_name}")
        
        with col2:
            if is_connected:
                st.success("Your WhatsApp is connected and ready to send notifications!")
            else:
                st.warning("Scan the QR code in 'Connect WhatsApp' tab to connect.")
            
            if st.button("Refresh Status", use_container_width=True):
                st.rerun()
    
    else:
        st.markdown("""
        <div class="status-badge status-error">
            NOT CONNECTED
        </div>
        """, unsafe_allow_html=True)
        
        st.warning("No WhatsApp instance configured yet. Go to 'Connect WhatsApp' tab.")

# =====================================================
# TAB 2: CONNECT WHATSAPP
# =====================================================
with tab2:
    st.markdown("## Connect Your WhatsApp Account")
    
    st.markdown("""
    <div class="info-box">
    <strong>How it works:</strong>
    <ul>
    <li>Enter a name for your WhatsApp instance</li>
    <li>Click "Create Instance" to generate a QR code</li>
    <li>Scan the QR code with your phone's WhatsApp</li>
    <li>Your account will be connected automatically</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if current_instance and current_instance.get("is_connected"):
        st.success("✅ Your WhatsApp is already connected. No need to set it up again.")
    else:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            instance_name = st.text_input(
                "Instance Name",
                placeholder="e.g., my-agency-whatsapp",
                help="A unique name for this WhatsApp instance"
            )
        
        with col2:
            st.write("")  # Spacing
        
        if st.button("📲 Create Instance", use_container_width=True, type="primary"):
            if not instance_name or instance_name.strip() == "":
                st.error("❌ Please enter an instance name")
            else:
                # Sanitize instance name for Evolution API (lowercase + hyphens only)
                sanitized_name = re.sub(r'[\s_]+', '-', instance_name.strip().lower())
                sanitized_name = re.sub(r'[^a-z0-9\-]', '', sanitized_name)
                sanitized_name = re.sub(r'-{2,}', '-', sanitized_name).strip('-')
                if len(sanitized_name) < 3:
                    st.error("❌ Instance name too short or invalid. Use 3+ alphanumeric characters.")
                else:
                    with st.spinner("Creating WhatsApp instance on Evolution API..."):
                        # Step 1: Create instance on Evolution API
                        api_result = whatsapp.create_instance(sanitized_name)
                        
                        if api_result.get("success"):
                            # Step 2: Save to database
                            db_result = db.create_whatsapp_instance(
                                agency_username=agency_username,
                                instance_name=sanitized_name
                            )
                            
                            if db_result.get("success"):
                                st.success(f"✅ Instance created: {sanitized_name}")
                                
                                # Wait for instance to initialize on Evolution API
                                with st.spinner("Waiting for instance to initialize..."):
                                    time.sleep(8)
                                
                                # Step 3: Get QR code from Evolution API (with retries)
                                qr_result = {"success": False}
                                with st.spinner("Generating QR code..."):
                                    for attempt in range(3):
                                        qr_result = whatsapp.get_qr_code(sanitized_name)
                                        if qr_result.get("success"):
                                            break
                                        if attempt < 2:
                                            with st.spinner(f"QR not ready, retrying in 5s (attempt {attempt+2}/3)..."):
                                                time.sleep(5)
                                    
                                    if qr_result.get("success"):
                                        qr_base64 = qr_result.get("base64")
                                        
                                        # Update instance with QR
                                        db.update_whatsapp_instance_qr(agency_username, qr_base64)
                                        
                                        st.success("✅ QR code generated successfully!")
                                        
                                        # Display QR code
                                        st.markdown("## Scan This QR Code")
                                        import base64 as b64mod
                                        # Strip data URI prefix if present
                                        raw = qr_base64
                                        if "," in raw and raw.startswith("data:"):
                                            raw = raw.split(",", 1)[1]
                                        try:
                                            img_bytes = b64mod.b64decode(raw)
                                            st.image(img_bytes, width=280, caption="Scan with WhatsApp")
                                        except Exception:
                                            st.code(qr_base64[:80] + "...", language=None)
                                            st.warning("QR image could not render. Copy the raw data above.")
                                        
                                        st.caption("This QR code expires in 5 minutes. After scanning, your WhatsApp will be connected.")
                                        st.info("Once you scan the QR code, check the 'Connection Status' tab to confirm your connection.")
                                        
                                        # Auto-refresh hint
                                        st.markdown("---")
                                        if st.button("🔄 Check Connection Status"):
                                            st.rerun()
                                    else:
                                        st.error(f"❌ Failed to generate QR code: {qr_result.get('message', 'Unknown error')}")
                                        st.info("💡 Tip: Make sure your Evolution API URL and API KEY are correct in the config.")
                            else:
                                st.error(f"❌ Failed to save instance: {db_result.get('message')}")
                        else:
                            st.error(f"❌ Failed on Evolution API: {api_result.get('message')}")
                            st.info("💡 Make sure:\n- Evolution API URL is correct\n- API Key is valid\n- Instance name uses only letters, numbers, and underscores\n- No spaces or special characters")

# =====================================================
# TAB 3: SETTINGS
# =====================================================
with tab3:
    st.markdown("## WhatsApp Instance Settings")
    
    if current_instance:
        st.markdown("### Current Instance Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Instance Name**: `{current_instance.get('instance_name')}`
            
            **Status**: {current_instance.get('status', 'unknown').upper()}
            
            **Is Connected**: {'Yes ✅' if current_instance.get('is_connected') else 'No ❌'}
            """)
        
        with col2:
            st.markdown(f"""
            **Phone Number**: {current_instance.get('phone_number', 'Not registered yet')}
            
            **Created**: {str(current_instance.get('created_at', 'Unknown'))[:10]}
            
            **Last Updated**: {str(current_instance.get('updated_at', 'Unknown'))[:10]}
            """)
        
        st.divider()
        
        # Disconnect / Reset
        st.markdown("### Disconnect WhatsApp")
        st.warning("⚠️ Disconnecting will stop all WhatsApp notifications until you reconnect.")
        
        if st.button("🔌 Disconnect WhatsApp Instance", use_container_width=True, type="secondary"):
            with st.spinner("Disconnecting..."):
                # Try to logout from Evolution API
                logout_result = whatsapp.disconnect_instance(current_instance.get("instance_name"))
                
                # Delete from database
                delete_result = db.delete_whatsapp_instance(agency_username)
                
                if delete_result.get("success"):
                    st.success("✅ WhatsApp instance disconnected successfully")
                    st.info("You can create a new instance anytime from the 'Connect WhatsApp' tab")
                    st.rerun()
                else:
                    st.error("❌ Failed to disconnect: " + delete_result.get("message", "Unknown error"))
    
    else:
        st.info("📌 No WhatsApp instance configured yet. Go to 'Connect WhatsApp' tab to set one up.")

# =====================================================
# FOOTER
# =====================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85em; margin-top: 30px;">
    <p>💡 <strong>Tip:</strong> Once connected, your WhatsApp will receive automatic notifications for bookings and cancellations</p>
    <p>🔒 Your WhatsApp credentials are secure and only used for sending notifications</p>
</div>
""", unsafe_allow_html=True)
