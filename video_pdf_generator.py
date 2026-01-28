"""
Video PDF Report Generator for Defactra AI
Generates comprehensive PDF reports from video analysis with frame-by-frame defect detection
IMPROVED: Professional text-based defect descriptions with color-coded tables
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
from PIL import Image
import io

from translations import get_text, get_severity_color
from image_annotator import annotate_image_with_defects, create_thumbnail


class DefactraVideoReportTemplate:
    """Custom PDF template for video reports"""

    def __init__(self, language='english'):
        self.language = language

    def header(self, canvas, doc):
        """Draw header on each page"""
        canvas.saveState()

        # Header background
        canvas.setFillColorRGB(0.06, 0.05, 0.16)
        canvas.rect(0, A4[1] - 80, A4[0], 80, fill=1, stroke=0)

        # Title
        canvas.setFillColorRGB(0, 0.96, 1)
        canvas.setFont("Helvetica-Bold", 24)
        canvas.drawString(40, A4[1] - 45, "DEFACTRA AI - VIDEO ANALYSIS")

        canvas.setFillColorRGB(0.63, 0.63, 1)
        canvas.setFont("Helvetica", 10)
        canvas.drawString(40, A4[1] - 65, "Video Inspection Report")

        canvas.restoreState()

    def footer(self, canvas, doc):
        """Draw footer on each page"""
        canvas.saveState()

        # Footer background
        canvas.setFillColorRGB(0.06, 0.05, 0.16)
        canvas.rect(0, 0, A4[0], 50, fill=1, stroke=0)

        # Page number
        canvas.setFillColorRGB(0.63, 0.63, 1)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawRightString(A4[0] - 40, 15, f"Page {doc.page}")

        canvas.restoreState()


def create_custom_styles(language='english'):
    """Create custom paragraph styles"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#00F5FF'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#00F5FF'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='SubsectionHeader',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#0080FF'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#303030'),
        spaceAfter=6,
        alignment=TA_JUSTIFY
    ))

    styles.add(ParagraphStyle(
        name='DefectDescription',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#404040'),
        spaceAfter=4,
        leftIndent=10,
        alignment=TA_LEFT
    ))

    return styles


def get_severity_display_color(severity):
    """
    Get display colors for severity levels

    Returns tuple of (background_color, text_color)
    """
    severity_colors = {
        'critical': (colors.HexColor('#DC2626'), colors.white),  # Red
        'high': (colors.HexColor('#F59E0B'), colors.white),      # Orange
        'medium': (colors.HexColor('#FCD34D'), colors.black),    # Yellow
        'low': (colors.HexColor('#10B981'), colors.white),       # Green
    }
    return severity_colors.get(severity.lower(), (colors.HexColor('#6B7280'), colors.white))


def create_defect_details_table(detections, styles):
    """
    Create professional color-coded table for defect details

    Args:
        detections: List of detection dictionaries
        styles: Report styles

    Returns:
        List of reportlab elements (table, spacers, etc.)
    """
    elements = []

    if not detections:
        no_defects = Paragraph(
            "<i>No defects detected in this frame</i>",
            styles['DefectDescription']
        )
        elements.append(no_defects)
        return elements

    # Header for defect details
    header = Paragraph(
        f"<b>Defects Detected: {len(detections)}</b>",
        styles['SubsectionHeader']
    )
    elements.append(header)
    elements.append(Spacer(1, 8))

    # Create individual defect cards
    for idx, detection in enumerate(detections, 1):
        defect_elements = create_defect_card(detection, idx, styles)
        elements.extend(defect_elements)

        # Add spacing between defects
        if idx < len(detections):
            elements.append(Spacer(1, 10))

    return elements


