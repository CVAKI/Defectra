"""
List Available Gemini Models
"""

from google import genai

API_KEY = "AIzaSyD0uUbukq6B5nJrdRclsy4TuUlw91Hosgk"

print("=" * 70)
print("Listing Available Gemini Models")
print("=" * 70)
print()

try:
    client = genai.Client(api_key=API_KEY)

    print("Fetching available models...")
    print()

    # List all models
    models = client.models.list()

    print("Available models:")
    print("-" * 70)
    for model in models:
        print(f"Model: {model.name}")
        print(f"  Display Name: {model.display_name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  Supported methods: {model.supported_generation_methods}")
        print()

except Exception as e:
    print(f"❌ ERROR: {e}")
    print()
    print("Trying alternative approach...")
    print()

    # Try with direct model names
    test_models = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro',
        'gemini-1.5-pro-latest',
        'gemini-pro-vision',
        'gemini-pro',
    ]

    for model_name in test_models:
        try:
            print(f"Testing: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents="Hello"
            )
            print(f"  ✅ {model_name} works!")
            print(f"     Response: {response.text[:50]}...")
            print()
        except Exception as e:
            print(f"  ❌ {model_name} failed: {str(e)[:100]}")
            print()