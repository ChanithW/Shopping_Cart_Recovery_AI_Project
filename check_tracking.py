import MySQLdb
import MySQLdb.cursors

conn = MySQLdb.connect(host='localhost', user='root', password='', database='ecommerce')
cursor = conn.cursor(MySQLdb.cursors.DictCursor)

# Check recent cart abandonment log entries
cursor.execute('''
    SELECT id, user_id, email_opened, link_clicked, purchase_completed,  
           opened_at, clicked_at, completed_at, created_at
    FROM cart_abandonment_log 
    ORDER BY created_at DESC 
    LIMIT 5
''')

rows = cursor.fetchall()

print("Recent Cart Abandonment Log Entries:")
print("=" * 100)
for row in rows:
    print(f"\nID: {row['id']}")
    print(f"User ID: {row['user_id']}")
    print(f"Email Opened: {row['email_opened']}")
    print(f"Link Clicked: {row['link_clicked']}")
    print(f"Purchase Completed: {row['purchase_completed']}")
    print(f"Opened At: {row['opened_at']}")
    print(f"Clicked At: {row['clicked_at']}")
    print(f"Completed At: {row['completed_at']}")
    print(f"Created At: {row['created_at']}")
    print("-" * 100)

cursor.close()
conn.close()
