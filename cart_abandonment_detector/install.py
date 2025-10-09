"""
Installation script for cart abandonment detector
Installs dependencies and sets up the system
"""

import subprocess
import sys
import os

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"   {text}")
    print("="*60)

def run_command(cmd, description):
    """Run a command and report status"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        if e.stderr:
            print(f"  Error: {e.stderr}")
        return False

def check_env_file():
    """Check if .env file exists and has required settings"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    if not os.path.exists(env_path):
        print("\n⚠ .env file not found!")
        return False
    
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    required_vars = ['GEMINI_API_KEY', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'BASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if var not in env_content or f"{var}=" in env_content and env_content.split(f"{var}=")[1].split('\n')[0].strip() == '':
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠ Missing or empty environment variables: {', '.join(missing_vars)}")
        print("\nPlease add these to your .env file:")
        for var in missing_vars:
            if var == 'GEMINI_API_KEY':
                print(f"  {var}=your_api_key_from_https://makersuite.google.com")
            else:
                print(f"  {var}=your_value")
        return False
    
    print("\n✓ .env file configured correctly")
    return True

def main():
    """Main installation function"""
    print_header("Cart Abandonment Detector - Installation")
    
    print("\nThis script will install all required dependencies.")
    print("Make sure you're in your virtual environment!\n")
    
    response = input("Continue with installation? (y/n): ")
    if response.lower() != 'y':
        print("\nInstallation cancelled.")
        sys.exit(0)
    
    # Step 1: Install Python dependencies
    print_header("Step 1: Installing Python Dependencies")
    
    packages = [
        'google-generativeai',
        'scikit-learn',
        'numpy',
        'flask-mail'
    ]
    
    for package in packages:
        run_command(f'pip install {package}', f'Installing {package}')
    
    # Step 2: Check environment configuration
    print_header("Step 2: Checking Environment Configuration")
    env_ok = check_env_file()
    
    # Step 3: Test imports
    print_header("Step 3: Testing Imports")
    
    try:
        import google.generativeai
        print("✓ google-generativeai imported successfully")
    except ImportError:
        print("✗ Failed to import google-generativeai")
    
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        print("✓ scikit-learn imported successfully")
    except ImportError:
        print("✗ Failed to import scikit-learn")
    
    try:
        import numpy
        print("✓ numpy imported successfully")
    except ImportError:
        print("✗ Failed to import numpy")
    
    try:
        from flask_mail import Mail
        print("✓ flask-mail imported successfully")
    except ImportError:
        print("✗ Failed to import flask-mail")
    
    # Step 4: Create logs directory
    print_header("Step 4: Creating Directories")
    
    logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"✓ Created logs directory: {logs_dir}")
    else:
        print(f"✓ Logs directory already exists: {logs_dir}")
    
    # Final summary
    print_header("Installation Summary")
    
    if env_ok:
        print("\n✅ Installation completed successfully!")
        print("\nNext steps:")
        print("1. Make sure your .env file has GEMINI_API_KEY set")
        print("2. Run tests: python test_detector.py")
        print("3. Start detector: python run_detector.py")
        print("\nSee QUICKSTART.md for detailed usage instructions.")
    else:
        print("\n⚠ Installation completed with warnings!")
        print("\nPlease complete these steps:")
        print("1. Add missing variables to .env file")
        print("2. Get Gemini API key from: https://makersuite.google.com/app/apikey")
        print("3. Run this installer again to verify")
        
        print("\nQuick .env template:")
        print("""
GEMINI_API_KEY=your_gemini_api_key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
BASE_URL=http://127.0.0.1:8080
        """)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nInstallation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
