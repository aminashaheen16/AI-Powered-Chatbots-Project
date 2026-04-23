import sqlite3
import os

DB_PATH = 'data/inventory.db'

def setup_db():
    if not os.path.exists('data'):
        os.makedirs('data')
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop existing table if any
    cursor.execute("DROP TABLE IF EXISTS Assets")
    
    # Create table with correct schema
    cursor.execute("""
    CREATE TABLE Assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        status TEXT NOT NULL,
        vendor TEXT,
        location TEXT
    )
    """)
    
    # Seed data
    assets = [
        ('MacBook Pro', 15, 'Active', 'Apple', 'Room 101'),
        ('Dell Monitor', 20, 'Active', 'Dell', 'Warehouse A'),
        ('Cisco Router', 5, 'Active', 'Cisco', 'Server Room'),
        ('HP Printer', 2, 'Inactive', 'HP', 'Room 202'),
        ('Old Laptop', 10, 'Disposed', 'Generic', 'None'),
        ('iPad Air', 12, 'Active', 'Apple', 'Room 101'),
        ('Office Chair', 50, 'Active', 'Steelcase', 'Office 1'),
        ('Testing Server', 1, 'Inactive', 'IBM', 'Server Room')
    ]
    
    cursor.executemany("INSERT INTO Assets (name, quantity, status, vendor, location) VALUES (?, ?, ?, ?, ?)", assets)
    
    conn.commit()
    conn.close()
    print("Database setup and seeded successfully at data/inventory.db")

if __name__ == "__main__":
    setup_db()
