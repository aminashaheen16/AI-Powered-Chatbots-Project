import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/inventory.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables (SQLite syntax: INTEGER PRIMARY KEY AUTOINCREMENT)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS AssetCategories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER,
        vendor_id INTEGER,
        location_id INTEGER,
        status TEXT DEFAULT 'Active',
        quantity INTEGER DEFAULT 0,
        FOREIGN KEY (category_id) REFERENCES AssetCategories(id),
        FOREIGN KEY (vendor_id) REFERENCES Vendors(id),
        FOREIGN KEY (location_id) REFERENCES Locations(id)
    )
    ''')

    # Seed data if empty
    cursor.execute("SELECT COUNT(*) FROM AssetCategories")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO AssetCategories (name) VALUES ('Laptops'), ('Monitors'), ('Furniture')")
        cursor.execute("INSERT INTO Vendors (name, contact) VALUES ('Dell', 'sales@dell.com'), ('IKEA', 'info@ikea.com')")
        cursor.execute("INSERT INTO Locations (name, address) VALUES ('Headquarters', '123 Tech St'), ('Warehouse', '456 Storage Ave')")
        
        # Adding some assets with different statuses
        assets = [
            ('XPS 15', 1, 1, 1, 'Active', 10),
            ('UltraSharp 27', 2, 1, 1, 'Active', 5),
            ('Office Chair', 3, 2, 2, 'Active', 20),
            ('Old Laptop', 1, 1, 2, 'Retired', 2),
            ('Broken Monitor', 2, 1, 2, 'Disposed', 1)
        ]
        cursor.executemany("INSERT INTO Assets (name, category_id, vendor_id, location_id, status, quantity) VALUES (?, ?, ?, ?, ?, ?)", assets)

    conn.commit()
    conn.close()

def execute_query(query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        return {"columns": column_names, "data": results}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
