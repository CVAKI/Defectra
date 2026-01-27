import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
from PIL import Image
import io
import base64
from datetime import datetime
import uuid

# ============================================
# PAGE CONFIGURATION (KEEP AS IS)
# ============================================
st.set_page_config(
    page_title="Property Inspection AI",
    page_icon="🏠",
    layout="wide"
)

# ============================================
# CUSTOM CSS (KEEP AS IS)
# ============================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stAlert {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
    }
    .upload-section {
        background-color: #f0f8ff;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #1f77b4;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# CONNECTION (KEEP AS IS)
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
# NEW HELPER FUNCTIONS
# ============================================

def image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def analyze_image_with_ai(image):
    """
    DEMO AI Detection - Replace with real AI later
    """
    # Simulated detections for now
    import random

    defects = ['crack', 'damp', 'wiring', 'leak', 'mold', 'paint']
    severities = ['critical', 'high', 'medium', 'low']

    num_detections = random.randint(1, 3)

    detections = []
    for i in range(num_detections):
        detections.append({
            "detected_object": random.choice(defects),
            "confidence_score": round(random.uniform(60, 95), 1),
            "bounding_box": '{"x": 100, "y": 100, "width": 200, "height": 150}',
            "severity": random.choice(severities),
            "description": f"Detected {random.choice(defects)} with AI vision analysis"
        })

    return detections


# ============================================
# HEADER (KEEP AS IS)
# ============================================
st.markdown('<h1 class="main-header">🏠 Property Inspection AI</h1>', unsafe_allow_html=True)
st.markdown("### AI-Powered Defect Detection & Risk Analysis")
st.markdown("---")

# ============================================
# UPDATED SIDEBAR WITH MODE SELECTION
# ============================================
with st.sidebar:
    st.header("🔍 Navigation")

    # ADD THIS: Mode selector
    app_mode = st.radio(
        "Choose Mode:",
        ["📊 View Existing Reports", "📸 New Inspection (Upload Images)"],
        index=0
    )

    st.markdown("---")

    # Only show property selector in View mode
    if app_mode == "📊 View Existing Reports":
        st.header("🔍 Property Selection")

        # Get all properties (KEEP THIS)
        properties_df = pd.read_sql("""
            SELECT property_id, address, city 
            FROM properties 
            ORDER BY property_id
        """, conn)
        properties_df.columns = properties_df.columns.str.lower()

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

# ============================================
# MODE 1: NEW INSPECTION (NEW FEATURE)
# ============================================

if app_mode == "📸 New Inspection (Upload Images)":
    st.header("📸 New Property Inspection with AI")
    st.info("👉 Upload property images and let AI detect defects automatically!")

    # Property Information Form
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

    st.markdown("---")

    # Room Information
    st.subheader("🚪 Room Information")
    col1, col2 = st.columns(2)

    with col1:
        room_name = st.text_input("Room Name", placeholder="Kitchen, Master Bedroom, etc.")
    with col2:
        room_type = st.selectbox("Room Type", ["bedroom", "kitchen", "bathroom", "living", "balcony", "other"])

    st.markdown("---")

    # Image Upload
    st.subheader("📤 Upload Inspection Images")
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)

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
    if uploaded_files and st.button("🤖 Analyze with AI & Generate Report", type="primary", use_container_width=True):

        # Validation
        if not property_address or not room_name:
            st.error("⚠️ Please fill in Property Address and Room Name")
            st.stop()

        with st.spinner("🔍 AI is analyzing your images... This may take a moment..."):

            # Generate IDs
            property_id = f"P{str(uuid.uuid4())[:6].upper()}"
            room_id = f"R{str(uuid.uuid4())[:6].upper()}"

            try:
                cursor = conn.cursor()

                # Insert property
                cursor.execute(f"""
                    INSERT INTO properties (property_id, address, city, property_type, bedrooms, area_sqft, year_built)
                    VALUES ('{property_id}', '{property_address}', '{property_city}', '{property_type}', 
                            {bedrooms}, {area_sqft}, {year_built})
                """)

                # Insert room
                cursor.execute(f"""
                    INSERT INTO rooms (room_id, property_id, room_name, room_type, floor_number)
                    VALUES ('{room_id}', '{property_id}', '{room_name}', '{room_type}', 0)
                """)

                st.success(f"✅ Property created: {property_id}")

                # Process images
                all_findings = []

                progress_bar = st.progress(0)
                for idx, uploaded_file in enumerate(uploaded_files):
                    progress_bar.progress((idx + 1) / len(uploaded_files))

                    # Read image
                    image = Image.open(uploaded_file)
                    image_base64 = image_to_base64(image)

                    # Generate upload ID
                    upload_id = f"UPL{str(uuid.uuid4())[:6].upper()}"

                    # Store image
                    cursor.execute(f"""
                        INSERT INTO uploaded_images 
                        (upload_id, property_id, room_name, upload_timestamp, image_data, image_format, file_size_kb, uploaded_by)
                        VALUES ('{upload_id}', '{property_id}', '{room_name}', CURRENT_TIMESTAMP(), 
                                'base64_data_truncated', 'png', 100, 'web_user')
                    """)

                    # AI Detection
                    detections = analyze_image_with_ai(image)

                    # Store each detection
                    for detection in detections:
                        detection_id = f"DET{str(uuid.uuid4())[:6].upper()}"
                        finding_id = f"F{str(uuid.uuid4())[:6].upper()}"

                        # Store AI detection
                        cursor.execute(f"""
                            INSERT INTO ai_detections 
                            (detection_id, upload_id, detected_object, confidence_score, bounding_box, severity, description, detection_timestamp)
                            VALUES ('{detection_id}', '{upload_id}', '{detection["detected_object"]}', 
                                    {detection["confidence_score"]}, '{detection["bounding_box"]}', 
                                    '{detection["severity"]}', '{detection["description"]}', CURRENT_TIMESTAMP())
                        """)

                        # Store as finding
                        cursor.execute(f"""
                            INSERT INTO findings 
                            (finding_id, room_id, inspection_date, finding_text, inspector_notes, detection_id, upload_id, ai_generated)
                            VALUES ('{finding_id}', '{room_id}', CURRENT_DATE(), 
                                    '{detection["detected_object"]} detected by AI', 
                                    '{detection["description"]}', 
                                    '{detection_id}', '{upload_id}', TRUE)
                        """)

                        # Store labeled image
                        cursor.execute(f"""
                            INSERT INTO labeled_images 
                            (image_id, finding_id, image_label, metadata)
                            VALUES ('I{str(uuid.uuid4())[:6].upper()}', '{finding_id}', 
                                    '{detection["detected_object"]}', '{detection["description"]}')
                        """)

                        all_findings.append(detection)

                conn.commit()
                progress_bar.empty()

                # Success message
                st.success(f"🎉 Analysis Complete!")
                st.balloons()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📸 Images Analyzed", len(uploaded_files))
                with col2:
                    st.metric("🔍 Defects Found", len(all_findings))
                with col3:
                    st.metric("🆔 Property ID", property_id)

                # Show findings
                st.markdown("---")
                st.subheader("🔍 AI Detection Results")

                for i, finding in enumerate(all_findings, 1):
                    severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(finding['severity'],
                                                                                                  '⚪')
                    st.markdown(f"{i}. {severity_icon} **{finding['detected_object'].upper()}** - "
                                f"{finding['severity'].capitalize()} ({finding['confidence_score']:.1f}% confidence)")
                    st.caption(finding['description'])

                st.markdown("---")
                st.info(
                    f"📊 **Next Step:** Go to 'View Existing Reports' mode and select property **{property_id}** to see the full risk analysis!")

            except Exception as e:
                st.error(f"❌ Error: {e}")
                conn.rollback()

