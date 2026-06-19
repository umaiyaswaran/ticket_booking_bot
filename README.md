# 🎫 Smart Ticket Booking System - Complete Setup

## System Overview

Your ticket booking system is now fully AI-assisted with the following features:

### ✅ Features Implemented

#### **1. User Management**
- User signup/login
- Travel Agency signup/login  
- Role-based access control

#### **2. Intelligent Chatbot**
- Conversational booking flow
- Route inquiry
- Agency availability check
- Seat selection with real-time availability
- Passenger information collection
- Booking confirmation

#### **3. Database Functions**
- User authentication
- Booking management
- Agency profile management
- Route and seat availability tracking
- Booking statistics

#### **4. User Interface**
- Modern Streamlit dashboard
- Login/Registration pages
- AI Chatbot interface
- Agency Dashboard with:
  - Booking statistics
  - Booking history
  - Route management
  - Agency settings

---

## How to Use

### **Starting the Application**

```bash
streamlit run app.py
```

The app will start on `http://localhost:8501`

---

## User Workflow

### **1. User Booking a Ticket**

1. **Login/Sign Up**
   - Click "👤 User Login" tab
   - Create account or login with existing credentials

2. **Start Booking**
   - Click "📝 Book Ticket" button
   - Chat with bot: "I want to book a ticket from Delhi to Mumbai on 13/07/2026"

3. **Bot will:**
   - ✅ Find available agencies for your route
   - ✅ Show available seats
   - ✅ Collect your passenger details (name, age)
   - ✅ Confirm booking details
   - ✅ Create booking and store in database

4. **View Bookings**
   - Click "📋 My Bookings" to see all your reservations
   - Click "❌ Cancel" to cancel any booking

### **Example Conversation**

```
You: I want to book a ticket from Delhi to Mumbai on 13/07/2026

Bot: Found 3 agencies for this route:
1. Express Travel
2. Comfort Journey
3. Budget Tours

Which agency would you like? (1, 2, or 3)

You: 1

Bot: Available seats: 1, 3, 5, 7, 9, 12, 15
Which seat do you prefer?

You: 5

Bot: Now let's get your passenger details.
Please provide your name and age (format: John, 25)

You: Rajesh Kumar, 28

Bot: [Shows booking summary]
Confirm booking? (yes/no)

You: yes

Bot: ✅ BOOKING CONFIRMED!
Booking ID: 1001
```

---

## Agency Workflow

### **1. Agency Setup**

1. **Register Agency**
   - Click "🏢 Agency Login" tab
   - Click "📝 Register"
   - Fill in:
     - Agency Name
     - Username/Password
     - Total Vehicles
     - Seats Per Vehicle
     - Routes (format: City1-City2, City3-City4)

2. **Example Routes Entry:**
   ```
   Delhi-Mumbai, Mumbai-Bangalore, Delhi-Goa
   ```

### **2. Agency Dashboard**

After login, agencies can:

#### **📊 Statistics Tab**
- Total bookings count
- Vehicle information
- Booking trends chart
- Recent booking data

#### **📋 Bookings Tab**
- View all confirmed bookings
- Passenger details
- Route information
- Booking status
- Summary statistics

#### **🛣️ Routes Tab**
- View all available routes
- Number of routes offered

#### **⚙️ Settings Tab**
- Current configuration
- Agency details

---

## Technical Details

### **Database Collections**

1. **users**
   - username (unique)
   - password
   - role (User / Travel Agency)
   - created_at

2. **agencies**
   - username (unique)
   - agency_name
   - routes: [{source, destination}]
   - total_vehicles
   - seats_per_vehicle
   - created_at

3. **bookings**
   - booking_id (unique)
   - username (user who booked)
   - agency_username (agency providing service)
   - source, destination
   - date, seat
   - passenger_name, passenger_age
   - status (confirmed/cancelled)
   - created_at

---

## Chatbot Commands

| Command | Example | Function |
|---------|---------|----------|
| **Book Ticket** | "book Delhi to Mumbai on 13/07/2026" | Start booking flow |
| **Show Bookings** | "show my bookings" | List your reservations |
| **Cancel Booking** | "cancel booking 1001" | Cancel a ticket |
| **View Routes** | "what routes are available" | List all routes |
| **Help** | "help" | Display command menu |

---

## Advanced Chat Features

### **Date Formats Supported**
- YYYY-MM-DD (2026-06-13)
- DD/MM/YYYY (13/06/2026)
- DD-MM-YYYY (13-06-2026)

### **Seat Number Formats**
- Numeric: 1, 12, 25
- Alphanumeric: A1, B12, C5

### **Passenger Info Extraction**
- "My name is John, age 28"
- "John, 28"
- "I'm 28 years old, name is John"

---

## Key Functions Reference

### **Database Functions (db.py)**

```python
# User Management
db.create_user(username, password, role, agency_details)
db.login_user(username, password)

# Booking Management
db.create_booking(username, agency_username, source, destination, date, seat)
db.get_user_bookings(username)
db.get_bookings_by_agency(agency_username)
db.cancel_booking(booking_id)

# Route & Seat Management
db.get_agencies_by_route(source, destination)
db.get_available_seats(agency_username, source, destination, date)
db.check_seat_availability(agency_username, source, destination, date, seat)
db.search_routes(source, destination)
```

### **Chatbot Functions (chatbot.py)**

```python
# Main processing
process_message(user_message, username)

# Conversation management
get_conversation(username)

# Extraction functions
extract_route_info(text)
extract_date(text)
extract_passenger_info(text)
extract_seat(text)

# Booking handlers
handle_route_inquiry(conv, message)
handle_agency_selection(conv, message)
handle_seat_selection(conv, message)
handle_passenger_info(conv, message)
handle_booking_confirmation(conv, message, username)
```

---

## File Structure

```
ticket_booking/
├── app.py                 # Main Streamlit application
├── db.py                 # Database operations
├── chatbot.py            # AI chatbot logic
├── config.py             # Configuration
├── main.py               # FastAPI (optional)
├── chatbot_test.py       # Testing utilities
└── DATABASE_STRUCTURE.md # Schema documentation
```

---

## Troubleshooting

### **Connection Issues**
If MongoDB connection fails:
1. Check internet connection
2. Verify MongoDB Atlas credentials
3. Check IP whitelist in MongoDB

### **Chatbot Not Responding**
1. Check API key validity
2. Ensure internet connectivity
3. Check OpenRouter service status

### **No Available Agencies**
1. Verify agency has been created
2. Check if route is configured correctly
3. Ensure agency status is active

---

## Next Steps / Enhancements

- [ ] Payment gateway integration
- [ ] Email confirmation system
- [ ] SMS notifications
- [ ] Multi-language support
- [ ] Mobile app development
- [ ] Advanced analytics
- [ ] Referral system
- [ ] Rating & reviews

---

## API Endpoints (if using FastAPI)

```
GET  /                  # Health check
POST /chat              # Send message to chatbot
POST /book              # Create booking
GET  /bookings          # Get user bookings
```

---

## Support

For issues or questions, check the **Help** section in the chatbot or contact support.

---

**System Status: ✅ Ready to Use**

Last Updated: 2026-06-08
Version: 1.0.0
