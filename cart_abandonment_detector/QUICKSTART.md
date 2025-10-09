# Cart Abandonment Detector - Quick Setup Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Install Dependencies
```bash
pip install google-generativeai scikit-learn numpy flask-mail
```

### Step 2: Get Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy your key

### Step 3: Configure .env
Add to your `.env` file:
```env
GEMINI_API_KEY=your_api_key_here
BASE_URL=http://127.0.0.1:8080
```

### Step 4: Test the System
```bash
cd cart_abandonment_detector
python test_detector.py
```

### Step 5: Run Standalone (Optional)
```bash
python run_detector.py
```

Or integrate with your Flask app (see `integration_example.py`)

## 📧 Email Template Preview

The system generates beautiful HTML emails with:
- ✅ Personalized greeting
- ✅ Cart summary table
- ✅ Discount badges (10% or 20% based on cart value)
- ✅ Free shipping notification
- ✅ AI-generated recommendation text
- ✅ 3 product recommendation cards with images
- ✅ Big "Return to Cart" button

## 🎯 How It Works

1. **Every 30 seconds**: Check database for carts inactive for 1+ minute
2. **Calculate discount**: 
   - Cart > $100 → 10% OFF
   - Cart > $500 → 20% OFF
   - All carts → FREE SHIPPING
3. **Generate recommendations**:
   - Use TF-IDF on product descriptions
   - Calculate cosine similarity
   - Return top 3 similar products
4. **AI enhancement**: Gemini creates personalized text
5. **Send email**: Beautiful HTML email with all details

## 🧪 Testing Without Running Full Detector

```bash
# Test individual components
python test_detector.py

# This will:
# - Test database connection
# - Test recommendation engine
# - Test email generation
# - Save sample email to HTML file
```

## 📊 Database Table Created

The system auto-creates this table:
```sql
CREATE TABLE cart_abandonment_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    cart_total DECIMAL(10, 2) NOT NULL,
    email_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ⚙️ Configuration Options

Edit `config.py` to change:
- Abandonment threshold (default: 1 minute)
- Check interval (default: 30 seconds)
- Discount tiers ($100, $500)
- Number of recommendations (default: 3)

## 🔧 Integration with Your App

### Option 1: Background Thread (Recommended)
```python
# In your app.py
from cart_abandonment_detector import CartAbandonmentDetector
import threading
import asyncio

detector = CartAbandonmentDetector(mail_app=mail)

def start_detector():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(detector.start_monitoring())

threading.Thread(target=start_detector, daemon=True).start()
```

### Option 2: Separate Process
```bash
# Run in separate terminal/screen/tmux
python cart_abandonment_detector/run_detector.py
```

### Option 3: Manual Trigger (for testing)
```python
@app.route('/admin/check-abandonment')
async def check_abandonment():
    await detector.check_abandoned_carts()
    return {"status": "checked"}
```

## 📝 Example Email Output

**Subject:** 🛒 John, you left something in your cart! + 20% OFF!

**Body:**
```
Hi John! 👋

We noticed you left some awesome items in your cart...

🎉 Special Offer: 20% OFF your entire order!
Your new total: $799.99 (save $200!)

🚚 FREE SHIPPING on your order!

[Cart Summary Table]
- Laptop Dell XPS 13 x1 - $999.99
- Total: $999.99

[Big Return to Cart Button]

You Might Also Love...
"Based on your interest in high-performance laptops, we think 
you'll love these complementary accessories that enhance your 
computing experience..."

[3 Product Cards with Images and Links]
```

## 🐛 Troubleshooting

### No emails sending?
- Check `MAIL_USERNAME` and `MAIL_PASSWORD` in .env
- For Gmail: Enable "App Passwords" in Google Account settings
- Check `logs/cart_abandonment.log` for errors

### Recommendations not working?
- Ensure products have descriptions in database
- Check logs for TF-IDF errors
- Lower `SIMILARITY_THRESHOLD` in config

### Gemini API errors?
- Verify API key is correct
- Check quota at https://makersuite.google.com
- System works without Gemini (uses fallback text)

## 📈 Performance

- ✅ Async email sending (doesn't block)
- ✅ Product catalog cached in memory
- ✅ Efficient SQL queries
- ✅ Runs in background thread
- ✅ Handles hundreds of carts per minute

## 🔒 Security

- ✅ Only sends to verified user emails
- ✅ Tracks sent emails (no duplicates)
- ✅ Secure SMTP connection
- ✅ API keys in .env (not in code)

## 📚 Further Reading

- `README.md` - Full documentation
- `integration_example.py` - Flask integration examples
- `test_detector.py` - Test suite
- `config.py` - All configuration options

## 💡 Pro Tips

1. **Test first**: Run `test_detector.py` before going live
2. **Monitor logs**: Check `logs/cart_abandonment.log` regularly
3. **Adjust timing**: 1 minute is aggressive, consider 15-30 minutes for production
4. **A/B test**: Try different discount tiers
5. **Track conversions**: Monitor how many users return after email

## 🆘 Support

Questions? Check the logs first:
```bash
tail -f logs/cart_abandonment.log
```

## 🎉 You're Ready!

Run the test suite and start detecting abandoned carts:
```bash
python test_detector.py
python run_detector.py
```
