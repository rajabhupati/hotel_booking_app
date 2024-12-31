import sqlite3
import logging

def init_db():
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    check_in TEXT,
    check_out TEXT,
    guests INTEGER,
    room_type TEXT,
    room_price REAL,
    breakfast TEXT,
    payment_method TEXT,
    status TEXT
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_type TEXT,
    price REAL
    )''')
    
    cursor.execute('SELECT COUNT(*) FROM rooms')
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Standard', 100.0)")
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Deluxe', 150.0)")
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Suite', 200.0)")
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Executive Suite', 300.0)")
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Family Room', 250.0)")
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Penthouse', 500.0)")
        cursor.execute("INSERT INTO rooms (room_type, price) VALUES ('Budget Room', 80.0)")
    
    conn.commit()
    conn.close()

def add_booking(user_id, check_in, check_out, guests, room_type, room_price, breakfast, payment_method):
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO bookings (user_id, check_in, check_out, guests, room_type, room_price, breakfast, payment_method, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, check_in, check_out, guests, room_type, room_price, breakfast, payment_method, 'booked'))
    conn.commit()
    conn.close()

def get_room_options():
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()
    cursor.execute('SELECT room_type, price FROM rooms')
    rooms = cursor.fetchall()
    conn.close()
    return rooms

def get_booking_details(user_id):
    logging.info(f"Fetching booking details for user_id: {user_id}")
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT room_type, check_in, check_out, room_price FROM bookings WHERE user_id = ?', (user_id,))
        booking = cursor.fetchone()
        logging.info(f"Booking details retrieved: {booking}")
        return booking
    except Exception as e:
        logging.error(f"Error fetching booking details: {e}")
        return None
    finally:
        conn.close()

def get_room_price(room_type: str) -> float:
    """Fetches the price of a given room type from the database."""
    
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT price FROM rooms WHERE LOWER(room_type) = LOWER(?)', (room_type,))
        result = cursor.fetchone()
        
        if result:
            price = result[0]
            logging.info(f"Price for {room_type} retrieved: ${price}")
            return price
        else:
            logging.warning(f"No price found for room type: {room_type}")
            return 0.0  # Return 0 if no such room type exists
          
    except Exception as e:
        logging.error(f"Error retrieving price for {room_type}: {e}")
        return 0.0  # Return 0 in case of error
      
    finally:
        conn.close()
