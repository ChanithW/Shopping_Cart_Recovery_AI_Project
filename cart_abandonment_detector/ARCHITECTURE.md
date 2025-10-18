# Cart Abandonment Detection System - Technical Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask E-Commerce App                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Cart Abandonment Detector                   │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  CartAbandonmentDetector (Main Controller)      │  │  │
│  │  │  - Monitors cart table every 30 seconds         │  │  │
│  │  │  - Identifies inactive carts (1+ min)           │  │  │
│  │  │  - Triggers recovery workflow                   │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                          │                             │  │
│  │           ┌──────────────┼──────────────┐              │  │
│  │           ▼              ▼              ▼              │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐   │  │
│  │  │ Email       │ │ Recommend.   │ │ Database     │   │  │
│  │  │ Service     │ │ Engine       │ │ Connection   │   │  │
│  │  └─────────────┘ └──────────────┘ └──────────────┘   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │  MySQL   │     │  Gemini  │     │   SMTP   │
  │ Database │     │   API    │     │  Server  │
  └──────────┘     └──────────┘     └──────────┘
```

## Component Details

### 1. CartAbandonmentDetector (Main Controller)

**File:** `cart_abandonment_detector.py`

**Responsibilities:**
- Continuous monitoring loop (async)
- Cart abandonment detection logic
- Workflow orchestration
- Logging and tracking

**Key Methods:**
```python
check_abandoned_carts()      # Main detection logic
start_monitoring()            # Continuous loop
stop_monitoring()             # Graceful shutdown
_log_abandonment_event()      # Database tracking
```

**Detection Algorithm:**
```python
1. Query carts WHERE created_at <= (NOW() - 1 minute)
2. Exclude users who have orders after cart creation
3. Group by user_id
4. For each abandoned cart:
   - Skip if already processed (in-memory set)
   - Fetch cart items and calculate total
   - Generate email content
   - Send email
   - Mark as processed
   - Log to database
```

### 2. RecommendationEngine (AI-Powered Recommendations)

**File:** `cart_abandonment_detector.py`

**Responsibilities:**
- Product similarity calculation
- AI content generation
- Product catalog management

**Technologies:**
- **TF-IDF Vectorization:** Converts product descriptions to numerical vectors
- **Cosine Similarity:** Measures similarity between cart items and products
- **Gemini AI:** Generates personalized recommendation text

**Algorithm:**
```python
1. Load all products from database (cached in memory)
2. Build TF-IDF matrix from:
   - Product names
   - Product descriptions
   - Product categories
3. For recommendations:
   - Build query vector from cart items
   - Calculate cosine similarity with all products
   - Sort by similarity (highest first)
   - Exclude cart items
   - Return top 3 products
4. Enhance with Gemini AI:
   - Send product list to Gemini
   - Get personalized recommendation text
   - Fallback to template text if API fails
```

**TF-IDF Example:**
```python
Products:
- "Laptop Dell XPS high-performance ultrabook"
- "iPhone 14 Pro smartphone camera"
- "Wireless Mouse ergonomic"

Cart: ["Laptop Dell XPS"]

TF-IDF Matrix:
         laptop  dell  xps  high  iphone  wireless  mouse
Laptop     0.5   0.5  0.5   0.5    0.0      0.0     0.0
iPhone     0.0   0.0  0.0   0.0    0.7      0.0     0.0  
Mouse      0.0   0.0  0.0   0.0    0.0      0.6     0.6

Cosine Similarity:
Laptop ↔ iPhone: 0.0
Laptop ↔ Mouse:  0.0

(Mouse and iPhone not similar to laptop in this simple example)
```

### 3. EmailService (Email Generation & Sending)

**File:** `cart_abandonment_detector.py`

**Responsibilities:**
- Discount calculation
- HTML email generation
- Plain text email generation
- Email sending (async)

**Discount Tiers:**
```python
Cart Total       Discount    Free Shipping
-----------      --------    -------------
< $100              0%            ✓
$100 - $499        10%            ✓
$500+              20%            ✓
```

**Email Components:**
1. **Header:** Brand logo and greeting
2. **Discount Badge:** Prominent if applicable
3. **Free Shipping Badge:** Always shown
4. **Cart Summary:** Table with items, quantities, prices
5. **CTA Button:** "Return to Cart" (big, green)
6. **AI Recommendation Text:** Personalized by Gemini
7. **Product Cards:** 3 recommendations with images
8. **Footer:** Contact info and unsubscribe

**Async Email Sending:**
```python
async def send_email():
    # Use Flask-Mail if available
    if self.mail_app:
        await asyncio.to_thread(self.mail_app.send, msg)
    else:
        # Fallback to SMTP
        server = smtplib.SMTP(...)
        await asyncio.to_thread(server.send_message, msg)
