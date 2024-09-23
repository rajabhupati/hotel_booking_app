import sqlite3

# Function to initialize the SQLite database
def init_db():
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()

    # Create the bookings table if it doesn't exist
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

    # Create the rooms table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_type TEXT,
            price REAL
        )
    ''')

    # Insert default room types with prices if the rooms table is empty
    cursor.execute('SELECT COUNT(*) FROM rooms')
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Standard', 100.0)")
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Deluxe', 150.0)")
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Suite', 200.0)")

    conn.commit()
    conn.close()

# Function to add a new booking to the database
def add_booking(user_id, check_in, check_out, guests, room_type, room_price):
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()

    # Insert new booking into the bookings table
    cursor.execute('''
        INSERT INTO bookings (user_id, check_in, check_out, guests, room_type, room_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, check_in, check_out, guests, room_type, room_price, 'booked'))

    conn.commit()
    conn.close()

# Function to get all available room options (room type and price)
def get_room_options():
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()

    cursor.execute('SELECT room_type, price FROM rooms')
    rooms = cursor.fetchall()

    conn.close()
    return rooms

# Function to get all bookings (for reference or admin purposes)
def get_bookings():
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM bookings')
    rows = cursor.fetchall()

    conn.close()
    return rows
