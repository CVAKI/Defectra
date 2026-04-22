"""
Google Gemini Vision API Integration for Property Inspection
============================================================

Updated to use Gemini 2.5 models with robust 503 retry + fallback model logic.

Installation:
    pip install google-genai

Get your API key:
    https://aistudio.google.com/app/apikey
"""

from google import genai
from google.genai import types
import json
import time
import streamlit as st
from PIL import Image
import io

# Model priority list — tried in order on 503/overload errors
GEMINI_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-1.5-flash-8b',
]

# Retry configuration
MAX_RETRIES = 5
# Backoff delays in seconds between each retry attempt
RETRY_DELAYS = [5, 15, 30, 60, 90]


def _is_overload_error(err: Exception) -> bool:
    """Returns True if the error is a transient 503 / capacity / quota error."""
    s = str(err).upper()
    return any(keyword in s for keyword in [
        "503", "UNAVAILABLE", "HIGH DEMAND", "OVERLOADED",
        "RESOURCE_EXHAUSTED", "CAPACITY", "TRY AGAIN"
    ])


def _call_gemini(client, model: str, img_bytes: bytes, system_prompt: str):
    """Single attempt to call Gemini with one model."""
    return client.models.generate_content(
        model=model,
        contents=[
            system_prompt,
            types.Part.from_bytes(data=img_bytes, mime_type="image/png")
        ]
    )


def _call_with_retry(client, img_bytes: bytes, system_prompt: str):
    """
    Try each model in GEMINI_MODELS with exponential backoff.
    Raises the last exception if everything fails.
    """
    last_err = None

    for model in GEMINI_MODELS:
        for attempt in range(MAX_RETRIES):
            try:
                response = _call_gemini(client, model, img_bytes, system_prompt)
                if attempt > 0 or model != GEMINI_MODELS[0]:
                    st.info(f"✅ Connected using model: **{model}**")
                return response

            except Exception as e:
                last_err = e

                if _is_overload_error(e):
                    # Still retries left on this model
                    if attempt < MAX_RETRIES - 1:
                        wait = RETRY_DELAYS[attempt]
                        st.warning(
                            f"⏳ [{model}] Gemini busy (attempt {attempt + 1}/{MAX_RETRIES}). "
                            f"Retrying in {wait}s…"
                        )
                        time.sleep(wait)
                        continue
                    else:
                        # All retries on this model exhausted → try next model
                        st.warning(f"⚠️ [{model}] All retries exhausted. Trying next model…")
                        break
                else:
                    # Non-retriable error — raise immediately
                    raise

    raise last_err  # All models failed


# ── Main analysis function ────────────────────────────────────────────────────

