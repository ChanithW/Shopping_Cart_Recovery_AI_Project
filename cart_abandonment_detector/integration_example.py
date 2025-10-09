"""
Flask App Integration Example
Shows how to integrate cart abandonment detector with your Flask app
"""

from flask import Flask
from flask_mail import Mail
import threading
import asyncio

# Import the detector
from cart_abandonment_detector import CartAbandonmentDetector

app = Flask(__name__)

# Configure Flask-Mail (already in your app.py)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_password'

mail = Mail(app)

# Initialize Cart Abandonment Detector
cart_detector = CartAbandonmentDetector(mail_app=mail)


def start_cart_detector():
    """Run detector in background thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(cart_detector.start_monitoring())
    except Exception as e:
        print(f"Cart detector error: {e}")
    finally:
        loop.close()


# Start detector in background thread (daemon so it stops when app stops)
detector_thread = threading.Thread(target=start_cart_detector, daemon=True)
detector_thread.start()

print("✅ Cart Abandonment Detector started in background")


# Optional: Add manual trigger endpoint for testing
@app.route('/admin/trigger-abandonment-check')
def trigger_abandonment_check():
    """Manual trigger for testing (admin only)"""
    import asyncio
    
    async def check():
        await cart_detector.check_abandoned_carts()
    
    # Run check
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check())
    loop.close()
    
    return {"status": "success", "message": "Abandonment check triggered"}


if __name__ == '__main__':
    app.run(debug=True, port=8080)
