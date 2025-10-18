# Admin Dashboard - Abandoned Carts Feature

## Overview

The admin dashboard now displays real-time abandoned cart information and email campaign tracking.

## Features Added

### 1. Abandoned Carts Statistics Card

- **Location:** Top of dashboard
- **Shows:** Total number of active abandoned carts
- **Color:** Red (high priority indicator)
- **Updates:** Automatically with each page refresh

### 2. Sidebar Navigation

- **New Link:** "Abandoned Carts" with badge showing count
- **Badge Color:** Red (danger) - only shows when carts exist
- **Quick Access:** Jumps directly to abandoned carts section

### 3. Active Abandoned Carts Table

Displays detailed information about current abandoned carts:

| Column            | Description                         |
| ----------------- | ----------------------------------- |
| **Customer**      | First and last name of the customer |
| **Email**         | Clickable mailto: link              |
| **Items**         | Number of items in cart (badge)     |
| **Cart Value**    | Total value of abandoned cart       |
| **Last Activity** | Minutes since last cart update      |
| **Status**        | Priority level based on time        |

**Status Badges :**

- 🔴 **High Priority** - Abandoned > 60 minutes ago
- ⚠️ **Medium** - Abandoned 30-60 minutes ago
- 🔵 **Recent** - Abandoned < 30 minutes ago

### 4. Recent Abandonment Emails Table

Tracks all sent abandonment recovery emails:

| Column         | Description                   |
| -------------- | ----------------------------- |
| **Email**      | Recipient email address       |
| **Cart Value** | Value of cart when email sent |
| **Discount**   | Percentage discount offered   |
| **Sent At**    | Timestamp of email send       |
| **Status**     | Email engagement level        |
| **Actions**    | View email details (future)   |

**Email Status Badges:**

- ✅ **Converted** (Green) - Customer completed purchase
- 👆 **Clicked** (Blue) - Customer clicked email link
- 📧 **Opened** (Yellow) - Customer opened email
- ✈️ **Sent** (Gray) - Email sent, no engagement yet

## Database Queries

### Abandoned Carts Detection

```sql
SELECT
    c.user_id,
    u.first_name,
    u.last_name,
    u.email,
    COUNT(c.id) as items_count,
    SUM(p.price * c.quantity) as cart_value,
    MAX(c.updated_at) as last_updated,
    TIMESTAMPDIFF(MINUTE, MAX(c.updated_at), NOW()) as minutes_ago
FROM cart c
JOIN users u ON c.user_id = u.id
JOIN products p ON c.product_id = p.id
LEFT JOIN orders o ON c.user_id = o.user_id
    AND o.created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
WHERE o.id IS NULL
AND c.updated_at < DATE_SUB(NOW(), INTERVAL 1 MINUTE)
GROUP BY c.user_id, u.first_name, u.last_name, u.email
ORDER BY cart_value DESC
LIMIT 10
```

### Email Campaign Tracking

```sql
SELECT
    cal.id,
    cal.user_id,
    u.email,
    cal.cart_value,
    cal.discount_offered,
    cal.sent_at,
    cal.opened,
    cal.clicked,
    cal.converted
FROM cart_abandonment_log cal
JOIN users u ON cal.user_id = u.id
ORDER BY cal.sent_at DESC
LIMIT 10
```

## Accessing the Feature

1. **Login to Admin:** `http://127.0.0.1:8080/admin`
2. **View Dashboard:** The abandoned carts section appears automatically
3. **Navigate:** Click "Abandoned Carts" in sidebar or scroll to section

## Real-Time Updates

- **Detection:** Background process checks every 30 seconds
- **Threshold:** Carts abandoned for > 1 minute are flagged
- **Auto-Email:** System sends recovery emails automatically
- **Dashboard:** Refresh page to see latest data

## Integration with Cart Abandonment Detector

The dashboard pulls data from the cart abandonment detection system running in the background:

- **Detector:** `cart_abandonment_detector/cart_abandonment_detector.py`
- **Config:** Threshold set to 1 minute (configurable in `config.py`)
- **Logging:** All activity logged to `logs/cart_abandonment.log`
- **Email Service:** Uses Gmail SMTP with Flask-Mail

## Metrics to Monitor

1. **Total Abandoned Carts** - Overall count
2. **Cart Value** - Potential revenue at risk
3. **Time Since Last Activity** - Urgency indicator
4. **Email Performance:**
   - Send rate
   - Open rate
   - Click rate
   - Conversion rate

## Future Enhancements (Planned)

- [ ] Filter abandoned carts by date range
- [ ] Export abandoned carts to CSV
- [ ] Manual email trigger button
- [ ] Email preview/edit before sending
- [ ] Conversion funnel visualization
- [ ] Revenue recovery chart
- [ ] Customer segmentation

## Technical Notes

- **Auto-Refresh:** Dashboard requires manual page refresh
- **Limit:** Shows top 10 abandoned carts (highest value first)
- **Performance:** Queries optimized with proper indexes
- **Caching:** Consider adding Redis for high-traffic sites

## Troubleshooting

**No abandoned carts showing:**

- Check if users have items in cart
- Verify cart hasn't been updated in last minute
- Ensure no orders placed in last 24 hours
- Check database connection

**Emails not tracked:**

- Verify `cart_abandonment_log` table exists
- Check email sending is successful
- Review logs: `logs/cart_abandonment.log`

## Support

For issues or questions, check:

- Main documentation: `cart_abandonment_detector/README.md`
- System logs: `cart_abandonment_detector/logs/`
- Test suite: `cart_abandonment_detector/test_detector.py`
