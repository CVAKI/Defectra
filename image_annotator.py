"""
Full-Page Image Annotation Module for Defactra AI
Returns annotated image and STRUCTURED LEGEND DATA (not image)
Professional format - EXACT SAME as video module
FIXED: Reduced marker sizes for better balance
"""

from PIL import Image, ImageDraw, ImageFont
import io


def annotate_image_with_defects(image, defects, language='english'):
    """
    Annotate image with numbered defect markers ONLY
    Returns: 1) Annotated image, 2) STRUCTURED legend data (not image)

    Args:
        image: PIL Image object
        defects: List of defect dictionaries with location and severity
        language: Language for labels

    Returns:
        Tuple of (annotated_image, legend_data)
        - annotated_image: PIL Image with markers
        - legend_data: List of dicts with defect details for professional rendering
    """
    # Create a copy to avoid modifying original
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)

    # Define colors for severity levels (matching video module)
    severity_colors = {
        'critical': '#DC2626',  # Red
        'high': '#F59E0B',      # Orange
        'medium': '#FCD34D',    # Yellow
        'low': '#10B981'        # Green
    }

    severity_labels = {
        'critical': 'CRITICAL',
        'high': 'HIGH',
        'medium': 'MEDIUM',
        'low': 'LOW'
    }

    # Try to load fonts - REDUCED SIZES
    try:
        # Reduced base size calculation for smaller markers
        base_size = max(18, min(image.width, image.height) // 35)
        marker_font = ImageFont.truetype("arial.ttf", base_size + 6)
        watermark_font = ImageFont.truetype("arial.ttf", base_size + 8)
    except:
        try:
            base_size = max(18, min(image.width, image.height) // 35)
            marker_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", base_size + 6)
            watermark_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", base_size + 8)
        except:
            marker_font = ImageFont.load_default()
            watermark_font = ImageFont.load_default()

    # Image dimensions
    img_width, img_height = annotated.size

    # If no defects, add a watermark to image only
    if not defects:
        watermark_text = "✓ No Major Defects Detected"
        bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (img_width - text_width) // 2
        y = 30

        padding = 20  # Reduced padding
        draw.rectangle(
            [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
            fill='#FFFFFF',
            outline='#00FF99',
            width=5  # Reduced border width
        )
        draw.text((x, y), watermark_text, fill='#000000', font=watermark_font)

        # Return image and None for legend data
        return annotated, None

    # Group defects by location keywords
    location_zones = {
        'top': [],
        'bottom': [],
        'left': [],
        'right': [],
        'center': [],
        'corner': [],
        'wall': [],
        'ceiling': [],
        'floor': []
    }

    # Categorize defects by location
    for i, defect in enumerate(defects):
        location = defect.get('location', '').lower()
        categorized = False

        for zone in location_zones.keys():
            if zone in location:
                location_zones[zone].append((i, defect))
                categorized = True
                break

        if not categorized:
            location_zones['center'].append((i, defect))

    # Build structured legend data
    legend_data = []
    marker_number = 1

    for zone, zone_defects in location_zones.items():
        for defect_idx, defect in zone_defects:
            defect_name = defect.get('detected_object', 'Defect')
            severity = defect.get('severity', 'medium').lower()
            location_text = defect.get('location', 'Not specified')
            description = defect.get('description', 'No description available')
            confidence = defect.get('confidence_score', 0)

            legend_data.append({
                'number': marker_number,
                'name': defect_name,
                'severity': severity,
                'severity_label': severity_labels.get(severity, severity.upper()),
                'severity_color': severity_colors.get(severity, '#808080'),
                'location': location_text,
                'description': description,
                'confidence': confidence
            })
            marker_number += 1

    # ======================================
    # DRAW MARKERS ON IMAGE ONLY - REDUCED SIZES
    # ======================================
    marker_number = 1
    zone_positions = {
        'top': (img_width // 2, img_height // 6),
        'bottom': (img_width // 2, 5 * img_height // 6),
        'left': (img_width // 6, img_height // 2),
        'right': (5 * img_width // 6, img_height // 2),
        'center': (img_width // 2, img_height // 2),
        'corner': (img_width - 80, 80),  # Reduced from 120
        'wall': (img_width // 3, img_height // 2),
        'ceiling': (img_width // 2, 80),  # Reduced from 120
        'floor': (img_width // 2, img_height - 80)  # Reduced from 120
    }

    for zone, zone_defects in location_zones.items():
        if not zone_defects:
            continue

        base_x, base_y = zone_positions.get(zone, (img_width // 2, img_height // 2))

        for j, (defect_idx, defect) in enumerate(zone_defects):
            # Calculate position with spacing - REDUCED SPACING
            offset = (j - len(zone_defects) // 2) * 70  # Reduced from 120
            x = base_x + offset
            y = base_y + (j * 35 if len(zone_defects) > 1 else 0)  # Reduced from 60

            # Ensure marker stays within image bounds
            x = max(60, min(x, img_width - 60))  # Reduced from 100
            y = max(60, min(y, img_height - 60))  # Reduced from 100

            severity = defect.get('severity', 'medium').lower()
            color = severity_colors.get(severity, '#808080')
            color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

            # Draw SMALLER marker circle - SIGNIFICANTLY REDUCED
            marker_radius = 28  # Reduced from 55 (almost half)

            # Outer white glow - REDUCED
            draw.ellipse(
                [x - marker_radius - 5, y - marker_radius - 5,
                 x + marker_radius + 5, y + marker_radius + 5],
                fill='#FFFFFF'
            )

            # Black border - REDUCED
            draw.ellipse(
                [x - marker_radius - 3, y - marker_radius - 3,
                 x + marker_radius + 3, y + marker_radius + 3],
                fill='#000000'
            )

            # Colored circle
            draw.ellipse(
                [x - marker_radius, y - marker_radius,
                 x + marker_radius, y + marker_radius],
                fill=color_rgb
            )

            # Draw number with THINNER outline
            number_text = str(marker_number)
            bbox = draw.textbbox((0, 0), number_text, font=marker_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Black outline - REDUCED thickness
            for offset_x in [-2, -1, 0, 1, 2]:  # Reduced from -5 to 5
                for offset_y in [-2, -1, 0, 1, 2]:  # Reduced from -5 to 5
                    if offset_x != 0 or offset_y != 0:
                        draw.text(
                            (x - text_width // 2 + offset_x, y - text_height // 2 + offset_y),
                            number_text,
                            fill='#000000',
                            font=marker_font
                        )

            # White number
            draw.text(
                (x - text_width // 2, y - text_height // 2),
                number_text,
                fill='#FFFFFF',
                font=marker_font
            )

            marker_number += 1

    # Return annotated image and structured legend data
    return annotated, legend_data


def create_thumbnail(image, max_size=(800, 600)):
    """
    Create a thumbnail of the image for the PDF

    Args:
        image: PIL Image object
        max_size: Maximum dimensions (width, height)

    Returns:
        PIL Image thumbnail
    """
    img_copy = image.copy()
    img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
    return img_copy


def get_severity_display_color(severity):
    """
    Get display colors for severity levels
    EXACT SAME as video module

    Returns tuple of (background_color, text_color)
    """
    from reportlab.lib import colors as rl_colors

    severity_colors = {
        'critical': (rl_colors.HexColor('#DC2626'), rl_colors.white),  # Red
        'high': (rl_colors.HexColor('#F59E0B'), rl_colors.white),      # Orange
        'medium': (rl_colors.HexColor('#FCD34D'), rl_colors.black),    # Yellow
        'low': (rl_colors.HexColor('#10B981'), rl_colors.white),       # Green
    }
    return severity_colors.get(severity.lower(), (rl_colors.HexColor('#6B7280'), rl_colors.white))


def create_defect_details_section(legend_data, styles):
    """
    Create professional defect details section for PDF reports
    EXACT SAME format as video module's create_defect_details_table

    Args:
        legend_data: List of defect dicts returned from annotate_image_with_defects
        styles: ReportLab styles object

    Returns:
        List of ReportLab elements (tables, paragraphs, spacers)
    """
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.units import inch
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer

    elements = []

    if not legend_data:
        no_defects = Paragraph(
            "<i>No defects detected in this image</i>",
            styles['DefectDescription']
        )
        elements.append(no_defects)
        return elements

    # Header for defect details
    header = Paragraph(
        f"<b>Defects Detected: {len(legend_data)}</b>",
        styles['SubsectionHeader']
    )
    elements.append(header)
    elements.append(Spacer(1, 8))

    # Create individual defect cards (same as video module)
    for idx, defect_info in enumerate(legend_data, 1):
        defect_elements = create_defect_card(defect_info, idx, styles)
        elements.extend(defect_elements)

        # Add spacing between defects
        if idx < len(legend_data):
            elements.append(Spacer(1, 10))

    return elements


def create_defect_card(detection, index, styles):
    """
    Create a professional card-style display for a single defect
    EXACT SAME as video module's create_defect_card function

    Args:
        detection: Detection dictionary (from legend_data)
        index: Defect number
        styles: Report styles

    Returns:
        List of reportlab elements
    """
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.units import inch
    from reportlab.platypus import Table, TableStyle, Paragraph

    elements = []

    # Extract detection info - handle both formats
    if 'name' in detection:
        # New format (from legend_data)
        defect_type = detection.get('name', 'Unknown Defect')
        severity = detection.get('severity', 'medium')
        confidence = detection.get('confidence', 0)
        location = detection.get('location', 'Not specified')
        description = detection.get('description', 'No description available')
    else:
        # Old format (direct detection dict)
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
        ('BACKGROUND', (0, 0), (0, 0), rl_colors.HexColor('#F3F4F6')),
        ('BACKGROUND', (1, 0), (1, 0), bg_color),
        ('TEXTCOLOR', (0, 0), (0, 0), rl_colors.HexColor('#1F2937')),
        ('TEXTCOLOR', (1, 0), (1, 0), text_color),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, rl_colors.HexColor('#E5E7EB')),
    ]))

    elements.append(header_table)

    # Create details table
    details_data = [
        ['Location:', location],
        ['Confidence:', f'{confidence:.1f}%'],
    ]

    details_table = Table(details_data, colWidths=[1.2 * inch, 4.8 * inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), rl_colors.HexColor('#F9FAFB')),
        ('TEXTCOLOR', (0, 0), (0, -1), rl_colors.HexColor('#6B7280')),
        ('TEXTCOLOR', (1, 0), (1, -1), rl_colors.HexColor('#1F2937')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, rl_colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(details_table)

    # Add description in a bordered box
    description_data = [[Paragraph(f"<b>Description:</b> {description}", styles['DefectDescription'])]]

    description_table = Table(description_data, colWidths=[6 * inch])
    description_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), rl_colors.HexColor('#FFFBEB')),
        ('TEXTCOLOR', (0, 0), (-1, -1), rl_colors.HexColor('#78350F')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 1, rl_colors.HexColor('#FDE68A')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(description_table)

    return elements