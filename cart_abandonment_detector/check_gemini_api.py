"""
Quick script to test if your Gemini API key is valid
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='../.env')

# Import config to get latest model
sys.path.insert(0, os.path.dirname(__file__))
import config

def check_gemini_api():
    """Test Gemini API key validity"""
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    
    print("=" * 60)
    print("🔍 GEMINI API KEY VALIDATION")
    print("=" * 60)
    
    # Check if key exists
    if not api_key:
        print("\n❌ NO API KEY FOUND")
        print("\nThe GEMINI_API_KEY is not set in your .env file.")
        print("\n📝 To get an API key:")
        print("   1. Visit: https://makersuite.google.com/app/apikey")
        print("   2. Click 'Create API Key'")
        print("   3. Copy the key")
        print("   4. Add to .env file:")
        print("      GEMINI_API_KEY=your_actual_api_key_here")
        print("\n💡 NOTE: The system works fine WITHOUT Gemini API!")
        print("   - Uses fallback template text")
        print("   - All other features work normally")
        print("   - Emails still get sent with discounts & recommendations")
        return False
    
    # Check if key is empty or placeholder
    if api_key.strip() == '' or api_key == 'your_actual_api_key_here':
        print("\n⚠️  API KEY IS PLACEHOLDER")
        print(f"\nCurrent value: '{api_key}'")
        print("\nPlease replace with a real API key from:")
        print("https://makersuite.google.com/app/apikey")
        print("\n💡 NOTE: The system works fine WITHOUT Gemini API!")
        return False
    
    # Show key info (masked)
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"\n✓ API Key found: {masked_key}")
    print(f"✓ Key length: {len(api_key)} characters")
    
    # Try to import and test
    try:
        print("\n📦 Importing google.generativeai...")
        import google.generativeai as genai
        print("✓ Library imported successfully")
        
        print("\n🔐 Configuring API key...")
        genai.configure(api_key=api_key)
        print("✓ API key configured")
        
        print("\n🤖 Testing API connection...")
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        print(f"✓ Model initialized: {config.GEMINI_MODEL}")
        
        print("\n💬 Sending test prompt...")
        response = model.generate_content("Say 'Hello! API is working!'")
        
        if response and response.text:
            print(f"✓ Response received: {response.text.strip()}")
            
            print("\n" + "=" * 60)
            print("✅ GEMINI API KEY IS VALID AND WORKING!")
            print("=" * 60)
            print("\n🎉 Your cart abandonment emails will have:")
            print("   ✓ AI-generated personalized content")
            print("   ✓ More engaging and human-like text")
            print("   ✓ Higher conversion rates")
            print("\n✨ All features are now fully enabled!")
            return True
        else:
            print("\n⚠️  No response text received")
            return False
            
    except ImportError as e:
        print(f"\n❌ IMPORT ERROR: {e}")
        print("\nPlease install: pip install google-generativeai")
        return False
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ API ERROR: {error_msg}")
        
        if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            print("\n🔴 The API key is INVALID")
            print("\nPossible issues:")
            print("   1. Key was typed incorrectly")
            print("   2. Key has been revoked")
            print("   3. Key hasn't been activated yet")
            print("\n📝 Solutions:")
            print("   1. Double-check the key in .env file")
            print("   2. Generate a new key at: https://makersuite.google.com/app/apikey")
            print("   3. Make sure there are no extra spaces")
            
        elif "quota" in error_msg.lower():
            print("\n🔴 API QUOTA EXCEEDED")
            print("\nYou've hit the free tier limit.")
            print("Wait 24 hours or upgrade your plan.")
            
        elif "404" in error_msg:
            print("\n🔴 MODEL NOT FOUND")
            print("\nThe 'gemini-1.5-flash' model might not be available.")
            print("This is rare - usually a temporary Google issue.")
            
        else:
            print("\n🔴 UNEXPECTED ERROR")
            print("\nTry:")
            print("   1. Check your internet connection")
            print("   2. Wait a few minutes and try again")
            print("   3. Generate a new API key")
        
        print("\n💡 NOTE: The system works fine WITHOUT Gemini API!")
        print("   - Emails will use fallback template text")
        print("   - All other features work normally")
        return False

if __name__ == "__main__":
    try:
        check_gemini_api()
    except KeyboardInterrupt:
        print("\n\n⚠️  Check cancelled by user")
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
