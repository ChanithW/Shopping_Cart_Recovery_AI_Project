"""
Cleanup script to remove duplicate email log entries
This will keep only the most recent entry for each user+cart_hash combination
"""

import MySQLdb
import MySQLdb.cursors
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def cleanup_duplicates():
    """Remove duplicate email entries, keeping only the most recent one per user+cart_hash"""
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
        
        print("Checking for duplicate email entries...")
        
        # Find duplicates (same user, same cart, same time period)
        cursor.execute("""
            SELECT user_id, cart_hash, DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') as time_group, COUNT(*) as count
            FROM cart_abandonment_log
            WHERE email_sent = TRUE
            GROUP BY user_id, cart_hash, time_group
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            print("No duplicates found!")
            cursor.close()
            conn.close()
            return
        
        print(f"Found {len(duplicates)} sets of duplicates")
        
        total_deleted = 0
        
        for dup in duplicates:
            user_id = dup['user_id']
            cart_hash = dup['cart_hash']
            time_group = dup['time_group']
            count = dup['count']
            
            print(f"Processing user_id={user_id}, cart_hash={cart_hash[:8]}..., time={time_group} ({count} duplicates)")
            
            # Keep the first entry (lowest id), delete others in the same time group
            cursor.execute("""
                DELETE FROM cart_abandonment_log
                WHERE user_id = %s AND cart_hash = %s 
                AND DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') = %s
                AND email_sent = TRUE
                AND id NOT IN (
                    SELECT * FROM (
                        SELECT MIN(id) 
                        FROM cart_abandonment_log
                        WHERE user_id = %s AND cart_hash = %s 
                        AND DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') = %s
                        AND email_sent = TRUE
                    ) as keep_record
                )
            """, (user_id, cart_hash, time_group, user_id, cart_hash, time_group))
            
            deleted = cursor.rowcount
            total_deleted += deleted
            print(f"  Deleted {deleted} duplicate entries")
        
        conn.commit()
        print(f"\n✓ Cleanup complete! Removed {total_deleted} duplicate entries")
        
        # Show final count
        cursor.execute("SELECT COUNT(*) as total FROM cart_abandonment_log WHERE email_sent = TRUE")
        result = cursor.fetchone()
        print(f"Total email log entries remaining: {result['total']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Cart Abandonment Email Duplicate Cleanup")
    print("=" * 60)
    cleanup_duplicates()
