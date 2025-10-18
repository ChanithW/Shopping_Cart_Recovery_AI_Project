"""
Cart Abandonment Detector Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Abandonment Detection Settings
ABANDONMENT_THRESHOLD_MINUTES = 1  # 1 minute inactivity
CHECK_INTERVAL_SECONDS = 30  # Check every 30 seconds

# Discount Settings :
DISCOUNT_TIER_1_AMOUNT = 100  # $100+ gets 10% discount
DISCOUNT_TIER_1_PERCENT = 10

DISCOUNT_TIER_2_AMOUNT = 500  # $500+ get 20% discounts
DISCOUNT_TIER_2_PERCENT = 20

# Free shippings for all abandoned carts
FREE_SHIPPING_ENABLED = True 


# Email Settings
SENDER_EMAIL = os.getenv('MAIL_USERNAME', 'noreply@ecommerce.com')
SENDER_NAME = 'ECommerceStore'
EMAIL_TEMPLATE_PATH = 'templates/emails/cart_abandonment.html'

# Groq AI Settings (Fast & Free)
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = 'llama-3.3-70b-versatile'  # Latest model (as of Oct 2025)
GROQ_BASE_URL = 'https://api.groq.com/openai/v1'
GROQ_TEMPERATURE = 0.7
GROQ_MAX_TOKENS = 200

# Recommendation Settings
RECOMMENDATION_COUNT = 3
SIMILARITY_THRESHOLD = 0.01  # Very low threshold to ensure recommendations (was 0.1)

# Database Settings
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DB = os.getenv('MYSQL_DB', 'ecommerce')

# Logging Settings
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/cart_abandonment.log'  # Relative to main ecom directory

# URLs
BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:8080')
CART_URL = f'{BASE_URL}/cart'
CHECKOUT_URL = f'{BASE_URL}/checkout'
