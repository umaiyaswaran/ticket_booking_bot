# 🗄️ Smart Ticket Booking System - Database Structure

## 📊 Collections Overview

### 1. **users** Collection
Stores user login credentials and roles

```json
{
  "_id": ObjectId,
  "username": "testuser",
  "password": "password123",
  "role": "User Booking | Travel Agency",
  "created_at": ISODate("2024-06-08T12:00:00Z")
}
```

**Indexes:**
- `username` (unique)

**Roles:**
- `"User Booking"` - Regular passenger
- `"Travel Agency"` - Transport company

---

### 2. **agencies** Collection
Travel agency details and fleet information

```json
{
  "_id": ObjectId,
  "username": "testagency",
  "agency_name": "Express Travels",
  "routes": [
    {
      "source": "Chennai",
      "destination": "Bangalore"
    },
    {
      "source": "Bangalore",
      "destination": "Mysore"
    }
  ],
  "total_vehicles": 15,
  "seats_per_vehicle": 40,
  "created_at": ISODate("2024-06-08T12:00:00Z")
}
```

**Indexes:**
- `username` (unique)

**Key Fields:**
- `routes` - Array of {source, destination} objects
- `seats_per_vehicle` - Seats available per bus (all buses same capacity)

---

### 3. **bookings** Collection
Ticket booking records with full booking details

```json
{
  "_id": ObjectId,
  "booking_id": 1001,
  "username": "testuser",
  "agency_username": "testagency",
  "source": "Chennai",
  "destination": "Bangalore",
  "date": "2024-06-15",
  "seat": "A1",
  "passenger_name": "John Doe",
  "passenger_age": 25,
  "status": "confirmed",
  "created_at": ISODate("2024-06-08T12:00:00Z")
}
```

**Indexes:**
- `username, date` - For user's bookings lookup

**Status Values:**
- `"confirmed"` - Active booking
- `"cancelled"` - Cancelled booking (soft delete)

**Fields:**
- `booking_id` - Auto-incremented unique identifier
- `username` - Passenger who booked
- `agency_username` - Agency providing the service
- `source` - Starting city
- `destination` - Ending city
- `date` - Travel date (YYYY-MM-DD or DD/MM/YYYY)
- `seat` - Seat identifier (e.g., "A1", "1", etc.)

---

## 🔍 Database Functions

### User Management

#### Create User
```python
from db import create_user

result = create_user(
    username="newuser",
    password="pass123",
    role="User Booking"
)
# Returns: {"success": True, "message": "...", "user_id": "..."}
```

#### Login User
```python
from db import login_user

result = login_user(username="testuser", password="password123")
# Returns: {"success": True, "username": "testuser", "role": "User Booking"}
```

---

### Agency Management

#### Create Agency (during signup)
```python
create_user(
    username="agency1",
    password="pass123",
    role="Travel Agency",
    agency_details={
        "agency_name": "Quick Travels",
        "routes": [
            {"source": "Delhi", "destination": "Mumbai"},
            {"source": "Mumbai", "destination": "Bangalore"}
        ],
        "total_vehicles": 20,
        "seats_per_vehicle": 45
    }
)
```

#### Get Agency Details
```python
from db import get_agency

agency = get_agency(username="testagency")
# Returns: {"agency_name": "...", "routes": [...], "total_vehicles": 15, "seats_per_vehicle": 40}
```

#### Update Agency
```python
from db import update_agency

result = update_agency(
    username="testagency",
    agency_details={
        "agency_name": "Express Travels Updated",
        "routes": [...],
        "total_vehicles": 20,
        "seats_per_vehicle": 50
    }
)
```

#### Get Agencies by Route
```python
from db import get_agencies_by_route

agencies = get_agencies_by_route(source="Chennai", destination="Bangalore")
# Returns: [
#   {
#     "agency_username": "testagency",
#     "agency_name": "Express Travels",
#     "routes": [...],
#     "total_vehicles": 15,
#     "seats_per_vehicle": 40
#   }
# ]
```

#### Search Routes
```python
from db import search_routes

# All routes
all_routes = search_routes()

# Routes from specific source
delhi_routes = search_routes(source="Delhi")

# Routes to specific destination
routes_to_mumbai = search_routes(destination="Mumbai")
```

---

### Booking Management

#### Check Seat Availability
```python
from db import check_seat_availability

is_available = check_seat_availability(
    agency_username="testagency",
    source="Chennai",
    destination="Bangalore",
    date="2024-06-15",
    seat="A1"
)
# Returns: True or False
```

#### Get Available Seats
```python
from db import get_available_seats

available = get_available_seats(
    agency_username="testagency",
    source="Chennai",
    destination="Bangalore",
    date="2024-06-15"
)
# Returns: ["A1", "A2", "B1", "B3", ...]
```

#### Create Booking
```python
from db import create_booking

result = create_booking(
    username="testuser",
    agency_username="testagency",
    source="Chennai",
    destination="Bangalore",
    date="2024-06-15",
    seat="A1",
    passenger_name="John Doe",
    passenger_age=25
)
# Returns: {"success": True, "booking_id": 1001, "message": "Booking confirmed!"}
```

