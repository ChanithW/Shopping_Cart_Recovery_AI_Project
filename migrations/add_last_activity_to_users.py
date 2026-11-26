"""
Database migration: Add last_activity column to users table
This enables true idle detection for cart abandonment
"""
import mysql.connector
from mysql.connector import Error

def run_migration():
    """Add last_activity column to users table for idle detection"""
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='ecommerce'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            print("Connected to MySQL database")
            print("\n" + "="*60)
            print("MIGRATION: Add last_activity to users table")
            print("="*60 + "\n")
            
            # Add last_activity column
            alter_query = """
            ALTER TABLE users 
            ADD COLUMN last_activity TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP
            COMMENT 'Last time user was active on the site (for idle detection)'
            """
            
            try:
                cursor.execute(alter_query)
                connection.commit()
                print("✓ Successfully added last_activity column to users table")
            except Error as e:
                if "Duplicate column name" in str(e):
                    print("✓ last_activity column already exists")
                else:
                    raise e
            
            # Initialize last_activity for existing users
            print("\nInitializing last_activity for existing users...")
            cursor.execute("""
                UPDATE users 
                SET last_activity = CURRENT_TIMESTAMP 
                WHERE last_activity IS NULL
            """)
            connection.commit()
            print(f"✓ Updated {cursor.rowcount} existing users")
            
            # Create index for performance
            print("\nCreating index for performance...")
            try:
                cursor.execute("""
                    CREATE INDEX idx_last_activity ON users(last_activity)
                """)
                connection.commit()
                print("✓ Created index on last_activity column")
            except Error as e:
                if "Duplicate key name" in str(e):
                    print("✓ Index already exists")
                else:
                    raise e
            
            # Verify the column
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            
            print("\n" + "="*60)
            print("Users table structure:")
            print("="*60)
            for column in columns:
                marker = "⭐" if column[0] == 'last_activity' else "  "
                print(f"{marker} {column[0]:20s} {column[1]:30s} {column[2]}")
            
            cursor.close()
            connection.close()
            
            print("\n" + "="*60)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nNext steps:")
            print("1. App will now track user activity on every page request")
            print("2. Cart abandonment will only trigger when user is truly idle")
            print("3. No more false positive emails! 🎉\n")
            
    except Error as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    run_migration()
