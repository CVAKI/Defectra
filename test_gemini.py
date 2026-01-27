"""
Final Working Gemini API Test Script
Corrected syntax for Gemini 2.5
"""

from google import genai
from google.genai import types
from PIL import Image
import io

# Your API key
API_KEY = "AIzaSyD0uUbukq6B5nJrdRclsy4TuUlw91Hosgk"

print("=" * 70)
print("Testing Gemini API Connection - Gemini 2.5")
print("=" * 70)
print()

try:
    # Initialize client
    print("1. Initializing Gemini client...")
    client = genai.Client(api_key=API_KEY)
    print("   ✅ Client initialized successfully")
    print()

    # Test text generation
    print("2. Testing text generation...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents="Say 'Hello! I am working!' if you can read this."
    )
    print(f"   ✅ Response: {response.text}")
    print()

    # Test with image - CORRECTED SYNTAX
    print("3. Testing image analysis...")
    # Create a simple test image (red square)
    test_img = Image.new('RGB', (100, 100), color='red')

    # Convert to bytes
    img_byte_arr = io.BytesIO()
    test_img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # Test image analysis with corrected syntax
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            "What is the main color in this image? Answer in one word.",
            types.Part.from_bytes(
                data=img_byte_arr,
                mime_type="image/png"
            )
        ]
    )
    print(f"   ✅ Image analysis response: {response.text}")
    print()

    print("=" * 70)
    print("🎉 SUCCESS! Your Gemini API is working perfectly!")
    print("=" * 70)
    print()
    print("✅ Working model: gemini-2.5-flash")
    print()
    print("Next steps:")
    print("1. Replace your gemini_intagration.py with the updated version")
    print("2. Verify your .streamlit/secrets.toml has the correct API key")
    print("3. Run: streamlit run app.py")
    print()
    print("Your property inspection AI is ready to use! 🏠")
    print()

except Exception as e:
    print(f"❌ ERROR: {e}")
    print()
    print("Troubleshooting:")
    print("- Check your API key is valid")
    print("- Make sure you have internet connection")
    print("- Verify the API key at: https://aistudio.google.com/app/apikey")
    print("- Try running: pip install --upgrade google-genai")
    print()