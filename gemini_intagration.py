"""
Google Gemini Vision API Integration for Property Inspection
============================================================

Updated to use Gemini 2.5 models with correct syntax (Jan 2026)

Installation:
    pip install google-genai

Get your API key:
    https://aistudio.google.com/app/apikey
"""

from google import genai
from google.genai import types
import json
import streamlit as st
from PIL import Image
import io


def analyze_image_with_gemini(image, api_key=None):
    """
    FREE AI-Powered Property Inspection using Google Gemini Vision API

    Args:
        image: PIL Image object
        api_key: Optional API key (if not in secrets)

    Returns:
        dict: Analysis results with defects, scores, and assessments
    """

    # Get API key from secrets or parameter
    if api_key is None:
        try:
            api_key = st.secrets["gemini"]["api_key"]
        except Exception:
            st.error("❌ Gemini API key not found. Please add it to .streamlit/secrets.toml")
            st.info("Get your FREE API key at: https://aistudio.google.com/app/apikey")
            return get_fallback_analysis(image)

    # Configure Gemini client
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"❌ Failed to initialize Gemini API: {e}")
        return get_fallback_analysis(image)

    # Comprehensive inspection prompt
    system_prompt = """You are an expert property inspector AI with extensive experience in building inspections, construction, and property maintenance. Analyze this image in extreme detail.

YOUR TASKS:

1. **Property Validation**:
   - First, determine if this is a property/building/room/structure image
   - If NOT (e.g., person, animal, vehicle, food, landscape without buildings), return: 
     {"is_property": false, "message": "This image does not appear to be property-related. Please upload images of buildings, rooms, or property structures."}

2. **Comprehensive Defect Detection** (if property image):
   Inspect EVERY visible aspect for defects:

   **Structural Issues**:
   - Cracks in walls, ceilings, floors (size, location, pattern)
   - Settlement, sagging, bulging
   - Damaged structural elements
   - Material deterioration

   **Water Damage**:
   - Leaks, water stains, discoloration patterns
   - Dampness, moisture, visible mold/mildew
   - Rust, corrosion on fixtures
   - Evidence of poor drainage

   **Electrical**:
   - Exposed wiring or damaged conduits
   - Damaged outlets, switches, light fixtures
   - Outdated electrical systems
   - Visible fire hazards

   **Finishes & Surfaces**:
   - Peeling, cracking, or bubbling paint
   - Damaged flooring, tiles, carpets
   - Wall surface damage
   - Window or door issues

   **Plumbing**:
   - Visible pipe damage or leaks
   - Fixture problems (sinks, toilets, faucets)
   - Drainage issues

   **Safety Hazards**:
   - Broken glass, sharp edges
   - Unstable fixtures or furniture
   - Tripping hazards
   - Missing safety features (railings, etc.)

   **Cleanliness & Maintenance**:
   - Excessive dirt, grime, or dust
   - Evidence of poor maintenance
   - Pest evidence
   - Ventilation problems

3. **Severity Classification Guidelines**:
   - **critical**: Immediate safety hazard or structural collapse risk
     Examples: Exposed live wiring, major structural cracks, severe mold with health risk, collapse danger

   - **high**: Significant damage requiring urgent repair within days/weeks
     Examples: Active water leaks, extensive water damage, compromised structural integrity, major electrical issues

   - **medium**: Moderate issues needing attention within 1-3 months
     Examples: Minor cracks, surface water damage, deteriorating finishes, outdated systems

   - **low**: Minor cosmetic or routine maintenance issues
     Examples: Small paint chips, minor wear and tear, dust accumulation, minor aesthetic issues

4. **For EACH defect, provide**:
   - Specific, descriptive name (e.g., "vertical hairline crack in drywall", not just "crack")
   - Exact location visible in image (e.g., "upper right corner near ceiling junction")
   - Confidence score (0-100) - be realistic
   - Detailed 2-3 sentence description explaining what you see and why it matters
   - Repair priority: immediate/urgent/routine/cosmetic
   - Impact on property safety, value, or usability

5. **Overall Property Assessment**:
   Calculate condition score (0-100):
   - 90-100: Excellent condition, minimal issues
   - 75-89: Good condition, minor maintenance needed
   - 55-74: Fair condition, moderate repairs required
   - 35-54: Poor condition, significant repairs needed
   - 0-34: Critical condition, major safety/structural concerns

   Usability rating: excellent/good/fair/poor/unsafe

IMPORTANT RULES:
- Be thorough but realistic - don't over-report trivial issues
- If you see NO defects, say so clearly (rare but possible)
- Always provide specific locations
- Explain WHY each defect matters
- Consider the overall context (new vs. old building, type of room, etc.)

RETURN ONLY VALID JSON - NO MARKDOWN, NO CODE BLOCKS, NO PREAMBLE:

{
  "is_property": true,
  "overall_condition_score": 75,
  "usability_rating": "good",
  "overall_assessment": "Brief 2-3 sentence summary of condition and main concerns",
  "defects": [
    {
      "detected_object": "specific descriptive defect name",
      "severity": "critical/high/medium/low",
      "confidence_score": 85,
      "location": "specific location in image",
      "description": "detailed 2-3 sentence explanation of defect, cause, and importance",
      "repair_priority": "immediate/urgent/routine/cosmetic",
      "estimated_impact": "specific impact on safety, value, or usability"
    }
  ]
}

If no defects visible, return empty defects array but still provide overall assessment noting that no visible issues were found (but hidden problems may exist)."""

    try:
        # Convert PIL Image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # Use Gemini 2.5 Flash (latest and fastest)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                system_prompt,
                types.Part.from_bytes(
                    data=img_byte_arr,
                    mime_type="image/png"
                )
            ]
        )

        # Get response text
        response_text = response.text.strip()

        # Clean potential markdown formatting
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        # Remove any leading/trailing whitespace or newlines
        response_text = response_text.strip()

        # Parse JSON
        result = json.loads(response_text)

        # Validate structure
        if not isinstance(result, dict):
            raise ValueError("Response is not a dictionary")

        # Add defects_summary if property image
        if result.get("is_property", False):
            if "defects" in result:
                result["defects_summary"] = {
                    "critical": len([d for d in result["defects"] if d.get('severity') == 'critical']),
                    "high": len([d for d in result["defects"] if d.get('severity') == 'high']),
                    "medium": len([d for d in result["defects"] if d.get('severity') == 'medium']),
                    "low": len([d for d in result["defects"] if d.get('severity') == 'low']),
                    "total": len(result["defects"])
                }

                # Rename "defects" to "detections" for compatibility with app
                result["detections"] = result.pop("defects")
            else:
                result["detections"] = []
                result["defects_summary"] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0}

        return result

    except json.JSONDecodeError as e:
        st.error(f"❌ Failed to parse Gemini response as JSON: {e}")
        st.error(f"Response preview: {response_text[:500] if 'response_text' in locals() else 'No response'}")

        # Try to extract any useful information from the response
        try:
            # Sometimes Gemini adds extra text before/after JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                st.success("✅ Successfully extracted JSON from response")
                return result
        except:
            pass

        return get_fallback_analysis(image)

    except Exception as e:
        st.error(f"❌ Gemini API error: {e}")

        # Check for common errors
        error_str = str(e)
        if "API_KEY_INVALID" in error_str or "invalid api key" in error_str.lower():
            st.error("🔑 Invalid API key. Please check your Gemini API key.")
            st.info("Get a new key at: https://aistudio.google.com/app/apikey")
        elif "QUOTA_EXCEEDED" in error_str or "quota" in error_str.lower():
            st.warning("⏰ Rate limit exceeded. Free tier: 60 requests/min, 1500/day. Please wait a moment.")
        elif "SAFETY" in error_str:
            st.warning("⚠️ Image blocked by safety filters. Try a different image.")

        return get_fallback_analysis(image)


