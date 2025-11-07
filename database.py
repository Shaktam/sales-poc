import sqlite3
from datetime import datetime
import os

DB_NAME = 'pos_system.db'

def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with all required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # Add image_url column to existing items table if it doesn't exist
    try:
        cursor.execute('ALTER TABLE items ADD COLUMN image_url TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists, ignore the error
        pass
    
    # Create bills table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_number TEXT NOT NULL UNIQUE,
            total_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create bill_items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (bill_id) REFERENCES bills(id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    ''')
    
    conn.commit()
    
    # Check if database is empty and seed with sample data
    cursor.execute('SELECT COUNT(*) as count FROM categories')
    category_count = cursor.fetchone()['count']
    
    if category_count == 0:
        seed_sample_data(cursor, conn)
    
    conn.close()

def seed_sample_data(cursor, conn):
    """Seed the database with sample categories and items for testing."""
    # Insert 2 categories
    cursor.execute('INSERT INTO categories (name) VALUES (?)', ('Health_Basket',))
    category1_id = cursor.lastrowid
    
    cursor.execute('INSERT INTO categories (name) VALUES (?)', ('Aswins',))
    category2_id = cursor.lastrowid
    
    # Insert items for Health Basket
    Health_Basket_items = [
        ('Wireless Mouse', 25.99, 'https://via.placeholder.com/200x200?text=Wireless+Mouse'),
        ('USB Keyboard', 35.50, 'https://via.placeholder.com/200x200?text=USB+Keyboard'),
        ('HDMI Cable', 12.99, 'https://via.placeholder.com/200x200?text=HDMI+Cable'),
        ('USB Flash Drive 32GB', 15.00, 'https://via.placeholder.com/200x200?text=USB+Flash+Drive'),
    ]
    
    for item_name, price, image_url in Health_Basket_items:
        cursor.execute('''
            INSERT INTO items (category_id, name, price, image_url)
            VALUES (?, ?, ?, ?)
        ''', (category1_id, item_name, price, image_url))
    
    # Insert items for Aswins
    Aswins_items = [
        ('T-Shirt', 19.99, 'https://via.placeholder.com/200x200?text=T-Shirt'),
        ('Jeans', 49.99, 'https://via.placeholder.com/200x200?text=Jeans'),
        ('Sneakers', 79.99, 'https://via.placeholder.com/200x200?text=Sneakers'),
        ('Jacket', 89.99, 'https://via.placeholder.com/200x200?text=Jacket'),
    ]
    
    for item_name, price, image_url in Aswins_items:
        cursor.execute('''
            INSERT INTO items (category_id, name, price, image_url)
            VALUES (?, ?, ?, ?)
        ''', (category2_id, item_name, price, image_url))
    
    conn.commit()

if __name__ == '__main__':
    init_db()
    print(f"Database '{DB_NAME}' initialized successfully!")

