import sqlite3
DB_NAME = "tickets.db"
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bookings'")
        table_exists = cur.fetchone() is not None
        
        if table_exists:
            cur.execute("PRAGMA table_info(bookings)")
            columns = {row[1] for row in cur.fetchall()}
            required_cols = {'id', 'name', 'age', 'source', 'destination', 'date', 'seat'}
            if not required_cols.issubset(columns):
                cur.execute("DROP TABLE bookings")
                table_exists = False
        
        if not table_exists:
            cur.execute("""
            CREATE TABLE bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL,
                seat TEXT NOT NULL
            )
            """)
    except Exception as e:
        print(f"Database init error: {e}")
        try:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL,
                seat TEXT NOT NULL
            )
            """)
        except:
            pass
    conn.commit()
    conn.close()
def add_booking(name, age, source, destination, date, seat):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO bookings (name, age, source, destination, date, seat)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (name, age, source, destination, date, seat))
    conn.commit()
    conn.close()
def get_bookings():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings")
    data = cur.fetchall()
    conn.close()
    return data
def cancel_booking(booking_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()