def get_fallback_analysis(image):
    """
    Fallback analysis when API is unavailable
    Uses basic image analysis as backup
    """
    import numpy as np

    try:
        img_array = np.array(image)
        avg_brightness = np.mean(img_array)

        detections = [{
            "detected_object": "API Unavailable - Manual Inspection Required",
            "confidence_score": 50.0,
            "severity": "medium",
            "location": "Unable to analyze",
            "description": "AI analysis service is currently unavailable. Please verify your API key and internet connection. Professional manual inspection is recommended for accurate defect detection.",
            "repair_priority": "urgent",
            "estimated_impact": "Unknown - requires professional assessment"
        }]

        return {
            "is_property": True,
            "overall_condition_score": 70,
            "usability_rating": "fair",
            "overall_assessment": "Unable to perform AI analysis. Please check your API configuration and try again.",
            "defects_summary": {"critical": 0, "high": 0, "medium": 1, "low": 0, "total": 1},
            "detections": detections
        }
    except Exception:
        return {
            "is_property": False,
            "message": "Unable to analyze image. Please try again or contact support."
        }


# Test function
def test_gemini_connection(api_key):
    """
    Test if Gemini API is working
    Returns: (success: bool, message: str)
    """
    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Hello! Are you working? Reply with 'Yes, I am working!' if you can read this."
        )

        if response.text:
            return True, f"✅ Gemini API connection successful! Response: {response.text}"
        else:
            return False, "❌ Received empty response from Gemini"

    except Exception as e:
        return False, f"❌ Connection failed: {str(e)}"


# Example usage and setup instructions
if __name__ == "__main__":
    """
    Setup and usage instructions for Gemini Vision integration
    """
    print("=" * 70)
    print("Google Gemini Vision API Integration for Property Inspection")
    print("=" * 70)
    print()
    print("🎉 USING LATEST GEMINI 2.5 MODELS!")
    print("- ✅ Completely FREE (generous free tier)")
    print("- ✅ 60 requests per minute")
    print("- ✅ 1,500 requests per day")
    print("- ✅ Powerful vision capabilities")
    print("- ✅ Faster than ever with Gemini 2.5 Flash")
    print()
    print("📋 Using: gemini-2.5-flash")
    print()
    print("🚀 Ready to use!")
    print("=" * 70)