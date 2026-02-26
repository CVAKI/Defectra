import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
from PIL import Image
import io
import base64
from datetime import datetime
import uuid
import numpy as np
from gemini_intagration import analyze_image_with_gemini
from pdf_report_generator import generate_pdf_report
from video_pdf_generator import generate_video_pdf_report
from video_processor import VideoProcessor, save_uploaded_video, cleanup_temp_file, format_timestamp
from translations import get_text
from image_annotator import annotate_image_with_defects

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Defactra AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'language' not in st.session_state:
    st.session_state.language = 'english'
if 'stored_images' not in st.session_state:
    st.session_state.stored_images = []
if 'stored_defects' not in st.session_state:
    st.session_state.stored_defects = []
if 'stored_property_data' not in st.session_state:
    st.session_state.stored_property_data = {}
# NEW: PDF generation flags
if 'show_pdf_button' not in st.session_state:
    st.session_state.show_pdf_button = False
if 'current_property_id' not in st.session_state:
    st.session_state.current_property_id = None

# VIDEO-specific session state
if 'video_analysis_complete' not in st.session_state:
    st.session_state.video_analysis_complete = False
if 'video_analysis_results' not in st.session_state:
    st.session_state.video_analysis_results = None
if 'video_key_frames' not in st.session_state:
    st.session_state.video_key_frames = []
if 'video_info' not in st.session_state:
    st.session_state.video_info = None

