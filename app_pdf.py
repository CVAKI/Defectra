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
if 'show_pdf_button' not in st.session_state:
    st.session_state.show_pdf_button = False
if 'current_property_id' not in st.session_state:
    st.session_state.current_property_id = None

# ============================================
# ENHANCED CUSTOM CSS WITH ANIMATIONS
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=Space+Mono:wght@400;700&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); background-attachment: fixed; }
    .main-header { font-size: 3.5rem; font-weight: 800; text-align: center; padding: 2rem 1rem; background: linear-gradient(120deg, #00f5ff, #0080ff, #ff00ff, #ff0080); background-size: 300% 300%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: gradientShift 8s ease infinite; letter-spacing: 0.05em; text-transform: uppercase; position: relative; }
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
    .stButton > button { background: linear-gradient(135deg, #00f5ff, #0080ff); color: white; border: none; border-radius: 12px; padding: 0.8rem 2rem; font-weight: 700; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 0.05em; box-shadow: 0 4px 16px rgba(0, 128, 255, 0.4); }
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
    """AI-Powered Property Inspection"""
    return analyze_image_with_gemini(image)


# ============================================
# HEADER WITH LANGUAGE SELECTOR
# ============================================
st.markdown('<h1 class="main-header">Defactra AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="text-align: center; color: #a0a0ff; font-size: 1.1rem;">Intelligent Defect Detection & Property Risk Analysis Platform</p>',
    unsafe_allow_html=True)

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
        index=list(language_options.values()).index(st.session_state.language),
        key='language_selector'
    )
    st.session_state.language = language_options[selected_lang]

st.markdown("---")

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h2 style='color: #00f5ff; font-weight: 800; margin: 0;'>🔍 DEFACTRA</h2>
        <p style='color: #a0a0ff; font-size: 0.8rem; margin: 0;'>AI-POWERED INSPECTION</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔍 Navigation")

    app_mode = st.radio(
        "Choose Mode:",
        ["📊 View Existing Reports", "📸 New Inspection (Upload Images)"],
        index=0
    )

    st.markdown("---")

    if app_mode == "📊 View Existing Reports":
        st.markdown("### 🏢 Property Selection")
        properties_df = pd.read_sql("SELECT property_id, address, city FROM properties ORDER BY property_id", conn)
        properties_df.columns = properties_df.columns.str.lower()

        if len(properties_df) > 0:
            selected_property = st.selectbox(
                "Select Property:",
                properties_df['property_id'].tolist(),
                format_func=lambda x: properties_df[properties_df['property_id'] == x]['address'].iloc[0]
            )
            prop_info = properties_df[properties_df['property_id'] == selected_property].iloc[0]
            st.markdown(f"**📍 Location:** {prop_info['city']}")
            st.markdown(f"**🆔 ID:** {selected_property}")

            if st.button("🔄 Refresh Data", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()
        else:
            st.warning("No properties found.")
            selected_property = None

# ============================================
# MODE 1: NEW INSPECTION
# ============================================
if app_mode == "📸 New Inspection (Upload Images)":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("📸 New Property Inspection with Defactra AI")
    st.info("👉 Upload property images and let Defactra AI detect defects automatically!")
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
    st.subheader("🚪 Room Information")
    col1, col2 = st.columns(2)
    with col1:
        room_name = st.text_input("Room Name", placeholder="Kitchen, Master Bedroom, etc.")
    with col2:
        room_type = st.selectbox("Room Type", ["bedroom", "kitchen", "bathroom", "living", "balcony", "other"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Image Upload
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📤 Upload Inspection Images")
    uploaded_files = st.file_uploader(
        "Drop images here or click to browse",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} image(s) uploaded")
        cols = st.columns(min(len(uploaded_files), 4))
        for idx, uploaded_file in enumerate(uploaded_files[:4]):
            with cols[idx]:
                image = Image.open(uploaded_file)
                st.image(image, caption=f"Image {idx + 1}", use_container_width=True)
        if len(uploaded_files) > 4:
            st.info(f"...and {len(uploaded_files) - 4} more image(s)")

    st.markdown('</div>', unsafe_allow_html=True)

    # Analyze Button
    if uploaded_files and st.button("🤖 Analyze with Defactra AI", type="primary", use_container_width=True):
        if not property_address or not room_name:
            st.error("⚠️ Please fill in Property Address and Room Name")
            st.stop()

        with st.spinner("🔍 Analyzing images..."):
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

                    uploaded_file.seek(0)
                    image = Image.open(uploaded_file)
                    processed_images.append(image.copy())  # IMPORTANT: Use .copy()

                    image_base64 = image_to_base64(image)
                    uploaded_file.seek(0)
                    file_size_kb = len(uploaded_file.read()) / 1024
                    uploaded_file.seek(0)
                    image_format = image.format.lower() if image.format else 'png'

                    # AI Analysis
                    analysis_result = analyze_image_with_ai(image)

                    if not analysis_result["is_property"]:
                        non_property_count += 1
                        st.warning(f"⚠️ Image {idx + 1}: {analysis_result['message']}")
                        continue

                    upload_id = f"UPL{str(uuid.uuid4())[:6].upper()}"

                    cursor.execute("""
                        INSERT INTO uploaded_images 
                        (upload_id, property_id, room_name, upload_timestamp, image_data, image_format, file_size_kb, uploaded_by)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP(), %s, %s, %s, %s)
                    """, (upload_id, property_id, room_name, image_base64, image_format, int(file_size_kb), 'web_user'))

                    for detection in analysis_result["detections"]:
                        detection_id = f"DET{str(uuid.uuid4())[:6].upper()}"
                        finding_id = f"F{str(uuid.uuid4())[:6].upper()}"

                        escaped_description = detection["description"].replace("'", "''")
                        escaped_object = detection["detected_object"].replace("'", "''")

                        cursor.execute("""
                            INSERT INTO ai_detections 
                            (detection_id, upload_id, detected_object, confidence_score, bounding_box, severity, description, detection_timestamp)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP())
                        """, (detection_id, upload_id, escaped_object, detection["confidence_score"], '',
                              detection["severity"], escaped_description))

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

                # CRITICAL: Store data in session state IMMEDIATELY
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
                    st.session_state.show_pdf_button = True
                    st.session_state.current_property_id = property_id

                    st.success(f"🎉 Analysis Complete!")
                    st.balloons()

                    # Show metrics
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(
                            f'<div class="metric-card"><div class="metric-value">{len(uploaded_files) - non_property_count}</div><div class="metric-label">📸 Images</div></div>',
                            unsafe_allow_html=True)
                    with col2:
                        st.markdown(
                            f'<div class="metric-card"><div class="metric-value">{len(all_findings)}</div><div class="metric-label">🔍 Defects</div></div>',
                            unsafe_allow_html=True)
                    with col3:
                        st.markdown(
                            f'<div class="metric-card"><div class="metric-value">{all_findings[0]["overall_score"]}/100</div><div class="metric-label">🎯 Score</div></div>',
                            unsafe_allow_html=True)
                    with col4:
                        st.markdown(
                            f'<div class="metric-card"><div class="metric-value">{all_findings[0]["usability"].split("-")[0].strip()}</div><div class="metric-label">📊 Usability</div></div>',
                            unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Show findings
                    st.markdown("---")
                    st.subheader("🔍 Detection Results")

                    critical = [f for f in all_findings if f['severity'] == 'critical']
                    high = [f for f in all_findings if f['severity'] == 'high']

                    if critical:
                        st.markdown("### 🔴 CRITICAL Issues")
                        for i, f in enumerate(critical, 1):
                            st.markdown(f"""
                            <div class="defect-card critical-card">
                                <h4>{i}. {f['detected_object'].upper()}</h4>
                                <p><strong>Location:</strong> {f['location']}</p>
                                <p><strong>Confidence:</strong> {f['confidence_score']:.1f}%</p>
                                <p><strong>Description:</strong> {f['description']}</p>
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
                                <p><strong>Description:</strong> {f['description']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    # Force rerun to show PDF button
                    st.rerun()

                else:
                    st.error("❌ No valid property images found.")

            except Exception as e:
                st.error(f"❌ Error: {e}")
                conn.rollback()
                import traceback

                with st.expander("Error Details"):
                    st.code(traceback.format_exc())

    # PDF GENERATION SECTION - Shows AFTER analysis is complete
    if st.session_state.show_pdf_button and st.session_state.stored_property_data:
        st.markdown("---")
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📄 Generate Professional PDF Report")

        st.success(f"✅ Ready to generate PDF for property: {st.session_state.current_property_id}")
        st.info(
            f"📊 Report will include {len(st.session_state.stored_images)} images and {len(st.session_state.stored_defects)} defects")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Language:** {st.session_state.language.title()}")
            st.write(f"**Property:** {st.session_state.stored_property_data['address']}")

        with col2:
            if st.button("🎨 Generate PDF", type="primary", use_container_width=True, key="gen_pdf_btn"):
                with st.spinner("Creating PDF report..."):
                    try:
                        # Generate PDF
                        pdf_buffer = generate_pdf_report(
                            property_data=st.session_state.stored_property_data,
                            defects=st.session_state.stored_defects,
                            images=st.session_state.stored_images,
                            language=st.session_state.language
                        )

                        st.success("✅ PDF Generated Successfully!")

                        # Download button
                        filename = f"Defactra_Report_{st.session_state.current_property_id}_{st.session_state.language}.pdf"
                        st.download_button(
                            label="⬇️ Download PDF Report",
                            data=pdf_buffer.getvalue(),
                            file_name=filename,
                            mime="application/pdf",
                            use_container_width=True,
                            key="dl_pdf_btn"
                        )

                        st.balloons()

                    except Exception as e:
                        st.error(f"❌ PDF Generation Error: {e}")
                        import traceback

                        with st.expander("🔍 Error Details"):
                            st.code(traceback.format_exc())

        st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# MODE 2: VIEW REPORTS (Simplified for space)
# ============================================
elif app_mode == "📊 View Existing Reports":
    if selected_property is None:
        st.warning("⚠️ No properties available.")
    else:
        st.header(f"📊 Property: {selected_property}")
        st.info("Full view reports functionality - Use the fixed complete version for all features")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #8080ff;'>
    <p>🔍 Defactra AI | Powered by Snowflake & Google Gemini AI</p>
    <p>📄 Professional multilingual PDF reports</p>
</div>
""", unsafe_allow_html=True)