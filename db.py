from pymongo import MongoClient, DESCENDING
from datetime import datetime
import string

# =========================
# MongoDB Connection
# =========================
MONGO_URI = "mongodb+srv://Umaiyaswaran:Password_7585@cluster0.x706nl9.mongodb.net/ticket_booking?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)

db = client["ticket_booking"]

# Collections
bookings_collection = db["bookings"]
users_collection = db["users"]
agencies_collection = db["agencies"]

print("🔗 MongoDB Connection Settings:")
print(f"   Database: {db.name}")
print(f"   Collections: bookings, users, agencies")
print(f"   URI: {MONGO_URI[:50]}...")


# =========================
# Init DB
# =========================
def init_db():
    try:
        # Test connection
        client.admin.command("ping")
        print("✅ MongoDB Connected Successfully")
        
        # Get database and collection info
        db_list = client.list_database_names()
        print(f"📊 Available Databases: {db_list}")
        
        # Check if ticket_booking exists
        if "ticket_booking" in db_list:
            collections = db.list_collection_names()
            print(f"📋 Collections in ticket_booking: {collections}")
        
        # Create indexes for better query performance
        users_collection.create_index("username", unique=True)
        bookings_collection.create_index([("username", 1), ("date", 1)])
        agencies_collection.create_index("username", unique=True)
        print("✅ Database indexes created")
        
    except Exception as e:
        print("❌ MongoDB Connection Failed:", e)


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
        
        print(f"\n📝 INSERTING BOOKING:")
        print(f"   Data: {booking_data}")

        result = bookings_collection.insert_one(booking_data)

        print(f"✅ INSERTED SUCCESSFULLY:")
        print(f"   MongoDB ObjectID: {result.inserted_id}")
        print(f"   Booking ID: {booking_id}")
        print(f"   Acknowledged: {result.acknowledged}")

        return booking_id

    except Exception as e:
        print(f"❌ INSERT ERROR: {e}")
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
        
        print(f"\n📋 RETRIEVED {count} BOOKINGS FROM MONGODB")
        
        return result
    
    except Exception as e:
        print(f"❌ GET BOOKINGS ERROR: {e}")
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
        
        print(f"📋 RETRIEVED {count} BOOKINGS FOR USER: {username}")
        return result
    
    except Exception as e:
        print(f"❌ GET USER BOOKINGS ERROR: {e}")
        return []


# =========================
# Cancel Booking
# =========================
def cancel_booking(booking_id):
    try:
        result = bookings_collection.update_one(
            {"booking_id": int(booking_id)},
            {"$set": {"status": "cancelled"}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Booking {booking_id} cancelled successfully")
            return {"success": True, "message": "Booking cancelled successfully"}
        else:
            print(f"❌ Booking {booking_id} not found")
            return {"success": False, "message": "Booking not found"}
    except Exception as e:
        print(f"❌ CANCEL BOOKING ERROR: {e}")
        return {"success": False, "message": str(e)}


# =========================
# USER AUTHENTICATION FUNCTIONS
# =========================

# =========================
# Create User (Signup)
# =========================
def create_user(username, password, role, agency_details=None, gender_option=None, full_name=None, age=None):
    """Create a new user account (User or Travel Agency)"""
    try:
        # Check if user already exists
        if users_collection.find_one({"username": username}):
            return {"success": False, "message": "Username already exists"}
        
        user_data = {
            "username": username,
            "password": password,  # In production, hash this!
            "role": role,
            "gender": gender_option,  # Store gender for users
            "full_name": full_name,  # Store full name
            "age": age,  # Store age
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
        print(f"❌ CREATE USER ERROR: {e}")
        return {"success": False, "message": str(e)}


# =========================
# Login User
# =========================
def login_user(username, password):
    try:
        user = users_collection.find_one({
            "username": username,
            "password": password
        })
        
        if user:
            return {
                "success": True,
                "message": "Login successful!",
                "username": user.get("username"),
                "role": user.get("role")
            }
        else:
            return {"success": False, "message": "Invalid username or password"}
    
    except Exception as e:
        print(f"❌ LOGIN ERROR: {e}")
        return {"success": False, "message": str(e)}


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
        print(f"❌ GET AGENCY ERROR: {e}")
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
                "seats_per_vehicle": int(agency_details.get("seats_per_vehicle", 0))
            }}
        )
        return {"success": result.modified_count > 0, "message": "Agency updated"}
    except Exception as e:
        print(f"❌ UPDATE AGENCY ERROR: {e}")
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
        
        print(f"🚍 FOUND {len(agencies)} AGENCIES FOR ROUTE: {source} → {destination}")
        return agencies
    
    except Exception as e:
        print(f"❌ GET AGENCIES BY ROUTE ERROR: {e}")
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
            print(f"❌ SEAT UNAVAILABLE: {agency_username} | {seat} | {date}")
            return False
        
        print(f"✅ SEAT AVAILABLE: {agency_username} | {seat} | {date}")
        return True
    
    except Exception as e:
        print(f"❌ CHECK AVAILABILITY ERROR: {e}")
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
        
        print(f"✅ BOOKING CREATED SUCCESSFULLY")
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
        print(f"❌ CREATE BOOKING ERROR: {e}")
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
        
        print(f"📋 RETRIEVED {len(bookings)} BOOKINGS FOR AGENCY: {agency_username}")
        return bookings
    
    except Exception as e:
        print(f"❌ GET BOOKINGS BY AGENCY ERROR: {e}")
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
        
        print(f"🪑 {len(available)}/{total_seats} SEATS AVAILABLE")
        return available
    
    except Exception as e:
        print(f"❌ GET AVAILABLE SEATS ERROR: {e}")
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
        print(f"❌ GET BOOKED SEATS ERROR: {e}")
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
        print(f"❌ GET GENDER MAP ERROR: {e}")
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
        print(f"❌ GET USER PROFILE ERROR: {e}")
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
        print(f"❌ UPDATE PROFILE ERROR: {e}")
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
        
        print(f"🛣️  FOUND {len(routes)} ROUTES")
        return routes
    
    except Exception as e:
        print(f"❌ SEARCH ROUTES ERROR: {e}")
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
        print(f"❌ GET BOOKING DETAILS ERROR: {e}")
        return None