# ============================================
# ENHANCED CUSTOM CSS WITH ANIMATIONS
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=Space+Mono:wght@400;700&display=swap');

    /* Global Styles */
    * {
        font-family: 'Outfit', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        background-attachment: fixed;
    }

    /* Animated Header */
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        padding: 2rem 1rem;
        background: linear-gradient(120deg, #00f5ff, #0080ff, #ff00ff, #ff0080);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientShift 8s ease infinite;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        position: relative;
    }

    .main-header::before {
        content: '🔍';
        position: absolute;
        left: 50%;
        top: -40px;
        transform: translateX(-50%);
        font-size: 4rem;
        animation: float 3s ease-in-out infinite;
    }

    @keyframes float {
        0%, 100% {
            transform: translateX(-50%) translateY(0px);
        }
        50% {
            transform: translateX(-50%) translateY(-10px);
        }
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .subtitle {
        text-align: center;
        color: #a0a0ff;
        font-size: 1.1rem;
        font-weight: 300;
        margin-top: -1rem;
        margin-bottom: 2rem;
        letter-spacing: 0.05em;
        animation: fadeInUp 1s ease-out;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Glass Morphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        animation: slideIn 0.6s ease-out;
    }

    .glass-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 48px rgba(0, 255, 255, 0.2);
        border-color: rgba(0, 255, 255, 0.3);
    }

    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Metric Cards with Animation */
    .metric-card {
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.1) 0%, rgba(255, 0, 255, 0.1) 100%);
        border: 2px solid rgba(0, 245, 255, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        animation: popIn 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s;
    }

    .metric-card:hover::before {
        left: 100%;
    }

    .metric-card:hover {
        transform: scale(1.05) rotate(1deg);
        box-shadow: 0 8px 32px rgba(0, 245, 255, 0.4);
        border-color: rgba(0, 245, 255, 0.6);
    }

    @keyframes popIn {
        0% {
            opacity: 0;
            transform: scale(0.8);
        }
        50% {
            transform: scale(1.1);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #00f5ff;
        text-shadow: 0 0 20px rgba(0, 245, 255, 0.5);
        font-family: 'Space Mono', monospace;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #b0b0ff;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.5rem;
        font-weight: 600;
    }

    /* Upload Section */
    .upload-section {
        background: linear-gradient(135deg, rgba(0, 128, 255, 0.1), rgba(255, 0, 255, 0.1));
        border: 3px dashed rgba(0, 245, 255, 0.4);
        border-radius: 24px;
        padding: 3rem;
        text-align: center;
        margin: 2rem 0;
        transition: all 0.3s ease;
        animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% {
            box-shadow: 0 0 0 0 rgba(0, 245, 255, 0.4);
        }
        50% {
            box-shadow: 0 0 0 20px rgba(0, 245, 255, 0);
        }
    }

    .upload-section:hover {
        border-color: rgba(0, 245, 255, 0.8);
        background: linear-gradient(135deg, rgba(0, 128, 255, 0.15), rgba(255, 0, 255, 0.15));
        animation: none;
    }

    /* Defect Cards with Severity Colors */
    .defect-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1rem 0;
        border-left: 5px solid;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        animation: slideInLeft 0.5s ease-out;
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    .defect-card:hover {
        transform: translateX(10px);
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5);
    }

    .critical-card { 
        border-left-color: #ff0066;
        background: linear-gradient(90deg, rgba(255, 0, 102, 0.1), transparent);
    }

    .high-card { 
        border-left-color: #ff6600;
        background: linear-gradient(90deg, rgba(255, 102, 0, 0.1), transparent);
    }

    .medium-card { 
        border-left-color: #ffcc00;
        background: linear-gradient(90deg, rgba(255, 204, 0, 0.1), transparent);
    }

    .low-card { 
        border-left-color: #00ff99;
        background: linear-gradient(90deg, rgba(0, 255, 153, 0.1), transparent);
    }

    .defect-card h4 {
        color: #00f5ff;
        font-weight: 700;
        font-size: 1.3rem;
        margin-bottom: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .defect-card p {
        color: #d0d0ff;
        line-height: 1.6;
        margin: 0.5rem 0;
    }

    .defect-card strong {
        color: #00f5ff;
        font-weight: 600;
    }

    /* Language Selector Card */
    .language-card {
        background: linear-gradient(135deg, rgba(255, 0, 255, 0.1) 0%, rgba(0, 128, 255, 0.1) 100%);
        border: 2px solid rgba(255, 0, 255, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
    }

    /* Video Badge */
    .video-badge {
        display: inline-block;
        background: linear-gradient(135deg, #FF6600, #FF0066);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-left: 0.5rem;
        animation: pulse 2s ease-in-out infinite;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00f5ff, #0080ff);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-weight: 700;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0, 128, 255, 0.4);
        position: relative;
        overflow: hidden;
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }

    .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0, 245, 255, 0.6);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(15, 12, 41, 0.95), rgba(36, 36, 62, 0.95));
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(0, 245, 255, 0.2);
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #00f5ff;
        font-weight: 700;
    }

    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #00f5ff, #ff00ff);
        animation: progressGlow 1.5s ease-in-out infinite;
    }

    @keyframes progressGlow {
        0%, 100% {
            box-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
        }
        50% {
            box-shadow: 0 0 20px rgba(255, 0, 255, 0.8);
        }
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(0, 0, 0, 0.2);
        padding: 0.5rem;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        color: #a0a0ff;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00f5ff, #0080ff);
        color: white;
        box-shadow: 0 4px 16px rgba(0, 245, 255, 0.4);
    }

    /* Dataframe Styling */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }

    /* Success/Error/Warning Messages */
    .stAlert {
        border-radius: 12px;
        border-left: 4px solid;
        backdrop-filter: blur(10px);
        animation: slideInRight 0.5s ease-out;
    }

    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    /* Loading Spinner Enhancement */
    .stSpinner > div {
        border-color: #00f5ff !important;
        border-right-color: transparent !important;
    }

    /* Section Headers */
    h1, h2, h3 {
        color: #00f5ff;
        font-weight: 700;
        text-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
    }

    /* Text Colors */
    p, label, span {
        color: #d0d0ff;
    }

    /* Input Fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 2px solid rgba(0, 245, 255, 0.3);
        border-radius: 8px;
        color: white;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within {
        border-color: rgba(0, 245, 255, 0.8);
        box-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
    }

    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(0, 245, 255, 0.5), transparent);
        margin: 2rem 0;
    }

    /* Image Preview */
    .stImage {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease;
    }

    .stImage:hover {
        transform: scale(1.05);
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #8080ff;
        font-size: 0.9rem;
        animation: fadeIn 2s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.2);
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #00f5ff, #0080ff);
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #0080ff, #ff00ff);
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# CONNECTION
# ============================================
@st.cache_resource
def get_snowflake_connection():
    """Create connection to Snowflake"""
    try:
        conn = snowflake.connector.connect(
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            account=st.secrets["snowflake"]["account"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"]
        )
        return conn
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        st.stop()


conn = get_snowflake_connection()


# ============================================
# HELPER FUNCTIONS
# ============================================

def image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def analyze_image_with_ai(image):
    """AI-Powered Property Inspection using FREE Google Gemini API"""
    return analyze_image_with_gemini(image)


# ============================================
# HEADER WITH LANGUAGE SELECTOR
# ============================================
st.markdown('<h1 class="main-header">Defactra AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle"><span class="video-badge">Intelligent Defect Detection & Property Risk Analysis Platform </span></p>',
            unsafe_allow_html=True)

# Language selector in a prominent position
col1, col2, col3 = st.columns([2, 1, 2])
with col2:

    st.session_state.language = 'english'
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ============================================
# SIDEBAR WITH MODE SELECTION
# ============================================
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h2 style='color: #00f5ff; font-weight: 800; margin: 0;'>🔍 DEFACTRA</h2>
        <p style='color: #a0a0ff; font-size: 0.8rem; margin: 0; letter-spacing: 0.2em;'>AI-POWERED INSPECTION</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔍 Navigation")

    app_mode = st.radio(
        "Choose Mode:",
        ["📊 View Existing Reports", "📸 New Inspection (Upload Images)", "🎥 New Video Inspection"],
        index=0
    )

    st.markdown("---")

    # Only show property selector in View mode
    if app_mode == "📊 View Existing Reports":
        st.markdown("### 🏢 Property Selection")

        properties_df = pd.read_sql("""
            SELECT property_id, address, city 
            FROM properties 
            ORDER BY property_id
        """, conn)
        properties_df.columns = properties_df.columns.str.lower()

        if len(properties_df) > 0:
            selected_property = st.selectbox(
                "Select Property:",
                properties_df['property_id'].tolist(),
                format_func=lambda x: properties_df[properties_df['property_id'] == x]['address'].iloc[0]
            )

            st.markdown("---")

            prop_info = properties_df[properties_df['property_id'] == selected_property].iloc[0]
            st.markdown(f"**📍 Location:** {prop_info['city']}")
            st.markdown(f"**🆔 ID:** {selected_property}")

            st.markdown("---")
            st.markdown("### 📊 Quick Actions")

            if st.button("🔄 Refresh Data", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()
        else:
            st.warning(
                "No properties found. Upload images in 'New Inspection' mode to create your first property report.")
            selected_property = None

# ============================================
# MODE 1: NEW IMAGE INSPECTION
# ============================================

if app_mode == "📸 New Inspection (Upload Images)":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("📸 New Property Inspection with Defactra AI")
    st.info(
        "👉 Upload property images and let Defactra AI detect defects automatically with detailed severity analysis!")
    st.markdown('</div>', unsafe_allow_html=True)

    # Property Information Form
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🏠 Property Information")
    col1, col2 = st.columns(2)

    with col1:
        property_address = st.text_input("📍 Address", placeholder="123 Main Street")
        property_city = st.text_input("🌆 City", placeholder="Trivandrum")
        property_type = st.selectbox("🏗️ Type", ["apartment", "villa", "house", "commercial"])

    with col2:
        bedrooms = st.number_input("🛏️ Bedrooms", min_value=1, max_value=10, value=3)
        area_sqft = st.number_input("📏 Area (sqft)", min_value=100, max_value=10000, value=1200)
        year_built = st.number_input("📅 Year Built", min_value=1900, max_value=2026, value=2020)
    st.markdown('</div>', unsafe_allow_html=True)

    # Room Information
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🚪 Room Information")
    col1, col2 = st.columns(2)

    with col1:
        room_name = st.text_input("Room Name", placeholder="Kitchen, Master Bedroom, etc.")
    with col2:
        room_type = st.selectbox("Room Type", ["bedroom", "kitchen", "bathroom", "living", "balcony", "other"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Image Upload
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📤 Upload Inspection Images")

    uploaded_files = st.file_uploader(
        "Drop images here or click to browse (supports: JPG, PNG)",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        help="Upload multiple images of the same room for comprehensive analysis"
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} image(s) uploaded")

        # Preview images
        cols = st.columns(min(len(uploaded_files), 4))
        for idx, uploaded_file in enumerate(uploaded_files[:4]):
            with cols[idx]:
                image = Image.open(uploaded_file)
                st.image(image, caption=f"Image {idx + 1}", use_container_width=True)

        if len(uploaded_files) > 4:
            st.info(f"...and {len(uploaded_files) - 4} more image(s)")

    st.markdown('</div>', unsafe_allow_html=True)

    # Analyze Button
    if uploaded_files and st.button("🤖 Analyze with Defactra AI & Generate Report", type="primary",
                                    use_container_width=True):

        # Validation
        if not property_address or not room_name:
            st.error("⚠️ Please fill in Property Address and Room Name")
            st.stop()

        with st.spinner("🔍 Defactra AI is analyzing your images... This may take a moment..."):

            # Generate IDs
            property_id = f"P{str(uuid.uuid4())[:6].upper()}"
            room_id = f"R{str(uuid.uuid4())[:6].upper()}"

            try:
                cursor = conn.cursor()

                # Insert property
                cursor.execute("""
                    INSERT INTO properties (property_id, address, city, property_type, bedrooms, area_sqft, year_built)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (property_id, property_address, property_city, property_type, bedrooms, area_sqft, year_built))

                # Insert room
                cursor.execute("""
                    INSERT INTO rooms (room_id, property_id, room_name, room_type, floor_number)
                    VALUES (%s, %s, %s, %s, %s)
                """, (room_id, property_id, room_name, room_type, 0))

                st.success(f"✅ Property created: {property_id}")

                # Process images
                all_findings = []
                non_property_count = 0
                processed_images = []

                progress_bar = st.progress(0)
                for idx, uploaded_file in enumerate(uploaded_files):
                    progress_bar.progress((idx + 1) / len(uploaded_files))

                    # Read image
                    uploaded_file.seek(0)
                    image = Image.open(uploaded_file)

                    # CRITICAL: Store image copy for PDF generation
                    processed_images.append(image.copy())

                    # Convert image to base64 for storage
                    image_base64 = image_to_base64(image)

                    # Get file size
                    uploaded_file.seek(0)
                    file_size_kb = len(uploaded_file.read()) / 1024
                    uploaded_file.seek(0)

                    # Get image format
                    image_format = image.format.lower() if image.format else 'png'

                    # AI Analysis
                    analysis_result = analyze_image_with_ai(image)

                    # Check if property image
                    if not analysis_result["is_property"]:
                        non_property_count += 1
                        st.warning(f"⚠️ Image {idx + 1}: {analysis_result['message']}")
                        continue

                    # Generate upload ID
                    upload_id = f"UPL{str(uuid.uuid4())[:6].upper()}"

                    # Store image with actual base64 data
                    cursor.execute("""
                        INSERT INTO uploaded_images 
                        (upload_id, property_id, room_name, upload_timestamp, image_data, image_format, file_size_kb, uploaded_by)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP(), %s, %s, %s, %s)
                    """, (upload_id, property_id, room_name, image_base64, image_format, int(file_size_kb), 'web_user'))

                    # Store each detection
                    for detection in analysis_result["detections"]:
                        detection_id = f"DET{str(uuid.uuid4())[:6].upper()}"
                        finding_id = f"F{str(uuid.uuid4())[:6].upper()}"

                        # Escape single quotes in description
                        escaped_description = detection["description"].replace("'", "''")
                        escaped_object = detection["detected_object"].replace("'", "''")

                        cursor.execute("""
                            INSERT INTO ai_detections 
                            (detection_id, upload_id, detected_object, confidence_score, bounding_box, severity, description, detection_timestamp)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP())
                        """, (detection_id, upload_id, escaped_object, detection["confidence_score"], '',
                              detection["severity"], escaped_description))

                        # Store as finding
                        cursor.execute("""
                            INSERT INTO findings 
                            (finding_id, room_id, inspection_date, finding_text, inspector_notes, detection_id, upload_id, ai_generated)
                            VALUES (%s, %s, CURRENT_DATE(), %s, %s, %s, %s, %s)
                        """, (finding_id, room_id, escaped_object, escaped_description, detection_id, upload_id, True))

                        all_findings.append({
                            **detection,
                            "overall_score": analysis_result["overall_condition_score"],
                            "usability": analysis_result["usability_rating"]
                        })

                conn.commit()
                progress_bar.empty()

                # CRITICAL: Store data for PDF generation with flags
                if len(all_findings) > 0:
                    st.session_state.stored_property_data = {
                        'property_id': property_id,
                        'address': property_address,
                        'city': property_city,
                        'property_type': property_type,
                        'bedrooms': int(bedrooms),
                        'area_sqft': int(area_sqft),
                        'year_built': int(year_built),
                        'room_name': room_name,
                        'overall_score': all_findings[0]['overall_score'],
                        'usability': all_findings[0]['usability']
                    }
                    st.session_state.stored_defects = all_findings
                    st.session_state.stored_images = processed_images
                    # Set flags for PDF generation
                    st.session_state.show_pdf_button = True
                    st.session_state.current_property_id = property_id

                # Success message
                if non_property_count > 0:
                    st.warning(f"⚠️ {non_property_count} image(s) were not property-related and were skipped.")

                if len(all_findings) > 0:
                    st.success(f"🎉 Analysis Complete!")
                    st.balloons()

                    # Metrics Display
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{len(uploaded_files) - non_property_count}</div>
                            <div class="metric-label">📸 Images Analyzed</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{len(all_findings)}</div>
                            <div class="metric-label">🔍 Defects Found</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{all_findings[0]['overall_score']}/100</div>
                            <div class="metric-label">🎯 Condition Score</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col4:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{all_findings[0]['usability'].split('-')[0].strip()}</div>
                            <div class="metric-label">📊 Usability</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Show detailed findings
                    st.markdown("---")
                    st.subheader("🔍 Comprehensive Defactra AI Detection Results")

                    # Group by severity
                    critical = [f for f in all_findings if f['severity'] == 'critical']
                    high = [f for f in all_findings if f['severity'] == 'high']
                    medium = [f for f in all_findings if f['severity'] == 'medium']
                    low = [f for f in all_findings if f['severity'] == 'low']

                    if critical:
                        st.markdown("### 🔴 CRITICAL Issues (Immediate Action Required)")
                        for i, f in enumerate(critical, 1):
                            st.markdown(f"""
                            <div class="defect-card critical-card">
                                <h4>{i}. {f['detected_object'].upper()}</h4>
                                <p><strong>Location:</strong> {f['location']}</p>
                                <p><strong>Confidence:</strong> {f['confidence_score']:.1f}%</p>
                                <p><strong>Priority:</strong> {f['repair_priority'].upper()}</p>
                                <p><strong>Description:</strong> {f['description']}</p>
                                <p><strong>Impact:</strong> {f['estimated_impact']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    if high:
                        st.markdown("### 🟠 HIGH Priority Issues")
                        for i, f in enumerate(high, 1):
                            st.markdown(f"""
                            <div class="defect-card high-card">
                                <h4>{i}. {f['detected_object'].title()}</h4>
                                <p><strong>Location:</strong> {f['location']}</p>
                                <p><strong>Confidence:</strong> {f['confidence_score']:.1f}%</p>
                                <p><strong>Priority:</strong> {f['repair_priority'].upper()}</p>
                                <p><strong>Description:</strong> {f['description']}</p>
                                <p><strong>Impact:</strong> {f['estimated_impact']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    if medium:
                        st.markdown("### 🟡 MEDIUM Priority Issues")
                        for i, f in enumerate(medium, 1):
                            st.markdown(f"""
                            <div class="defect-card medium-card">
                                <h4>{i}. {f['detected_object'].title()}</h4>
                                <p><strong>Location:</strong> {f['location']}</p>
                                <p><strong>Confidence:</strong> {f['confidence_score']:.1f}%</p>
                                <p><strong>Priority:</strong> {f['repair_priority'].upper()}</p>
                                <p><strong>Description:</strong> {f['description']}</p>
                                <p><strong>Impact:</strong> {f['estimated_impact']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    if low:
                        with st.expander("🟢 LOW Priority Issues (Click to expand)"):
                            for i, f in enumerate(low, 1):
                                st.markdown(f"""
                                <div class="defect-card low-card">
                                    <h4>{i}. {f['detected_object'].title()}</h4>
                                    <p><strong>Location:</strong> {f['location']}</p>
                                    <p><strong>Confidence:</strong> {f['confidence_score']:.1f}%</p>
                                    <p><strong>Description:</strong> {f['description']}</p>
                                </div>
                                """, unsafe_allow_html=True)

                    # Force rerun to show PDF button
                    st.rerun()

                else:
                    st.error(
                        "❌ No valid property images were found. Please upload images of buildings, rooms, or property structures.")

            except Exception as e:
                st.error(f"❌ Error: {e}")
                conn.rollback()
                import traceback

                with st.expander("Error Details"):
                    st.code(traceback.format_exc())

    # PDF GENERATION SECTION - Shows AFTER analysis complete (outside the analyze button)
    if st.session_state.show_pdf_button and st.session_state.stored_property_data and not st.session_state.video_analysis_complete:
        st.markdown("---")
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📄 Download Professional Report")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(
                f"📥 Ready to generate PDF for property: **{st.session_state.current_property_id}**")
            st.caption(
                f"Report includes {len(st.session_state.stored_images)} images and {len(st.session_state.stored_defects)} defects in {st.session_state.language.title()}")

        with col2:
            if st.button("🎨 Generate PDF Report", type="primary", use_container_width=True,
                         key="new_inspection_pdf"):
                with st.spinner(f"Generating report in {st.session_state.language}..."):
                    try:
                        # Generate PDF
                        pdf_buffer = generate_pdf_report(
                            property_data=st.session_state.stored_property_data,
                            defects=st.session_state.stored_defects,
                            images=st.session_state.stored_images,
                            language=st.session_state.language
                        )

                        st.success("✅ Report generated successfully!")

                        # Download button
                        filename = f"Defactra_Report_{st.session_state.current_property_id}_{st.session_state.language}.pdf"
                        st.download_button(
                            label="⬇️ Download PDF Report",
                            data=pdf_buffer.getvalue(),
                            file_name=filename,
                            mime="application/pdf",
                            use_container_width=True,
                            key="download_new_pdf"
                        )

                        st.balloons()

                    except Exception as e:
                        st.error(f"❌ Error generating PDF: {e}")
                        import traceback

                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.info(
            f"📊 **Next Step:** Go to 'View Existing Reports' mode and select property **{st.session_state.current_property_id}** to see the full risk analysis and historical data!")

# ============================================
# MODE 2: NEW VIDEO INSPECTION
# ============================================

elif app_mode == "🎥 New Video Inspection":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("🎥 Video Property Inspection with Defactra AI")
    st.info("👉 Upload a video walkthrough and let AI analyze every frame for defects!")
    st.markdown('</div>', unsafe_allow_html=True)

    # Property Information
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🏠 Property Information")
    col1, col2 = st.columns(2)

    with col1:
        property_address = st.text_input("📍 Address", placeholder="123 Main Street", key="video_address")
        property_city = st.text_input("🌆 City", placeholder="Trivandrum", key="video_city")
        property_type = st.selectbox("🏗️ Type", ["apartment", "villa", "house", "commercial"], key="video_type")

    with col2:
        bedrooms = st.number_input("🛏️ Bedrooms", min_value=1, max_value=10, value=3, key="video_bedrooms")
        area_sqft = st.number_input("📏 Area (sqft)", min_value=100, max_value=10000, value=1200, key="video_area")
        year_built = st.number_input("📅 Year Built", min_value=1900, max_value=2026, value=2020, key="video_year")
    st.markdown('</div>', unsafe_allow_html=True)

    # Room Information
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🚪 Room/Area Information")
    room_name = st.text_input("Area Name", placeholder="Full Property Walkthrough, Kitchen Tour, etc.", key="video_room")
    st.markdown('</div>', unsafe_allow_html=True)

    # Video Upload
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🎥 Upload Inspection Video")

    st.info("""
    **Video Tips:**
    - Walk slowly through the property
    - Keep camera steady
    - Focus on walls, ceilings, floors
    - Good lighting helps detection
    - Supported: MP4, AVI, MOV, MKV
    - Max file size: 200MB
    """)

    uploaded_video = st.file_uploader(
        "Drop video here or click to browse",
        type=['mp4', 'avi', 'mov', 'mkv', 'webm'],
        accept_multiple_files=False,
        key="video_uploader"
    )

    if uploaded_video:
        file_size_mb = len(uploaded_video.getvalue()) / (1024 * 1024)
        st.success(f"✅ Video uploaded: {uploaded_video.name} ({file_size_mb:.1f} MB)")

        # Show video preview
        st.video(uploaded_video)

    st.markdown('</div>', unsafe_allow_html=True)

    # Analysis Settings
    with st.expander("⚙️ Advanced Settings"):
        col1, col2 = st.columns(2)
        with col1:
            frame_interval = st.slider(
                "Frame Sampling Rate",
                min_value=10,
                max_value=60,
                value=30,
                help="Extract 1 frame every N frames (30 = ~1 frame/second for 30fps video)",
                key="video_frame_interval"
            )
        with col2:
            max_frames = st.slider(
                "Maximum Frames to Analyze",
                min_value=20,
                max_value=200,
                value=100,
                help="Limit analysis for faster processing",
                key="video_max_frames"
            )

    # Analyze Button
    if uploaded_video and st.button("🤖 Analyze Video with Defactra AI", type="primary", use_container_width=True, key="analyze_video_btn"):
        if not property_address or not room_name:
            st.error("⚠️ Please fill in Property Address and Area Name")
            st.stop()

        # Save video temporarily
        with st.spinner("📹 Processing video..."):
            temp_video_path = save_uploaded_video(uploaded_video)

            try:
                # Initialize video processor
                processor = VideoProcessor(
                    frame_interval=frame_interval,
                    max_frames=max_frames
                )

                # Get video info
                video_info = processor.get_video_info(temp_video_path)
                st.session_state.video_info = video_info

                # Show video info
                st.info(f"""
                **Video Details:**
                - Duration: {int(video_info['duration'] // 60)}:{int(video_info['duration'] % 60):02d}
                - Resolution: {video_info['width']}x{video_info['height']}
                - Frame Rate: {video_info['fps']:.1f} fps
                - Total Frames: {video_info['total_frames']}
                """)

                # Extract and analyze frames
                progress_text = st.empty()
                progress_bar = st.progress(0)

                def update_progress(progress):
                    progress_text.text(f"🔍 Analyzing frames... {int(progress * 100)}%")
                    progress_bar.progress(progress)

                # Analyze video
                analysis_results = processor.analyze_video_with_ai(
                    temp_video_path,
                    analyze_image_with_gemini,
                    progress_callback=update_progress
                )

                progress_text.empty()
                progress_bar.empty()

                if not analysis_results['success']:
                    st.error(f"❌ Analysis failed: {analysis_results.get('error', 'Unknown error')}")
                    cleanup_temp_file(temp_video_path)
                    st.stop()

                # Store results
                st.session_state.video_analysis_results = analysis_results
                st.session_state.video_analysis_complete = True

                # Generate property in database
                property_id = f"P{str(uuid.uuid4())[:6].upper()}"
                room_id = f"R{str(uuid.uuid4())[:6].upper()}"

                cursor = conn.cursor()

                # Insert property
                cursor.execute("""
                    INSERT INTO properties (property_id, address, city, property_type, bedrooms, area_sqft, year_built)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (property_id, property_address, property_city, property_type, bedrooms, area_sqft, year_built))

                # Insert room
                cursor.execute("""
                    INSERT INTO rooms (room_id, property_id, room_name, room_type, floor_number)
                    VALUES (%s, %s, %s, %s, %s)
                """, (room_id, property_id, room_name, 'video_inspection', 0))

                # Store detections
                for detection in analysis_results.get('all_detections', []):
                    detection_id = f"DET{str(uuid.uuid4())[:6].upper()}"
                    finding_id = f"F{str(uuid.uuid4())[:6].upper()}"

                    escaped_description = detection["description"].replace("'", "''")
                    escaped_object = detection["detected_object"].replace("'", "''")

                    cursor.execute("""
                        INSERT INTO ai_detections 
                        (detection_id, upload_id, detected_object, confidence_score, bounding_box, severity, description, detection_timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP())
                    """, (detection_id, 'VIDEO_ANALYSIS', escaped_object, detection["confidence_score"],
                          f"Frame {detection['frame_number']} @ {detection['timestamp_formatted']}",
                          detection["severity"], escaped_description))

                    cursor.execute("""
                        INSERT INTO findings 
                        (finding_id, room_id, inspection_date, finding_text, inspector_notes, detection_id, upload_id, ai_generated)
                        VALUES (%s, %s, CURRENT_DATE(), %s, %s, %s, %s, %s)
                    """, (finding_id, room_id, escaped_object,
                          f"{escaped_description} [Frame {detection['frame_number']} @ {detection['timestamp_formatted']}]",
                          detection_id, 'VIDEO_ANALYSIS', True))

                conn.commit()

                # Prepare data for PDF
                st.session_state.stored_property_data = {
                    'property_id': property_id,
                    'address': property_address,
                    'city': property_city,
                    'property_type': property_type,
                    'bedrooms': int(bedrooms),
                    'area_sqft': int(area_sqft),
                    'year_built': int(year_built),
                    'room_name': room_name,
                    'overall_score': analysis_results['average_score'],
                    'usability': 'video_inspection'
                }

                # Extract key frames with defects
                key_frames = []
                frames_data = processor.extract_frames(temp_video_path)

                for frame_analysis in analysis_results.get('frame_analyses', [])[:10]:  # Top 10 frames
                    if len(frame_analysis['detections']) > 0:
                        # Find matching frame
                        for frame_img, timestamp, frame_num in frames_data:
                            if frame_num == frame_analysis['frame_number']:
                                key_frames.append((frame_img.copy(), timestamp, frame_analysis['detections']))
                                break

                st.session_state.video_key_frames = key_frames
                st.session_state.current_property_id = property_id
                st.session_state.show_pdf_button = True

                # Cleanup
                cleanup_temp_file(temp_video_path)

                st.success("🎉 Video Analysis Complete!")
                st.balloons()

                # Show results
                st.markdown("---")
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-value">{analysis_results["frames_analyzed"]}</div><div class="metric-label">📸 Frames</div></div>',
                        unsafe_allow_html=True)
                with col2:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-value">{analysis_results["total_defects"]}</div><div class="metric-label">🔍 Defects</div></div>',
                        unsafe_allow_html=True)
                with col3:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-value">{analysis_results["average_score"]}/100</div><div class="metric-label">🎯 Score</div></div>',
                        unsafe_allow_html=True)
                with col4:
                    st.markdown(
                        f'<div class="metric-card"><div class="metric-value">{analysis_results["unique_defect_types"]}</div><div class="metric-label">📊 Unique Issues</div></div>',
                        unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

                # Show defect timeline
                st.subheader("🕐 Defect Timeline")
                defect_timeline = analysis_results.get('defect_timeline', {})

                if defect_timeline:
                    for defect_type, info in list(defect_timeline.items())[:5]:
                        severity = info['severity']
                        card_class = f"{severity}-card"

                        st.markdown(f"""
                        <div class="defect-card {card_class}">
                            <h4>{info['defect_type'].upper()}</h4>
                            <p><strong>Severity:</strong> {severity.upper()}</p>
                            <p><strong>Detected:</strong> {info['frame_count']} times</p>
                            <p><strong>Timeline:</strong> {format_timestamp(info['first_seen'])} - {format_timestamp(info['last_seen'])}</p>
                            <p><strong>Avg Confidence:</strong> {info['avg_confidence']:.1f}%</p>
                        </div>
                        """, unsafe_allow_html=True)

                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                cleanup_temp_file(temp_video_path)
                import traceback

                with st.expander("Error Details"):
                    st.code(traceback.format_exc())

    # PDF Generation for Video
    if st.session_state.show_pdf_button and st.session_state.video_analysis_complete:
        st.markdown("---")
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📄 Generate Video Inspection Report")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"📥 Ready to generate video PDF for property: **{st.session_state.current_property_id}**")
            st.caption(f"Report includes video analysis with {len(st.session_state.video_key_frames)} key frames in {st.session_state.language.title()}")

        with col2:
            if st.button("🎨 Generate PDF Report", type="primary", use_container_width=True, key="video_pdf"):
                with st.spinner("Creating video report..."):
                    try:
                        pdf_buffer = generate_video_pdf_report(
                            property_data=st.session_state.stored_property_data,
                            video_info=st.session_state.video_info,
                            video_analysis=st.session_state.video_analysis_results,
                            key_frames=st.session_state.video_key_frames,
                            language=st.session_state.language
                        )

                        st.success("✅ PDF Generated!")

                        filename = f"Defactra_Video_Report_{st.session_state.current_property_id}_{st.session_state.language}.pdf"
                        st.download_button(
                            label="⬇️ Download Video Report PDF",
                            data=pdf_buffer.getvalue(),
                            file_name=filename,
                            mime="application/pdf",
                            use_container_width=True,
                            key="download_video_pdf"
                        )
                        st.balloons()

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        import traceback

                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.info(
            f"📊 **Next Step:** Go to 'View Existing Reports' mode and select property **{st.session_state.current_property_id}** to see the full analysis!")

# ============================================
# MODE 3: VIEW REPORTS (REMAINS UNCHANGED)
# ============================================

elif app_mode == "📊 View Existing Reports":

    if selected_property is None:
        st.warning("⚠️ No properties available. Please use 'New Inspection' mode to upload images first.")
    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard",
            "🤖 AI Detection",
            "🖼️ Annotated Images",
            "📈 Risk Analysis",
            "📝 Summary Report"
        ])

        # TAB 1: DASHBOARD OVERVIEW
        with tab1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.header("📊 Property Overview Dashboard")

            prop_risk = pd.read_sql(f"""
                SELECT * FROM property_risk_scores 
                WHERE property_id = '{selected_property}'
            """, conn)
            prop_risk.columns = prop_risk.columns.str.lower()

            if not prop_risk.empty:
                risk_data = prop_risk.iloc[0]

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{risk_data['property_risk_score']}/100</div>
                        <div class="metric-label">🎯 Risk Score (Grade: {risk_data['property_grade']})</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{risk_data['property_risk_category']}</div>
                        <div class="metric-label">⚠️ Risk Level</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{int(risk_data['total_defects'])}</div>
                        <div class="metric-label">🔍 Total Defects ({int(risk_data['total_critical'])} Critical)</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{int(risk_data['high_risk_rooms'])}/{int(risk_data['total_rooms'])}</div>
                        <div class="metric-label">🚪 High Risk Rooms</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("---")

                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("🚪 Room-by-Room Breakdown")

                rooms_df = pd.read_sql(f"""
                    SELECT 
                        room_name,
                        room_type,
                        room_risk_score,
                        risk_category,
                        total_defects,
                        critical_count,
                        high_count,
                        medium_count
                    FROM room_risk_scores
                    WHERE property_id = '{selected_property}'
                    ORDER BY room_risk_score DESC
                """, conn)
                rooms_df.columns = rooms_df.columns.str.lower()

                def highlight_risk(row):
                    if row['risk_category'] == 'High Risk':
                        return ['background-color: rgba(255, 0, 102, 0.2)'] * len(row)
                    elif row['risk_category'] == 'Medium Risk':
                        return ['background-color: rgba(255, 204, 0, 0.2)'] * len(row)
                    else:
                        return ['background-color: rgba(0, 255, 153, 0.2)'] * len(row)

                styled_rooms = rooms_df.style.apply(highlight_risk, axis=1)
                st.dataframe(styled_rooms, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("---")
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("📊 Risk Score Visualization")

                fig = px.bar(
                    rooms_df,
                    x='room_name',
                    y='room_risk_score',
                    color='risk_category',
                    color_discrete_map={
                        'High Risk': '#ff0066',
                        'Medium Risk': '#ffcc00',
                        'Low Risk': '#00ff99'
                    },
                    title="Risk Score by Room",
                    labels={'room_name': 'Room', 'room_risk_score': 'Risk Score (0-100)'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#d0d0ff'
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No risk analysis data available for this property yet.")

        # TAB 2: AI DETECTION DETAILS
        with tab2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.header("🤖 AI Detection Results")

            # Get all AI detections for this property
            detections_df = pd.read_sql(f"""
                SELECT 
                    ad.detected_object,
                    ad.confidence_score,
                    ad.severity,
                    ad.description,
                    ad.detection_timestamp,
                    ui.room_name,
                    ui.upload_timestamp
                FROM ai_detections ad
                JOIN uploaded_images ui ON ad.upload_id = ui.upload_id
                WHERE ui.property_id = '{selected_property}'
                ORDER BY ad.detection_timestamp DESC
            """, conn)
            detections_df.columns = detections_df.columns.str.lower()

            if not detections_df.empty:
                # Summary metrics
                col1, col2, col3 = st.columns(3)

                with col1:
                    total_detections = len(detections_df)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{total_detections}</div>
                        <div class="metric-label">🔍 Total Detections</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    avg_confidence = detections_df['confidence_score'].mean()
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{avg_confidence:.1f}%</div>
                        <div class="metric-label">🎯 Avg Confidence</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    unique_rooms = detections_df['room_name'].nunique()
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{unique_rooms}</div>
                        <div class="metric-label">🚪 Rooms Inspected</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # Group detections by severity
                st.subheader("📋 Detection Details by Severity")

                critical = detections_df[detections_df['severity'] == 'critical']
                high = detections_df[detections_df['severity'] == 'high']
                medium = detections_df[detections_df['severity'] == 'medium']
                low = detections_df[detections_df['severity'] == 'low']

                if len(critical) > 0:
                    st.markdown("### 🔴 Critical Issues")
                    for _, detection in critical.iterrows():
                        st.markdown(f"""
                        <div class="defect-card critical-card">
                            <h4>{detection['detected_object'].upper()}</h4>
                            <p><strong>Room:</strong> {detection['room_name']}</p>
                            <p><strong>Confidence:</strong> {detection['confidence_score']:.1f}%</p>
                            <p><strong>Description:</strong> {detection['description']}</p>
                            <p><strong>Detected:</strong> {detection['detection_timestamp']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                if len(high) > 0:
                    st.markdown("### 🟠 High Priority Issues")
                    for _, detection in high.iterrows():
                        st.markdown(f"""
                        <div class="defect-card high-card">
                            <h4>{detection['detected_object'].title()}</h4>
                            <p><strong>Room:</strong> {detection['room_name']}</p>
                            <p><strong>Confidence:</strong> {detection['confidence_score']:.1f}%</p>
                            <p><strong>Description:</strong> {detection['description']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                if len(medium) > 0:
                    with st.expander("🟡 Medium Priority Issues"):
                        for _, detection in medium.iterrows():
                            st.markdown(f"""
                            <div class="defect-card medium-card">
                                <h4>{detection['detected_object'].title()}</h4>
                                <p><strong>Room:</strong> {detection['room_name']}</p>
                                <p><strong>Confidence:</strong> {detection['confidence_score']:.1f}%</p>
                                <p><strong>Description:</strong> {detection['description']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                if len(low) > 0:
                    with st.expander("🟢 Low Priority Issues"):
                        for _, detection in low.iterrows():
                            st.markdown(f"""
                            <div class="defect-card low-card">
                                <h4>{detection['detected_object'].title()}</h4>
                                <p><strong>Room:</strong> {detection['room_name']}</p>
                                <p><strong>Description:</strong> {detection['description']}</p>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("No AI detections found for this property yet.")

            st.markdown('</div>', unsafe_allow_html=True)

        # TAB 3: ANNOTATED IMAGES
        with tab3:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.header("🖼️ Annotated Inspection Images")

            # Fetch images and defects for this property
            images_df = pd.read_sql(f"""
                SELECT 
                    ui.upload_id,
                    ui.room_name,
                    ui.image_data,
                    ui.upload_timestamp
                FROM uploaded_images ui
                WHERE ui.property_id = '{selected_property}'
                ORDER BY ui.upload_timestamp DESC
            """, conn)
            images_df.columns = images_df.columns.str.lower()

            if not images_df.empty:
                st.info(f"📸 Found {len(images_df)} image(s) for this property")

                for idx, img_row in images_df.iterrows():
                    st.markdown(f"### 🏠 {img_row['room_name']} - Image {idx + 1}")
                    st.caption(f"Uploaded: {img_row['upload_timestamp']}")

                    # Get defects for this image
                    defects_df = pd.read_sql(f"""
                        SELECT 
                            detected_object,
                            severity,
                            confidence_score,
                            description
                        FROM ai_detections
                        WHERE upload_id = '{img_row['upload_id']}'
                    """, conn)
                    defects_df.columns = defects_df.columns.str.lower()

                    # Convert defects to list format for annotator
                    defects_list = []
                    for _, defect in defects_df.iterrows():
                        defects_list.append({
                            'detected_object': defect['detected_object'],
                            'severity': defect['severity'],
                            'confidence_score': defect['confidence_score'],
                            'location': f"Detected in {img_row['room_name']}",
                            'description': defect['description']
                        })

                    try:
                        # Decode base64 image
                        image_data = base64.b64decode(img_row['image_data'])
                        original_image = Image.open(io.BytesIO(image_data))

                        # Annotate image with defects
                        annotated_image = annotate_image_with_defects(
                            original_image,
                            defects_list,
                            st.session_state.language
                        )

                        # Display annotated image
                        st.image(annotated_image, use_container_width=True)

                        # Show defect count
                        st.caption(f"🔍 {len(defects_list)} defect(s) marked on this image")

                    except Exception as e:
                        st.error(f"Error displaying image: {e}")

                    st.markdown("---")
            else:
                st.info("No images found for this property. Images may not have been stored during inspection.")

            st.markdown('</div>', unsafe_allow_html=True)

        # TAB 4: RISK ANALYSIS
        with tab4:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.header("📈 Comprehensive Risk Analysis")

            # Get property data
            prop_risk = pd.read_sql(f"""
                SELECT * FROM property_risk_scores 
                WHERE property_id = '{selected_property}'
            """, conn)
            prop_risk.columns = prop_risk.columns.str.lower()

            if not prop_risk.empty:
                risk_data = prop_risk.iloc[0]

                # Risk breakdown
                st.subheader("🎯 Risk Score Breakdown")

                col1, col2 = st.columns(2)

                with col1:
                    # Severity distribution pie chart
                    severity_data = pd.DataFrame({
                        'Severity': ['Critical', 'High', 'Medium', 'Low'],
                        'Count': [
                            int(risk_data['total_critical']),
                            int(risk_data['total_high']),
                            int(risk_data['total_medium']),
                            int(risk_data['total_low'])
                        ]
                    })

                    fig_pie = px.pie(
                        severity_data,
                        values='Count',
                        names='Severity',
                        title='Defects by Severity',
                        color='Severity',
                        color_discrete_map={
                            'Critical': '#ff0066',
                            'High': '#ff6600',
                            'Medium': '#ffcc00',
                            'Low': '#00ff99'
                        }
                    )
                    fig_pie.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#d0d0ff'
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

                with col2:
                    # Risk gauge
                    st.markdown(f"""
                    <div style='text-align: center; padding: 2rem;'>
                        <div style='font-size: 4rem; font-weight: 800; color: #00f5ff;'>
                            {int(risk_data['property_risk_score'])}
                        </div>
                        <div style='font-size: 1.5rem; color: #a0a0ff; margin-top: 1rem;'>
                            Risk Score
                        </div>
                        <div style='font-size: 2rem; font-weight: 700; color: #ff0066; margin-top: 1rem;'>
                            Grade: {risk_data['property_grade']}
                        </div>
                        <div style='font-size: 1.2rem; color: #b0b0ff; margin-top: 1rem;'>
                            {risk_data['property_risk_category']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # Recommendations
                st.subheader("💡 Recommendations")

                if risk_data['property_risk_category'] == 'High Risk':
                    st.error("""
                    **⚠️ HIGH RISK PROPERTY - Immediate Action Required**

                    - Schedule professional inspection immediately
                    - Address all critical issues before occupancy
                    - Budget for significant repairs
                    - Consider structural engineer consultation
                    """)
                elif risk_data['property_risk_category'] == 'Medium Risk':
                    st.warning("""
                    **⚡ MEDIUM RISK PROPERTY - Attention Needed**

                    - Plan repairs within 1-3 months
                    - Get quotes from qualified contractors
                    - Monitor high-priority issues closely
                    - Schedule follow-up inspection after repairs
                    """)
                else:
                    st.success("""
                    **✅ LOW RISK PROPERTY - Good Condition**

                    - Maintain regular inspection schedule
                    - Address minor issues as routine maintenance
                    - Keep documentation of all repairs
                    - Consider preventive maintenance plan
                    """)
            else:
                st.info("No risk analysis data available yet.")

            st.markdown('</div>', unsafe_allow_html=True)

        # TAB 5: SUMMARY REPORT WITH PDF DOWNLOAD
        with tab5:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.header("📝 Executive Summary Report")

            # Get property info
            prop_info = pd.read_sql(f"""
                SELECT * FROM properties 
                WHERE property_id = '{selected_property}'
            """, conn)
            prop_info.columns = prop_info.columns.str.lower()

            # Get risk info
            risk_info = pd.read_sql(f"""
                SELECT * FROM property_risk_scores 
                WHERE property_id = '{selected_property}'
            """, conn)
            risk_info.columns = risk_info.columns.str.lower()

            if not prop_info.empty and not risk_info.empty:
                prop = prop_info.iloc[0]
                risk = risk_info.iloc[0]

                # Property details
                st.subheader("🏠 Property Information")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
                    - **Address:** {prop['address']}
                    - **City:** {prop['city']}
                    - **Type:** {prop['property_type'].title()}
                    """)

                with col2:
                    st.markdown(f"""
                    - **Bedrooms:** {int(prop['bedrooms'])}
                    - **Area:** {int(prop['area_sqft'])} sq ft
                    - **Year Built:** {int(prop['year_built'])}
                    """)

                st.markdown("---")

                # Inspection summary
                st.subheader("🔍 Inspection Summary")

                st.markdown(f"""
                **Overall Assessment:** {risk['property_risk_category']} (Grade: {risk['property_grade']})

                **Risk Score:** {int(risk['property_risk_score'])}/100

                **Defects Found:**
                - 🔴 Critical: {int(risk['total_critical'])}
                - 🟠 High: {int(risk['total_high'])}
                - 🟡 Medium: {int(risk['total_medium'])}
                - 🟢 Low: {int(risk['total_low'])}
                - **Total:** {int(risk['total_defects'])}

                **Rooms Inspected:** {int(risk['total_rooms'])}
                **High Risk Rooms:** {int(risk['high_risk_rooms'])}
                """)

                st.markdown("---")

                # PDF Download Section
                st.subheader("📄 Download Professional Report")

                col1, col2 = st.columns([2, 1])
                with col1:
                    st.info(f"📥 Generate a comprehensive PDF report in {st.session_state.language.title()}")

                with col2:
                    if st.button("🎨 Generate PDF", type="primary", use_container_width=True, key="existing_report_pdf"):
                        with st.spinner("Generating comprehensive report..."):
                            try:
                                # Prepare property data
                                prop_data = {
                                    'property_id': selected_property,
                                    'address': prop['address'],
                                    'city': prop['city'],
                                    'property_type': prop['property_type'],
                                    'bedrooms': int(prop['bedrooms']),
                                    'area_sqft': int(prop['area_sqft']),
                                    'year_built': int(prop['year_built']),
                                    'room_name': 'Multiple Rooms',
                                    'overall_score': int(risk['property_risk_score']),
                                    'usability': risk['property_risk_category'].lower()
                                }

                                # Fetch defects
                                defects_df = pd.read_sql(f"""
                                    SELECT 
                                        ad.detected_object,
                                        ad.severity,
                                        ad.confidence_score,
                                        ad.description,
                                        ui.room_name
                                    FROM ai_detections ad
                                    JOIN uploaded_images ui ON ad.upload_id = ui.upload_id
                                    WHERE ui.property_id = '{selected_property}'
                                    ORDER BY 
                                        CASE ad.severity
                                            WHEN 'critical' THEN 1
                                            WHEN 'high' THEN 2
                                            WHEN 'medium' THEN 3
                                            WHEN 'low' THEN 4
                                            ELSE 5
                                        END
                                """, conn)
                                defects_df.columns = defects_df.columns.str.lower()

                                defects = []
                                for _, row in defects_df.iterrows():
                                    defects.append({
                                        'detected_object': row['detected_object'] or 'Issue Found',
                                        'description': row['description'] or 'No description available',
                                        'severity': row['severity'] or 'medium',
                                        'confidence_score': row['confidence_score'] or 75.0,
                                        'location': row['room_name'],
                                        'repair_priority': 'routine',
                                        'estimated_impact': 'Requires attention'
                                    })

                                # Fetch images
                                images_df = pd.read_sql(f"""
                                    SELECT image_data
                                    FROM uploaded_images
                                    WHERE property_id = '{selected_property}'
                                    LIMIT 5
                                """, conn)
                                images_df.columns = images_df.columns.str.lower()

                                images = []
                                for _, img_row in images_df.iterrows():
                                    try:
                                        image_data = base64.b64decode(img_row['image_data'])
                                        image = Image.open(io.BytesIO(image_data))
                                        images.append(image)
                                    except:
                                        pass

                                # If no images, create placeholder
                                if not images:
                                    placeholder = Image.new('RGB', (800, 600), color='#1a1a2e')
                                    from PIL import ImageDraw, ImageFont

                                    draw = ImageDraw.Draw(placeholder)
                                    try:
                                        font = ImageFont.truetype(
                                            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
                                    except:
                                        font = ImageFont.load_default()
                                    text = f"Property: {selected_property}\n{len(defects)} Defects Found"
                                    draw.text((100, 250), text, fill='#00f5ff', font=font)
                                    images = [placeholder]

                                # Generate PDF
                                pdf_buffer = generate_pdf_report(
                                    property_data=prop_data,
                                    defects=defects,
                                    images=images,
                                    language=st.session_state.language
                                )

                                st.success("✅ Report generated!")

                                # Download button
                                filename = f"Defactra_Report_{selected_property}_{st.session_state.language}.pdf"
                                st.download_button(
                                    label="⬇️ Download PDF Report",
                                    data=pdf_buffer.getvalue(),
                                    file_name=filename,
                                    mime="application/pdf",
                                    use_container_width=True,
                                    key="download_existing_pdf"
                                )

                                st.balloons()

                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                                import traceback

                                with st.expander("Error Details"):
                                    st.code(traceback.format_exc())

                st.markdown("---")

                # Text report download
                report_data = f"""
PROPERTY INSPECTION REPORT
Generated by Defactra AI
{'=' * 50}

PROPERTY DETAILS
Address: {prop['address']}
City: {prop['city']}
Type: {prop['property_type'].title()}
Bedrooms: {int(prop['bedrooms'])}
Area: {int(prop['area_sqft'])} sq ft
Year Built: {int(prop['year_built'])}

RISK ASSESSMENT
Overall Risk: {risk['property_risk_category']}
Risk Score: {int(risk['property_risk_score'])}/100
Property Grade: {risk['property_grade']}

DEFECTS SUMMARY
Critical Issues: {int(risk['total_critical'])}
High Priority: {int(risk['total_high'])}
Medium Priority: {int(risk['total_medium'])}
Low Priority: {int(risk['total_low'])}
Total Defects: {int(risk['total_defects'])}

ROOMS ANALYZED
Total Rooms: {int(risk['total_rooms'])}
High Risk Rooms: {int(risk['high_risk_rooms'])}

{'=' * 50}
Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Powered by Defactra AI
"""

                st.download_button(
                    label="📥 Download Text Report",
                    data=report_data,
                    file_name=f"defactra_report_{selected_property}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.info("No summary data available yet.")

            st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>🔍 Defactra AI | Powered by Snowflake & Google Gemini AI</p>
    <p>Advanced AI-powered defect detection with severity analysis and risk assessment</p>
    <p>📸 Image & 🎥 Video Inspection | 📄 Professional multilingual PDF reports</p>
</div>
""", unsafe_allow_html=True)