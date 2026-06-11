"""
Enhanced Chatbot Module for AI-Assisted Ticket Booking
Handles intelligent conversation flow with users through all booking stages
"""

from openai import OpenAI
import db
import re
from datetime import datetime

API_KEY = "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"
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    timeout=15.0,
    max_retries=1,
)

# =====================================================
# CONVERSATION STATE MANAGEMENT
# =====================================================
class BookingConversation:
    """Manages conversation state for a user booking"""
    
    def __init__(self, username):
        self.username = username
        self.stage = "initial"  # Stages: initial, route_info, available_agencies, seat_selection, passenger_info_other, confirmation
        self.source = None
        self.destination = None
        self.date = None
        self.selected_agency = None
        self.available_agencies = []
        self.selected_seat = None
        self.passenger_name = None
        self.passenger_age = None
        self.passenger_gender = None  # Track passenger gender
        self.available_seats = []
        self.booking_for_other = False  # True when booking a second ticket for another person
    
    def reset(self):
        """Reset conversation state"""
        self.stage = "initial"
        self.source = None
        self.destination = None
        self.date = None
        self.selected_agency = None
        self.available_agencies = []
        self.selected_seat = None
        self.passenger_name = None
        self.passenger_age = None
        self.passenger_gender = None
        self.available_seats = []
        self.booking_for_other = False

# Store conversations per user
active_conversations = {}

def get_conversation(username):
    """Get or create a conversation for user"""
    if username not in active_conversations:
        active_conversations[username] = BookingConversation(username)
    return active_conversations[username]

def ai_response(user_input, system_prompt=None):
    """Get AI response from OpenRouter API"""
    try:
        default_system = "You are a helpful ticket booking assistant. Answer questions about the booking system and provide travel tips."
        
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt or default_system
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error contacting AI service: {str(e)}"

# =====================================================
# BOOKING EXTRACTION FUNCTIONS
# =====================================================

def extract_route_info(text):
    """Extract source and destination from user text"""
    info = {}
    text_lower = text.lower()
    
    # 1. Remove travel dates first to avoid matching them in route names
    clean_text = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '', text_lower)
    clean_text = re.sub(r'\b\d{2}[\/-]\d{2}[\/-]\d{4}\b', '', clean_text)
    
    # 2. Remove "on" or "at" preceding/succeeding the dates
    clean_text = re.sub(r'\b(on|at)\b\s*$', '', clean_text)
    clean_text = re.sub(r'\b(on|at)\b\s+', ' ', clean_text)
    
    # 3. Remove common booking-related keywords and phrases
    keywords_pattern = r'\b(i want to to book|i want to book|i want to|i would like to to book|i would like to book|i would like to|to book|book|booking|reserve|tickets?)\b\s*'
    clean_text = re.sub(keywords_pattern, '', clean_text)
    
    # Normalize spaces
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    # Pattern 1: "from X to Y"
    from_to_match = re.search(r'from\s+([A-Za-z\s]+?)\s+to\s+([A-Za-z\s]+?)(?:\s*,|$)', clean_text)
    if from_to_match:
        info['source'] = from_to_match.group(1).strip().title()
        info['destination'] = from_to_match.group(2).strip().title()
        return info
    
    # Pattern 2: "X to Y" (simple pattern without "from")
    simple_to_match = re.search(r'\b([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+to\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b', clean_text)
    if simple_to_match:
        info['source'] = simple_to_match.group(1).strip().title()
        info['destination'] = simple_to_match.group(2).strip().title()
        return info
    
    return info


def extract_date(text):
    """Extract travel date from text"""
    text_lower = text.lower()
    
    # Date patterns
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
        r'(\d{2}/\d{2}/\d{4})',  # DD/MM/YYYY
        r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY
    ]
    
    for pattern in date_patterns:
        date_match = re.search(pattern, text)
        if date_match:
            date_str = date_match.group(1)
            return convert_date_format(date_str)
    
    return None

