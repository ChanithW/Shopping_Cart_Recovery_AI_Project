# Bug Fix: Unknown Column 'c.updated_at' Error

## Issue
Admin dashboard at `http://127.0.0.1:8080/admin` was throwing:
```
Error: (1054, "Unknown column 'c.updated_at' in 'where clause'")
```

## Root Cause
The SQL queries in the admin dashboard were using `c.updated_at` column, but the `cart` table schema only has:
- `created_at` (timestamp when item was added to cart)
- No `updated_at` column

## Database Schema (database.sql)
```sql
CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- ✅ Only this exists
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_product (user_id, product_id)
);
```

## Fix Applied
Modified `app.py` admin dashboard queries to use `created_at` instead of `updated_at`:

### Query 1: Total Abandoned Carts Count
**Before:**
```sql
WHERE o.id IS NULL
AND c.updated_at < DATE_SUB(NOW(), INTERVAL 1 MINUTE)  -- ❌ Wrong column
```

**After:**
```sql
WHERE o.id IS NULL
AND c.created_at < DATE_SUB(NOW(), INTERVAL 1 MINUTE)  -- ✅ Correct column
```

### Query 2: Abandoned Cart Details
**Before:**
```sql
MAX(c.updated_at) as last_updated,                     -- ❌ Wrong column
TIMESTAMPDIFF(MINUTE, MAX(c.updated_at), NOW()) as minutes_ago  -- ❌ Wrong column
...
WHERE o.id IS NULL
AND c.updated_at < DATE_SUB(NOW(), INTERVAL 1 MINUTE)  -- ❌ Wrong column
```

**After:**
```sql
MAX(c.created_at) as last_updated,                     -- ✅ Correct column
TIMESTAMPDIFF(MINUTE, MAX(c.created_at), NOW()) as minutes_ago  -- ✅ Correct column
...
WHERE o.id IS NULL
AND c.created_at < DATE_SUB(NOW(), INTERVAL 1 MINUTE)  -- ✅ Correct column
```

## Files Modified
- ✅ `app.py` - Lines 407-439 (admin_dashboard route)
  - Fixed 2 SQL queries (total abandoned carts count + abandoned cart details)

## Impact
- **Behavior Change:** Now tracks time since cart item was **first added** (created_at) instead of **last updated** (which doesn't exist)
- **Logic:** For abandonment detection, using `created_at` makes sense - we want to know how long items have been sitting in the cart
- **Compatibility:** Cart abandonment detector (`cart_abandonment_detector.py`) was already using `created_at` correctly

## Testing
After fix, admin dashboard should:
1. ✅ Load without errors at `http://127.0.0.1:8080/admin`
2. ✅ Display abandoned carts count correctly
3. ✅ Show abandoned cart details table
4. ✅ Calculate "minutes ago" based on `created_at`

## Prevention
If you need to track when cart items are updated (quantity changes), you would need to:
1. Add `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` to cart table
2. Run migration: `ALTER TABLE cart ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;`
3. Update queries to use `updated_at` for last activity tracking

## Auto-Reload
Since Flask is running in debug mode (`debug=True`), the changes should auto-reload automatically. Just refresh the admin page.

**Status:** ✅ FIXED - Admin dashboard should now work correctly!
