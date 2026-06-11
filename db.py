from pymongo import MongoClient, DESCENDING
from datetime import datetime
import string
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# =========================
# MongoDB Connection
# =========================
MONGO_URI = os.getenv("MONGO_URI", "")

if not MONGO_URI:
    _user = quote_plus(os.getenv("MONGO_USER", "Umaiyaswaran"))
    _pass = quote_plus(os.getenv("MONGO_PASS", "Password_7585"))
    _host = os.getenv("MONGO_HOST", "cluster0.x706nl9.mongodb.net")
    _db = os.getenv("MONGO_DB", "ticket_booking")
    MONGO_URI = f"mongodb+srv://{_user}:{_pass}@{_host}/{_db}?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000, socketTimeoutMS=5000)

db = client["ticket_booking"]

# Collections
bookings_collection = db["bookings"]
users_collection = db["users"]
agencies_collection = db["agencies"]
notifications_collection = db["notifications"]
buses_collection = db["buses"]
cancellations_collection = db["cancellations"]
whatsapp_instances_collection = db["whatsapp_instances"]
admins_collection = db["admins"]
revenue_collection = db["revenue"]


# =========================
# Init DB
# =========================
def init_db():
    try:
        client.admin.command("ping")
        users_collection.create_index("username", unique=True)
        bookings_collection.create_index([("username", 1), ("date", 1)])
        bookings_collection.create_index("agency_username")
        bookings_collection.create_index("booking_id")
        agencies_collection.create_index("username", unique=True)
        buses_collection.create_index("agency_username")
        cancellations_collection.create_index("booking_id")
        whatsapp_instances_collection.create_index("agency_username", unique=True)
        admins_collection.create_index("username", unique=True)
        revenue_collection.create_index([("agency_username", 1), ("date", 1)])
    except Exception as e:
        print(f"MongoDB Connection Failed: {e}")


# =========================
# Get Next Booking ID
# =========================
def get_next_booking_id():
    last = bookings_collection.find_one(sort=[("booking_id", DESCENDING)])

    if last and "booking_id" in last:
        return last["booking_id"] + 1

    return 1001


