"""
List all available Gemini models
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv(dotenv_path='../.env')

api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

print("=" * 60)
print("📋 AVAILABLE GEMINI MODELS")
print("=" * 60)

try:
    models = genai.list_models()
    
    generate_models = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            generate_models.append(model.name)
            print(f"\n✓ {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description}")
    
    print("\n" + "=" * 60)
    print(f"✅ Found {len(generate_models)} models that support content generation")
    print("=" * 60)
    
    if generate_models:
        print("\n🎯 RECOMMENDED MODEL:")
        print(f"   {generate_models[0]}")
        
except Exception as e:
    print(f"\n❌ Error listing models: {e}")