def extract_passenger_info(text):
    """Extract name, age, and gender from text - supports multiple formats"""
    info = {}
    text_lower = text.lower()
    text_clean = text.strip().strip("'\"")  # Remove quotes
    
    # Try comma-separated format first: "umaiyas,20" or "umaiyas, 20, male"
    if ',' in text_clean:
        parts = [p.strip().strip("'\"") for p in text_clean.split(',')]
        if len(parts) >= 2:
            # First part is name
            potential_name = parts[0].strip()
            # Accept names that contain at least one letter (allow numbers/symbols like 'E2E User')
            if potential_name and re.search(r'[A-Za-z]', potential_name):
                info['name'] = potential_name.title()
            
            # Second part onwards - look for age (first 1-3 digit number) and gender
            for part in parts[1:]:
                if 'age' not in info:
                    age_match = re.search(r'\b(\d{1,3})\b', part)
                    if age_match:
                        age = int(age_match.group(1))
                        if 1 <= age <= 100:
                            info['age'] = age
                            continue
                
                if 'gender' not in info:
                    p_lower = part.lower().strip()
                    if p_lower in ['male', 'm']:
                        info['gender'] = 'Male'
                    elif p_lower in ['female', 'f']:
                        info['gender'] = 'Female'
                    elif p_lower in ['neutral', 'n']:
                        info['gender'] = 'Neutral'
    
    # If we got age/gender but not name, try to extract name from first part
    if ('age' in info or 'gender' in info) and 'name' not in info:
        name_match = re.search(r'^[\w\s]+', text_clean)
        if name_match:
            potential_name = name_match.group(0).strip().split(',')[0].strip()
            if re.search(r'[A-Za-z]', potential_name):
                info['name'] = potential_name.title()
    
    # Try natural language patterns for name
    if 'name' not in info:
        name_pattern = r'(?:name|i\'m|i am|my name is)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)'
        name_match = re.search(name_pattern, text, re.IGNORECASE)
        if name_match:
            info['name'] = name_match.group(1).strip().title()
    
    # Try to extract age from natural language
    if 'age' not in info:
        # Pattern 1: "age 20" or "age: 20"
        age_pattern = r'age\s*[:\s]*(\d{1,2})'
        age_match = re.search(age_pattern, text_lower)
        if age_match:
            age = int(age_match.group(1))
            if 1 <= age <= 100:
                info['age'] = age
        
        # Pattern 2: "20 years old" or "20 years"
        if 'age' not in info:
            age_pattern = r'(\d{1,2})\s*years?(?:\s*old)?'
            age_match = re.search(age_pattern, text_lower)
            if age_match:
                age = int(age_match.group(1))
                if 1 <= age <= 100:
                    info['age'] = age
        
        # Pattern 3: Just a number 1-100 in the text (fallback)
        if 'age' not in info:
            age_pattern = r'\b(\d{1,2})\b'
            age_matches = re.findall(age_pattern, text_lower)
            for match in age_matches:
                age = int(match)
                if 1 <= age <= 100:
                    info['age'] = age
                    break

    # Look for gender in the entire text if not found yet
    if 'gender' not in info:
        gender_match = re.search(r'\b(male|female|neutral)\b', text_lower)
        if gender_match:
            info['gender'] = gender_match.group(1).title()
        else:
            m_match = re.search(r'\b(m|f|n)\b', text_lower)
            if m_match:
                g = m_match.group(1)
                if g == 'm':
                    info['gender'] = 'Male'
                elif g == 'f':
                    info['gender'] = 'Female'
                elif g == 'n':
                    info['gender'] = 'Neutral'
                    
    return info


def extract_seat(text):
    """Extract seat number/code from text"""
    # Seat patterns: 1, 12, A1, A12, etc.
    seat_pattern = r'seat\s+([A-Z]?\d{1,2})|(\d{1,2})|([A-Z]\d{1,2})'
    seat_match = re.search(seat_pattern, text, re.IGNORECASE)
    
    if seat_match:
        seat = (seat_match.group(1) or seat_match.group(2) or seat_match.group(3)).upper()
        return seat
    
    return None

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
    
    return None

# =====================================================
# ROUTE MAP VISUALIZATION
# =====================================================

def generate_route_map_html(routes):
    """Generate HTML visual map of available routes"""
    html = '<div style="font-family: Arial, sans-serif; text-align: center; margin: 20px 0;">'
    html += '<div style="font-weight: bold; margin-bottom: 15px; font-size: 14px;">🗺️ AVAILABLE ROUTES</div>'
    
    html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 15px 0;">'
    
    for route in routes:
        source = route.get('source', 'Unknown')
        destination = route.get('destination', 'Unknown')
        html += f'''
        <div style="border: 2px solid #00d4ff; border-radius: 8px; padding: 15px; background: #f0f9ff;">
            <div style="font-weight: bold; color: #00d4ff; margin-bottom: 10px;">{source}</div>
            <div style="font-size: 20px; color: #667eea;">↓</div>
            <div style="font-weight: bold; color: #00d4ff; margin-top: 10px;">{destination}</div>
        </div>
        '''
    
    html += '</div>'
    html += '</div>'
    
    return html

# =====================================================
# SEAT MAP VISUALIZATION
# =====================================================