**Validation checks:**
- ✅ Agency exists
- ✅ Route exists in agency
- ✅ Seat is available
- ✅ Creates booking if all checks pass

#### Get User Bookings
```python
from db import get_user_bookings

bookings = get_user_bookings(username="testuser")
# Returns: [
#   {
#     "booking_id": 1001,
#     "username": "testuser",
#     "agency_username": "testagency",
#     "source": "Chennai",
#     "destination": "Bangalore",
#     "date": "2024-06-15",
#     "seat": "A1",
#     "passenger_name": "John Doe",
#     "passenger_age": 25,
#     "status": "confirmed",
#     "created_at": ISODate(...)
#   }
# ]
```

#### Get Agency's Bookings
```python
from db import get_bookings_by_agency

bookings = get_bookings_by_agency(
    agency_username="testagency",
    start_date="2024-06-01",
    end_date="2024-06-30"
)
# Returns: List of all bookings for this agency in date range
```

#### Cancel Booking
```python
from db import cancel_booking

result = cancel_booking(booking_id=1001)
# Returns: True/False
# Sets status to "cancelled" instead of deleting
```

#### Get Booking Details
```python
from db import get_booking_details

booking = get_booking_details(booking_id=1001)
# Returns: Complete booking information
```

---

## 🚀 Common Workflows

### Workflow 1: User Books a Ticket

```python
from db import (
    get_agencies_by_route,
    get_available_seats,
    check_seat_availability,
    create_booking
)

# Step 1: Find agencies for route
agencies = get_agencies_by_route(source="Chennai", destination="Bangalore")
# User chooses an agency

# Step 2: Get available seats
available = get_available_seats(
    agency_username=agencies[0]["agency_username"],
    source="Chennai",
    destination="Bangalore",
    date="2024-06-15"
)
# User selects seat "A1"

# Step 3: Create booking (validation happens inside)
result = create_booking(
    username="testuser",
    agency_username=agencies[0]["agency_username"],
    source="Chennai",
    destination="Bangalore",
    date="2024-06-15",
    seat="A1",
    passenger_name="John Doe",
    passenger_age=25
)

if result["success"]:
    print(f"Booking confirmed! ID: {result['booking_id']}")
else:
    print(f"Booking failed: {result['message']}")
```

### Workflow 2: View and Cancel Booking

```python
from db import get_user_bookings, cancel_booking

# Get all bookings
bookings = get_user_bookings(username="testuser")

# Display bookings
for b in bookings:
    print(f"ID: {b['booking_id']} - {b['source']} to {b['destination']}")

# Cancel a booking
if cancel_booking(booking_id=bookings[0]['booking_id']):
    print("Booking cancelled successfully")
```

### Workflow 3: Agency Manages Routes

```python
from db import get_agency, update_agency

# Get current agency info
agency = get_agency(username="testagency")

# Add new route
new_routes = agency["routes"] + [
    {"source": "Hyderabad", "destination": "Pune"}
]

# Update
result = update_agency(
    username="testagency",
    agency_details={
        **agency,
        "routes": new_routes,
        "total_vehicles": 25  # Also update vehicle count
    }
)
```

---

## 📈 Analytics & Reporting

### Get total bookings for agency
```python
from db import get_bookings_by_agency

bookings = get_bookings_by_agency("testagency")
total = len(bookings)
confirmed = len([b for b in bookings if b["status"] == "confirmed"])
cancelled = len([b for b in bookings if b["status"] == "cancelled"])
```

### Get route revenue
```python
from db import get_bookings_by_agency

bookings = get_bookings_by_agency("testagency")
route_key = "Chennai-Bangalore"
revenue_bookings = [
    b for b in bookings 
    if f"{b['source']}-{b['destination']}" == route_key and b["status"] == "confirmed"
]
```

---

## ⚙️ Database Indexes

**Current indexes for performance:**

| Collection | Field(s) | Type |
|-----------|---------|------|
| users | username | unique |
| agencies | username | unique |
| bookings | username, date | compound |

**Query patterns optimized:**
- Finding user's bookings (by username + date)
- Checking for duplicate usernames
- Agency lookup by username

---

## 🔒 Security Notes

⚠️ **Current Status:** Passwords stored in plain text
- In production: Use bcrypt, scrypt, or similar hashing
- Add salt to prevent rainbow table attacks
- Implement password strength requirements

---

## 🎯 Next Steps

1. **Test the API** - Create test bookings through each workflow
2. **Update app.py** - Use new `create_booking()` instead of `add_booking()`
3. **Build UI** - Add route search, seat selection, availability display
4. **Add Analytics** - Dashboard showing bookings, revenue, utilization
5. **Implement Security** - Add password hashing, input validation
6. **Add Notifications** - Email confirmations, SMS alerts

---

*Last Updated: 2024-06-08*
*Database Version: 2.0 (Multi-Agency)*
