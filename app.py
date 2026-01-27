import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Property Inspection AI",
    page_icon="🏠",
    layout="wide"
)

# ============================================
# CUSTOM CSS STYLING
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
</style>
""", unsafe_allow_html=True)


# ============================================
# SNOWFLAKE CONNECTION
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
# HEADER
# ============================================
st.markdown('<h1 class="main-header">🏠 Property Inspection AI</h1>', unsafe_allow_html=True)
st.markdown("### AI-Powered Defect Detection & Risk Analysis")
st.markdown("---")

# ============================================
# SIDEBAR - PROPERTY SELECTION
# ============================================
with st.sidebar:
    st.header("🔍 Property Selection")

    # Get all properties
    properties_df = pd.read_sql("""
        SELECT property_id, address, city 
        FROM properties 
        ORDER BY property_id
    """, conn)

    # Fix column names (Snowflake returns uppercase)
    properties_df.columns = properties_df.columns.str.lower()

    # Property selector
    selected_property = st.selectbox(
        "Select Property:",
        properties_df['property_id'].tolist(),
        format_func=lambda x: properties_df[properties_df['property_id'] == x]['address'].iloc[0]
    )

    st.markdown("---")

    # Property info
    prop_info = properties_df[properties_df['property_id'] == selected_property].iloc[0]
    st.markdown(f"**📍 Location:** {prop_info['city']}")
    st.markdown(f"**🆔 ID:** {selected_property}")

    st.markdown("---")
    st.markdown("### 📊 Quick Actions")

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# ============================================
# MAIN CONTENT - TABS
# ============================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "🤖 AI Detection",
    "📈 Risk Analysis",
    "📝 Summary Report"
])

# ============================================
# TAB 1: DASHBOARD OVERVIEW
# ============================================
with tab1:
    st.header("📊 Property Overview Dashboard")

    # Get property risk data
    prop_risk = pd.read_sql(f"""
        SELECT * FROM property_risk_scores 
        WHERE property_id = '{selected_property}'
    """, conn)

    # Fix column names
    prop_risk.columns = prop_risk.columns.str.lower()

    if not prop_risk.empty:
        risk_data = prop_risk.iloc[0]

        # KPI Metrics Row 1
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

        # Room Breakdown
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

        # Fix column names
        rooms_df.columns = rooms_df.columns.str.lower()


        # Display rooms table with color coding
        def highlight_risk(row):
            if row['risk_category'] == 'High Risk':
                return ['background-color: #ffcccc'] * len(row)
            elif row['risk_category'] == 'Medium Risk':
                return ['background-color: #fff4cc'] * len(row)
            else:
                return ['background-color: #ccffcc'] * len(row)


        styled_rooms = rooms_df.style.apply(highlight_risk, axis=1)
        st.dataframe(styled_rooms, use_container_width=True, hide_index=True)

        # Chart: Room Risk Scores
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

# ============================================
# TAB 2: AI DETECTION RESULTS
# ============================================
with tab2:
    st.header("🤖 AI-Powered Defect Detection")

    # Get AI classifications
    ai_results = pd.read_sql(f"""
        SELECT 
            r.room_name,
            acd.finding_text,
            acd.ai_defect_type as detected_type,
            acd.ai_severity as severity,
            acd.human_label,
            CASE 
                WHEN acd.ai_defect_type = acd.human_label THEN '✅ Verified'
                ELSE '⚠️ Review'
            END as validation_status
        FROM ai_classified_defects acd
        JOIN rooms r ON acd.room_id = r.room_id
        WHERE r.property_id = '{selected_property}'
        ORDER BY 
            CASE acd.ai_severity 
                WHEN 'critical' THEN 1 
                WHEN 'high' THEN 2 
                WHEN 'medium' THEN 3 
                ELSE 4 
            END
    """, conn)

    # Fix column names
    ai_results.columns = ai_results.columns.str.lower()

    if not ai_results.empty:
        # Summary Stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("🔍 Total Detections", len(ai_results))
        with col2:
            critical = len(ai_results[ai_results['severity'] == 'critical'])
            st.metric("🔴 Critical", critical)
        with col3:
            high = len(ai_results[ai_results['severity'] == 'high'])
            st.metric("🟠 High", high)
        with col4:
            medium = len(ai_results[ai_results['severity'] == 'medium'])
            st.metric("🟡 Medium", medium)

        st.markdown("---")

        # Detailed Results Table
        st.subheader("📋 Detailed AI Classification Results")


        def color_severity(val):
            colors = {
                'critical': 'background-color: #ff4444; color: white; font-weight: bold',
                'high': 'background-color: #ff8800; color: white',
                'medium': 'background-color: #ffcc00',
                'low': 'background-color: #88ff88'
            }
            return colors.get(val, '')


        styled_ai = ai_results.style.map(
            color_severity,
            subset=['severity']
        )

        st.dataframe(styled_ai, use_container_width=True, hide_index=True)

        # Chart: Defect Type Distribution
        st.markdown("---")
        st.subheader("📊 Defect Type Distribution")

        defect_counts = ai_results['detected_type'].value_counts().reset_index()
        defect_counts.columns = ['Defect Type', 'Count']

        fig2 = px.pie(
            defect_counts,
            names='Defect Type',
            values='Count',
            title="Distribution of Detected Defects"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.success("✅ No defects detected! Property is in excellent condition.")

# ============================================
# TAB 3: RISK ANALYSIS
# ============================================
with tab3:
    st.header("📈 Comprehensive Risk Analysis")

    # Property-level analysis
    prop_risk = pd.read_sql(f"""
        SELECT * FROM property_risk_scores 
        WHERE property_id = '{selected_property}'
    """, conn)

    # Fix column names
    prop_risk.columns = prop_risk.columns.str.lower()
    prop_risk = prop_risk.iloc[0]

    # Risk Score Gauge
    st.subheader("🎯 Overall Property Risk Score")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Create gauge chart
        fig_gauge = px.bar(
            x=[prop_risk['property_risk_score']],
            y=['Risk Score'],
            orientation='h',
            title=f"Property Risk: {prop_risk['property_risk_score']}/100",
            color_discrete_sequence=['#ff4444' if prop_risk['property_risk_score'] > 70
                                     else '#ffaa00' if prop_risk['property_risk_score'] > 40
            else '#44ff44']
        )
        fig_gauge.update_xaxes(range=[0, 100])
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col2:
        st.markdown("### 📊 Grade Breakdown")
        st.markdown(f"**Grade:** {prop_risk['property_grade']}")
        st.markdown(f"**Category:** {prop_risk['property_risk_category']}")
        st.markdown(f"**Total Defects:** {int(prop_risk['total_defects'])}")
        st.markdown(f"**Critical Issues:** {int(prop_risk['total_critical'])}")

    st.markdown("---")

    # Severity Breakdown
    st.subheader("⚠️ Severity Breakdown")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🔴 Critical")
        st.metric("Count", int(prop_risk['total_critical']))
        st.progress(min(int(prop_risk['total_critical']) * 0.3, 1.0))

    with col2:
        st.markdown("#### 🟠 High")
        st.metric("Count", int(prop_risk['total_high']))
        st.progress(min(int(prop_risk['total_high']) * 0.2, 1.0))

    with col3:
        st.markdown("#### 🟡 Medium")
        st.metric("Count", int(prop_risk['total_medium']))
        st.progress(min(int(prop_risk['total_medium']) * 0.15, 1.0))

    st.markdown("---")

    # Recommendations
    st.subheader("💡 Recommendations")

    if prop_risk['property_risk_score'] >= 70:
        st.error("🔴 **HIGH RISK PROPERTY** - Not recommended for purchase without major repairs")
        st.markdown("- Immediate professional inspection required")
        st.markdown("- Address all critical issues before proceeding")
        st.markdown("- Consider significant price negotiation")
    elif prop_risk['property_risk_score'] >= 40:
        st.warning("🟡 **MEDIUM RISK PROPERTY** - Proceed with caution")
        st.markdown("- Get quotes for repair costs")
        st.markdown("- Negotiate price reduction based on findings")
        st.markdown("- Request seller to fix critical/high issues")
    else:
        st.success("🟢 **LOW RISK PROPERTY** - Good condition for purchase")
        st.markdown("- Minor repairs needed")
        st.markdown("- Property is generally safe")
        st.markdown("- Good investment opportunity")

# ============================================
# TAB 4: SUMMARY REPORT
# ============================================
with tab4:
    st.header("📝 Plain-Language Inspection Summary")

    # Get AI-generated summary
    summary_data = pd.read_sql(f"""
        SELECT 
            risk_score,
            risk_category,
            plain_language_summary
        FROM inspection_summaries
        WHERE entity_type = 'property' 
          AND entity_id = '{selected_property}'
    """, conn)

    # Fix column names
    summary_data.columns = summary_data.columns.str.lower()

    if not summary_data.empty:
        summary = summary_data.iloc[0]

        # Display summary with nice formatting
        risk_icons = {
            'High Risk': '🔴',
            'Medium Risk': '🟡',
            'Low Risk': '🟢'
        }

        icon = risk_icons.get(summary['risk_category'], '⚪')

        st.markdown(f"## {icon} {summary['risk_category']}")
        st.markdown(f"**Risk Score:** {summary['risk_score']}/100")

        st.markdown("---")

        st.markdown("### 📄 AI-Generated Summary")
        st.info(summary['plain_language_summary'])

        st.markdown("---")

        # Download Report Button
        st.subheader("💾 Export Report")

        # Get property risk data for report
        prop_risk_df = pd.read_sql(f"""
            SELECT * FROM property_risk_scores 
            WHERE property_id = '{selected_property}'
        """, conn)
        prop_risk_df.columns = prop_risk_df.columns.str.lower()
        prop_risk = prop_risk_df.iloc[0]

        # Create report text
        report_text = f"""
