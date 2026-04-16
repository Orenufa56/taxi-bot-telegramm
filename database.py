import sqlite3
import logging
from datetime import datetime

DB_PATH = "taxi_bot.db"

# Флаг для отслеживания инициализации (ГЛОБАЛЬНЫЙ)
_DB_INITIALIZED = False

def init_db():
    """Инициализация базы данных (только один раз)"""
    global _DB_INITIALIZED
    if _DB_INITIALIZED:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            total_orders INTEGER DEFAULT 0,
            created_at TEXT,
            last_order_at TEXT
        )
    ''')
    
    # Таблица заказов
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
            comment TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    _DB_INITIALIZED = True
    logging.info("✅ База данных инициализирована (один раз)")

def add_user(user_id: int, username: str, first_name: str, last_name: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

def update_user_phone(user_id: int, phone: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET phone = ?, last_order_at = ?
        WHERE user_id = ?
    ''', (phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
    
    cursor.execute('''
        UPDATE users SET total_orders = total_orders + 1
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()

def add_order(user_id: int, username: str, from_city: str, to_city: str, 
              order_date: str, order_time: str, phone: str, comment: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO orders (user_id, username, from_city, to_city, order_date, order_time, phone, comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, from_city, to_city, order_date, order_time, phone, comment, 
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

def get_user_history(user_id: int, limit: int = 10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT from_city, to_city, order_date, order_time, created_at, status
        FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_user_stats(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT total_orders, phone, created_at, last_order_at
        FROM users
        WHERE user_id = ?
    ''', (user_id,))
    
    stats = cursor.fetchone()
    conn.close()
    return stats
