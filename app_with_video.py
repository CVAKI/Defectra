"""
Defactra AI - Enhanced with Video Processing
Property inspection with both image and video analysis
"""

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

# Import modules
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
    page_title="Defactra AI - Image & Video",
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
# CUSTOM CSS (same as original)
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=Space+Mono:wght@400;700&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); background-attachment: fixed; }
    .main-header { font-size: 3.5rem; font-weight: 800; text-align: center; padding: 2rem 1rem; background: linear-gradient(120deg, #00f5ff, #0080ff, #ff00ff, #ff0080); background-size: 300% 300%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: gradientShift 8s ease infinite; }
    @keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .glass-card { background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(20px); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.15); padding: 2rem; margin: 1rem 0; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); }
    .metric-card { background: linear-gradient(135deg, rgba(0, 245, 255, 0.1) 0%, rgba(255, 0, 255, 0.1) 100%); border: 2px solid rgba(0, 245, 255, 0.3); border-radius: 16px; padding: 1.5rem; text-align: center; }
    .metric-value { font-size: 2.5rem; font-weight: 800; color: #00f5ff; text-shadow: 0 0 20px rgba(0, 245, 255, 0.5); font-family: 'Space Mono', monospace; }
    .metric-label { font-size: 0.9rem; color: #b0b0ff; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.5rem; font-weight: 600; }
    .defect-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); padding: 1.5rem; border-radius: 16px; margin: 1rem 0; border-left: 5px solid; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3); }
    .critical-card { border-left-color: #ff0066; background: linear-gradient(90deg, rgba(255, 0, 102, 0.1), transparent); }
    .high-card { border-left-color: #ff6600; background: linear-gradient(90deg, rgba(255, 102, 0, 0.1), transparent); }
    .medium-card { border-left-color: #ffcc00; background: linear-gradient(90deg, rgba(255, 204, 0, 0.1), transparent); }
    .low-card { border-left-color: #00ff99; background: linear-gradient(90deg, rgba(0, 255, 153, 0.1), transparent); }
    h1, h2, h3 { color: #00f5ff; font-weight: 700; }
    p, label, span { color: #d0d0ff; }
    .stButton > button { background: linear-gradient(135deg, #00f5ff, #0080ff); color: white; border: none; border-radius: 12px; padding: 0.8rem 2rem; font-weight: 700; text-transform: uppercase; box-shadow: 0 4px 16px rgba(0, 128, 255, 0.4); }
    .video-badge { display: inline-block; background: linear-gradient(135deg, #FF6600, #FF0066); color: white; padding: 0.3rem 0.8rem; border-radius: 8px; font-size: 0.8rem; font-weight: 700; margin-left: 0.5rem; }
</style>
""", unsafe_allow_html=True)


# ============================================
# CONNECTION
# ============================================
@st.cache_resource
def get_snowflake_connection():
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
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


# ============================================
# HEADER
# ============================================
st.markdown('<h1 class="main-header">Defactra AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="text-align: center; color: #a0a0ff; font-size: 1.1rem;">🎥 Image & Video Inspection Platform <span class="video-badge">NEW: VIDEO</span></p>',
    unsafe_allow_html=True
)

# Language selector
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    language_options = {
        '🇬🇧 English': 'english',
        '🇮🇳 മലയാളം': 'malayalam',
        '🇮🇳 हिंदी': 'hindi'
    }
    selected_lang = st.selectbox(
        "🌐 Language",
        options=list(language_options.keys()),
        index=list(language_options.values()).index(st.session_state.language)
    )
    st.session_state.language = language_options[selected_lang]

st.markdown("---")

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h2 style='color: #00f5ff; margin: 0;'>🔍 DEFACTRA</h2>
        <p style='color: #a0a0ff; font-size: 0.8rem;'>IMAGE & VIDEO AI</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔍 Navigation")

    app_mode = st.radio(
        "Choose Mode:",
        [
            "📊 View Existing Reports",
            "📸 New Image Inspection",
            "🎥 New Video Inspection"
        ],
        index=0
    )

# ============================================
# MODE 3: NEW VIDEO INSPECTION
# ============================================
if app_mode == "🎥 New Video Inspection":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("🎥 Video Property Inspection with Defactra AI")
    st.info("👉 Upload a video walkthrough and let AI analyze every frame for defects!")
    st.markdown('</div>', unsafe_allow_html=True)

    # Property Information
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
    st.subheader("🚪 Room/Area Information")
    room_name = st.text_input("Area Name", placeholder="Full Property Walkthrough, Kitchen Tour, etc.")
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
        accept_multiple_files=False
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
                help="Extract 1 frame every N frames (30 = ~1 frame/second for 30fps video)"
            )
        with col2:
            max_frames = st.slider(
                "Maximum Frames to Analyze",
                min_value=20,
                max_value=200,
                value=100,
                help="Limit analysis for faster processing"
            )

    # Analyze Button
    if uploaded_video and st.button("🤖 Analyze Video with Defactra AI", type="primary", use_container_width=True):
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
                        use_container_width=True
                    )
                    st.balloons()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback

                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())

        st.markdown('</div>', unsafe_allow_html=True)

# Note: Original image inspection mode would go here (Mode 2)
# Original view reports mode would go here (Mode 1)

elif app_mode == "📸 New Image Inspection":
    st.info("📸 Image inspection mode - Use your existing app.py code here")
    st.write("This would be your original image upload and analysis flow")

elif app_mode == "📊 View Existing Reports":
    st.info("📊 View reports mode - Use your existing app.py code here")
    st.write("This would show existing property reports from database")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #8080ff;'>
    <p>🔍 Defactra AI | 📸 Image & 🎥 Video Inspection Platform</p>
    <p>Powered by Snowflake & Google Gemini AI</p>
</div>
""", unsafe_allow_html=True)