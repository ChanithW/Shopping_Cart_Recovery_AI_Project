"""
Standalone runner script for cart abandonment detector
Can be run separately from the main Flask app
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cart_abandonment_detector import start_abandonment_monitor

if __name__ == '__main__':
    print("=" * 60)
    print("   Cart Abandonment Detection System")
    print("=" * 60)
    print("\nStarting abandonment monitor...")
    print("Press Ctrl+C to stop\n")
    
    try:
        detector = start_abandonment_monitor()
    except KeyboardInterrupt:
        print("\n\nMonitor stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