# =========================
# Add Booking (OLD STYLE - Legacy Support)
# =========================
def add_booking(name, age, source, destination, date, seat):
    """
    Legacy function for backward compatibility.
    Creates booking without agency association.
    """
    try:
        booking_id = get_next_booking_id()

        booking_data = {
            "booking_id": booking_id,
            "username": "guest",  # Legacy support
            "agency_username": None,
            "name": name,
            "age": age,
            "source": source,
            "destination": destination,
            "date": date,
            "seat": seat,
            "status": "confirmed",
            "created_at": datetime.now()
        }
        
        print(f"\n INSERTING BOOKING:")
        print(f"   Data: {booking_data}")

        result = bookings_collection.insert_one(booking_data)

        print(f" INSERTED SUCCESSFULLY:")
        print(f"   MongoDB ObjectID: {result.inserted_id}")
        print(f"   Booking ID: {booking_id}")
        print(f"   Acknowledged: {result.acknowledged}")

        return booking_id

    except Exception as e:
        print(f" INSERT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


# =========================
# Get All Bookings (ALL)
# =========================
def get_bookings():
    try:
        result = []

        bookings_found = bookings_collection.find({"status": {"$ne": "cancelled"}})
        count = 0
        
        for booking in bookings_found:
            count += 1
            result.append((
                booking.get("booking_id"),      # [0]
                booking.get("name"),             # [1]
                booking.get("age"),              # [2]
                booking.get("destination"),      # [3]
                booking.get("date"),             # [4]
                booking.get("seat"),             # [5]
                booking.get("source")            # [6]
            ))
        
        print(f"\n RETRIEVED {count} BOOKINGS FROM MONGODB")
        
        return result
    
    except Exception as e:
        print(f" GET BOOKINGS ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []


# =========================
# Get User Bookings
# =========================
def get_user_bookings(username):
    """Get all bookings for a specific user"""
    try:
        result = []
        
        bookings_found = bookings_collection.find({"username": username, "status": {"$ne": "cancelled"}})
        count = 0
        
        for booking in bookings_found:
            count += 1
            # Handle both legacy "name" and new "passenger_name" fields
            passenger_name = booking.get("passenger_name") or booking.get("name", "N/A")
            passenger_age = booking.get("passenger_age") or booking.get("age", "N/A")
            
            result.append({
                "booking_id": booking.get("booking_id"),
                "username": booking.get("username"),
                "agency_username": booking.get("agency_username"),
                "passenger_name": passenger_name,
                "passenger_age": passenger_age,
                "source": booking.get("source"),
                "destination": booking.get("destination"),
                "date": booking.get("date"),
                "seat": booking.get("seat"),
                "status": booking.get("status", "confirmed"),
                "created_at": booking.get("created_at")
            })
        
        print(f" RETRIEVED {count} BOOKINGS FOR USER: {username}")
        return result
    
    except Exception as e:
        print(f" GET USER BOOKINGS ERROR: {e}")
        return []


# =========================
# Cancel Booking
# =========================
def cancel_booking(booking_id):
    """Cancel a booking and return full booking data for notifications."""
    try:
        booking = bookings_collection.find_one({"booking_id": int(booking_id)})
        if not booking:
            return {"success": False, "message": "Booking not found"}
        
        result = bookings_collection.update_one(
            {"booking_id": int(booking_id)},
            {"$set": {"status": "cancelled"}}
        )
        
        if result.modified_count > 0:
            print(f" Booking {booking_id} cancelled successfully")
            return {"success": True, "message": "Booking cancelled successfully", "booking": booking}
        else:
            print(f" Booking {booking_id} not found")
            return {"success": False, "message": "Booking not found"}
    except Exception as e:
        print(f" CANCEL BOOKING ERROR: {e}")
        return {"success": False, "message": str(e)}


# =========================
# USER AUTHENTICATION FUNCTIONS
# =========================

# =========================
# Create User (Signup)
# =========================
def create_user(username, password, role, agency_details=None, gender_option=None, full_name=None, age=None, phone=None):
    """Create a new user account (User or Travel Agency) with password hashing."""
    try:
        # Check if user already exists
        if users_collection.find_one({"username": username}):
            return {"success": False, "message": "Username already exists"}
        
        # Hash password
        from auth import hash_password
        hashed_pw = hash_password(password)
        
        user_data = {
            "username": username,
            "password": hashed_pw,
            "role": role,
            "gender": gender_option,
            "full_name": full_name,
            "age": age,
            "phone": phone or "",
            "created_at": datetime.now()
        }
        
        result = users_collection.insert_one(user_data)
        
        # If Travel Agency role, create agency profile
        if role == "Travel Agency" and agency_details:
            # Convert routes from list of dicts to proper format
            routes = agency_details.get("routes", [])
            if isinstance(routes[0], str) if routes else False:
                # Convert from list of strings to list of dicts
                routes = [{"source": r.split("-")[0], "destination": r.split("-")[1]} 
                         for r in routes if "-" in r]
            
            agency_data = {
                "username": username,
                "agency_name": agency_details.get("agency_name", ""),
                "routes": routes,
                "total_vehicles": int(agency_details.get("total_vehicles", 0)),
                "seats_per_vehicle": int(agency_details.get("seats_per_vehicle", 0)),
                "bus_type": agency_details.get("bus_type", "Standard (2x2)"),
                "created_at": datetime.now()
            }
            agencies_collection.insert_one(agency_data)
        
        return {"success": True, "message": "Account created successfully!", "user_id": str(result.inserted_id)}
    
    except Exception as e:
        print(f" CREATE USER ERROR: {e}")
        return {"success": False, "message": str(e)}


# =========================
# Login User
# =========================
def login_user(username, password):
    """Login with password hashing support."""
    try:
        user = users_collection.find_one({"username": username})
        
        if user:
            stored_pw = user.get("password", "")
            from auth import verify_password
            if verify_password(password, stored_pw):
                return {
                    "success": True,
                    "message": "Login successful!",
                    "username": user.get("username"),
                    "role": user.get("role")
                }
            elif password == stored_pw:
                from auth import hash_password
                users_collection.update_one(
                    {"username": username},
                    {"$set": {"password": hash_password(password)}}
                )
                return {
                    "success": True,
                    "message": "Login successful!",
                    "username": user.get("username"),
                    "role": user.get("role")
                }
        
        return {"success": False, "message": "Invalid username or password"}
    
    except Exception as e:
        err = str(e)
        if "authentication failed" in err or "bad auth" in err:
            return {"success": False, "message": "Database connection error. Please check MONGO_URI environment variable."}
        return {"success": False, "message": f"Login error: {err[:100]}"}


# =========================
# Get Agency Details
# =========================
def get_agency(username):
    try:
        agency = agencies_collection.find_one({"username": username})
        if agency:
            return {
                "agency_name": agency.get("agency_name", ""),
                "routes": agency.get("routes", []),
                "total_vehicles": agency.get("total_vehicles", 0),
                "seats_per_vehicle": agency.get("seats_per_vehicle", 0)
            }
        return None
    except Exception as e:
        print(f" GET AGENCY ERROR: {e}")
        return None


# =========================
# Update Agency
# =========================
def update_agency(username, agency_details):
    try:
        # Convert routes from string format to dict format if needed
        routes = agency_details.get("routes", [])
        if routes and isinstance(routes[0], str):
            routes = [{"source": r.split("-")[0], "destination": r.split("-")[1]} 
                     for r in routes if "-" in r]
        
        result = agencies_collection.update_one(
            {"username": username},
            {"$set": {
                "agency_name": agency_details.get("agency_name", ""),
                "routes": routes,
                "total_vehicles": int(agency_details.get("total_vehicles", 0)),
                "seats_per_vehicle": int(agency_details.get("seats_per_vehicle", 0)),
                "bus_type": agency_details.get("bus_type", "Standard (2x2)")
            }}
        )
        return {"success": result.matched_count > 0, "message": "Agency updated"}
    except Exception as e:
        print(f" UPDATE AGENCY ERROR: {e}")
        return {"success": False, "message": str(e)}


# =========================
# MULTI-AGENCY BOOKING FUNCTIONS
# =========================

# =========================
# Get Agencies by Route
# =========================
def get_agencies_by_route(source, destination):
    """
    Find all agencies that offer a specific route
    
    Args:
        source: Starting city
        destination: Ending city
    
    Returns:
        List of agencies with their details
    """
    try:
        agencies = []
        
        # Search for agencies that have this route
        result = agencies_collection.find({
            "routes": {
                "$elemMatch": {
                    "source": {"$regex": source, "$options": "i"},
                    "destination": {"$regex": destination, "$options": "i"}
                }
            }
        })
        
        for agency in result:
            agencies.append({
                "agency_username": agency.get("username"),
                "agency_name": agency.get("agency_name", ""),
                "routes": agency.get("routes", []),
                "total_vehicles": agency.get("total_vehicles", 0),
                "seats_per_vehicle": agency.get("seats_per_vehicle", 0)
            })
        
        print(f" FOUND {len(agencies)} AGENCIES FOR ROUTE: {source} → {destination}")
        return agencies
    
    except Exception as e:
        print(f" GET AGENCIES BY ROUTE ERROR: {e}")
        return []


# =========================
# Check Seat Availability
# =========================
def check_seat_availability(agency_username, source, destination, date, seat):
    """
    Check if a seat is available for booking
    
    Args:
        agency_username: Agency providing the service
        source: Starting city
        destination: Ending city
        date: Travel date
        seat: Seat number/identifier
    
    Returns:
        True if seat is available, False if already booked
    """
    try:
        # Check if this exact seat is already booked for this route and date
        existing_booking = bookings_collection.find_one({
            "agency_username": agency_username,
            "source": {"$regex": source, "$options": "i"},
            "destination": {"$regex": destination, "$options": "i"},
            "date": date,
            "seat": seat,
            "status": {"$ne": "cancelled"}  # Ignore cancelled bookings
        })
        
        if existing_booking:
            print(f" SEAT UNAVAILABLE: {agency_username} | {seat} | {date}")
            return False
        
        print(f" SEAT AVAILABLE: {agency_username} | {seat} | {date}")
        return True
    
    except Exception as e:
        print(f" CHECK AVAILABILITY ERROR: {e}")
        return False


# =========================
# Create Booking (NEW - Multi-Agency)
# =========================
def create_booking(username, agency_username, source, destination, date, seat, 
                   passenger_name=None, passenger_age=None, passenger_gender=None):
    """
    Create a new booking with agency validation
    
    Args:
        username: User booking the ticket
        agency_username: Agency providing the service
        source: Starting city
        destination: Ending city
        date: Travel date (YYYY-MM-DD or DD/MM/YYYY)
        seat: Seat number/identifier
        passenger_name: Optional passenger name
        passenger_age: Optional passenger age
        passenger_gender: Optional passenger gender (Male/Female)
    
    Returns:
        {"success": True/False, "booking_id": int, "message": str}
    """
    try:
        # 1. Check if agency exists
        agency = agencies_collection.find_one({"username": agency_username})
        if not agency:
            return {"success": False, "message": f"Agency '{agency_username}' not found"}
        
        # 2. Check if route exists in agency
        route_exists = False
        for route in agency.get("routes", []):
            if (route.get("source", "").lower() == source.lower() and 
                route.get("destination", "").lower() == destination.lower()):
                route_exists = True
                break
        
        if not route_exists:
            return {"success": False, "message": f"Route {source}-{destination} not available for this agency"}
        
        # 3. Check seat availability
        if not check_seat_availability(agency_username, source, destination, date, seat):
            return {"success": False, "message": f"Seat {seat} is already booked for this date"}
        
        # 4. Get next booking ID
        booking_id = get_next_booking_id()
        
        # 5. Insert booking
        booking_data = {
            "booking_id": booking_id,
            "username": username,
            "agency_username": agency_username,
            "source": source,
            "destination": destination,
            "date": date,
            "seat": seat,
            "passenger_name": passenger_name,
            "passenger_age": passenger_age,
            "passenger_gender": passenger_gender,  # Store gender
            "status": "confirmed",
            "created_at": datetime.now()
        }
        
        result = bookings_collection.insert_one(booking_data)
        
        print(f" BOOKING CREATED SUCCESSFULLY")
        print(f"   Booking ID: {booking_id}")
        print(f"   Agency: {agency.get('agency_name')}")
        print(f"   Route: {source} → {destination}")
        print(f"   Date: {date}, Seat: {seat}, Gender: {passenger_gender}")
        
        return {
            "success": True,
            "booking_id": booking_id,
            "message": f"Booking confirmed! Booking ID: {booking_id}"
        }
    
    except Exception as e:
        print(f" CREATE BOOKING ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}


# =========================
# Get Bookings by Agency
# =========================
def get_bookings_by_agency(agency_username, start_date=None, end_date=None):
    """
    Get all bookings for an agency
    
    Args:
        agency_username: Agency username
        start_date: Optional filter (YYYY-MM-DD)
        end_date: Optional filter (YYYY-MM-DD)
    
    Returns:
        List of bookings
    """
    try:
        query = {"agency_username": agency_username, "status": {"$ne": "cancelled"}}
        
        # Add date filters if provided
        if start_date and end_date:
            query["date"] = {"$gte": start_date, "$lte": end_date}
        
        bookings = list(bookings_collection.find(query).sort("date", 1))
        
        print(f" RETRIEVED {len(bookings)} BOOKINGS FOR AGENCY: {agency_username}")
        return bookings
    
    except Exception as e:
        print(f" GET BOOKINGS BY AGENCY ERROR: {e}")
        return []


# =========================
# Get Available Seats for a Route
# =========================
def get_available_seats(agency_username, source, destination, date):
    """
    Get all available seats for a specific route and date
    
    Args:
        agency_username: Agency providing the service
        source: Starting city
        destination: Ending city
        date: Travel date
    
    Returns:
        List of available seat numbers
    """
    try:
        # Get agency details
        agency = agencies_collection.find_one({"username": agency_username})
        if not agency:
            return []
        
        total_seats = agency.get("seats_per_vehicle", 0)
        bus_type = agency.get("bus_type", "Standard (2x2)")
        # Determine seats per row based on bus type
        if "Luxury" in bus_type:
            seats_per_row = 3
        elif "Sleeper" in bus_type:
            seats_per_row = 2
        else:
            seats_per_row = 4
        
        # Generate seat codes like A1, A2, B1, B2 ...
        row_labels = list(string.ascii_uppercase)
        all_seats = []
        seat_count = 0
        row = 0
        while seat_count < total_seats:
            for col in range(1, seats_per_row + 1):
                seat_count += 1
                if seat_count > total_seats:
                    break
                seat_code = f"{row_labels[row]}{col}"
                all_seats.append(seat_code)
            row += 1
        
        # Get booked seats
        booked = bookings_collection.find({
            "agency_username": agency_username,
            "source": {"$regex": source, "$options": "i"},
            "destination": {"$regex": destination, "$options": "i"},
            "date": date,
            "status": {"$ne": "cancelled"}
        })
        
        booked_seats = [str(b.get("seat")) for b in booked]
        
        # Available seats = all seats - booked seats (handle numeric legacy values)
        available = [s for s in all_seats if s not in booked_seats and (s.isalpha() or s.isalnum())]
        # Also include numeric seat identifiers if stored that way and match index
        # Map numeric booked seats to possible all_seats by position
        numeric_booked = [b for b in booked_seats if b.isdigit()]
        if numeric_booked:
            numeric_booked_set = set(numeric_booked)
            # Remove seats by their numeric index (1-based)
            available = [s for idx, s in enumerate(all_seats, start=1) if str(idx) not in numeric_booked_set and s not in booked_seats]
        
        print(f" {len(available)}/{total_seats} SEATS AVAILABLE")
        return available
    
    except Exception as e:
        print(f" GET AVAILABLE SEATS ERROR: {e}")
        return []


# =========================
# Get Booked Seats for a Route
# =========================
def get_booked_seats(agency_username, source, destination, date):
    """
    Get all booked seats for a specific route and date
    
    Args:
        agency_username: Agency providing the service
        source: Starting city
        destination: Ending city
        date: Travel date
    
    Returns:
        List of booked seat numbers
    """
    try:
        booked = bookings_collection.find({
            "agency_username": agency_username,
            "source": {"$regex": source, "$options": "i"},
            "destination": {"$regex": destination, "$options": "i"},
            "date": date,
            "status": {"$ne": "cancelled"}
        })
        
        booked_seats = [str(b.get("seat")) for b in booked]
        return booked_seats
    
    except Exception as e:
        print(f" GET BOOKED SEATS ERROR: {e}")
        return []


# =========================
# Get Gender Map for Booked Seats
# =========================
def get_gender_map(agency_username, source, destination, date):
    """
    Get a map of seats to passenger gender
    
    Args:
        agency_username: Agency providing the service
        source: Starting city
        destination: Ending city
        date: Travel date
    
    Returns:
        Dictionary mapping seat codes to 'Male' or 'Female'
    """
    try:
        gender_map = {}
        booked = bookings_collection.find({
            "agency_username": agency_username,
            "source": {"$regex": source, "$options": "i"},
            "destination": {"$regex": destination, "$options": "i"},
            "date": date,
            "status": {"$ne": "cancelled"}
        })
        
        for b in booked:
            seat = str(b.get("seat"))
            gender = b.get("passenger_gender", "Male")  # Default to Male if not specified
            gender_map[seat] = gender
        
        return gender_map
    
    except Exception as e:
        print(f" GET GENDER MAP ERROR: {e}")
        return {}


# =========================
# Get User Profile
# =========================
def get_user_profile(username):
    """Get user profile information"""
    try:
        user = users_collection.find_one({"username": username})
        if user:
            return {
                "username": user.get("username"),
                "full_name": user.get("full_name", "Unknown"),
                "age": user.get("age"),
                "gender": user.get("gender"),
                "role": user.get("role")
            }
        return None
    except Exception as e:
        print(f" GET USER PROFILE ERROR: {e}")
        return None


# =========================
# Update User Profile
# =========================
def update_user_profile(username, full_name=None, age=None, gender=None):
    """Update user profile information"""
    try:
        update_data = {}
        if full_name:
            update_data["full_name"] = full_name
        if age:
            update_data["age"] = age
        if gender:
            update_data["gender"] = gender
        
        if update_data:
            result = users_collection.update_one(
                {"username": username},
                {"$set": update_data}
            )
            return {"success": result.modified_count > 0, "message": "Profile updated successfully"}
        return {"success": False, "message": "No data to update"}
    except Exception as e:
        print(f" UPDATE PROFILE ERROR: {e}")
        return {"success": False, "message": str(e)}



# =========================
# Search Routes by Source/Destination
# =========================
def search_routes(source=None, destination=None):
    """
    Search for available routes
    
    Args:
        source: Optional source city
        destination: Optional destination city
    
    Returns:
        List of unique routes across all agencies
    """
    try:
        routes = []
        query = {}
        
        if source or destination:
            query["routes"] = {"$elemMatch": {}}
            if source:
                query["routes"]["$elemMatch"]["source"] = {"$regex": source, "$options": "i"}
            if destination:
                query["routes"]["$elemMatch"]["destination"] = {"$regex": destination, "$options": "i"}
        
        agencies = agencies_collection.find(query)
        
        seen_routes = set()
        for agency in agencies:
            for route in agency.get("routes", []):
                route_key = f"{route.get('source', '')} - {route.get('destination', '')}"
                if route_key not in seen_routes:
                    routes.append(route)
                    seen_routes.add(route_key)
        
        print(f"️  FOUND {len(routes)} ROUTES")
        return routes
    
    except Exception as e:
        print(f" SEARCH ROUTES ERROR: {e}")
        return []


# =========================
# Get Booking Details
# =========================
def get_booking_details(booking_id):
    """Get detailed information about a specific booking"""
    try:
        booking = bookings_collection.find_one({"booking_id": booking_id})
        if booking:
            return {
                "booking_id": booking.get("booking_id"),
                "username": booking.get("username"),
                "agency_username": booking.get("agency_username"),
                "source": booking.get("source"),
                "destination": booking.get("destination"),
                "date": booking.get("date"),
                "seat": booking.get("seat"),
                "passenger_name": booking.get("passenger_name"),
                "passenger_age": booking.get("passenger_age"),
                "status": booking.get("status", "confirmed"),
                "created_at": booking.get("created_at")
            }
        return None
    except Exception as e:
        print(f" GET BOOKING DETAILS ERROR: {e}")
        return None


# =========================
# NOTIFICATION FUNCTIONS
# =========================

def get_next_notification_id():
    """Auto-increment notification ID"""
    last = notifications_collection.find_one(sort=[("notification_id", DESCENDING)])
    if last and "notification_id" in last:
        return last["notification_id"] + 1
    return 5001


def send_notification(agency_username, to_username, booking_id, message):
    """
    Agency sends a notification/message to a user who booked a ticket.

    Args:
        agency_username: Username of the agency sending the message
        to_username: Username of the user who booked the ticket
        booking_id: Related booking ID (for context)
        message: The message text

    Returns:
        {"success": True/False, "message": str}
    """
    try:
        # Resolve agency display name
        agency = agencies_collection.find_one({"username": agency_username})
        agency_name = agency.get("agency_name", agency_username) if agency else agency_username

        notification_id = get_next_notification_id()

        notification_data = {
            "notification_id": notification_id,
            "agency_username": agency_username,
            "agency_name": agency_name,
            "to_username": to_username,
            "booking_id": booking_id,
            "message": message,
            "is_read": False,
            "created_at": datetime.now()
        }

        notifications_collection.insert_one(notification_data)
        print(f" NOTIFICATION SENT → {to_username} | Booking #{booking_id}")
        return {"success": True, "message": "Notification sent successfully!"}

    except Exception as e:
        print(f" SEND NOTIFICATION ERROR: {e}")
        return {"success": False, "message": str(e)}


def get_user_notifications(username):
    """
    Get all notifications for a user, newest first.

    Args:
        username: The user's username

    Returns:
        List of notification dicts
    """
    try:
        results = []
        notes = notifications_collection.find(
            {"to_username": username}
        ).sort("created_at", DESCENDING)

        for n in notes:
            results.append({
                "notification_id": n.get("notification_id"),
                "agency_username": n.get("agency_username"),
                "agency_name": n.get("agency_name"),
                "booking_id": n.get("booking_id"),
                "message": n.get("message"),
                "is_read": n.get("is_read", False),
                "created_at": n.get("created_at")
            })

        print(f" RETRIEVED {len(results)} NOTIFICATIONS FOR: {username}")
        return results

    except Exception as e:
        print(f" GET USER NOTIFICATIONS ERROR: {e}")
        return []


def mark_notifications_read(username):
    """
    Mark all notifications for a user as read.

    Args:
        username: The user's username
    """
    try:
        result = notifications_collection.update_many(
            {"to_username": username, "is_read": False},
            {"$set": {"is_read": True}}
        )
        print(f" MARKED {result.modified_count} NOTIFICATIONS AS READ FOR: {username}")
    except Exception as e:
        print(f" MARK NOTIFICATIONS READ ERROR: {e}")


def get_unread_notification_count(username):
    """
    Get count of unread notifications for a user.

    Args:
        username: The user's username

    Returns:
        Integer count of unread notifications
    """
    try:
        count = notifications_collection.count_documents(
            {"to_username": username, "is_read": False}
        )
        return count
    except Exception as e:
        print(f" GET UNREAD COUNT ERROR: {e}")
        return 0


# =========================
# ADMIN FUNCTIONS
# =========================

def create_admin(username, password, full_name="Admin"):
    """Create an admin account."""
    try:
        if admins_collection.find_one({"username": username}):
            return {"success": False, "message": "Admin username already exists"}
        from auth import hash_password
        admins_collection.insert_one({
            "username": username,
            "password": hash_password(password),
            "full_name": full_name,
            "role": "admin",
            "created_at": datetime.now()
        })
        return {"success": True, "message": "Admin created successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def login_admin(username, password):
    """Validate admin credentials."""
    try:
        admin = admins_collection.find_one({"username": username})
        if admin:
            from auth import verify_password
            if verify_password(password, admin.get("password", "")):
                return {"success": True, "message": "Login successful", "username": admin["username"], "role": "admin"}
        return {"success": False, "message": "Invalid admin credentials"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_all_users():
    """Get all users (admin function)."""
    try:
        users = list(users_collection.find({}, {"password": 0}))
        return users
    except Exception as e:
        print(f" GET ALL USERS ERROR: {e}")
        return []


def get_all_agencies():
    """Get all agencies (admin function)."""
    try:
        agencies = list(agencies_collection.find({}))
        return agencies
    except Exception as e:
        print(f" GET ALL AGENCIES ERROR: {e}")
        return []


def get_all_bookings_admin():
    """Get all bookings for admin view."""
    try:
        bookings = list(bookings_collection.find({}).sort("created_at", DESCENDING))
        return bookings
    except Exception as e:
        return []


def get_system_stats():
    """Get system-wide statistics for admin dashboard."""
    try:
        total_users = users_collection.count_documents({"role": "User"})
        total_agencies = agencies_collection.count_documents({})
        total_bookings = bookings_collection.count_documents({})
        confirmed_bookings = bookings_collection.count_documents({"status": "confirmed"})
        cancelled_bookings = bookings_collection.count_documents({"status": "cancelled"})
        return {
            "total_users": total_users,
            "total_agencies": total_agencies,
            "total_bookings": total_bookings,
            "confirmed_bookings": confirmed_bookings,
            "cancelled_bookings": cancelled_bookings
        }
    except Exception as e:
        return {}


# =========================
# PHONE NUMBER SUPPORT
# =========================

def get_user_phone(username):
    """Get user's phone number."""
    try:
        user = users_collection.find_one({"username": username})
        if user:
            return user.get("phone", "")
        return ""
    except Exception:
        return ""


def update_user_phone(username, phone):
    """Update user's phone number."""
    try:
        result = users_collection.update_one(
            {"username": username},
            {"$set": {"phone": phone}}
        )
        return {"success": result.modified_count > 0}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_user_profile(username):
    """Get user profile information (enhanced with phone)."""
    try:
        user = users_collection.find_one({"username": username})
        if user:
            return {
                "username": user.get("username"),
                "full_name": user.get("full_name", "Unknown"),
                "age": user.get("age"),
                "gender": user.get("gender"),
                "phone": user.get("phone", ""),
                "role": user.get("role")
            }
        return None
    except Exception as e:
        print(f" GET USER PROFILE ERROR: {e}")
        return None


# =========================
# BUS MANAGEMENT
# =========================

def add_bus(agency_username, bus_name, bus_type, total_seats, plate_number=""):
    """Add a bus to an agency's fleet."""
    try:
        bus_data = {
            "agency_username": agency_username,
            "bus_name": bus_name,
            "bus_type": bus_type,
            "total_seats": int(total_seats),
            "plate_number": plate_number,
            "is_active": True,
            "created_at": datetime.now()
        }
        result = buses_collection.insert_one(bus_data)
        return {"success": True, "bus_id": str(result.inserted_id)}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_agency_buses(agency_username):
    """Get all buses for an agency."""
    try:
        return list(buses_collection.find({"agency_username": agency_username}))
    except Exception:
        return []


def delete_bus(bus_id):
    """Delete a bus."""
    try:
        from bson import ObjectId
        result = buses_collection.delete_one({"_id": ObjectId(bus_id)})
        return {"success": result.deleted_count > 0}
    except Exception as e:
        return {"success": False, "message": str(e)}


# =========================
# REVENUE TRACKING
# =========================

def record_revenue(agency_username, booking_id, amount, source, destination, date):
    """Record revenue for a booking."""
    try:
        revenue_collection.insert_one({
            "agency_username": agency_username,
            "booking_id": booking_id,
            "amount": float(amount),
            "source": source,
            "destination": destination,
            "date": date,
            "created_at": datetime.now()
        })
        return {"success": True}
    except Exception:
        return {"success": False}


def get_agency_revenue(agency_username, start_date=None, end_date=None):
    """Get total revenue for an agency."""
    try:
        query = {"agency_username": agency_username}
        if start_date and end_date:
            query["date"] = {"$gte": start_date, "$lte": end_date}
        pipeline = [
            {"$match": query},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
        ]
        result = list(revenue_collection.aggregate(pipeline))
        if result:
            return {"total_revenue": result[0]["total"], "total_bookings": result[0]["count"]}
        return {"total_revenue": 0, "total_bookings": 0}
    except Exception:
        return {"total_revenue": 0, "total_bookings": 0}


def get_revenue_by_route(agency_username):
    """Get revenue breakdown by route."""
    try:
        pipeline = [
            {"$match": {"agency_username": agency_username}},
            {"$group": {
                "_id": {"source": "$source", "destination": "$destination"},
                "total_revenue": {"$sum": "$amount"},
                "booking_count": {"$sum": 1}
            }},
            {"$sort": {"total_revenue": -1}}
        ]
        return list(revenue_collection.aggregate(pipeline))
    except Exception:
        return []


# =========================
# WHATSAPP INSTANCE MANAGEMENT
# =========================

def save_whatsapp_instance(agency_username, instance_name, result=None):
    """Save or update WhatsApp instance for an agency."""
    try:
        status = "created"
        phone = ""
        if result and isinstance(result, dict):
            data = result.get("data", {})
            if isinstance(data, dict):
                phone = data.get("number", "")
                status = data.get("connectionStatus", "created")
        whatsapp_instances_collection.update_one(
            {"agency_username": agency_username},
            {"$set": {
                "instance_name": instance_name,
                "phone": phone,
                "status": status,
                "connected": status in ("open", "connected"),
                "updated_at": datetime.now()
            }},
            upsert=True
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


# Removed duplicate functions - see unified definitions below


# =========================
# ENHANCED BOOKING CANCEL (with WhatsApp)
# =========================

def cancel_booking_enhanced(booking_id):
    """Cancel booking and return full booking data for notifications."""
    try:
        booking = bookings_collection.find_one({"booking_id": int(booking_id)})
        if not booking:
            return {"success": False, "message": "Booking not found"}

        result = bookings_collection.update_one(
            {"booking_id": int(booking_id)},
            {"$set": {"status": "cancelled"}}
        )

        if result.modified_count > 0:
            return {"success": True, "booking": booking, "message": "Booking cancelled"}
        return {"success": False, "message": "Booking not found"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# =========================
# PASSENGER MANAGEMENT
# =========================

def get_agency_passengers(agency_username):
    """Get unique passengers who booked with an agency."""
    try:
        pipeline = [
            {"$match": {"agency_username": agency_username, "status": "confirmed"}},
            {"$group": {
                "_id": "$username",
                "passenger_name": {"$first": "$passenger_name"},
                "total_bookings": {"$sum": 1},
                "last_booking": {"$max": "$created_at"}
            }},
            {"$sort": {"last_booking": -1}}
        ]
        return list(bookings_collection.aggregate(pipeline))
    except Exception:
        return []


# =========================
# SEAT OCCUPANCY ANALYTICS
# =========================

def get_seat_occupancy(agency_username, date=None):
    """Get seat occupancy stats for an agency."""
    try:
        agency = agencies_collection.find_one({"username": agency_username})
        if not agency:
            return {}

        total_capacity = agency.get("total_vehicles", 0) * agency.get("seats_per_vehicle", 0)
        query = {"agency_username": agency_username, "status": "confirmed"}
        if date:
            query["date"] = date

        booked = bookings_collection.count_documents(query)
        return {
            "total_capacity": total_capacity,
            "booked_seats": booked,
            "available_seats": total_capacity - booked,
            "occupancy_rate": round((booked / total_capacity * 100), 1) if total_capacity > 0 else 0
        }
    except Exception:
        return {}


# =========================
# ROUTE ANALYTICS
# =========================

def get_route_stats(agency_username):
    """Get booking stats by route for an agency."""
    try:
        pipeline = [
            {"$match": {"agency_username": agency_username, "status": "confirmed"}},
            {"$group": {
                "_id": {"source": "$source", "destination": "$destination"},
                "total_bookings": {"$sum": 1},
                "unique_passengers": {"$addToSet": "$username"}
            }},
            {"$project": {
                "source": "$_id.source",
                "destination": "$_id.destination",
                "total_bookings": 1,
                "passenger_count": {"$size": "$unique_passengers"}
            }},
            {"$sort": {"total_bookings": -1}}
        ]
        return list(bookings_collection.aggregate(pipeline))
    except Exception:
        return []
# =========================
# WHATSAPP INSTANCE MANAGEMENT
# =========================

def create_whatsapp_instance(agency_username, instance_name, phone_number=""):
    """Create a WhatsApp instance record for an agency."""
    try:
        # Check if agency exists
        if not agencies_collection.find_one({"username": agency_username}):
            return {"success": False, "message": "Agency not found"}
        
        # Check if instance already exists
        existing = whatsapp_instances_collection.find_one({"agency_username": agency_username})
        if existing:
            return {"success": False, "message": "Agency already has a WhatsApp instance configured"}
        
        instance_data = {
            "agency_username": agency_username,
            "instance_name": instance_name,
            "phone_number": phone_number,
            "status": "pending_qr",  # pending_qr -> scanned -> connected -> active
            "qr_code": None,
            "is_connected": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = whatsapp_instances_collection.insert_one(instance_data)
        print(f" WhatsApp instance created for agency: {agency_username}")
        return {"success": True, "message": "Instance created successfully", "instance_name": instance_name}
    
    except Exception as e:
        print(f" CREATE WHATSAPP INSTANCE ERROR: {e}")
        return {"success": False, "message": str(e)}


def get_whatsapp_instance(agency_username):
    """Get WhatsApp instance for an agency."""
    try:
        instance = whatsapp_instances_collection.find_one({"agency_username": agency_username})
        if instance:
            return {
                "instance_name": instance.get("instance_name"),
                "phone_number": instance.get("phone_number"),
                "status": instance.get("status", "pending_qr"),
                "is_connected": instance.get("is_connected", False),
                "qr_code": instance.get("qr_code"),
                "created_at": instance.get("created_at"),
                "updated_at": instance.get("updated_at")
            }
        return None
    except Exception as e:
        print(f" GET WHATSAPP INSTANCE ERROR: {e}")
        return None


def update_whatsapp_instance_qr(agency_username, qr_code_base64):
    """Update QR code for WhatsApp instance."""
    try:
        result = whatsapp_instances_collection.update_one(
            {"agency_username": agency_username},
            {"$set": {
                "qr_code": qr_code_base64,
                "status": "scanned",
                "updated_at": datetime.now()
            }}
        )
        return {"success": result.matched_count > 0, "message": "QR code updated"}
    except Exception as e:
        print(f" UPDATE QR CODE ERROR: {e}")
        return {"success": False, "message": str(e)}


def mark_whatsapp_connected(agency_username, phone_number=""):
    """Mark WhatsApp instance as connected."""
    try:
        update_data = {
            "is_connected": True,
            "status": "connected",
            "updated_at": datetime.now()
        }
        if phone_number:
            update_data["phone_number"] = phone_number
        
        result = whatsapp_instances_collection.update_one(
            {"agency_username": agency_username},
            {"$set": update_data}
        )
        return {"success": result.matched_count > 0, "message": "Instance marked as connected"}
    except Exception as e:
        print(f" MARK CONNECTED ERROR: {e}")
        return {"success": False, "message": str(e)}


def delete_whatsapp_instance(agency_username):
    """Delete/disconnect WhatsApp instance for an agency."""
    try:
        result = whatsapp_instances_collection.delete_one({"agency_username": agency_username})
        return {"success": result.deleted_count > 0, "message": "Instance deleted successfully"}
    except Exception as e:
        print(f" DELETE WHATSAPP INSTANCE ERROR: {e}")
        return {"success": False, "message": str(e)}


def get_all_whatsapp_instances():
    """Get all WhatsApp instances (for admin)."""
    try:
        instances = list(whatsapp_instances_collection.find({}))
        return [{"agency_username": i.get("agency_username"), "status": i.get("status"), "is_connected": i.get("is_connected")} for i in instances]
    except Exception as e:
        return []
