"""
Add unique constraint to prevent duplicate email logs
This will prevent the same cart from being logged multiple times within a short period
"""

import MySQLdb
import MySQLdb.cursors
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def add_unique_constraint():
    """Add a unique index to prevent duplicate logs for same user+cart within 24 hours"""
    try:
        # Connect to database
        conn = MySQLdb.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=MySQLdb.cursors.DictCursor
        )
        cursor = conn.cursor()
        
        print("Adding database constraints to prevent duplicate emails...")
        
        # First, let's check if the index already exists
        cursor.execute("""
            SHOW INDEX FROM cart_abandonment_log 
            WHERE Key_name = 'idx_user_cart_unique'
        """)
        
        existing_index = cursor.fetchone()
        
        if existing_index:
            print("✓ Unique index already exists!")
            cursor.close()
            conn.close()
            return
        
        # Add composite index on user_id and cart_hash for faster duplicate checks
        print("Creating composite index on (user_id, cart_hash, created_at)...")
        cursor.execute("""
            CREATE INDEX idx_user_cart_unique 
            ON cart_abandonment_log (user_id, cart_hash, created_at)
        """)
        
        conn.commit()
        print("✓ Index created successfully!")
        
        # Show the indexes
        cursor.execute("SHOW INDEX FROM cart_abandonment_log")
        indexes = cursor.fetchall()
        
        print("\nCurrent indexes on cart_abandonment_log:")
        for idx in indexes:
            print(f"  - {idx['Key_name']}: {idx['Column_name']}")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Database optimization complete!")
        
    except Exception as e:
        print(f"Error adding constraint: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Cart Abandonment Log - Database Optimization")
    print("=" * 60)
    add_unique_constraint()
