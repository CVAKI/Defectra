"""
PDF Report Generator for Defactra AI
Creates professional inspection reports with annotated images and professional defect cards
UPDATED to work with new image_annotator format (structured data instead of legend images)
FIXED: Removed duplicate PageBreak that caused blank page before Recommendations
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from datetime import datetime
from PIL import Image
import io

from translations import get_text, get_severity_color
from image_annotator import (
    annotate_image_with_defects,
    create_thumbnail,
    create_defect_details_section  # NEW: Professional defect cards
)


class DefactraReportTemplate:
    """Custom PDF template with Defactra branding"""

    def __init__(self, language='english'):
        self.language = language

    def header(self, canvas, doc):
        """Draw header on each page"""
        canvas.saveState()

        # Header background
        canvas.setFillColorRGB(0.06, 0.05, 0.16)
        canvas.rect(0, A4[1] - 80, A4[0], 80, fill=1, stroke=0)

        # Defactra logo/title
        canvas.setFillColorRGB(0, 0.96, 1)
        canvas.setFont("Helvetica-Bold", 24)
        canvas.drawString(40, A4[1] - 45, "DEFACTRA AI")

        canvas.setFillColorRGB(0.63, 0.63, 1)
        canvas.setFont("Helvetica", 10)
        canvas.drawString(40, A4[1] - 65, get_text('generated_by', self.language))

        canvas.restoreState()

    def footer(self, canvas, doc):
        """Draw footer on each page"""
        canvas.saveState()

        # Footer background
        canvas.setFillColorRGB(0.06, 0.05, 0.16)
        canvas.rect(0, 0, A4[0], 50, fill=1, stroke=0)

        # Disclaimer
        canvas.setFillColorRGB(0.63, 0.63, 1)
        canvas.setFont("Helvetica", 8)
        disclaimer = get_text('disclaimer', self.language)
        canvas.drawCentredString(A4[0] / 2, 30, disclaimer)

        # Page number
        canvas.setFont("Helvetica-Bold", 9)
        page_text = f"{get_text('page', self.language)} {doc.page}"
        canvas.drawRightString(A4[0] - 40, 15, page_text)

        canvas.restoreState()


def create_custom_styles(language='english'):
    """Create custom paragraph styles"""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#00F5FF'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))

    # Section header
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#00F5FF'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    ))

    # Subsection header
    styles.add(ParagraphStyle(
        name='SubsectionHeader',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#0080FF'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    ))

    # Normal text
    styles.add(ParagraphStyle(
        name='CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#303030'),
        spaceAfter=6,
        alignment=TA_JUSTIFY
    ))

    # Defect description (for professional cards)
    styles.add(ParagraphStyle(
        name='DefectDescription',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#404040'),
        spaceAfter=4,
        leftIndent=10,
        alignment=TA_LEFT
    ))

    # Defect desc (for old format compatibility)
    styles.add(ParagraphStyle(
        name='DefectDesc',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#404040'),
        spaceAfter=4,
        leftIndent=20
    ))

    return styles


def generate_pdf_report(
        property_data,
        defects,
        images,
        language='english',
        output_path=None
):
    """
    Generate comprehensive PDF report with annotated images and professional defect cards

    Args:
        property_data: Dictionary with property information
        defects: List of defect dictionaries
        images: List of PIL Image objects
        language: Language for report (english/malayalam/hindi)
        output_path: Path to save PDF (if None, returns BytesIO)

    Returns:
        Path to PDF or BytesIO object
    """

    # Create PDF
    if output_path is None:
        output = io.BytesIO()
    else:
        output = output_path

    # Use A4 page size
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=100,
        bottomMargin=70
    )

    # Custom template
    template = DefactraReportTemplate(language)

    # Story (content)
    story = []
    styles = create_custom_styles(language)

    # ==========================================
    # TITLE PAGE
    # ==========================================

    title = Paragraph(
        get_text('report_title', language),
        styles['CustomTitle']
    )
    story.append(title)
    story.append(Spacer(1, 20))

    # Property ID and date
    inspection_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    date_text = f"{get_text('inspection_date', language)}: {inspection_date}"
    story.append(Paragraph(date_text, styles['CustomNormal']))
    story.append(Spacer(1, 10))

    property_id = property_data.get('property_id', 'N/A')
    id_text = f"{get_text('property_id', language)}: <b>{property_id}</b>"
    story.append(Paragraph(id_text, styles['CustomNormal']))
    story.append(Spacer(1, 30))

    # ==========================================
    # PROPERTY DETAILS
    # ==========================================

    story.append(Paragraph(get_text('property_details', language), styles['SectionHeader']))
    story.append(Spacer(1, 10))

    property_details = [
        [get_text('address', language), property_data.get('address', 'N/A')],
        [get_text('city', language), property_data.get('city', 'N/A')],
        [get_text('property_type', language), property_data.get('property_type', 'N/A')],
        [get_text('bedrooms', language), str(property_data.get('bedrooms', 'N/A'))],
        [get_text('area', language), f"{property_data.get('area_sqft', 'N/A')} sq ft"],
        [get_text('year_built', language), str(property_data.get('year_built', 'N/A'))],
        [get_text('room_name', language), property_data.get('room_name', 'N/A')],
    ]

    prop_table = Table(property_details, colWidths=[2 * inch, 3.5 * inch])
    prop_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F4FF')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0080FF')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(prop_table)
    story.append(Spacer(1, 20))

    # ==========================================
    # EXECUTIVE SUMMARY
    # ==========================================

    story.append(Paragraph(get_text('executive_summary', language), styles['SectionHeader']))
    story.append(Spacer(1, 10))

    # Summary metrics
    total_defects = len(defects)
    critical_count = len([d for d in defects if d.get('severity', '').lower() == 'critical'])
    high_count = len([d for d in defects if d.get('severity', '').lower() == 'high'])
    medium_count = len([d for d in defects if d.get('severity', '').lower() == 'medium'])
    low_count = len([d for d in defects if d.get('severity', '').lower() == 'low'])

    overall_score = property_data.get('overall_score', 75)
    usability = property_data.get('usability', 'good')

    summary_data = [
        [get_text('overall_condition', language), f"{overall_score}/100"],
        [get_text('usability_rating', language), usability.upper()],
        [get_text('total_defects', language), str(total_defects)],
        [get_text('critical_issues', language), str(critical_count)],
        [get_text('high_priority', language), str(high_count)],
        [get_text('medium_priority', language), str(medium_count)],
        [get_text('low_priority', language), str(low_count)],
    ]

    summary_table = Table(summary_data, colWidths=[3 * inch, 2.5 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F8FF')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#00F5FF')),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    # Color coding for severity
    if critical_count > 0:
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (1, 3), (1, 3), colors.HexColor('#FF0066')),
            ('TEXTCOLOR', (1, 3), (1, 3), colors.white),
        ]))
    if high_count > 0:
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (1, 4), (1, 4), colors.HexColor('#FF6600')),
            ('TEXTCOLOR', (1, 4), (1, 4), colors.white),
        ]))
    if medium_count > 0:
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (1, 5), (1, 5), colors.HexColor('#FFCC00')),
        ]))
    if low_count > 0:
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (1, 6), (1, 6), colors.HexColor('#00FF99')),
        ]))

    story.append(summary_table)
    story.append(Spacer(1, 20))

    # ==========================================
    # ANNOTATED IMAGES WITH PROFESSIONAL DEFECT CARDS
    # (NEW FORMAT - Using structured data)
    # ==========================================

    if images:
        story.append(PageBreak())
        story.append(Paragraph(get_text('defect_analysis', language), styles['SectionHeader']))
        story.append(Spacer(1, 10))

        for idx, img in enumerate(images, 1):
            # Annotate image - NOW RETURNS (annotated_img, legend_data)
            # legend_data is a LIST of defect dictionaries, NOT an image
            annotated_img, legend_data = annotate_image_with_defects(img, defects, language)

            # PAGE 1: ANNOTATED IMAGE with markers
            img_thumbnail = create_thumbnail(annotated_img, max_size=(600, 500))

            # Convert to ReportLab Image
            img_buffer = io.BytesIO()
            img_thumbnail.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            # Make image as large as possible on page
            rl_img = RLImage(img_buffer, width=6.5 * inch, height=5 * inch, kind='proportional')

            caption = Paragraph(
                f"<b>{get_text('defect_analysis', language)} - Image {idx}</b>",
                styles['CustomNormal']
            )

            story.append(KeepTogether([caption, Spacer(1, 5), rl_img]))
            story.append(Spacer(1, 15))

            # PAGE 2: PROFESSIONAL DEFECT CARDS (using structured data)
            if legend_data is not None and len(legend_data) > 0:
                # Add section header
                defects_header = Paragraph(
                    f"<b>Defect Details - Image {idx}</b>",
                    styles['SubsectionHeader']
                )
                story.append(defects_header)
                story.append(Spacer(1, 10))

                # Use the professional defect cards function from image_annotator
                defect_elements = create_defect_details_section(legend_data, styles)
                for element in defect_elements:
                    story.append(element)

                # ⭐ FIXED: Only add PageBreak if this is NOT the last image
                # This prevents a blank page before recommendations
                if idx < len(images):
                    story.append(PageBreak())  # Only between images, not after last one

    # ==========================================
    # RECOMMENDATIONS
    # ⭐ FIXED: Single PageBreak here (removed duplicate)
    # ==========================================

    story.append(PageBreak())  # Only ONE PageBreak before recommendations
    story.append(Paragraph(get_text('recommendations', language), styles['SectionHeader']))
    story.append(Spacer(1, 10))

    # Generate recommendations
    recommendations = []

    if critical_count > 0:
        recommendations.append(f"• {get_text('rec_critical', language)}")

    if high_count > 0:
        recommendations.append(f"• {get_text('rec_high', language)}")

    if medium_count > 0:
        recommendations.append(f"• {get_text('rec_medium', language)}")

    if low_count > 0:
        recommendations.append(f"• {get_text('rec_low', language)}")

    recommendations.append(f"• {get_text('rec_general', language)}")

    for rec in recommendations:
        story.append(Paragraph(rec, styles['CustomNormal']))
        story.append(Spacer(1, 6))

    # ==========================================
    # BUILD PDF
    # ==========================================

    # Build with custom template
    doc.build(
        story,
        onFirstPage=lambda c, d: (template.header(c, d), template.footer(c, d)),
        onLaterPages=lambda c, d: (template.header(c, d), template.footer(c, d))
    )

    # Return output
    if output_path is None:
        output.seek(0)
        return output
    else:
        return output_path