# ============================================
# MODE 2: VIEW REPORTS (YOUR EXISTING CODE - KEEP UNCHANGED)
# ============================================

elif app_mode == "📊 View Existing Reports":

    # PASTE ALL YOUR EXISTING TAB CODE HERE (Dashboard, AI Detection, Risk Analysis, Summary)
    # Keep it EXACTLY as it is now - don't change anything

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "🤖 AI Detection",
        "📈 Risk Analysis",
        "📝 Summary Report"
    ])

    # ============================================
    # TAB 1: DASHBOARD OVERVIEW (KEEP AS IS)
    # ============================================
    with tab1:
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
                st.metric(
                    label="🎯 Risk Score",
                    value=f"{risk_data['property_risk_score']}/100",
                    delta=f"Grade: {risk_data['property_grade']}",
                    delta_color="inverse"
                )

            with col2:
                st.metric(
                    label="⚠️ Risk Level",
                    value=risk_data['property_risk_category']
                )

            with col3:
                st.metric(
                    label="🔍 Total Defects",
                    value=int(risk_data['total_defects']),
                    delta=f"{int(risk_data['total_critical'])} Critical"
                )

            with col4:
                st.metric(
                    label="🚪 High Risk Rooms",
                    value=f"{int(risk_data['high_risk_rooms'])}/{int(risk_data['total_rooms'])}"
                )

            st.markdown("---")

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
                    return ['background-color: #ffcccc'] * len(row)
                elif row['risk_category'] == 'Medium Risk':
                    return ['background-color: #fff4cc'] * len(row)
                else:
                    return ['background-color: #ccffcc'] * len(row)


            styled_rooms = rooms_df.style.apply(highlight_risk, axis=1)
            st.dataframe(styled_rooms, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("📊 Risk Score Visualization")

            fig = px.bar(
                rooms_df,
                x='room_name',
                y='room_risk_score',
                color='risk_category',
                color_discrete_map={
                    'High Risk': '#ff4444',
                    'Medium Risk': '#ffaa00',
                    'Low Risk': '#44ff44'
                },
                title="Risk Score by Room",
                labels={'room_name': 'Room', 'room_risk_score': 'Risk Score (0-100)'}
            )
            st.plotly_chart(fig, use_container_width=True)

    # ... (KEEP ALL OTHER TABS - TAB 2, 3, 4 exactly as they are in your current code)

    # I'm omitting them here to save space, but you should paste your full existing tab code

# ============================================
# FOOTER (KEEP AS IS)
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🏠 Property Inspection AI | Powered by Snowflake & AI Vision</p>
    <p>View existing reports or upload new images for instant AI analysis</p>
</div>
""", unsafe_allow_html=True)