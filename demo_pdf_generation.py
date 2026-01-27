"""
PDF Integration Module for Defactra AI
Add this code to your existing app.py to enable PDF report downloads
"""
import pandas as pd
import streamlit as st
from pdf_report_generator import generate_pdf_report
from PIL import Image
import io


def add_pdf_download_section(property_data, defects, images, language='english'):
    """
    Add PDF download section to Streamlit app

    Args:
        property_data: Dictionary with property information
        defects: List of defect dictionaries
        images: List of PIL Image objects
        language: Report language (english/malayalam/hindi)
    """

    st.markdown("---")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📄 Download Inspection Report")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.info("📥 Generate a professional PDF report with annotated images and detailed analysis")

        # Language selection
        language_options = {
            'English': 'english',
            'മലയാളം (Malayalam)': 'malayalam',
            'हिंदी (Hindi)': 'hindi'
        }
        selected_lang = st.selectbox(
            "📝 Select Report Language:",
            options=list(language_options.keys()),
            index=0
        )
        language_code = language_options[selected_lang]

    with col2:
        # Generate PDF button
        if st.button("🎨 Generate PDF Report", type="primary", use_container_width=True):
            with st.spinner(f"Generating report in {selected_lang}..."):
                try:
                    # Generate PDF
                    pdf_buffer = generate_pdf_report(
                        property_data=property_data,
                        defects=defects,
                        images=images,
                        language=language_code
                    )

                    # Success message
                    st.success("✅ Report generated successfully!")

                    # Download button
                    filename = f"Defactra_Report_{property_data['property_id']}_{language_code}.pdf"
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_buffer.getvalue(),
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )

                    st.balloons()

                except Exception as e:
                    st.error(f"❌ Error generating PDF: {e}")
                    st.info("Please try again or contact support if the issue persists.")

    st.markdown('</div>', unsafe_allow_html=True)


def add_pdf_download_to_existing_reports(conn, property_id, language='english'):
    """
    Add PDF download functionality for existing reports in View mode

    Args:
        conn: Snowflake connection
        property_id: Property ID to generate report for
        language: Report language
    """

    st.markdown("---")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📄 Download Report for This Property")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Language selection
        language_options = {
            'English': 'english',
            'മലയാളം (Malayalam)': 'malayalam',
            'हिंदी (Hindi)': 'hindi'
        }
        selected_lang = st.selectbox(
            "📝 Report Language:",
            options=list(language_options.keys()),
            index=0,
            key=f"lang_{property_id}"
        )
        language_code = language_options[selected_lang]

    with col2:
        if st.button("🎨 Generate PDF", type="primary", use_container_width=True, key=f"pdf_{property_id}"):
            with st.spinner("Generating comprehensive report..."):
                try:
                    # Fetch property data
                    prop_df = pd.read_sql(f"""
                        SELECT * FROM properties WHERE property_id = '{property_id}'
                    """, conn)
                    prop_df.columns = prop_df.columns.str.lower()

                    if prop_df.empty:
                        st.error("Property not found")
                        return

                    prop_data = {
                        'property_id': property_id,
                        'address': prop_df['address'].iloc[0],
                        'city': prop_df['city'].iloc[0],
                        'property_type': prop_df['property_type'].iloc[0],
                        'bedrooms': prop_df['bedrooms'].iloc[0],
                        'area_sqft': prop_df['area_sqft'].iloc[0],
                        'year_built': prop_df['year_built'].iloc[0],
                        'room_name': 'Multiple Rooms',
                        'overall_score': 75,  # You can calculate this from room_risk_scores
                        'usability': 'good'
                    }

                    # Fetch defects/findings
                    defects_df = pd.read_sql(f"""
                        SELECT 
                            f.finding_text as detected_object,
                            f.inspector_notes as description,
                            ad.severity,
                            ad.confidence_score,
                            ad.detected_object as location,
                            r.room_name
                        FROM findings f
                        JOIN rooms r ON f.room_id = r.room_id
                        LEFT JOIN ai_detections ad ON f.detection_id = ad.detection_id
                        WHERE r.property_id = '{property_id}'
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
                            'location': f"{row['room_name']} - {row['location']}" if row.get('location') else row[
                                'room_name'],
                            'repair_priority': 'routine',
                            'estimated_impact': 'Requires attention'
                        })

                    # Note: For existing reports, we don't have the actual images
                    # You could either:
                    # 1. Store images in Snowflake and retrieve them
                    # 2. Use placeholder images
                    # 3. Generate report without images

                    # For now, we'll create a placeholder image
                    from PIL import Image, ImageDraw, ImageFont

                    placeholder = Image.new('RGB', (800, 600), color='#1a1a2e')
                    draw = ImageDraw.Draw(placeholder)

                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
                    except:
                        font = ImageFont.load_default()

                    text = f"Property: {property_id}\n{len(defects)} Defects Found"
                    draw.text((100, 250), text, fill='#00f5ff', font=font)

                    images = [placeholder]

                    # Generate PDF
                    pdf_buffer = generate_pdf_report(
                        property_data=prop_data,
                        defects=defects,
                        images=images,
                        language=language_code
                    )

                    st.success("✅ Report generated!")

                    # Download button
                    filename = f"Defactra_Report_{property_id}_{language_code}.pdf"
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_buffer.getvalue(),
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"dl_{property_id}"
                    )

                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    st.markdown('</div>', unsafe_allow_html=True)


# ===========================================
# INSTRUCTIONS FOR INTEGRATION
# ===========================================

"""
HOW TO INTEGRATE PDF DOWNLOAD INTO YOUR EXISTING APP.PY:

1. Add imports at the top of app.py (after existing imports):

   from pdf_report_generator import generate_pdf_report
   from translations import get_text
   import sys
   sys.path.append('/home/claude')  # If modules are in a different directory

2. In the "New Inspection" mode, AFTER the analysis is complete (after all_findings is populated),
   add this code BEFORE displaying the results:

   # Store data for PDF generation
   if len(all_findings) > 0:
       property_pdf_data = {
           'property_id': property_id,
           'address': property_address,
           'city': property_city,
           'property_type': property_type,
           'bedrooms': bedrooms,
           'area_sqft': area_sqft,
           'year_built': year_built,
           'room_name': room_name,
           'overall_score': all_findings[0]['overall_score'],
           'usability': all_findings[0]['usability']
       }

       # Collect images
       pdf_images = []
       for uploaded_file in uploaded_files:
           uploaded_file.seek(0)  # Reset file pointer
           image = Image.open(uploaded_file)
           pdf_images.append(image)

       # After showing all the defect cards, add:
       add_pdf_download_section(property_pdf_data, all_findings, pdf_images)

3. In the "View Existing Reports" mode, in the Dashboard tab (tab1), 
   after displaying the room breakdown table, add:

   # Add PDF download
   add_pdf_download_to_existing_reports(conn, selected_property)

4. Copy these files to your Streamlit app directory:
   - pdf_report_generator.py
   - translations.py
   - image_annotator.py
   - app_pdf_integration.py (this file)

5. Install required package:
   pip install reportlab

6. Run your app:
   streamlit run app.py
"""