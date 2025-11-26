import sqlite3
import os
import time
from contextlib import contextmanager
from typing import Generator
import logging

# Database configuration
DATABASE_PATH = "db/library.db"
SEED_SQL_PATH = "db/seed.sql"

# Set up logging
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the SQLite database with all tables and seed data"""
    # Create db directory if it doesn't exist
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        cursor = conn.cursor()
        
        # Enable better concurrency settings
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA busy_timeout = 5000")
        
        # Create tables
        create_tables(cursor)
        
        # Check if database is empty and seed if needed
        cursor.execute("SELECT COUNT(*) as count FROM books")
        book_count = cursor.fetchone()["count"]
        
        if book_count == 0:
            print("Seeding database with initial data...")
            seed_database(cursor)
        
        conn.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def create_tables(cursor: sqlite3.Cursor):
    """Create all required tables"""
    
    # Books table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            isbn TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            total_amount DECIMAL(10,2) DEFAULT 0,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    """)
    
    # Order items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            book_isbn TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
            FOREIGN KEY (book_isbn) REFERENCES books (isbn)
        )
    """)
    
    # Chat sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            title TEXT DEFAULT 'New Conversation'
        )
    """)
    
    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
    """)
    
    # Tool calls table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            tool_name TEXT NOT NULL,
            input_args TEXT NOT NULL,
            output TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
            FOREIGN KEY (message_id) REFERENCES messages (id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_calls_session_id ON tool_calls(session_id)")

def seed_database(cursor: sqlite3.Cursor):
    """Seed the database with initial data"""
    
    # Insert books
    books = [
        ('9780134685991', 'Clean Code: A Handbook of Agile Software Craftsmanship', 'Robert C. Martin', 47.49, 25),
        ('9780201633610', 'Design Patterns: Elements of Reusable Object-Oriented Software', 'Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides', 54.99, 18),
        ('9780135957059', 'The Pragmatic Programmer: Your Journey to Mastery', 'David Thomas, Andrew Hunt', 42.50, 32),
        ('9780321125217', 'Domain-Driven Design: Tackling Complexity in the Heart of Software', 'Eric Evans', 56.75, 12),
        ('9780134757599', 'Clean Architecture: A Craftsman\'s Guide to Software Structure and Design', 'Robert C. Martin', 49.99, 22),
        ('9780134494166', 'Accelerate: The Science of Lean Software and DevOps', 'Nicole Forsgren, Jez Humble, Gene Kim', 39.95, 15),
        ('9780136554828', 'Site Reliability Engineering: How Google Runs Production Systems', 'Betsy Beyer, Chris Jones, Jennifer Petoff, Niall Richard Murphy', 51.25, 8),
        ('9780132350884', 'Working Effectively with Legacy Code', 'Michael Feathers', 45.00, 20),
        ('9780321942067', 'Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation', 'Jez Humble, David Farley', 52.99, 14),
        ('9780137054899', 'The Clean Coder: A Code of Conduct for Professional Programmers', 'Robert C. Martin', 38.95, 28)
    ]
    
    cursor.executemany(
        "INSERT INTO books (isbn, title, author, price, stock) VALUES (?, ?, ?, ?, ?)",
        books
    )
    
    # Insert customers
    customers = [
        ('Alice Johnson', 'alice.johnson@email.com'),
        ('Bob Smith', 'bob.smith@email.com'),
        ('Carol Davis', 'carol.davis@email.com'),
        ('David Wilson', 'david.wilson@email.com'),
        ('Eva Brown', 'eva.brown@email.com'),
        ('Frank Miller', 'frank.miller@email.com')
    ]
    
    cursor.executemany(
        "INSERT INTO customers (name, email) VALUES (?, ?)",
        customers
    )
    
    # Insert orders
    orders = [
        (1, 142.47),
        (2, 54.99),
        (3, 128.25),
        (4, 56.75)
    ]
    
    cursor.executemany(
        "INSERT INTO orders (customer_id, total_amount) VALUES (?, ?)",
        orders
    )
    
    # Insert order items
    order_items = [
        (1, '9780134685991', 3, 47.49),
        (2, '9780201633610', 1, 54.99),
        (3, '9780135957059', 3, 42.50),
        (4, '9780321125217', 1, 56.75)
    ]
    
    cursor.executemany(
        "INSERT INTO order_items (order_id, book_isbn, quantity, unit_price) VALUES (?, ?, ?, ?)",
        order_items
    )
    
    # Update book stock based on orders
    cursor.execute("""
        UPDATE books 
        SET stock = stock - (
            SELECT COALESCE(SUM(quantity), 0) 
            FROM order_items 
            WHERE order_items.book_isbn = books.isbn
        )
    """)

@contextmanager
def get_db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    """Simple database cursor context manager without nested connections"""
    conn = None
    cursor = None
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Initialize database when module is imported
init_database()
