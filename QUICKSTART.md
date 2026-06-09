# 🚀 Quick Start Guide - Smart Ticket Booking System

## System is Ready! 🎉

Your complete AI-assisted ticket booking system is now fully functional with:
- ✅ User login/registration
- ✅ Agency login/registration  
- ✅ Intelligent chatbot for bookings
- ✅ Real-time seat availability
- ✅ Agency dashboard with statistics
- ✅ Database integration

---

## Getting Started in 2 Steps

### **Step 1: Start the Application**

```bash
streamlit run app.py
```

Your app will open at: `http://localhost:8501`

---

### **Step 2: Test with Sample Accounts**

#### **Option A: Test User Booking**

1. Click **👤 User Login**
2. Use credentials:
   - Username: `john_user`
   - Password: `password123`
3. Click **Login**

#### **Option B: Test Agency Dashboard**

1. Click **🏢 Agency Login**
2. Use credentials:
   - Username: `express_travel`
   - Password: `agency123`
3. Click **Login**

---

## Complete Booking Flow Demo

### **User Booking a Ticket**

1. **Login** as `john_user` / `password123`

2. **Click "📝 Book Ticket"** button

3. **Chat with Bot:**
   ```
   User: I want to book a ticket from Delhi to Mumbai on 13/07/2026
   ```

4. **Bot will show:**
   ```
   ✅ Found 3 agency(ies) for your route:

   1. **Express Travel**
      Total Seats Available: 50
      Date: 2026-07-13

   2. **Comfort Journey**
      Total Seats Available: 45
      Date: 2026-07-13

   3. **Budget Tours**
      Total Seats Available: 40
      Date: 2026-07-13

   Which agency would you like to book with? (Reply with number 1-3)
   ```

5. **Select Agency:**
   ```
   User: 1
   ```

6. **Bot shows available seats:**
   ```
   ✅ Available seats for 2026-07-13:
   2, 3, 4, 5, 6, 7, 8, 9, 10...

   Which seat would you like? (Enter seat number)
   ```

7. **Choose a seat:**
   ```
   User: 5
   ```

8. **Provide passenger details:**
   ```
   📝 Now let's get your passenger details.
   
   Please provide:
   1. Your full name
   2. Your age

   User: John Doe, 28
   ```

9. **Confirm booking:**
   ```
   🎫 **BOOKING SUMMARY**
   ━━━━━━━━━━━━━━━━━━━━━━━━
   📍 Route: Delhi → Mumbai
   🏢 Agency: Express Travel
   📅 Date: 2026-07-13
   💺 Seat: 5
   👤 Passenger: John Doe
   🎂 Age: 28
   ━━━━━━━━━━━━━━━━━━━━━━━━
   
   Confirm booking? (Reply: 'yes' or 'no')

   User: yes
   ```

10. **Booking confirmed:**
    ```
    ✅ **BOOKING CONFIRMED!**
    ━━━━━━━━━━━━━━━━━━━━━━━━
    📌 Booking ID: 1011
    📍 Route: Delhi → Mumbai
    📅 Date: 2026-07-13
    💺 Seat: 5
    👤 Passenger: John Doe
    ━━━━━━━━━━━━━━━━━━━━━━━━
    ```

---

## Agency Dashboard Features

### **Login as Agency**

1. Use credentials: `express_travel` / `agency123`

### **📊 Statistics Tab**
Shows:
- Total bookings
- Vehicles info
- Seats capacity
- Booking trends chart

### **📋 Bookings Tab**
View all bookings with:
- Passenger names & ages
- Routes & dates
- Seat numbers
- Booking status

### **🛣️ Routes Tab**
View all routes offered by agency

### **⚙️ Settings Tab**
View agency configuration

---

## Available Routes for Testing

| Route | Agencies |
|-------|----------|
| Delhi → Mumbai | Express, Comfort, Budget |
| Delhi → Goa | Express, Comfort |
| Delhi → Jaipur | Budget |
| Mumbai → Bangalore | Comfort |
| Mumbai → Goa | Comfort |
| Mumbai → Pune | Budget |
| Bangalore → Chennai | Comfort |

---

## Sample Test Scenarios

