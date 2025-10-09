#!/usr/bin/env python3
"""
Script to create admin user with proper password hash
Run this script after setting up the database
"""

import MySQLdb
from werkzeug.security import generate_password_hash

# Database configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'password'  # Update this with your MySQL password
DB_NAME = 'ecommerce'

def create_admin_user():
    try:
        # Connect to database
        connection = MySQLdb.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            db=DB_NAME
        )
        cursor = connection.cursor()
        
        # Check if admin user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", ('admin@ecommerce.com',))
        if cursor.fetchone():
            print("Admin user already exists!")
            return
        
        # Create password hash
        password_hash = generate_password_hash('admin123')
        
        # Insert admin user
        cursor.execute("""
            INSERT INTO users (name, email, password, role) 
            VALUES (%s, %s, %s, %s)
        """, ('Admin User', 'admin@ecommerce.com', password_hash, 'admin'))
        
        connection.commit()
        print("Admin user created successfully!")
        print("Email: admin@ecommerce.com")
        print("Password: admin123")
        
    except MySQLdb.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    print("Creating admin user...")
    create_admin_user()