PROPERTY INSPECTION REPORT
========================================

Property: {prop_risk['address']}
Inspection Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}

RISK ASSESSMENT
========================================
Overall Risk Score: {prop_risk['property_risk_score']}/100
Property Grade: {prop_risk['property_grade']}
Risk Category: {prop_risk['property_risk_category']}

Total Defects Found: {int(prop_risk['total_defects'])}
Critical Issues: {int(prop_risk['total_critical'])}
High Priority Issues: {int(prop_risk['total_high'])}
Medium Priority Issues: {int(prop_risk['total_medium'])}

High Risk Rooms: {int(prop_risk['high_risk_rooms'])}/{int(prop_risk['total_rooms'])}

SUMMARY
========================================
{summary['plain_language_summary']}

RECOMMENDATIONS
========================================
"""
        if prop_risk['property_risk_score'] >= 70:
            report_text += "- HIGH RISK: Not recommended without major repairs\n- Get professional inspection\n- Address all critical issues"
        elif prop_risk['property_risk_score'] >= 40:
            report_text += "- MEDIUM RISK: Proceed with caution\n- Get repair cost estimates\n- Negotiate price reduction"
        else:
            report_text += "- LOW RISK: Good condition\n- Minor repairs needed\n- Safe for purchase"

        st.download_button(
            label="📥 Download Text Report",
            data=report_text,
            file_name=f"inspection_report_{selected_property}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.warning("⚠️ No summary available for this property.")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🏠 Property Inspection AI | Powered by Snowflake Cortex AI & Streamlit</p>
    <p>Built for safer, smarter property decisions</p>
</div>
""", unsafe_allow_html=True)