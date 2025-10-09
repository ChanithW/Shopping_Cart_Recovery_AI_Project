#!/usr/bin/env python3
"""
Quick Admin Creator - Creates admin user directly
"""
import MySQLdb
from werkzeug.security import generate_password_hash

# Database connection
try:
    conn = MySQLdb.connect(
        host='localhost',
        user='root',
        password='',
        db='ecommerce'
    )
    cursor = conn.cursor()
    
    # Admin credentials
    admin_name = 'Admin User'
    admin_email = 'admin@ecommerce.com'
    admin_password = 'admin123'
    
    # Check if admin exists
    cursor.execute("SELECT id, name, role FROM users WHERE email = %s", (admin_email,))
    existing = cursor.fetchone()
    
    if existing:
        print(f"✅ Admin user already exists: {existing}")
        # Update to admin role
        cursor.execute("UPDATE users SET role = 'admin' WHERE email = %s", (admin_email,))
        conn.commit()
        print(f"✅ Updated to admin role")
    else:
        # Create new admin
        hashed = generate_password_hash(admin_password)
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'admin')",
            (admin_name, admin_email, hashed)
        )
        conn.commit()
        print(f"✅ Admin user created!")
    
    print(f"\n📋 Admin Credentials:")
    print(f"   Email: {admin_email}")
    print(f"   Password: {admin_password}")
    print(f"\n🔗 Login: http://127.0.0.1:8080/login")
    print(f"📊 Admin: http://127.0.0.1:8080/admin")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
