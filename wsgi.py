#!/usr/bin/env python3
"""
Production WSGI entry point for the E-commerce application
"""
from app import app
import os

# Production configuration
app.config.update(
    DEBUG=False,
    ENV='production',
    SECRET_KEY=os.environ.get('SECRET_KEY', 'production-secret-key-change-this'),
    # Add any production-specific settings here
)

# Ensure all required directories exist
os.makedirs('static/images/products', exist_ok=True)

if __name__ == "__main__":
    # This allows running with python wsgi.py for testing
    app.run(host='0.0.0.0', port=5000, debug=False)
else:
    # This is the WSGI callable for production servers
    application = app