```

### 4. DatabaseConnection (MySQL Handler)

**File:** `cart_abandonment_detector.py`

**Responsibilities:**
- Connection pooling
- Query execution
- Error handling

**Tables Used:**
```sql
cart (existing):
- id, user_id, product_id, quantity, created_at

users (existing):
- id, name, email, role

products (existing):
- id, name, description, price, category, image, stock

orders (existing):
- id, user_id, total_amount, created_at

cart_abandonment_log (auto-created):
- id, user_id, cart_total, email_sent, created_at
```

## Data Flow

### Complete Workflow

```
1. User adds items to cart → created_at timestamp recorded
2. User leaves site (no checkout for 1+ minute)
3. Detector checks database every 30 seconds
4. Abandoned cart detected:
   ├─ User: John Doe (john@example.com)
   ├─ Cart: Laptop ($999), Mouse ($29)
   └─ Total: $1,028
5. Discount calculation:
   └─ $1,028 > $500 → 20% discount
6. Recommendation engine:
   ├─ Build query: "Laptop ultrabook Mouse ergonomic"
   ├─ Calculate similarity with all products
   ├─ Top 3: Keyboard ($89), Monitor ($299), Webcam ($79)
   └─ Gemini AI enhancement:
       "Based on your high-performance laptop selection, 
        these accessories will complete your setup..."
7. Email generation:
   ├─ Subject: "🛒 John, you left something in your cart! + 20% OFF!"
   ├─ HTML content with all components
   └─ Plain text fallback
8. Email sent asynchronously
9. Log to database:
   └─ cart_abandonment_log table
