#!/usr/bin/env python3
"""
Production server launcher for E-commerce platform
Uses Waitress WSGI server for production deployment
"""
import os
import sys
from waitress import serve
from wsgi import application

def main():
    print("=" * 60)
    print("   E-Commerce Platform - Production Server")
    print("=" * 60)
    print()
    
    # Configuration
    host = '0.0.0.0'
    port = 8080
    threads = 8
    
    print(f"🚀 Starting production server...")
    print(f"🌐 Server: Waitress (Production WSGI Server)")
    print(f"🔒 Debug Mode: DISABLED")
    print(f"⚡ Threads: {threads}")
    print()
    print("=" * 60)
    print("   Your E-Commerce Website is LIVE!")
    print("=" * 60)
    print()
    print(f"🌐 Local URL:    http://localhost:{port}")
    print(f"🌐 Network URL:  http://{host}:{port}")
    print()
    print("🔑 Admin Login:")
    print("📧 Email:    admin@ecommerce.com")
    print("🔐 Password: admin123")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    try:
        # Start the production server
        serve(
            application,
            host=host,
            port=port,
            threads=threads,
            connection_limit=1000,
            cleanup_interval=30,
            channel_timeout=120,
            asyncore_use_poll=True,
            max_request_header_size=262144,
            max_request_body_size=1073741824,
            expose_tracebacks=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()