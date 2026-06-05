from openai import OpenAI
import db
import re
API_KEY = "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"
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)
def ai_response(user_input):
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful ticket booking assistant. Answer questions about the booking system and provide travel tips."
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error contacting AI service: {str(e)}"
def extract_booking_info(text):
    """Extract name, age, source, destination, date, seat from user input"""
    info = {}
    text_lower = text.lower()
    if ',' in text and text.count(',') >= 4:
        parts = [p.strip() for p in text.split(',')]
        if len(parts) >= 6:
            try:
                name, age_str, source, dest, date_str, seat = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                if name and len(name) > 1 and not name.isdigit():
                    info['name'] = name.title()
                age = int(age_str)
                if 1 <= age <= 100:
                    info['age'] = age
                if source and len(source) > 1:
                    info['source'] = source.title()
                if dest and len(dest) > 1:
                    info['destination'] = dest.title()
                date_converted = convert_date_format(date_str)
                if date_converted:
                    info['date'] = date_converted
                if seat and len(seat) > 0:
                    info['seat'] = seat.strip().upper()
                
                return info
            except (ValueError, IndexError):
                pass
    age_pattern = r'age\s*[:\s]*(\d{1,2})'
    age_match = re.search(age_pattern, text_lower)
    if age_match:
        age = int(age_match.group(1))
        if 1 <= age <= 100:
            info['age'] = age
    else:
    
        age_matches = re.findall(r'\b([1-9]\d)\b', text)
        if age_matches:
            try:
                age = int(age_matches[0])
                if 1 <= age <= 100:
                    info['age'] = age
            except ValueError:
                pass
    
   
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',  
        r'(\d{2}/\d{2}/\d{4})',  
        r'(\d{2}-\d{2}-\d{4})',  
        r'(\d{2}\.\d{2}\.\d{4})',
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, text)
        if date_match:
            date_str = date_match.group(1)
            date_converted = convert_date_format(date_str)
            if date_converted:
                info['date'] = date_converted
                break
    from_to_match = re.search(r'from\s+([A-Za-z\s]+?)\s+to\s+([A-Za-z\s]+?)(?:\s*,|\s+(?:on|at|name|age|date|seat)|$)', text_lower)
    if from_to_match:
        source = from_to_match.group(1).strip().title()
        dest = from_to_match.group(2).strip().title()
        if source and len(source) > 1 and source not in ['Name', 'Age', 'Date', 'Seat']:
            info['source'] = source
        if dest and len(dest) > 1 and dest not in ['Name', 'Age', 'Date', 'Seat']:
            info['destination'] = dest
    seat_match = re.search(r'seat\s+([A-Z]?\d{1,2})', text, re.IGNORECASE)
    if not seat_match:
        seat_match = re.search(r'\b([A-Z]\d{1,2})\b', text)
    if seat_match:
        seat = seat_match.group(1).upper()
        if seat not in ['A0', 'B0'] and seat != str(info.get('age', '')):  # Don't use if it's same as age
            info['seat'] = seat
    else:
        all_numbers = re.findall(r'\b(\d{1,2})\b', text)
        for num in all_numbers:
            if int(num) != info.get('age') and int(num) > 0:
                if 'seat' not in text_lower[:text_lower.find(num)]:
                    continue
                if 'seat' in text_lower[:text_lower.find(num)]:
                    info['seat'] = num
                    break
    name_keyword = re.search(r'(?:name|my name)\s+(?:is\s+)?([A-Za-z]+)', text, re.IGNORECASE)
    if name_keyword:
        potential_name = name_keyword.group(1).strip()
        if potential_name not in [info.get('source', ''), info.get('destination', '')] and potential_name.lower() not in ['is', 'am', 'are', 'be', 'being']:
            if potential_name and len(potential_name) > 1:
                info['name'] = potential_name.title()
    if 'name' not in info:
        name_keyword = re.search(r'(?:i\s+(?:am|m|\'m)\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
        if name_keyword:
            potential_name = name_keyword.group(1).strip()
            if potential_name not in [info.get('source', ''), info.get('destination', '')] and potential_name.lower() not in ['is', 'am', 'are', 'be']:
                if potential_name and len(potential_name) > 2:
                    info['name'] = potential_name
    if 'name' not in info and ('source' in info or 'destination' in info):
        all_names = re.findall(r'\b([A-Z][a-z]+)\b', text)
        for name in all_names:
            if name not in [info.get('source', ''), info.get('destination', '')] and name not in ['From', 'To', 'Date', 'Seat', 'Age', 'Name', 'Book', 'A', 'I', 'The', 'Is', 'Am']:
                info['name'] = name
                break
    
    return info
def convert_date_format(date_str):
    """Convert various date formats to YYYY-MM-DD"""
    if not date_str:
        return None
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return date_str
    if re.match(r'\d{2}/\d{2}/\d{4}', date_str):
        parts = date_str.split('/')
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    if re.match(r'\d{2}-\d{2}-\d{4}', date_str):
        parts = date_str.split('-')
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    if re.match(r'\d{2}\.\d{2}\.\d{4}', date_str):
        parts = date_str.split('.')
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    
    return None
def process_message(msg):
    """Process user message and route to appropriate action"""
    print(f"[PROCESS_MESSAGE START] Received message: {repr(msg)}")
    msg_lower = msg.lower().strip()
    if any(word in msg_lower for word in ["cancel", "delete", "remove"]):
        id_match = re.search(r'\b(\d+)\b', msg)
        if id_match:
            booking_id = int(id_match.group(1))
            try:
                bookings = db.get_bookings()
                if any(b[0] == booking_id for b in bookings):
                    db.cancel_booking(booking_id)
                    return f"Booking #{booking_id} has been successfully cancelled."
                else:
                    return f"Booking #{booking_id} not found. Please check the ID."
            except Exception as e:
                return f"Error cancelling booking: {str(e)}"
        else:
            return "Please provide the booking ID to cancel. Example: 'cancel booking 1'"
    elif any(word in msg_lower for word in ["view", "show", "list"]):
    
    id_match = re.search(r'\b(\d+)\b', msg)
    bookings = db.get_bookings()

    if not bookings:
        return "No bookings found in the system yet."

    # Show specific booking
    if id_match:
        booking_id = int(id_match.group(1))

        for booking in bookings:
            if booking[0] == booking_id:
                return (
                    f"🎫 Booking Details\n\n"
                    f"ID: {booking[0]}\n"
                    f"Name: {booking[1]}\n"
                    f"Age: {booking[2]}\n"
                    f"Source: {booking[6]}\n"
                    f"Destination: {booking[3]}\n"
                    f"Date: {booking[4]}\n"
                    f"Seat: {booking[5]}"
                )

        return f"Booking ID {booking_id} not found."

    # Show all bookings
    response = f"Found {len(bookings)} booking(s):\n\n"

    for booking in bookings:
        response += (
            f"ID {booking[0]}: "
            f"{booking[1]} ({booking[2]} yrs) | "
            f"{booking[6]} to {booking[3]} | "
            f"Date: {booking[4]} | "
            f"Seat: {booking[5]}\n"
        )

    return response
    elif any(word in msg_lower for word in ["help", "what", "how"]):
        return "I can help you with:\n\n📌 Book: Say 'book from Delhi to Mumbai, name John, age 28, date 2025-06-10, seat A1'\n   OR use format: 'John,28,Delhi,Mumbai,13/07/2026,28'\n\n📌 View: Say 'show all bookings' or 'view tickets'\n\n📌 Cancel: Say 'cancel booking 1' (replace 1 with ID)\n\nYou can also use the menu buttons above!"
    info = extract_booking_info(msg)
    has_booking_keyword = any(word in msg_lower for word in ["book", "reserve", "ticket"])
    print(f"[DEBUG] Message: {repr(msg)}")
    print(f"[DEBUG] Comma count: {msg.count(',')}")
    print(f"[DEBUG] has_booking_keyword: {has_booking_keyword}")
    print(f"[DEBUG] Extracted info: {info}")
    print(f"[DEBUG] Booking condition: {has_booking_keyword or (msg.count(',') >= 4)}")
    if has_booking_keyword or (msg.count(',') >= 4):
        if all(key in info for key in ['name', 'age', 'source', 'destination', 'date', 'seat']):
            try:
                db.add_booking(
                    name=info['name'],
                    age=int(info['age']),
                    source=info['source'],
                    destination=info['destination'],
                    date=info['date'],
                    seat=info['seat']
                )
                return f"✅ Booking confirmed! Ticket booked for {info['name']}, age {info['age']}, from {info['source']} to {info['destination']} on {info['date']}, seat {info['seat']}."
            except Exception as e:
                return f"❌ Error booking ticket: {str(e)}"
        else:
            # Provide helpful hints about what's missing
            missing = []
            found = []
            
            if 'name' in info:
                found.append(f'name={info["name"]}')
            else:
                missing.append('name (your name)')
            
            if 'age' in info:
                found.append(f'age={info["age"]}')
            else:
                missing.append('age')
            
            if 'source' in info:
                found.append(f'from={info["source"]}')
            else:
                missing.append('source (from where)')
            
            if 'destination' in info:
                found.append(f'to={info["destination"]}')
            else:
                missing.append('destination (to where)')
            
            if 'date' in info:
                found.append(f'date={info["date"]}')
            else:
                missing.append('date (DD/MM/YYYY or YYYY-MM-DD)')
            
            if 'seat' in info:
                found.append(f'seat={info["seat"]}')
            else:
                missing.append('seat (like A1, B5, or 28)')
            
            found_str = ', '.join(found) if found else 'nothing'
            missing_str = ', '.join(missing)
            
            return f"I found: {found_str}\n\nPlease provide: {missing_str}\n\nFormat: 'name,age,source,destination,date,seat'"
    else:
        return ai_response(msg)