def create_defect_card(detection, index, styles):
    """
    Create a professional card-style display for a single defect

    Args:
        detection: Detection dictionary
        index: Defect number
        styles: Report styles

    Returns:
        List of reportlab elements
    """
    elements = []

    # Extract detection info
    defect_type = detection.get('detected_object', 'Unknown Defect')
    severity = detection.get('severity', 'medium')
    confidence = detection.get('confidence_score', 0)
    location = detection.get('location', 'Not specified')
    description = detection.get('description', 'No description available')

    # Get colors for severity
    bg_color, text_color = get_severity_display_color(severity)

    # Create defect header table with colored severity badge
    header_data = [
        [
            Paragraph(f"<b>{index}. {defect_type.upper()}</b>", styles['CustomNormal']),
            Paragraph(
                f"<font color='white'><b>{severity.upper()}</b></font>",
                styles['CustomNormal']
            )
        ]
    ]

    header_table = Table(header_data, colWidths=[4.5 * inch, 1.5 * inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#F3F4F6')),
        ('BACKGROUND', (1, 0), (1, 0), bg_color),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1F2937')),
        ('TEXTCOLOR', (1, 0), (1, 0), text_color),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
    ]))

    elements.append(header_table)

    # Create details table
    details_data = [
        ['Location:', location],
        ['Confidence:', f'{confidence:.1f}%'],
    ]

    details_table = Table(details_data, colWidths=[1.2 * inch, 4.8 * inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F9FAFB')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(details_table)

    # Add description in a bordered box
    description_data = [[Paragraph(f"<b>Description:</b> {description}", styles['DefectDescription'])]]

    description_table = Table(description_data, colWidths=[6 * inch])
    description_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFBEB')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#78350F')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#FDE68A')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(description_table)

    return elements


def generate_video_pdf_report(
        property_data,
        video_info,
        video_analysis,
        key_frames,
        language='english',
        output_path=None
):
    """
    Generate PDF report from video analysis with professional text-based defect descriptions

    Args:
        property_data: Property information dict
        video_info: Video metadata dict
        video_analysis: Analysis results dict
        key_frames: List of (frame_image, timestamp, detections) tuples
        language: Report language
        output_path: Output path or None for BytesIO
    """

    # Create PDF
    if output_path is None:
        output = io.BytesIO()
    else:
        output = output_path

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=100,
        bottomMargin=70
    )

    template = DefactraVideoReportTemplate(language)
    story = []
    styles = create_custom_styles(language)

    # ==========================================
    # TITLE PAGE
    # ==========================================

    title = Paragraph(
        "VIDEO INSPECTION REPORT",
        styles['CustomTitle']
    )
    story.append(title)
    story.append(Spacer(1, 20))

    # Property and video info
    inspection_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    date_text = f"Inspection Date: {inspection_date}"
    story.append(Paragraph(date_text, styles['CustomNormal']))
    story.append(Spacer(1, 10))

    property_id = property_data.get('property_id', 'N/A')
    id_text = f"Property ID: <b>{property_id}</b>"
    story.append(Paragraph(id_text, styles['CustomNormal']))
    story.append(Spacer(1, 30))

    # ==========================================
    # PROPERTY DETAILS
    # ==========================================

    story.append(Paragraph("Property Details", styles['SectionHeader']))
    story.append(Spacer(1, 10))

    property_details = [
        ["Address", property_data.get('address', 'N/A')],
        ["City", property_data.get('city', 'N/A')],
        ["Type", property_data.get('property_type', 'N/A')],
        ["Area Inspected", property_data.get('room_name', 'N/A')],
    ]

    prop_table = Table(property_details, colWidths=[2 * inch, 3.5 * inch])
    prop_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F4FF')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0080FF')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(prop_table)
    story.append(Spacer(1, 20))

    # ==========================================
    # VIDEO INFORMATION
    # ==========================================

    if video_info:
        story.append(Paragraph("Video Information", styles['SectionHeader']))
        story.append(Spacer(1, 10))

        duration_min = int(video_info.get('duration', 0) // 60)
        duration_sec = int(video_info.get('duration', 0) % 60)

        video_details = [
            ["Duration", f"{duration_min}:{duration_sec:02d}"],
            ["Resolution", f"{video_info.get('width', 0)}x{video_info.get('height', 0)}"],
            ["Frame Rate", f"{video_info.get('fps', 0):.1f} fps"],
            ["Total Frames", str(video_info.get('total_frames', 0))],
        ]

        video_table = Table(video_details, colWidths=[2 * inch, 3.5 * inch])
        video_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F8FF')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(video_table)
        story.append(Spacer(1, 20))

    # ==========================================
    # ANALYSIS SUMMARY
    # ==========================================

    if video_analysis:
        story.append(Paragraph("Analysis Summary", styles['SectionHeader']))
        story.append(Spacer(1, 10))

        summary_data = [
            ["Frames Analyzed", str(video_analysis.get('frames_analyzed', 0))],
            ["Total Defects Found", str(video_analysis.get('total_defects', 0))],
            ["Average Condition Score", f"{video_analysis.get('average_score', 0)}/100"],
            ["Unique Defect Types", str(video_analysis.get('unique_defect_types', 0))],
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
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))

    # ==========================================
    # KEY FRAMES WITH DEFECTS
    # ==========================================

    if key_frames:
        story.append(PageBreak())
        story.append(Paragraph("Key Frame Analysis", styles['SectionHeader']))
        story.append(Spacer(1, 10))

        for idx, (frame_img, timestamp, detections) in enumerate(key_frames[:10], 1):
            # Annotate the frame image (just the visual annotations, no legend)
            annotated_img, _ = annotate_image_with_defects(frame_img, detections, language)

            # Create thumbnail
            img_thumbnail = create_thumbnail(annotated_img, max_size=(600, 400))

            img_buffer = io.BytesIO()
            img_thumbnail.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            rl_img = RLImage(img_buffer, width=6.5 * inch, height=4 * inch, kind='proportional')

            # Format timestamp
            time_min = int(timestamp // 60)
            time_sec = int(timestamp % 60)
            time_formatted = f"{time_min}:{time_sec:02d}"

            # Frame caption
            caption = Paragraph(
                f"<b>Frame {idx} - Timestamp: {time_formatted}</b>",
                styles['SubsectionHeader']
            )

            # Add frame image
            story.append(caption)
            story.append(Spacer(1, 5))
            story.append(rl_img)
            story.append(Spacer(1, 15))

            # Add professional text-based defect details
            defect_details = create_defect_details_table(detections, styles)
            for element in defect_details:
                story.append(element)

            # Page break after each frame analysis
            story.append(PageBreak())

    # ==========================================
    # DEFECT TIMELINE
    # ==========================================

    if video_analysis and 'defect_timeline' in video_analysis:
        story.append(Paragraph("Defect Timeline", styles['SectionHeader']))
        story.append(Spacer(1, 10))

        timeline = video_analysis.get('defect_timeline', {})

        for defect_type, info in list(timeline.items())[:10]:
            severity = info.get('severity', 'medium')
            bg_color, text_color = get_severity_display_color(severity)

            # Create timeline entry
            timeline_data = [[
                Paragraph(f"<b>{defect_type.upper()}</b>", styles['CustomNormal']),
                Paragraph(f"<b>{severity.upper()}</b>", styles['CustomNormal'])
            ]]

            timeline_header = Table(timeline_data, colWidths=[4.5 * inch, 1.5 * inch])
            timeline_header.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#F3F4F6')),
                ('BACKGROUND', (1, 0), (1, 0), bg_color),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1F2937')),
                ('TEXTCOLOR', (1, 0), (1, 0), text_color),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ]))

            story.append(timeline_header)

            # Timeline details
            details_text = f"""
            Detected: <b>{info.get('frame_count', 0)} times</b> | 
            Average Confidence: <b>{info.get('avg_confidence', 0):.1f}%</b><br/>
            First seen: {format_timestamp(info.get('first_seen', 0))} | 
            Last seen: {format_timestamp(info.get('last_seen', 0))}
            """

            story.append(Paragraph(details_text, styles['CustomNormal']))
            story.append(Spacer(1, 12))

    # ==========================================
    # RECOMMENDATIONS
    # ==========================================

    story.append(PageBreak())
    story.append(Paragraph("Recommendations", styles['SectionHeader']))
    story.append(Spacer(1, 10))

    recommendations = [
        "• Review all critical and high-severity defects immediately",
        "• Schedule professional inspection for structural issues",
        "• Document repair progress with follow-up video inspections",
        "• Maintain regular property maintenance schedule",
        "• Consider preventive measures for recurring issues"
    ]

    for rec in recommendations:
        story.append(Paragraph(rec, styles['CustomNormal']))
        story.append(Spacer(1, 6))

    # ==========================================
    # BUILD PDF
    # ==========================================

    doc.build(
        story,
        onFirstPage=lambda c, d: (template.header(c, d), template.footer(c, d)),
        onLaterPages=lambda c, d: (template.header(c, d), template.footer(c, d))
    )

    if output_path is None:
        output.seek(0)
        return output
    else:
        return output_path


def format_timestamp(seconds):
    """Format seconds to MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"