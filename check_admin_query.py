import MySQLdb
import MySQLdb.cursors

conn = MySQLdb.connect(host='localhost', user='root', password='', database='ecommerce')
cursor = conn.cursor(MySQLdb.cursors.DictCursor)

# Simulate what the admin dashboard query does
cursor.execute('''
    SELECT 
        cal.id,
        u.email,
        cal.cart_total as cart_value,
        cal.created_at as sent_at,
        15 as discount_offered,
        cal.email_opened as opened,
        cal.link_clicked as clicked,
        cal.purchase_completed as converted,
        cal.click_count,
        cal.opened_at,
        cal.clicked_at,
        cal.completed_at
    FROM cart_abandonment_log cal
    JOIN users u ON cal.user_id = u.id
    WHERE cal.email_sent = TRUE
    ORDER BY cal.created_at DESC
    LIMIT 3
''')

rows = cursor.fetchall()

print("Admin Dashboard Query Results:")
print("=" * 100)
for row in rows:
    print(f"\nID: {row['id']}")
    print(f"Email: {row['email']}")
    print(f"Cart Value: {row['cart_value']}")
    print(f"Opened: {row['opened']} (type: {type(row['opened'])})")
    print(f"Clicked: {row['clicked']} (type: {type(row['clicked'])})")
    print(f"Converted: {row['converted']} (type: {type(row['converted'])})")
    
    # Test Jinja2-like conditions
    print(f"\nJinja2 boolean tests:")
    print(f"  if opened: {bool(row['opened'])}")
    print(f"  if clicked: {bool(row['clicked'])}")
    print(f"  if converted: {bool(row['converted'])}")
    print("-" * 100)

cursor.close()
conn.close()
