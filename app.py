import sqlite3
from flask import Flask, request, jsonify, render_template
from nltk.tokenize import word_tokenize
import re
import nltk

app = Flask(__name__)

# Download required NLTK data
nltk.download('punkt')

# Track the state of the conversation
conversation_state = {}

# Function to initialize the SQLite database
def init_db():
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            check_in TEXT,
            check_out TEXT,
            guests INTEGER,
            room_type TEXT,
            room_price REAL,
            status TEXT
        )
    ''')

    # Create rooms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_type TEXT,
            price REAL
        )
    ''')

    # Insert room types with prices (if not already present)
    cursor.execute('SELECT COUNT(*) FROM rooms')
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Standard', 100.0)")
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Deluxe', 150.0)")
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Suite', 200.0)")

    conn.commit()
    conn.close()

# Function to get room options
def get_room_options():
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()

    cursor.execute('SELECT room_type, price FROM rooms')
    rooms = cursor.fetchall()

    conn.close()
    return rooms

# Function to add a new booking to the database
def add_booking(user_id, check_in, check_out, guests, room_type, room_price):
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO bookings (user_id, check_in, check_out, guests, room_type, room_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, check_in, check_out, guests, room_type, room_price, 'booked'))

    conn.commit()
    conn.close()

# Function to extract and validate dates
def extract_date(text):
    date_pattern = re.compile(r'\d{2}[-/]\d{2}[-/]\d{4}')
    date_match = date_pattern.search(text)
    
    if date_match:
        return date_match.group()
    return None

# Function to extract guests count
def extract_guests(text):
    number_pattern = re.compile(r'\d+')
    number_match = number_pattern.search(text)
    
    if number_match:
        return number_match.group()
    return None

# Route to render the UI
@app.route('/')
def index():
    return render_template('index.html')

# Chatbot route with sequential flow for room selection, booking, and date validation
@app.route('/chat', methods=['POST'])
def chat():
    user_id = request.remote_addr  # Use the user's IP address as a session ID
    text = request.json.get('text')

    # Initialize state if it's the first time interacting
    if user_id not in conversation_state:
        conversation_state[user_id] = {"step": "choose_room", "check_in": None, "check_out": None, "guests": None, "room_type": None, "room_price": None}

    state = conversation_state[user_id]
    response = ""

    # Ask user to choose a room type
    if state["step"] == "choose_room":
        rooms = get_room_options()
        response = "We have the following room options available:\n"
        for room in rooms:
            response += f"{room[0]}: ${room[1]} per night\n"
        response += "Please select a room type."
        state["step"] = "room_selection"

    # Handle room selection
    elif state["step"] == "room_selection":
        rooms = get_room_options()
        room_dict = {room[0].lower(): room[1] for room in rooms}
        selected_room = text.lower()

        if selected_room in room_dict:
            state["room_type"] = selected_room.capitalize()
            state["room_price"] = room_dict[selected_room]
            response = f"You selected {state['room_type']} for ${state['room_price']} per night. When would you like to check in? Please provide a valid date (e.g., 23-09-2024)."
            state["step"] = "check_in"
        else:
            response = "Please select a valid room type from the list."

    # Handle check-in date
    elif state["step"] == "check_in":
        check_in = extract_date(text)
        if check_in:
            state["check_in"] = check_in
            response = "Got it! Now, what is your check-out date? Please provide a valid date (e.g., 24-09-2024)."
            state["step"] = "check_out"
        else:
            response = "Please provide a valid check-in date (e.g., 23-09-2024)."

    # Handle check-out date
    elif state["step"] == "check_out":
        check_out = extract_date(text)
        if check_out:
            state["check_out"] = check_out
            response = "How many guests will be staying?"
            state["step"] = "guests"
        else:
            response = "Please provide a valid check-out date (e.g., 24-09-2024)."

    # Handle number of guests
    elif state["step"] == "guests":
        guests = extract_guests(text)
        if guests:
            state["guests"] = guests

            # Store booking in the SQLite database
            add_booking(user_id, state["check_in"], state["check_out"], state["guests"], state["room_type"], state["room_price"])
            response = f"Thank you! Your room is booked from {state['check_in']} to {state['check_out']} for {state['guests']} guests in a {state['room_type']} room at ${state['room_price']} per night."

            # Reset the conversation state after successful booking
            conversation_state[user_id] = {"step": "choose_room", "check_in": None, "check_out": None, "guests": None, "room_type": None, "room_price": None}
        else:
            response = "Please provide the number of guests."

    return jsonify({'response': response})

if __name__ == '__main__':
    init_db()  # Initialize the database when the app starts
    app.run(debug=True, host='0.0.0.0', port=5001)