def generate_seat_map_html(available_seats, booked_seats=None, selected_seat=None, gender_map=None):
    """Generate interactive HTML visual representation of bus seats with gender-based colors"""
    if booked_seats is None:
        booked_seats = []
    if gender_map is None:
        gender_map = {}
    
    # Parse seat codes (A1, A2, B1, B2, etc.)
    seat_grid = {}
    for seat in available_seats:
        if isinstance(seat, str) and len(seat) > 1 and seat[0].isalpha():
            row = seat[0]
            if row not in seat_grid:
                seat_grid[row] = {'available': [], 'booked': []}
            seat_grid[row]['available'].append(seat)
    
    for seat in booked_seats:
        if isinstance(seat, str) and len(seat) > 1 and seat[0].isalpha():
            row = seat[0]
            if row not in seat_grid:
                seat_grid[row] = {'available': [], 'booked': []}
            seat_grid[row]['booked'].append(seat)
    
    html = '<div style="font-family: Arial, sans-serif; text-align: center; margin: 20px 0;">'
    
    # Legend with color boxes
    html += '<div style="margin-bottom: 20px; padding: 15px; background: #e8f4f8; border-radius: 8px; border: 2px solid #00d4ff;">'
    html += '<div style="font-weight: bold; margin-bottom: 10px; font-size: 13px; color: #333;">SEAT LEGEND:</div>'
    html += '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; font-size: 12px;">'
    
    # Legend items with colored boxes
    html += '<div style="text-align: left; padding: 8px; background: #ffffff; border-radius: 4px;"><span style="display: inline-block; width: 24px; height: 24px; background: #ffffff; border: 3px solid #00d4ff; border-radius: 3px; margin-right: 8px; vertical-align: middle;"></span><strong style="color: #333;">⚪ Available</strong></div>'
    html += '<div style="text-align: left; padding: 8px; background: #ffffff; border-radius: 4px;"><span style="display: inline-block; width: 24px; height: 24px; background: #d3d3d3; border: 2px solid #999; border-radius: 3px; margin-right: 8px; vertical-align: middle;"></span><strong style="color: #333;">⚫ Booked</strong></div>'
    html += '<div style="text-align: left; padding: 8px; background: #fff0f5; border-radius: 4px;"><span style="display: inline-block; width: 24px; height: 24px; background: #ff1493; border: 2px solid #c71585; border-radius: 3px; margin-right: 8px; vertical-align: middle;"></span><strong style="color: #c71585;">🩷 Female</strong></div>'
    html += '<div style="text-align: left; padding: 8px; background: #e0f2ff; border-radius: 4px;"><span style="display: inline-block; width: 24px; height: 24px; background: #0099ff; border: 2px solid #0066cc; border-radius: 3px; margin-right: 8px; vertical-align: middle;"></span><strong style="color: #0066cc;">🔵 Male</strong></div>'
    html += '<div style="text-align: left; padding: 8px; background: #e8f8e8; border-radius: 4px;"><span style="display: inline-block; width: 24px; height: 24px; background: #00cc44; border: 2px solid #009900; border-radius: 3px; margin-right: 8px; vertical-align: middle;"></span><strong style="color: #009900;">🟢 Selected</strong></div>'
    html += '</div>'
    html += '</div>'
    
    # Bus container
    html += '<div style="display: inline-block; border: 3px solid #333; border-radius: 15px; padding: 20px; background: #f9f9f9;">'
    html += '<div style="font-weight: bold; margin-bottom: 15px; font-size: 14px; color: #333;">🚌 BUS SEATING LAYOUT</div>'
    
    rows = sorted(seat_grid.keys())
    for row in rows:
        available_in_row = sorted(seat_grid[row]['available'], key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
        booked_in_row = sorted(seat_grid[row]['booked'], key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
        
        all_row_seats = {}
        for seat in available_in_row:
            col = int(seat[1:]) if seat[1:].isdigit() else 0
            all_row_seats[col] = (seat, 'available')
        for seat in booked_in_row:
            col = int(seat[1:]) if seat[1:].isdigit() else 0
            all_row_seats[col] = (seat, 'booked')
        
        # Row layout
        html += '<div style="display: flex; align-items: center; margin: 8px 0; gap: 5px; justify-content: center;">'
        html += f'<span style="width: 25px; font-weight: bold; text-align: right; font-size: 12px;">{row}</span>'
        
        # Left seats
        for col in [1, 2]:
            if col in all_row_seats:
                seat_code, status = all_row_seats[col]
                is_selected = seat_code == selected_seat
                
                if status == 'available':
                    # Available seat - keep original logic
                    seat_gender = gender_map.get(seat_code, 'Neutral')
                    if seat_gender == 'Female':
                        bg_color = '#ff1493'
                        text_color = '#fff'
                    elif seat_gender == 'Male':
                        bg_color = '#0099ff'
                        text_color = '#fff'
                    else:
                        bg_color = '#ffffff'
                        text_color = '#333'
                    if is_selected:
                        bg_color = '#00cc44'
                        text_color = '#fff'
                    html += f'<div style="width: 40px; height: 40px; background: {bg_color}; border: 2px solid #00d4ff; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; cursor: pointer; color: {text_color};">{seat_code}</div>'
                else:
                    # Booked seat - check gender_map for proper coloring
                    booked_gender = gender_map.get(seat_code, 'Neutral')
                    if booked_gender == 'Female':
                        bg_color = '#ff1493'
                        border_color = '#c71585'
                        text_color = '#fff'
                        checkmark = '♀'
                    elif booked_gender == 'Male':
                        bg_color = '#0099ff'
                        border_color = '#0066cc'
                        text_color = '#fff'
                        checkmark = '♂'
                    else:
                        bg_color = '#d3d3d3'
                        border_color = '#999'
                        text_color = '#333'
                        checkmark = '✓'
                    html += f'<div style="width: 40px; height: 40px; background: {bg_color}; border: 2px solid {border_color}; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: {text_color};">{checkmark}</div>'
            else:
                html += '<div style="width: 40px; height: 40px;"></div>'
        
        # Aisle
        html += '<div style="width: 20px; text-align: center; font-size: 11px; color: #999; font-weight: bold;">||</div>'
        
        # Right seats
        max_col = max(all_row_seats.keys()) if all_row_seats else 4
        for col in ([3, 4] if max_col >= 4 else [2, 3]):
            if col in all_row_seats:
                seat_code, status = all_row_seats[col]
                is_selected = seat_code == selected_seat
                
                if status == 'available':
                    # Available seat - keep original logic
                    seat_gender = gender_map.get(seat_code, 'Neutral')
                    if seat_gender == 'Female':
                        bg_color = '#ff1493'
                        text_color = '#fff'
                    elif seat_gender == 'Male':
                        bg_color = '#0099ff'
                        text_color = '#fff'
                    else:
                        bg_color = '#ffffff'
                        text_color = '#333'
                    if is_selected:
                        bg_color = '#00cc44'
                        text_color = '#fff'
                    html += f'<div style="width: 40px; height: 40px; background: {bg_color}; border: 2px solid #00d4ff; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; cursor: pointer; color: {text_color};">{seat_code}</div>'
                else:
                    # Booked seat - check gender_map for proper coloring
                    booked_gender = gender_map.get(seat_code, 'Neutral')
                    if booked_gender == 'Female':
                        bg_color = '#ff1493'
                        border_color = '#c71585'
                        text_color = '#fff'
                        checkmark = '♀'
                    elif booked_gender == 'Male':
                        bg_color = '#0099ff'
                        border_color = '#0066cc'
                        text_color = '#fff'
                        checkmark = '♂'
                    else:
                        bg_color = '#d3d3d3'
                        border_color = '#999'
                        text_color = '#333'
                        checkmark = '✓'
                    html += f'<div style="width: 40px; height: 40px; background: {bg_color}; border: 2px solid {border_color}; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: {text_color};">{checkmark}</div>'
            else:
                html += '<div style="width: 40px; height: 40px;"></div>'
        
        html += '</div>'
    
    html += '</div>'
    html += '<div style="margin-top: 10px; font-size: 11px; color: #666;">👇 FRONT OF BUS 👇</div>'
    html += '</div>'
    
    return html



def get_adjacent_seats(seat_code):
    """Get the adjacent seat(s) for a given seat code (seats in same row)"""
    if not isinstance(seat_code, str) or len(seat_code) < 2:
        return []
    
    row = seat_code[0]
    try:
        col = int(seat_code[1:])
    except:
        return []
    
    adjacent = []
    # Adjacent seats in the same row
    if col > 1:
        adjacent.append(f"{row}{col - 1}")  # Left seat
    if col < 4:
        adjacent.append(f"{row}{col + 1}")  # Right seat
    
    return adjacent

def validate_seat_gender_conflict(seat_code, passenger_gender, gender_map, booked_seats):
    """
    Check if seat can be booked based on adjacent seat genders.
    Female passengers cannot book seats adjacent to male passengers and vice versa.
    Returns: (is_valid, error_message)
    """
    if passenger_gender == 'Neutral':
        return (True, "")
    
    adjacent_seats = get_adjacent_seats(seat_code)
    
    for adj_seat in adjacent_seats:
        adj_gender = gender_map.get(adj_seat, 'Neutral')
        
        # If adjacent seat has opposite gender, block booking
        if passenger_gender == 'Female' and adj_gender == 'Male':
            return (False, f"❌ Cannot book {seat_code} - Adjacent seat {adj_seat} is booked by a male passenger. Females need separate seating.")
        elif passenger_gender == 'Male' and adj_gender == 'Female':
            return (False, f"❌ Cannot book {seat_code} - Adjacent seat {adj_seat} is booked by a female passenger. Males need separate seating.")
    
    return (True, "")

# =====================================================
# BOOKING FLOW HANDLERS
# =====================================================

def handle_route_inquiry(conv, user_message):
    """Handle request for booking - collect route details"""
    text_lower = user_message.lower()
    
    # Extract route info if available
    route_info = extract_route_info(user_message)
    if 'source' in route_info:
        conv.source = route_info['source']
    if 'destination' in route_info:
        conv.destination = route_info['destination']
    
    # Extract date if available
    date = extract_date(user_message)
    if date:
        conv.date = date
    
    # Check if we have all required info
    if conv.source and conv.destination and conv.date:
        # Move to agency selection
        conv.stage = "available_agencies"
        return get_available_agencies_message(conv)
    
    # Ask for missing information
    missing = []
    if not conv.source:
        missing.append("source city (from where?)")
    if not conv.destination:
        missing.append("destination city (going where?)")
    if not conv.date:
        missing.append("travel date (in YYYY-MM-DD or DD/MM/YYYY format)")
    
    prompt = f"""You are a helpful ticket booking assistant. The user wants to book a ticket but hasn't provided:
    {', '.join(missing)}
    
    Respond naturally asking for the missing information. Be friendly and helpful."""
    
    return ai_response(user_message, system_prompt=prompt)

def get_available_agencies_message(conv):
    """Get available agencies for the route and ask user to choose"""
    if not conv.source or not conv.destination or not conv.date:
        return "❌ Missing route information. Please provide source, destination, and date."
    
    # Query database for available agencies
    agencies = db.get_agencies_by_route(conv.source, conv.destination)
    
    if not agencies:
        conv.stage = "initial"
        return f"❌ Sorry! No agencies found for route: {conv.source} → {conv.destination}\n\nWould you like to try another route?"
    
    conv.available_agencies = agencies
    conv.stage = "available_agencies"
    
    # Build message with available agencies
    response = f"""✅ Found {len(agencies)} agency(ies) for your route:\n\n"""
    
    for i, agency in enumerate(agencies, 1):
        response += f"{i}. **{agency['agency_name']}**\n"
        response += f"   Total Seats Available: {agency['seats_per_vehicle']}\n"
        response += f"   Date: {conv.date}\n\n"
    
    response += f"Which agency would you like to book with? (Reply with number 1-{len(agencies)} or agency name)"
    
    return response

def handle_agency_selection(conv, user_message, username=None):
    """Handle user selecting an agency"""
    text_lower = user_message.lower()
    
    # Try to match agency number or name
    if text_lower.isdigit():
        idx = int(text_lower) - 1
        if 0 <= idx < len(conv.available_agencies):
            conv.selected_agency = conv.available_agencies[idx]['agency_username']
            return get_available_seats_message(conv, username)
    
    # Try to match agency name
    for agency in conv.available_agencies:
        if agency['agency_name'].lower() in text_lower or text_lower in agency['agency_name'].lower():
            conv.selected_agency = agency['agency_username']
            return get_available_seats_message(conv, username)
    
    return f"❌ I didn't recognize that agency. Please choose from:\n" + \
           "\n".join([f"{i}. {a['agency_name']}" for i, a in enumerate(conv.available_agencies, 1)])

def get_available_seats_message(conv, username=None):
    """Show available seats for selected agency and date, filtered by gender compatibility"""
    if not conv.selected_agency:
        return "❌ Please select an agency first."
    
    # Get available seats from database
    available_seats = db.get_available_seats(conv.selected_agency, conv.source, conv.destination, conv.date)
    
    if not available_seats:
        conv.stage = "initial"
        return "❌ No seats available for this date. Please try another date or agency."
    
    # Get gender map and booked seats
    gender_map = db.get_gender_map(conv.selected_agency, conv.source, conv.destination, conv.date)
    booked_seats = db.get_booked_seats(conv.selected_agency, conv.source, conv.destination, conv.date)
    
    # Filter seats based on passenger gender compatibility
    passenger_gender = None
    if username:
        profile = db.get_user_profile(username)
        if profile:
            passenger_gender = profile.get('gender')
    
    # Remove seats with opposite gender conflicts from available list
    filtered_seats = available_seats.copy()
    if passenger_gender and passenger_gender != 'Neutral':
        seats_to_remove = []
        for seat in available_seats:
            adjacent_seats = get_adjacent_seats(seat)
            for adj_seat in adjacent_seats:
                adj_gender = gender_map.get(adj_seat, 'Neutral')
                if passenger_gender == 'Female' and adj_gender == 'Male':
                    seats_to_remove.append(seat)
                    break
                elif passenger_gender == 'Male' and adj_gender == 'Female':
                    seats_to_remove.append(seat)
                    break
        filtered_seats = [s for s in available_seats if s not in seats_to_remove]
    
    conv.available_seats = filtered_seats if filtered_seats else available_seats
    conv.stage = "seat_selection"
    
    # Generate visual seat map with all seats (for reference)
    seat_map_html = generate_seat_map_html(available_seats, booked_seats, gender_map=gender_map)
    
    # Format response with visual map
    info_text = ""
    if len(filtered_seats) < len(available_seats):
        info_text = f"\n⚠️ Note: {len(available_seats) - len(filtered_seats)} seats excluded due to gender compatibility rules.\n"
    
    response = f"""✅ **Bus Seating Layout - {conv.date}**
{info_text}
{seat_map_html}

📌 **Click a seat to select it or reply with the seat code** (e.g., "A1", "B2")"""
    
    return response


def handle_seat_selection(conv, user_message, username=None):
    """Handle user selecting a seat.
    If the user already has a booking on the same route/date, ask for the
    other passenger's name and age instead of reusing the profile."""
    seat = extract_seat(user_message)

    if not seat:
        return f"❌ Invalid seat. Available seats: {', '.join(conv.available_seats)}"

    if seat not in conv.available_seats:
        return f"❌ Seat {seat} is not available. Choose from: {', '.join(conv.available_seats)}"

    # Get gender map / booked seats for validation
    gender_map = db.get_gender_map(
        conv.selected_agency, conv.source, conv.destination, conv.date
    )
    booked_seats = db.get_booked_seats(
        conv.selected_agency, conv.source, conv.destination, conv.date
    )

    # Check if this user already has a booking on this route+date
    existing_bookings = db.get_user_bookings(username) if username else []
    already_booked = any(
        b.get('agency_username') == conv.selected_agency
        and b.get('source', '').lower() == (conv.source or '').lower()
        and b.get('destination', '').lower() == (conv.destination or '').lower()
        and str(b.get('date', '')) == str(conv.date or '')
        for b in existing_bookings
    )

    if already_booked:
        # Booking is for another person — ask for their details
        conv.booking_for_other = True
        conv.selected_seat = seat
        conv.stage = "passenger_info_other"
        return (
            f"💺 Seat **{seat}** selected!\n\n"
            "✅ You already have a booking on this route. "
            "This ticket will be for **another passenger**.\n\n"
            "👤 Please provide the passenger's **name, age, and gender (Male/Female)**:\n"
            "*(Format: Name, Age, Gender — e.g. `Ramesh, 32, Male`)*"
        )
    else:
        # First booking — auto-fill from the logged-in user's profile
        conv.booking_for_other = False
        passenger_gender = None
        if username:
            profile = db.get_user_profile(username)
            if profile:
                conv.passenger_name = profile.get('full_name', 'Unknown')
                conv.passenger_age = profile.get('age')
                conv.passenger_gender = profile.get('gender')
                passenger_gender = profile.get('gender')

        # Validate gender compatibility for adjacent seats
        is_valid, error_msg = validate_seat_gender_conflict(
            seat, passenger_gender or 'Neutral', gender_map, booked_seats
        )
        if not is_valid:
            return error_msg

        conv.selected_seat = seat
        return confirm_booking_message(conv)


def handle_passenger_info(conv, user_message):
    """Collect name, age, and gender for an 'other' passenger when booking_for_other is True."""
    if not conv.booking_for_other:
        # Fallback: just go to confirmation
        return confirm_booking_message(conv)

    # Try to parse name, age, and gender from the user's reply
    info = extract_passenger_info(user_message)

    if 'name' in info:
        conv.passenger_name = info['name']
    if 'age' in info:
        conv.passenger_age = info['age']
    if 'gender' in info:
        conv.passenger_gender = info['gender']

    if not conv.passenger_name:
        return (
            "⚠️ I couldn't catch the passenger's name. "
            "Please reply in the format: `Name, Age, Gender` (e.g. `Ramesh, 32, Male`)"
        )
    if not conv.passenger_age:
        return (
            f"⚠️ Got the name **{conv.passenger_name}** — now please provide their age and gender (Male/Female):\n"
            "*(Format: Age, Gender — e.g. `32, Male`)*"
        )
    if not conv.passenger_gender:
        return (
            f"⚠️ Got **{conv.passenger_name}**, {conv.passenger_age} years old — now please provide their gender (Male or Female):"
        )

    # Validate gender compatibility for adjacent seats
    gender_map = db.get_gender_map(
        conv.selected_agency, conv.source, conv.destination, conv.date
    )
    booked_seats = db.get_booked_seats(
        conv.selected_agency, conv.source, conv.destination, conv.date
    )
    is_valid, error_msg = validate_seat_gender_conflict(
        conv.selected_seat, conv.passenger_gender or 'Neutral', gender_map, booked_seats
    )
    if not is_valid:
        # Clear passenger gender and revert stage back to seat selection
        conv.passenger_gender = None
        conv.stage = "seat_selection"
        return f"{error_msg}\n\nPlease choose another seat. Available seats: {', '.join(conv.available_seats)}"

    return confirm_booking_message(conv)

def confirm_booking_message(conv):
    """Show booking summary and ask for confirmation"""
    conv.stage = "confirmation"
    
    agency = None
    for a in conv.available_agencies:
        if a['agency_username'] == conv.selected_agency:
            agency = a
            break
    
    response = f"""
🎫 **BOOKING SUMMARY**
━━━━━━━━━━━━━━━━━━━━━━━━
📍 Route: {conv.source} → {conv.destination}
🏢 Agency: {agency['agency_name'] if agency else 'N/A'}
📅 Date: {conv.date}
💺 Seat: {conv.selected_seat}
👤 Passenger: {conv.passenger_name}
🎂 Age: {conv.passenger_age}
━━━━━━━━━━━━━━━━━━━━━━━━

Confirm booking? (Reply: 'yes' or 'no')"""
    
    return response

def handle_booking_confirmation(conv, user_message, username):
    """Create the booking if confirmed"""
    text_lower = user_message.lower().strip()
    
    if 'yes' in text_lower or 'confirm' in text_lower or 'book' in text_lower:
        # Create booking in database
        result = db.create_booking(
            username=username,
            agency_username=conv.selected_agency,
            source=conv.source,
            destination=conv.destination,
            date=conv.date,
            seat=conv.selected_seat,
            passenger_name=conv.passenger_name,
            passenger_age=conv.passenger_age,
            passenger_gender=conv.passenger_gender  # Pass gender
        )
        
        if result['success']:
            booking_id = result['booking_id']
            response = f"""
✅ **BOOKING CONFIRMED!**
━━━━━━━━━━━━━━━━━━━━━━━━
📌 Booking ID: {booking_id}
📍 Route: {conv.source} → {conv.destination}
📅 Date: {conv.date}
💺 Seat: {conv.selected_seat}
👤 Passenger: {conv.passenger_name}
👥 Gender: {conv.passenger_gender}
━━━━━━━━━━━━━━━━━━━━━━━━

Your ticket has been successfully booked!
Thank you for choosing our service. 🙏"""
            
            # Send WhatsApp notifications
            try:
                import notifications as notif_manager
                booking_data = {
                    "booking_id": booking_id,
                    "username": username,
                    "agency_username": conv.selected_agency,
                    "source": conv.source,
                    "destination": conv.destination,
                    "date": conv.date,
                    "seat": conv.selected_seat,
                    "passenger_name": conv.passenger_name,
                    "passenger_age": conv.passenger_age,
                    "status": "confirmed"
                }
                notif_manager.send_booking_confirmation(booking_data)
            except Exception as e:
                print(f"WhatsApp notification error: {e}")
            
            conv.reset()
            return response
        else:
            return f"❌ Booking failed: {result['message']}"
    
    elif 'no' in text_lower or 'cancel' in text_lower:
        conv.reset()
        return "❌ Booking cancelled. How can I help you?"
    
    else:
        return "Please reply 'yes' to confirm or 'no' to cancel booking."

# =====================================================
# MAIN MESSAGE PROCESSOR
# =====================================================

def process_message(user_message, username="user"):
    """
    Main function to process user messages based on conversation flow
    """
    text_lower = user_message.lower().strip()
    
    # Command: Reset/Start Over
    if any(word in text_lower for word in ["reset", "start over", "new booking", "start fresh"]):
        if username in active_conversations:
            active_conversations[username].reset()
        return "✅ Conversation reset! Ready for a new booking. What would you like to do?"
    
    conv = get_conversation(username)
    print(f"[DEBUG] User: {username}, Stage: {conv.stage}, Source: {conv.source}, Destination: {conv.destination}")
    
    # Command: Help
    if any(word in text_lower for word in ["help", "what can you do", "menu"]):
        return """🤖 **CHATBOT ASSISTANCE**
━━━━━━━━━━━━━━━━━━━━━━━━
I can help you with:

🎫 **BOOK A TICKET**
Say: "I want to book a ticket from Delhi to Mumbai on 13/07/2026"
Or: "book Delhi to Mumbai"

📋 **VIEW YOUR BOOKINGS**
Say: "show my bookings" or "view tickets"

❌ **CANCEL A BOOKING**
Say: "cancel booking 1001"

ℹ️ **BOOKING INFO**
Say: "what routes are available?"

Type your request below! 👇"""
    
    # Command: View bookings
    if any(word in text_lower for word in ["show", "view", "list", "my booking"]):
        bookings = db.get_user_bookings(username)
        if not bookings:
            return "You don't have any bookings yet. Would you like to book a ticket?"
        
        response = "📋 **YOUR BOOKINGS**\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for booking in bookings:
            response += f"""
🎫 Booking #{booking['booking_id']}
📍 {booking['source']} → {booking['destination']}
📅 {booking['date']}
💺 Seat {booking['seat']}
👤 {booking['passenger_name']} ({booking['passenger_age']} yrs)
Status: {booking['status']}
"""
        return response
    
    # Command: Cancel booking
    if any(word in text_lower for word in ["cancel", "delete"]):
        id_match = re.search(r'\b(\d+)\b', user_message)
        if id_match:
            booking_id = int(id_match.group(1))
            result = db.cancel_booking(booking_id)
            if result['success']:
                # Send WhatsApp cancellation notification
                try:
                    import notifications as notif_manager
                    notif_manager.send_cancellation_notification(result['booking'])
                except Exception as e:
                    print(f"WhatsApp cancel notification error: {e}")
                return f"✅ {result['message']}"
            else:
                return f"❌ {result['message']}"
        return "Please provide booking ID. Example: 'cancel booking 1001'"
    
    # Command: View available routes
    if "route" in text_lower or "available" in text_lower:
        routes = db.search_routes()
        if not routes:
            return "No routes available at the moment."
        
        response = "🛣️  **AVAILABLE ROUTES**\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, route in enumerate(routes, 1):
            response += f"{i}. {route['source']} → {route['destination']}\n"
        return response
    
    # Booking flow
    if any(word in text_lower for word in ["book", "reserve", "ticket", "from", "to"]):
        # Check if this is a NEW booking request (contains route info)
        route_info = extract_route_info(user_message)
        if 'source' in route_info or 'destination' in route_info:
            # New booking request - reset conversation and start fresh
            conv.reset()
            return handle_route_inquiry(conv, user_message)
        
        # Continue existing booking flow
        if conv.stage == "initial":
            return handle_route_inquiry(conv, user_message)
        elif conv.stage == "available_agencies":
            return handle_agency_selection(conv, user_message, username)
        elif conv.stage == "seat_selection":
            return handle_seat_selection(conv, user_message, username)
        elif conv.stage in ("passenger_info", "passenger_info_other"):
            return handle_passenger_info(conv, user_message)
        elif conv.stage == "confirmation":
            return handle_booking_confirmation(conv, user_message, username)
    
    # If in middle of booking, continue flow
    if conv.stage != "initial":
        if conv.stage == "available_agencies":
            return handle_agency_selection(conv, user_message, username)
        elif conv.stage == "seat_selection":
            return handle_seat_selection(conv, user_message, username)
        elif conv.stage in ("passenger_info", "passenger_info_other"):
            return handle_passenger_info(conv, user_message)
        elif conv.stage == "confirmation":
            return handle_booking_confirmation(conv, user_message, username)
    
    # Default: AI response for general questions
    prompt = """You are a helpful ticket booking assistant. Answer the user's question about booking tickets, travel, 
and provide helpful information. Keep responses concise and friendly."""
    
    return ai_response(user_message, system_prompt=prompt)


# =====================================================
# LEGACY SUPPORT (for backward compatibility)
# =====================================================

def extract_booking_info(text):
    """Legacy function - extract booking info"""
    info = {}
    
    # Try comma-separated format
    if ',' in text:
        parts = [p.strip() for p in text.split(',')]
        if len(parts) >= 6:
            try:
                info['name'] = parts[0].title()
                info['age'] = int(parts[1])
                info['source'] = parts[2].title()
                info['destination'] = parts[3].title()
                info['date'] = convert_date_format(parts[4])
                info['seat'] = parts[5].upper()
                return info
            except (ValueError, IndexError):
                pass
    
    # Try individual extractions
    info.update(extract_route_info(text))
    info.update(extract_passenger_info(text))
    
    date = extract_date(text)
    if date:
        info['date'] = date
    
    seat = extract_seat(text)
    if seat:
        info['seat'] = seat
    
    return info