10. Mark as processed (won't send duplicate)
```

## Performance Characteristics

### Scalability

**Current Configuration:**
- Check interval: 30 seconds
- Abandonment threshold: 1 minute
- Max carts per check: Unlimited
- Async operations: Email sending, AI calls

**Performance Metrics:**
```
Database Query:     ~50ms   (depends on cart table size)
TF-IDF Calculation: ~100ms  (one-time per restart, then cached)
Similarity Calc:    ~20ms   (per cart, with 100 products)
Gemini API Call:    ~500ms  (per email, async)
Email Sending:      ~200ms  (per email, async)
Total per cart:     ~870ms  (mostly parallel)
```

**Throughput:**
- Sequential: ~70 carts/minute
- With async (10 concurrent): ~600 carts/minute

### Memory Usage

```
Product Cache:      ~1MB per 1000 products
TF-IDF Matrix:      ~2MB per 1000 products
In-memory tracking: ~100 bytes per processed cart
Total baseline:     ~50MB
```

### Optimization Strategies

1. **Product Caching:**
   - Loads once at startup
   - Rebuilds on detector restart
   - Could add auto-refresh every N hours

2. **Async Operations:**
   - Email sending doesn't block detection loop
   - Gemini API calls are async
   - Multiple emails can be sent in parallel

3. **Database Efficiency:**
   - Single query fetches all abandoned carts
   - Uses indexes on created_at and user_id
   - Batch operations where possible

4. **Rate Limiting:**
   - Check interval prevents database overload
   - In-memory tracking prevents duplicate sends
   - Could add max emails per check cycle

## Configuration Options

### config.py Settings

```python
# Timing
ABANDONMENT_THRESHOLD_MINUTES = 1    # Prod: 15-30 recommended
CHECK_INTERVAL_SECONDS = 30          # Prod: 60-300 recommended

# Discounts
DISCOUNT_TIER_1_AMOUNT = 100
DISCOUNT_TIER_1_PERCENT = 10
DISCOUNT_TIER_2_AMOUNT = 500
DISCOUNT_TIER_2_PERCENT = 20

# Recommendations
RECOMMENDATION_COUNT = 3
SIMILARITY_THRESHOLD = 0.1

# AI
GEMINI_API_KEY = ""
GEMINI_MODEL = "gemini-pro"
GEMINI_TEMPERATURE = 0.7
GEMINI_MAX_TOKENS = 500

# Email
SENDER_EMAIL = ""
SENDER_NAME = "ECommerceStore"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/cart_abandonment.log"
```

## Error Handling

### Graceful Degradation

```python
1. Gemini API fails:
   └─ Falls back to template text
   └─ Email still sent (without AI enhancement)

2. Email sending fails:
   └─ Logged to cart_abandonment_log with email_sent=False
   └─ Can be retried manually
   └─ Doesn't block next cart processing

3. Database connection fails:
   └─ Logs error
   └─ Retries on next check interval
   └─ Detector continues running

4. Recommendation engine fails:
   └─ Email sent without recommendations
   └─ Logs warning
   └─ Continues with next cart
```

### Logging Strategy

```python
INFO:  Cart detection, email sent, recommendations generated
WARN:  Gemini API fallback, missing recommendations
ERROR: Database errors, email failures, critical issues
DEBUG: SQL queries, similarity scores, detailed workflow
```

## Security Considerations

### Data Protection

1. **Email Privacy:**
   - Only sends to verified user emails from database
   - No email addresses exposed in logs (masked)
   - Uses secure SMTP (TLS)

2. **API Keys:**
   - Stored in .env (not in code)
   - Not logged
   - Not exposed in error messages

3. **SQL Injection:**
   - Uses parameterized queries (MySQLdb)
   - No user input in SQL
   - All values sanitized

### Rate Limiting

```python
# Built-in protections:
- In-memory tracking prevents duplicate sends
- Check interval prevents database hammering
- Gemini API has built-in rate limits (60 req/min)
- Email service has connection pooling
```

## Testing

### Test Suite (test_detector.py)

```python
test_database_connection()
├─ Connects to MySQL
├─ Counts products
├─ Counts users
└─ Counts cart items

test_recommendation_engine()
├─ Loads products
├─ Generates recommendations
├─ Tests TF-IDF calculation
├─ Tests Gemini API
└─ Verifies similarity scores

test_email_generation()
├─ Calculates discounts
├─ Generates HTML email
├─ Generates text email
├─ Saves sample to file
└─ Verifies all components
```

### Manual Testing

```python
# Test single cart check
from cart_abandonment_detector import CartAbandonmentDetector
import asyncio

detector = CartAbandonmentDetector()
asyncio.run(detector.check_abandoned_carts())

# Test recommendation engine
from cart_abandonment_detector import RecommendationEngine

engine = RecommendationEngine()
engine.load_products()
recommendations = engine.get_similar_products([
    {'product_id': 1, 'name': 'Laptop', 'category': 'Electronics'}
])
print(recommendations)
```

## Deployment

### Production Checklist

- [ ] Update abandonment threshold to 15-30 minutes
- [ ] Set check interval to 60-300 seconds  
- [ ] Configure GEMINI_API_KEY in .env
- [ ] Set up proper email service (not development SMTP)
- [ ] Enable log rotation
- [ ] Set up monitoring/alerts
- [ ] Test with small user segment first
- [ ] Monitor conversion rates
- [ ] Adjust discount tiers based on data

### Monitoring Metrics

```sql
-- Abandonment rate
SELECT 
    DATE(created_at) as date,
    COUNT(*) as abandoned_carts,
    SUM(cart_total) as lost_revenue
FROM cart_abandonment_log
GROUP BY DATE(created_at);

-- Recovery rate
SELECT 
    COUNT(*) as emails_sent,
    COUNT(CASE WHEN email_sent THEN 1 END) as successful,
    -- Join with orders to see conversions
FROM cart_abandonment_log;

-- Average cart value by tier
SELECT 
    CASE 
        WHEN cart_total >= 500 THEN '20% tier'
        WHEN cart_total >= 100 THEN '10% tier'
        ELSE 'No discount'
    END as tier,
    AVG(cart_total) as avg_cart,
    COUNT(*) as count
FROM cart_abandonment_log
GROUP BY tier;
``'