def analyze_image_with_gemini(image, api_key=None):
    """
    FREE AI-Powered Property Inspection using Google Gemini Vision API.

    Args:
        image: PIL Image object
        api_key: Optional API key (if not in secrets)

    Returns:
        dict: Analysis results with defects, scores, and assessments
    """

    # Resolve API key
    if api_key is None:
        try:
            api_key = st.secrets["gemini"]["api_key"]
        except Exception:
            st.error("❌ Gemini API key not found. Please add it to .streamlit/secrets.toml")
            st.info("Get your FREE API key at: https://aistudio.google.com/app/apikey")
            return get_fallback_analysis(image)

    # Initialise client
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"❌ Failed to initialise Gemini API: {e}")
        return get_fallback_analysis(image)

    # ── Prompt ────────────────────────────────────────────────────────────────
    system_prompt = """You are an expert property inspector AI with extensive experience in building inspections, construction, and property maintenance. Analyze this image in extreme detail.

YOUR TASKS:

1. **Property Validation**:
   - First, determine if this is a property/building/room/structure image
   - If NOT (e.g., person, animal, vehicle, food, landscape without buildings), return: 
     {"is_property": false, "message": "This image does not appear to be property-related. Please upload images of buildings, rooms, or property structures."}

2. **Comprehensive Defect Detection** (if property image):
   Inspect EVERY visible aspect for defects:

   **Structural Issues**: Cracks in walls, ceilings, floors; settlement, sagging, bulging; damaged structural elements; material deterioration.
   **Water Damage**: Leaks, water stains, discoloration; dampness, mold/mildew; rust, corrosion; evidence of poor drainage.
   **Electrical**: Exposed wiring; damaged outlets/switches; outdated systems; visible fire hazards.
   **Finishes & Surfaces**: Peeling/cracking paint; damaged flooring/tiles; window or door issues.
   **Plumbing**: Visible pipe damage; fixture problems; drainage issues.
   **Safety Hazards**: Broken glass; unstable fixtures; tripping hazards; missing safety features.
   **Cleanliness & Maintenance**: Excessive dirt; evidence of poor maintenance; pest evidence; ventilation problems.

3. **Severity Classification**:
   - critical: Immediate safety hazard or structural collapse risk
   - high: Significant damage requiring urgent repair within days/weeks
   - medium: Moderate issues needing attention within 1-3 months
   - low: Minor cosmetic or routine maintenance issues

4. **For EACH defect provide**:
   - Specific descriptive name, exact location, confidence score (0-100)
   - Detailed 2-3 sentence description
   - Repair priority: immediate/urgent/routine/cosmetic
   - Impact on property safety, value, or usability

5. **Overall Assessment**:
   - Condition score 0-100 and usability rating: excellent/good/fair/poor/unsafe

RETURN ONLY VALID JSON — NO MARKDOWN, NO CODE BLOCKS, NO PREAMBLE:

{
  "is_property": true,
  "overall_condition_score": 75,
  "usability_rating": "good",
  "overall_assessment": "Brief 2-3 sentence summary",
  "defects": [
    {
      "detected_object": "specific descriptive defect name",
      "severity": "critical/high/medium/low",
      "confidence_score": 85,
      "location": "specific location in image",
      "description": "detailed 2-3 sentence explanation",
      "repair_priority": "immediate/urgent/routine/cosmetic",
      "estimated_impact": "specific impact on safety, value, or usability"
    }
  ]
}"""

    # ── Convert image to bytes ─────────────────────────────────────────────────
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    # ── Call API with retry + fallback ────────────────────────────────────────
    response_text = None
    try:
        response = _call_with_retry(client, img_bytes, system_prompt)
        response_text = response.text.strip()

        # Strip markdown fences if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        if not isinstance(result, dict):
            raise ValueError("Response is not a dictionary")

        # Normalise: rename 'defects' → 'detections' for app compatibility
        if result.get("is_property", False):
            defects_list = result.pop("defects", [])
            result["detections"] = defects_list
            result["defects_summary"] = {
                "critical": len([d for d in defects_list if d.get('severity') == 'critical']),
                "high":     len([d for d in defects_list if d.get('severity') == 'high']),
                "medium":   len([d for d in defects_list if d.get('severity') == 'medium']),
                "low":      len([d for d in defects_list if d.get('severity') == 'low']),
                "total":    len(defects_list),
            }

        return result

    except json.JSONDecodeError as e:
        st.error(f"❌ Failed to parse Gemini response as JSON: {e}")
        if response_text:
            st.error(f"Response preview: {response_text[:500]}")

        # Last-chance: try to extract JSON with regex
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text or '', re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                st.success("✅ Successfully extracted JSON from response")
                return result
        except Exception:
            pass

        return get_fallback_analysis(image)

    except Exception as e:
        err_str = str(e)

        if _is_overload_error(e):
            st.error(
                "🔄 Gemini is experiencing very high demand and all models/retries "
                "have been exhausted. Please wait 1–2 minutes and try again."
            )
        elif "API_KEY_INVALID" in err_str or "invalid api key" in err_str.lower():
            st.error("🔑 Invalid API key. Please check your Gemini API key.")
            st.info("Get a new key at: https://aistudio.google.com/app/apikey")
        elif "QUOTA_EXCEEDED" in err_str or "quota" in err_str.lower():
            st.warning("⏰ Daily quota exceeded. Free tier: 1,500 requests/day. Try again tomorrow.")
        elif "SAFETY" in err_str:
            st.warning("⚠️ Image blocked by safety filters. Try a different image.")
        else:
            st.error(f"❌ Gemini API error: {e}")

        return get_fallback_analysis(image)


# ── Fallback ──────────────────────────────────────────────────────────────────

def get_fallback_analysis(image):
    """Fallback analysis shown when Gemini API is unavailable."""
    return {
        "is_property": True,
        "overall_condition_score": 70,
        "usability_rating": "fair",
        "overall_assessment": (
            "Unable to perform AI analysis. Gemini API is currently unavailable "
            "or experiencing high demand. Please try again in a few minutes."
        ),
        "defects_summary": {"critical": 0, "high": 0, "medium": 1, "low": 0, "total": 1},
        "detections": [{
            "detected_object": "API Unavailable — Manual Inspection Required",
            "confidence_score": 50.0,
            "severity": "medium",
            "location": "Unable to analyse",
            "description": (
                "AI analysis service is currently unavailable due to high demand. "
                "Please verify your API key, check your internet connection, and try again. "
                "Professional manual inspection is recommended in the meantime."
            ),
            "repair_priority": "urgent",
            "estimated_impact": "Unknown — requires professional assessment"
        }]
    }


# ── Connection test ───────────────────────────────────────────────────────────

def test_gemini_connection(api_key):
    """
    Test if Gemini API is working.
    Returns: (success: bool, message: str)
    """
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODELS[0],
            contents="Hello! Are you working? Reply with 'Yes, I am working!' if you can read this."
        )
        if response.text:
            return True, f"✅ Gemini API connection successful! Response: {response.text}"
        return False, "❌ Received empty response from Gemini"
    except Exception as e:
        return False, f"❌ Connection failed: {str(e)}"


if __name__ == "__main__":
    print("=" * 70)
    print("Google Gemini Vision API Integration for Property Inspection")
    print("=" * 70)
    print()
    print(f"Primary model : {GEMINI_MODELS[0]}")
    print(f"Fallback chain: {' → '.join(GEMINI_MODELS[1:])}")
    print(f"Max retries   : {MAX_RETRIES} per model")
    print(f"Backoff delays: {RETRY_DELAYS} seconds")
    print()
    print("🚀 Ready to use!")
    print("=" * 70)