# Cart Abandonment Detection System

## Overview
Automated cart abandonment detection and recovery system with AI-powered product recommendations.

## Features
- ✅ Automatic detection of abandoned carts (1-minute threshold)
- ✅ Tiered discount system ($100+ = 10% off, $500+ = 20% off)
- ✅ Free shipping for all abandoned carts
- ✅ AI-powered personalized emails using Gemini API
- ✅ TF-IDF + Cosine Similarity product recommendations
- ✅ Async email sending for performance
- ✅ Comprehensive logging and tracking

## Installation

### 1. Install Dependencies
```bash
pip install google-generativeai scikit-learn numpy flask-mail mysqlclient python-dotenv
```

### 2. Configure Environment Variables
Add to your `.env` file:
```env
# Gemini API Key (get from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# Email settings (already configured)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

# Base URL for links in emails
BASE_URL=http://127.0.0.1:8080
```

## Usage

### Option 1: Standalone Mode
Run the detector as a separate process:
```bash
cd cart_abandonment_detector
python run_detector.py
```

### Option 2: Integrated with Flask App
Add to your `app.py`:
```python
from cart_abandonment_detector import CartAbandonmentDetector
import threading

# Initialize detector
detector = CartAbandonmentDetector(mail_app=mail)

# Start in background thread
def start_detector():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(detector.start_monitoring())

detector_thread = threading.Thread(target=start_detector, daemon=True)
detector_thread.start()
```

## Configuration

Edit `config.py` to customize:
- `ABANDONMENT_THRESHOLD_MINUTES`: Time before cart is considered abandoned (default: 1)
- `CHECK_INTERVAL_SECONDS`: How often to check for abandoned carts (default: 30)
- `DISCOUNT_TIER_1_AMOUNT`: Minimum for 10% discount (default: $100)
- `DISCOUNT_TIER_2_AMOUNT`: Minimum for 20% discount (default: $500)
- `RECOMMENDATION_COUNT`: Number of products to recommend (default: 3)

## How It Works

1. **Detection**: System checks database every 30 seconds for carts inactive for 1+ minute
2. **Analysis**: Calculates cart total and determines discount tier
3. **Recommendations**: 
   - Uses TF-IDF vectorization on product descriptions
   - Calculates cosine similarity between cart items and all products
   - Selects top 3 most similar products
4. **AI Enhancement**: Gemini API generates personalized recommendation text
5. **Email Generation**: Creates beautiful HTML email with:
   - Personalized greeting
   - Cart summary
   - Discount offer (if applicable)
   - Free shipping notification
   - AI-generated recommendation text
   - Product recommendation cards with images and links
   - "Return to Cart" button
6. **Sending**: Email sent asynchronously via Flask-Mail or SMTP

## Email Example

Subject: 🛒 John, you left something in your cart! + 20% OFF!

Body:
- Personalized greeting
- Cart summary table
- "Special Offer: 20% OFF your entire order!" (for $500+ carts)
- "FREE SHIPPING on your order!"
- AI-generated text: "Based on your interest in laptops and accessories, we think you'll love these complementary items..."
- 3 product recommendation cards with images, descriptions, prices
- Big "Return to Cart & Complete Purchase" button

## Logging

Logs are written to `logs/cart_abandonment.log` and include:
- Cart detection events
- Email generation and sending
- Recommendation engine activity
- Errors and warnings

## Database Table

The system creates a `cart_abandonment_log` table to track:
- User ID
- Cart total
- Email sent status
- Timestamp

## API Requirements

### Gemini API
- Free tier: 60 requests/minute
- Get API key: https://makersuite.google.com/app/apikey
- Used for: Generating personalized recommendation text

### Email Service
- Uses existing Flask-Mail configuration
- Fallback to SMTP if Flask-Mail not available
- Supports Gmail, SendGrid, AWS SES, etc.

## Performance

- **Async Operations**: Email sending and AI API calls run asynchronously
- **Caching**: Product catalog cached in memory for fast similarity calculations
- **Efficient Queries**: Single query fetches all abandoned carts
- **Background Processing**: Runs in separate thread/process

## Troubleshooting

### No emails sending?
- Check MAIL_USERNAME and MAIL_PASSWORD in .env
- Enable "Less secure app access" or use App Password for Gmail
- Check logs/cart_abandonment.log for errors

### Recommendations not working?
- Ensure products exist in database with descriptions
- Check similarity threshold in config.py
- Verify product catalog loaded (check logs)

### Gemini API errors?
- Verify GEMINI_API_KEY is set correctly
- Check API quota at Google AI Studio
- System falls back to basic text if Gemini unavailable

## Testing

Test the system manually:
```python
# In Python shell
from cart_abandonment_detector import CartAbandonmentDetector
import asyncio

detector = CartAbandonmentDetector()
asyncio.run(detector.check_abandoned_carts())
```

## License
Part of ECommerceStore platform
