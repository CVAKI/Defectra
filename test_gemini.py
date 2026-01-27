"""
Quick Test Script for Gemini API
================================

Run this to verify your Gemini API is working before using it in the main app.

Usage:
    python test_gemini.py
"""

import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

st.set_page_config(page_title="Gemini API Test", page_icon="🧪", layout="wide")

st.title("🧪 Gemini API Connection Test")
st.markdown("---")

# Step 1: Check for API key
st.header("Step 1: API Key Check")

try:
    api_key = st.secrets["gemini"]["api_key"]
    st.success(f"✅ API Key found: {api_key[:20]}...{api_key[-4:]}")
    key_found = True
except Exception as e:
    st.error("❌ API Key NOT found in secrets!")
    st.info("""
    Please add your API key to `.streamlit/secrets.toml`:

    [gemini]
    api_key = "your-api-key-here"

    Get your FREE key at: https://makersuite.google.com/app/apikey
    """)
    key_found = False

st.markdown("---")

# Step 2: Test connection
if key_found:
    st.header("Step 2: Connection Test")

    if st.button("🔌 Test Connection", type="primary"):
        with st.spinner("Testing connection..."):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')

                response = model.generate_content("Say 'Hello! I'm working!' if you can read this.")

                if response.text:
                    st.success("✅ Connection Successful!")
                    st.info(f"Gemini Response: {response.text}")
                else:
                    st.error("❌ Received empty response")

            except Exception as e:
                st.error(f"❌ Connection Failed: {e}")

                # Provide specific error guidance
                error_str = str(e)
                if "API_KEY_INVALID" in error_str:
                    st.warning("🔑 Your API key appears to be invalid.")
                    st.info("Get a new one at: https://makersuite.google.com/app/apikey")
                elif "QUOTA_EXCEEDED" in error_str:
                    st.warning("⏰ Rate limit exceeded. Wait a minute and try again.")
                    st.info("Free tier: 60 requests/minute, 1500/day")
                else:
                    st.info("Check your internet connection and API key.")

    st.markdown("---")

    # Step 3: Test with image
    st.header("Step 3: Vision Test with Property Image")

    st.info("Upload a property image to test AI vision detection")

    test_image = st.file_uploader("Upload test image", type=['png', 'jpg', 'jpeg'])

    if test_image:
        image = Image.open(test_image)
        col1, col2 = st.columns(2)

        with col1:
            st.image(image, caption="Your test image", use_container_width=True)

        with col2:
            if st.button("🤖 Analyze with Gemini AI", type="primary"):
                with st.spinner("AI is analyzing..."):
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash')

                        prompt = """Analyze this image briefly. Is it a property/building/room image? 
                        If yes, list 2-3 main observations about the condition.
                        If no, say what it is instead.
                        Keep response under 100 words."""

                        response = model.generate_content([prompt, image])

                        st.success("✅ Analysis Complete!")
                        st.markdown("**AI Response:**")
                        st.write(response.text)

                        st.balloons()

                    except Exception as e:
                        st.error(f"❌ Analysis Failed: {e}")

st.markdown("---")

# Step 4: System info
st.header("Step 4: System Information")

col1, col2 = st.columns(2)

with col1:
    try:
        import google.generativeai

        st.success(f"✅ google-generativeai installed: v{google.generativeai.__version__}")
    except ImportError:
        st.error("❌ google-generativeai NOT installed")
        st.code("pip install google-generativeai")

with col2:
    try:
        import PIL

        st.success(f"✅ Pillow installed: v{PIL.__version__}")
    except ImportError:
        st.error("❌ Pillow NOT installed")
        st.code("pip install pillow")

st.markdown("---")

# Final status
st.header("📊 Final Status")

if key_found:
    st.success("""
    ✅ **All checks passed!**

    You're ready to use Gemini AI in your property inspection app!

    Next steps:
    1. Copy `gemini_vision_integration.py` to your project
    2. Update `app_improved.py` to use Gemini
    3. Run: `streamlit run app_improved.py`
    """)
else:
    st.warning("""
    ⚠️ **Setup incomplete**

    Please:
    1. Get API key from: https://makersuite.google.com/app/apikey
    2. Add it to `.streamlit/secrets.toml`
    3. Refresh this page
    """)

st.markdown("---")
st.caption("🏠 Property Inspection AI - Powered by Google Gemini (FREE)")