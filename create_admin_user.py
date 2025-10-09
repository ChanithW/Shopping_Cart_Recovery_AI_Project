#!/usr/bin/env python3
"""
Create admin user with proper password hash
"""
import MySQLdb
from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_HOST = os.getenv('MYSQL_HOST', 'localhost')
DB_USER = os.getenv('MYSQL_USER', 'root')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
DB_NAME = os.getenv('MYSQL_DB', 'ecommerce')

def create_admin_user():
    try:
        print("Creating admin user...")
        print(f"Connecting to database: {DB_HOST}/{DB_NAME}")
        
        # Connect to database
        connection = MySQLdb.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            db=DB_NAME
        )
        cursor = connection.cursor()
        
        # Check if admin user already exists
        cursor.execute("SELECT id, email FROM users WHERE email = %s", ('admin@ecommerce.com',))
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            print(f"Admin user already exists with ID: {existing_admin[0]}")
            print("Updating password...")
            
            # Update existing admin password
            password_hash = generate_password_hash('admin123')
            cursor.execute(
                "UPDATE users SET password = %s WHERE email = %s", 
                (password_hash, 'admin@ecommerce.com')
            )
        else:
            print("Creating new admin user...")
            
            # Create new admin user
            password_hash = generate_password_hash('admin123')
            cursor.execute("""
                INSERT INTO users (name, email, password, role, phone, address) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ('Admin User', 'admin@ecommerce.com', password_hash, 'admin', '', ''))
        
        connection.commit()
        
        # Verify the admin user
        cursor.execute("SELECT id, name, email, role FROM users WHERE email = %s", ('admin@ecommerce.com',))
        admin_user = cursor.fetchone()
        
        if admin_user:
            print("\n✅ Admin user created/updated successfully!")
            print(f"ID: {admin_user[0]}")
            print(f"Name: {admin_user[1]}")
            print(f"Email: {admin_user[2]}")
            print(f"Role: {admin_user[3]}")
            print("\n🔑 Login Credentials:")
            print("📧 Email: admin@ecommerce.com")
            print("🔐 Password: admin123")
        
        cursor.close()
        connection.close()
        
    except MySQLdb.Error as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("=" * 50)
    print("   Admin User Setup")
    print("=" * 50)
    create_admin_user()
    print("=" * 50)