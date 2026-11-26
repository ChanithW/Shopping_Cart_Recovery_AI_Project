"""
Diagnostic script to check idle detection setup
"""
import mysql.connector
from datetime import datetime, timedelta

def diagnose_idle_detection():
    print("=" * 70)
    print("IDLE DETECTION DIAGNOSTIC")
    print("=" * 70)
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='ecommerce'
        )
        cursor = conn.cursor(dictionary=True)
        
        # Test 1: Check if last_activity column exists
        print("\n1️⃣ Checking if last_activity column exists...")
        cursor.execute("SHOW COLUMNS FROM users LIKE 'last_activity'")
        result = cursor.fetchone()
        
        if not result:
            print("❌ PROBLEM FOUND: last_activity column does NOT exist!")
            print("   FIX: Run the migration:")
            print("   python migrations/add_last_activity_to_users.py")
            return False
        
        print(f"✅ last_activity column exists: {result['Type']}")
        
        # Test 2: Check if any users have last_activity set
        print("\n2️⃣ Checking if last_activity is being tracked...")
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(last_activity) as with_activity
            FROM users
        """)
        counts = cursor.fetchone()
        
        print(f"   Total users: {counts['total']}")
        print(f"   Users with activity: {counts['with_activity']}")
        
        if counts['with_activity'] == 0:
            print("⚠️  WARNING: No users have last_activity timestamp!")
            print("   This means activity tracking middleware is not working.")
        else:
            print(f"✅ {counts['with_activity']} users have activity tracking")
        
        # Test 3: Check recent user activity
        print("\n3️⃣ Checking recent user activity...")
        cursor.execute("""
            SELECT id, name, email, last_activity,
                   TIMESTAMPDIFF(SECOND, last_activity, NOW()) as seconds_idle
            FROM users
            WHERE last_activity IS NOT NULL
            ORDER BY last_activity DESC
            LIMIT 5
        """)
        users = cursor.fetchall()
        
        if users:
            for user in users:
                idle_secs = user['seconds_idle'] or 0
                status = "🟢 ACTIVE" if idle_secs < 60 else "🔴 IDLE"
                print(f"   {status} User #{user['id']} ({user['name']}): {idle_secs}s idle")
        else:
            print("   ⚠️  No users with activity data")
        
        # Test 4: Check cart abandonment query logic
        print("\n4️⃣ Testing abandonment detection query...")
        threshold = datetime.now() - timedelta(minutes=1)
        
        cursor.execute("""
            SELECT 
                c.user_id,
                u.name,
                u.last_activity,
                TIMESTAMPDIFF(SECOND, u.last_activity, NOW()) as seconds_idle,
                COUNT(*) as cart_items
            FROM cart c
            JOIN users u ON c.user_id = u.id
            WHERE u.last_activity <= %s
            AND u.last_activity IS NOT NULL
            GROUP BY c.user_id, u.name, u.last_activity
        """, (threshold,))
        
        idle_carts = cursor.fetchall()
        
        if idle_carts:
            print(f"   🚨 Found {len(idle_carts)} IDLE carts (would send emails):")
            for cart in idle_carts:
                print(f"      User: {cart['name']}, Idle: {cart['seconds_idle']}s, Items: {cart['cart_items']}")
        else:
            print("   ✅ No idle carts found (all users are active)")
        
        # Test 5: Check for ACTIVE users with carts (should NOT get emails)
        print("\n5️⃣ Checking ACTIVE users with carts...")
        active_threshold = datetime.now() - timedelta(seconds=30)
        
        cursor.execute("""
            SELECT 
                c.user_id,
                u.name,
                u.last_activity,
                TIMESTAMPDIFF(SECOND, u.last_activity, NOW()) as seconds_idle,
                COUNT(*) as cart_items
            FROM cart c
            JOIN users u ON c.user_id = u.id
            WHERE u.last_activity > %s
            OR u.last_activity IS NULL
            GROUP BY c.user_id, u.name, u.last_activity
        """, (active_threshold,))
        
        active_carts = cursor.fetchall()
        
        if active_carts:
            print(f"   🟢 Found {len(active_carts)} ACTIVE carts (PROTECTED from emails):")
            for cart in active_carts:
                idle = cart['seconds_idle'] or 0
                print(f"      User: {cart['name']}, Idle: {idle}s, Items: {cart['cart_items']} (SAFE)")
        else:
            print("   No active carts")
        
        # Test 6: Check if middleware would update
        print("\n6️⃣ Testing if activity tracking would work...")
        cursor.execute("SELECT id FROM users WHERE id = 1")
        test_user = cursor.fetchone()
        
        if test_user:
            # Get current timestamp
            cursor.execute("SELECT last_activity FROM users WHERE id = 1")
            before = cursor.fetchone()['last_activity']
            
            # Simulate middleware update
            cursor.execute("UPDATE users SET last_activity = NOW() WHERE id = 1")
            conn.commit()
            
            cursor.execute("SELECT last_activity FROM users WHERE id = 1")
            after = cursor.fetchone()['last_activity']
            
            if after != before:
                print(f"   ✅ Activity tracking works!")
                print(f"      Before: {before}")
                print(f"      After:  {after}")
            else:
                print(f"   ⚠️  Timestamp didn't change (might be same second)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    diagnose_idle_detection()
