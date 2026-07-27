import sqlite3
from datetime import datetime, timedelta

DB_NAME = "taxi_bot.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            first_seen TEXT,
            total_orders INTEGER DEFAULT 0,
            bonus_points INTEGER DEFAULT 0,
            used_bonus INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            from_city TEXT,
            to_city TEXT,
            order_date TEXT,
            order_time TEXT,
            phone TEXT,
            seats INTEGER DEFAULT 1,
            comment TEXT,
            price_per_seat INTEGER,
            price INTEGER,
            bonus_earned INTEGER DEFAULT 0,
            bonus_used INTEGER DEFAULT 0,
            final_price INTEGER,
            status TEXT DEFAULT 'новый',
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bonus_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_id INTEGER,
            amount INTEGER,
            type TEXT,
            description TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(user_id, username=None, first_name=None, last_name=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        first_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, last_name, first_seen, total_orders, bonus_points, used_bonus) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, first_name, last_name, first_seen, 0, 0, 0)
        )
        conn.commit()
    conn.close()

def update_user_name(user_id, name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (name, user_id))
    conn.commit()
    conn.close()

def update_user_phone(user_id, phone):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
    conn.commit()
    conn.close()

def get_user_bonus(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT bonus_points, used_bonus FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row if row else (0, 0)

def add_bonus(user_id, amount, order_id, description):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET bonus_points = bonus_points + ? WHERE user_id = ?", (amount, user_id))
    cursor.execute(
        "INSERT INTO bonus_history (user_id, order_id, amount, type, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, order_id, amount, "earned", description, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def use_bonus(user_id, amount, order_id, description):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET bonus_points = bonus_points - ?, used_bonus = used_bonus + ? WHERE user_id = ?", (amount, amount, user_id))
    cursor.execute(
        "INSERT INTO bonus_history (user_id, order_id, amount, type, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, order_id, amount, "used", description, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def add_order(user_id, username, from_city, to_city, order_date, order_time, phone, seats, comment, price_per_seat, price, bonus_earned, bonus_used, final_price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO orders (user_id, username, from_city, to_city, order_date, order_time, phone, seats, comment, price_per_seat, price, bonus_earned, bonus_used, final_price, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, from_city, to_city, order_date, order_time, phone, seats, comment, price_per_seat, price, bonus_earned, bonus_used, final_price, created_at))
    order_id = cursor.lastrowid
    cursor.execute("UPDATE users SET total_orders = total_orders + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return order_id

def get_user_history(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT from_city, to_city, order_date, order_time, seats, price, bonus_earned, bonus_used, final_price, status
        FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 10
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_user_stats(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT total_orders, phone, first_name, username, bonus_points, used_bonus FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_user_name(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_user_total_orders(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT total_orders FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def get_user_last_order(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT order_date, from_city, to_city, price_per_seat, price
        FROM orders 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_user_orders_by_status(user_id, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND status = ?", (user_id, status))
    count = cursor.fetchone()[0]
    conn.close()
    return count