### **Scenario 1: Book and View**
```
1. Login as john_user
2. Book Delhi→Mumbai ticket
3. Click "📋 My Bookings" to see all reservations
4. Try "cancel booking 1009"
```

### **Scenario 2: Multiple Agencies**
```
1. Login as sarah_user
2. Ask bot: "show available routes"
3. Try: "book from Delhi to Goa on 20/07/2026"
4. See multiple agencies available
5. Choose different agency
```

### **Scenario 3: Agency Statistics**
```
1. Login as express_travel (agency)
2. Check 📊 Statistics
3. See "3 bookings" 
4. View 📋 Bookings tab
5. See all passenger details
```

---

## Advanced Features

### **Chatbot Commands**

| Command | Example |
|---------|---------|
| Book | "Book Delhi to Mumbai on 13/07/2026" |
| View Bookings | "show my bookings" |
| Cancel | "cancel booking 1009" |
| Routes | "what routes are available" |
| Help | "help" |

### **Date Formats**
- `2026-07-13` (YYYY-MM-DD)
- `13/07/2026` (DD/MM/YYYY)  
- `13-07-2026` (DD-MM-YYYY)

### **Passenger Info**
- "John Doe, 28"
- "My name is John, age 28"
- "I'm 28 years old named John"

---

## System Architecture

```
┌─────────────────────────────────────┐
│    Streamlit UI (app.py)            │
│  ├─ Login/Registration              │
│  ├─ User Chatbot Interface          │
│  └─ Agency Dashboard                │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    Chatbot Module (chatbot.py)      │
│  ├─ Conversation Manager            │
│  ├─ Route Extraction                │
│  ├─ Booking Flow                    │
│  └─ AI Response Generation          │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    Database Module (db.py)          │
│  ├─ User Management                 │
│  ├─ Booking Management              │
│  ├─ Agency Management               │
│  └─ Route/Seat Availability         │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    MongoDB (Cloud)                  │
│  ├─ users collection                │
│  ├─ agencies collection             │
│  └─ bookings collection             │
└─────────────────────────────────────┘
```

---

## Troubleshooting

### **App won't start**
```bash
# Install dependencies
pip install streamlit pandas openai

# Check MongoDB connection
python -c "import db; db.init_db()"
```

### **No agencies showing**
- Verify agencies were created (check setup output)
- Try exact city names: "Delhi", "Mumbai" (case-sensitive)
- Check agency has routes configured

### **Can't login**
- Double-check username/password
- Verify account was created successfully
- Check MongoDB is accessible

### **Booking fails**
- Verify agency offers that route
- Check seat is available
- Try different seat number

---

## What's Implemented

### ✅ User Features
- [x] Signup/Login
- [x] Chat with AI bot
- [x] Book tickets conversationally
- [x] View bookings
- [x] Cancel bookings
- [x] Search routes

### ✅ Agency Features  
- [x] Agency registration
- [x] View all bookings
- [x] Booking statistics
- [x] Route management
- [x] Passenger tracking

### ✅ Chatbot Features
- [x] Intelligent conversation flow
- [x] Route inquiry
- [x] Agency search
- [x] Seat availability check
- [x] Passenger info collection
- [x] Booking confirmation
- [x] Multi-stage conversation state

### ✅ Database Features
- [x] User authentication
- [x] Booking management
- [x] Agency profiles
- [x] Route tracking
- [x] Seat availability
- [x] Booking statistics

---

## File Structure

```
ticket_booking/
├── 📄 app.py                    # Main Streamlit app
├── 🤖 chatbot.py               # AI chatbot logic
├── 🗄️ db.py                    # Database operations
├── 🚀 setup_test_data.py       # Create test data
├── 📖 README.md                # Full documentation
├── 📋 QUICKSTART.md            # This file
└── 📊 DATABASE_STRUCTURE.md    # Schema details
```

---

## Ready to Test? 🎉

Run this command now:

```bash
streamlit run app.py
```

Then:
1. Login with `john_user` / `password123`
2. Click "📝 Book Ticket"
3. Type: **"I want to book Delhi to Mumbai"**
4. Follow the bot's guidance!

---

**Happy Booking! 🎫**

For detailed documentation, see `README.md`
