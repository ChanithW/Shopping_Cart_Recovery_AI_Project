"""
Create different tracking statuses for testing the admin dashboard
"""
import MySQLdb
import MySQLdb.cursors

conn = MySQLdb.connect(host='localhost', user='root', password='', database='ecommerce')
cursor = conn.cursor(MySQLdb.cursors.DictCursor)

# Get the last 4 abandonment emails
cursor.execute('''
    SELECT id 
    FROM cart_abandonment_log 
    WHERE email_sent = TRUE 
    ORDER BY created_at DESC 
    LIMIT 4
''')

emails = cursor.fetchall()

if len(emails) < 4:
    print(f"Found only {len(emails)} emails. Need at least 4 for demo.")
    print("Creating variety with available emails...")

statuses = [
    ("Converted", True, True, True),
    ("Clicked only", False, True, False),
    ("Opened only", True, False, False),
    ("Sent only", False, False, False),
]

for i, email in enumerate(emails[:4]):
    log_id = email['id']
    status_name, opened, clicked, converted = statuses[i] if i < len(statuses) else statuses[-1]
    
    print(f"\nSetting email ID {log_id} to status: {status_name}")
    
    cursor.execute("""
        UPDATE cart_abandonment_log 
        SET email_opened = %s,
            link_clicked = %s,
            purchase_completed = %s,
            opened_at = IF(%s = TRUE, NOW(), NULL),
            clicked_at = IF(%s = TRUE, NOW(), NULL),
            completed_at = IF(%s = TRUE, NOW(), NULL),
            click_count = IF(%s = TRUE, 1, 0)
        WHERE id = %s
    """, (opened, clicked, converted, opened, clicked, converted, clicked, log_id))
    
    conn.commit()
    print(f"  ✓ Email {log_id}: opened={opened}, clicked={clicked}, converted={converted}")

print("\n✅ Demo data created!")
print("\nAdmin Dashboard should now show:")
print("  🟢 Converted (green badge)")
print("  🔵 Clicked (blue badge)")
print("  🟡 Opened (yellow badge)")
print("  ⚫ Sent (gray badge)")

cursor.close()
conn.close()
