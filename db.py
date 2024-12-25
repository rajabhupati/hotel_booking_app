import sqlite3

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

def get_bookings():
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bookings')
    rows = cursor.fetchall()
    conn.close()
    return rows
