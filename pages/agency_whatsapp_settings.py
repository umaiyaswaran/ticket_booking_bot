"""
Agency WhatsApp Settings Page
Allows agencies to create and manage WhatsApp instances
"""

import streamlit as st
import db
import whatsapp
import json
from datetime import datetime

def render_whatsapp_settings():
    """Render the WhatsApp settings page for agencies"""
    
    st.markdown("### 📱 WhatsApp Settings")
    st.markdown("---")
    
    agency_username = st.session_state.get("user")
    if not agency_username:
        st.error("❌ Please login first")
        return
    
    # Get current instance
    current_instance = db.get_whatsapp_instance(agency_username)
    
    # Tabs: Setup, Status, Help
    tab1, tab2, tab3 = st.tabs(["⚙️ Setup Instance", "📊 Connection Status", "❓ Help"])
    
    # ==========================================
    # TAB 1: SETUP INSTANCE
    # ==========================================
    with tab1:
        if current_instance and current_instance.get("is_connected"):
            st.success("✅ WhatsApp is connected and active!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", "Connected")
            with col2:
                st.metric("Instance", current_instance.get("instance_name", "N/A"))
            with col3:
                st.metric("Phone", current_instance.get("phone_number", "N/A"))
            
            if st.button("🔄 Reconnect WhatsApp", use_container_width=True):
                st.session_state.whatsapp_action = "reconnect"
                st.rerun()
            
            st.markdown("---")
            if st.button("❌ Disconnect WhatsApp", use_container_width=True):
                result = db.delete_whatsapp_instance(agency_username)
                if result["success"]:
                    st.success("✅ WhatsApp disconnected successfully")
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")
        
        else:
            st.info("📌 Set up WhatsApp to send booking confirmations and notifications to customers")
            
            # Step 1: Instance creation
            st.markdown("#### Step 1️⃣: Create Instance")
            
            instance_name = st.text_input(
                "Instance Name",
                placeholder="e.g., my_agency_whatsapp",
                help="Unique name for your WhatsApp instance (alphanumeric, underscore, hyphen only)"
            )
            
            if st.button("🚀 Create Instance", use_container_width=True, type="primary"):
                if not instance_name:
                    st.error("❌ Please enter an instance name")
                elif len(instance_name) < 3:
                    st.error("❌ Instance name must be at least 3 characters")
                else:
                    # Create instance in Evolution API
                    with st.spinner("🔄 Creating instance..."):
                        api_result = whatsapp.create_instance(instance_name)
                    
                    if api_result.get("success"):
                        # Store in database
                        db_result = db.create_whatsapp_instance(agency_username, instance_name)
                        if db_result.get("success"):
                            st.success(f"✅ Instance '{instance_name}' created successfully!")
                            st.session_state.whatsapp_instance_name = instance_name
                            st.rerun()
                        else:
                            st.error(f"❌ Database error: {db_result['message']}")
                    else:
                        st.error(f"❌ API Error: {api_result.get('message', 'Unknown error')}")
                        st.info("**Troubleshooting tips:**")
                        st.write("""
                        - Check that your instance name is unique
                        - Instance name should be lowercase
                        - No special characters (only letters, numbers, -, _)
                        - Contact support if the error persists
                        """)
            
            # Step 2: Get QR Code
            if current_instance and current_instance.get("status") == "pending_qr":
                st.markdown("---")
                st.markdown("#### Step 2️⃣: Scan QR Code")
                
                instance_name = current_instance.get("instance_name")
                
                if st.button("📷 Generate QR Code", use_container_width=True):
                    with st.spinner("🔄 Generating QR code..."):
                        qr_result = whatsapp.get_qr_code(instance_name)
                    
                    if qr_result.get("success"):
                        qr_base64 = qr_result.get("base64")
                        
                        # Update database with QR code
                        db.update_whatsapp_instance_qr(agency_username, qr_base64)
                        
                        # Display QR code
                        st.markdown("Scan this QR code with your WhatsApp phone number:")
                        st.markdown(f'<img src="data:image/png;base64,{qr_base64}" style="width:300px; margin: 20px 0;">', unsafe_allow_html=True)
                        
                        st.info("""
                        📱 **Instructions:**
                        1. Open WhatsApp on your phone
                        2. Go to Settings → Linked Devices → Link a Device
                        3. Point your phone camera at this QR code
                        4. Confirm the linking on your phone
                        """)
                        
                        # Polling for connection status
                        st.markdown("---")
                        if st.button("✅ QR Code Scanned", use_container_width=True):
                            with st.spinner("⏳ Waiting for connection..."):
                                import time
                                max_attempts = 10
                                for attempt in range(max_attempts):
                                    status = whatsapp.get_instance_status(instance_name)
                                    if status.get("connected"):
                                        db.mark_whatsapp_connected(agency_username)
                                        st.success("✅ WhatsApp connected successfully!")
                                        st.balloons()
                                        time.sleep(1)
                                        st.rerun()
                                    time.sleep(1)
                                
                                st.warning("⏱️ Connection timeout. Please try again.")
                    else:
                        st.error(f"❌ QR Code Error: {qr_result.get('message', 'Unknown error')}")
    
    # ==========================================
    # TAB 2: CONNECTION STATUS
    # ==========================================
    with tab2:
        if current_instance:
            st.markdown("#### Instance Information")
            
            info_cols = st.columns(2)
            with info_cols[0]:
                st.write("**Instance Name:** " + current_instance.get("instance_name", "N/A"))
                st.write("**Status:** " + ("🟢 Connected" if current_instance.get("is_connected") else "🔴 " + current_instance.get("status", "Unknown")))
            with info_cols[1]:
                st.write("**Phone Number:** " + (current_instance.get("phone_number") or "Not linked yet"))
                st.write("**Created:** " + (str(current_instance.get("created_at")).split()[0] if current_instance.get("created_at") else "N/A"))
            
            st.markdown("---")
            
            # Test notification
            st.markdown("#### Test Notification")
            test_phone = st.text_input(
                "Test Phone Number",
                placeholder="+919876543210 or 9876543210",
                help="Phone number to send test message to"
            )
            
            test_message = st.text_area(
                "Test Message",
                value="🎫 TicketHub Test - WhatsApp integration is working!",
                height=80
            )
            
            if st.button("📤 Send Test Message", use_container_width=True):
                if not test_phone:
                    st.error("❌ Please enter a phone number")
                else:
                    with st.spinner("📤 Sending message..."):
                        if current_instance.get("is_connected"):
                            result = whatsapp.send_text_message(
                                current_instance.get("instance_name"),
                                test_phone,
                                test_message
                            )
                            if result.get("success"):
                                st.success("✅ Test message sent successfully!")
                            else:
                                st.error(f"❌ {result.get('message', 'Failed to send message')}")
                        else:
                            st.error("❌ WhatsApp instance is not connected")
        else:
            st.info("📌 No WhatsApp instance configured. Set up one in the Setup tab.")
    
    # ==========================================
    # TAB 3: HELP & TROUBLESHOOTING
    # ==========================================
    with tab3:
        st.markdown("#### ❓ Frequently Asked Questions")
        
        with st.expander("❓ What is a WhatsApp Instance?"):
            st.write("""
            A WhatsApp Instance is a virtual connection between your agency and WhatsApp using the Evolution API.
            It allows you to send automated booking confirmations and notifications to customers.
            """)
        
        with st.expander("❓ Why is my QR code not generating?"):
            st.write("""
            **Possible reasons:**
            1. Evolution API server might be down (check your internet)
            2. Invalid API credentials in settings
            3. Instance name conflicts with existing instances
            4. Server timeout - try again in a moment
            
            **Solution:** Contact support or try creating with a different instance name.
            """)
        
        with st.expander("❓ Connection fails after scanning QR code"):
            st.write("""
            **Try these steps:**
            1. Make sure you're using the primary WhatsApp account
            2. Disable WhatsApp on your phone temporarily
            3. Scan the QR code again
            4. Wait 5-10 seconds before clicking "QR Code Scanned"
            5. Check your internet connection
            
            If the issue persists, disconnect and create a new instance.
            """)
        
        with st.expander("❓ Can I use WhatsApp Business API?"):
            st.write("""
            Currently, only personal WhatsApp accounts are supported through Baileys integration.
            WhatsApp Business API support will be added in future updates.
            """)
        
        with st.expander("❓ Are messages free?"):
            st.write("""
            Yes! Messages sent through WhatsApp Web (Baileys) are free and count as regular chats.
            There are no per-message charges through this integration.
            """)
        
        st.markdown("---")
        st.markdown("#### 🔗 Support")
        st.info("""
        **Need help?**
        - Email: support@tickethub.com
        - WhatsApp: +919876543210
        - Documentation: https://docs.tickethub.com/whatsapp-setup
        """)
