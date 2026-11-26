"""Download required NLTK data"""
import nltk

print("Downloading NLTK data...")
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
print("✓ NLTK data downloaded successfully")
