"""
Database migration script to add discount_offered column
"""
import mysql.connector
from mysql.connector import Error

def run_migration():
    """Add discount_offered column to cart_abandonment_log table"""
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
            
            # Add discount_offered column
            alter_query = """
            ALTER TABLE cart_abandonment_log 
            ADD COLUMN discount_offered DECIMAL(5,2) DEFAULT 0 
            COMMENT 'Discount percentage offered in abandonment email'
            """
            
            try:
                cursor.execute(alter_query)
                connection.commit()
                print("✓ Successfully added discount_offered column to cart_abandonment_log table")
            except Error as e:
                if "Duplicate column name" in str(e):
                    print("✓ discount_offered column already exists")
                else:
                    raise e
            
            # Verify the column
            cursor.execute("DESCRIBE cart_abandonment_log")
            columns = cursor.fetchall()
            
            print("\nTable structure:")
            for column in columns:
                print(f"  - {column[0]} ({column[1]})")
            
            cursor.close()
            connection.close()
            print("\nMigration completed successfully!")
            
    except Error as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    run_migration()
