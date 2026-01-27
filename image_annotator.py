"""
Clean Image Annotation Module for Defactra AI
Marks defects with numbered markers and detailed legend at bottom
IMPROVED VERSION - Larger, more visible markers
"""

from PIL import Image, ImageDraw, ImageFont
import io

def annotate_image_with_defects(image, defects, language='english'):
    """
    Annotate image with numbered defect markers and detailed legend

    Args:
        image: PIL Image object
        defects: List of defect dictionaries with location and severity
        language: Language for labels

    Returns:
        PIL Image with annotations
    """
    # Create a copy to avoid modifying original
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)

    # Define colors for severity levels - BRIGHTER, MORE VISIBLE
    severity_colors = {
        'critical': '#FF0066',
        'high': '#FF6600',
        'medium': '#FFD700',
        'low': '#00FF99'
    }

    # Try to load a font - LARGER SIZES
    try:
        font_size = max(28, min(image.width, image.height) // 30)  # INCREASED base size
        marker_font = ImageFont.truetype("arial.ttf", font_size + 8)  # BIGGER markers
        legend_title_font = ImageFont.truetype("arial.ttf", font_size)  # BIGGER title
        legend_font = ImageFont.truetype("arial.ttf", font_size - 4)  # BIGGER legend text
    except:
        try:
            marker_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size + 8)
            legend_title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            legend_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size - 4)
        except:
            marker_font = ImageFont.load_default()
            legend_title_font = ImageFont.load_default()
            legend_font = ImageFont.load_default()

    # Image dimensions
    img_width, img_height = annotated.size

    # If no defects, add a watermark
    if not defects:
        watermark_text = "✓ No Major Defects Detected"
        bbox = draw.textbbox((0, 0), watermark_text, font=marker_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (img_width - text_width) // 2
        y = 30

        padding = 20  # INCREASED padding
        draw.rectangle(
            [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
            fill='#FFFFFF',
            outline='#00FF99',
            width=5  # THICKER border
        )
        draw.text((x, y), watermark_text, fill='#000000', font=marker_font)

        return annotated

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

    # Calculate legend height needed (before drawing markers)
    legend_info = []
    marker_number = 1

    for zone, zone_defects in location_zones.items():
        for defect_idx, defect in zone_defects:
            defect_name = defect.get('detected_object', 'Defect')
            severity = defect.get('severity', 'medium').lower()
            legend_info.append({
                'number': marker_number,
                'name': defect_name,
                'severity': severity,
                'location': defect.get('location', 'Not specified')
            })
            marker_number += 1

    # Calculate legend dimensions - INCREASED spacing
    line_height = 45  # INCREASED from 35
    legend_padding = 25  # INCREASED from 20
    legend_title_height = 50  # INCREASED from 40
    legend_content_height = len(legend_info) * line_height + 25
    total_legend_height = legend_title_height + legend_content_height + legend_padding

    # Create new image with space for legend at bottom
    new_height = img_height + total_legend_height
    new_image = Image.new('RGB', (img_width, new_height), color='#FFFFFF')
    new_image.paste(annotated, (0, 0))

    # Update draw object to new image
    draw = ImageDraw.Draw(new_image)

    # Draw markers on original image area
    marker_number = 1
    zone_positions = {
        'top': (img_width // 2, img_height // 6),
        'bottom': (img_width // 2, 5 * img_height // 6),
        'left': (img_width // 6, img_height // 2),
        'right': (5 * img_width // 6, img_height // 2),
        'center': (img_width // 2, img_height // 2),
        'corner': (img_width - 100, 100),
        'wall': (img_width // 3, img_height // 2),
        'ceiling': (img_width // 2, 100),
        'floor': (img_width // 2, img_height - 100)
    }

    for zone, zone_defects in location_zones.items():
        if not zone_defects:
            continue

        base_x, base_y = zone_positions.get(zone, (img_width // 2, img_height // 2))

        for j, (defect_idx, defect) in enumerate(zone_defects):
            # Calculate position with more spacing
            offset = (j - len(zone_defects) // 2) * 100  # INCREASED from 80
            x = base_x + offset
            y = base_y + (j * 45 if len(zone_defects) > 1 else 0)  # INCREASED from 35

            # Ensure marker stays within image bounds
            x = max(80, min(x, img_width - 80))  # INCREASED margin
            y = max(80, min(y, img_height - 80))

            severity = defect.get('severity', 'medium').lower()
            color = severity_colors.get(severity, '#808080')
            color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

            # Draw marker circle - MUCH LARGER and MORE VISIBLE
            marker_radius = 40  # INCREASED from 28

            # Outer white glow - THICKER
            draw.ellipse(
                [x - marker_radius - 6, y - marker_radius - 6,
                 x + marker_radius + 6, y + marker_radius + 6],
                fill='#FFFFFF'
            )

            # Black border - THICKER
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

            # Draw number - WHITE with THICKER black outline
            number_text = str(marker_number)
            bbox = draw.textbbox((0, 0), number_text, font=marker_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Black outline - THICKER for better visibility
            for offset_x in [-3, -2, -1, 0, 1, 2, 3]:  # EXPANDED outline
                for offset_y in [-3, -2, -1, 0, 1, 2, 3]:
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

    # Draw legend at bottom
    legend_start_y = img_height + 15  # INCREASED spacing

    # Legend background
    draw.rectangle(
        [0, img_height, img_width, new_height],
        fill='#FFFFFF',
        outline='#CCCCCC',
        width=3  # THICKER border
    )

    # Legend title - BIGGER and BOLDER
    title_text = "DETECTED DEFECTS:"  # UPPERCASE for visibility
    draw.text((25, legend_start_y), title_text, fill='#000000', font=legend_title_font)

    # Divider line - THICKER
    draw.line(
        [25, legend_start_y + 35, img_width - 25, legend_start_y + 35],
        fill='#CCCCCC',
        width=3  # THICKER
    )

    # Draw each defect entry
    current_y = legend_start_y + 50  # INCREASED spacing

    for item in legend_info:
        severity = item['severity']
        color = severity_colors.get(severity, '#808080')
        color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

        # Number badge - LARGER
        badge_size = 32  # INCREASED from 24
        badge_x = 35
        badge_y = current_y - 3

        # Draw number badge (small circle) - THICKER borders
        draw.ellipse(
            [badge_x - 2, badge_y - 2, badge_x + badge_size + 2, badge_y + badge_size + 2],
            fill='#000000'
        )
        draw.ellipse(
            [badge_x, badge_y, badge_x + badge_size, badge_y + badge_size],
            fill=color_rgb
        )

        # Number in badge - LARGER font
        num_text = str(item['number'])
        bbox = draw.textbbox((0, 0), num_text, font=legend_font)
        num_width = bbox[2] - bbox[0]
        num_height = bbox[3] - bbox[1]

        draw.text(
            (badge_x + badge_size // 2 - num_width // 2,
             badge_y + badge_size // 2 - num_height // 2 - 1),
            num_text,
            fill='#FFFFFF',
            font=legend_font
        )

        # Defect name - LARGER, BOLDER
        defect_text = f"{item['name']}"
        draw.text((badge_x + badge_size + 20, current_y), defect_text, fill='#000000', font=legend_font)

        # Severity indicator - LARGER, BOLDER
        severity_label = f"[{item['severity'].upper()}]"
        severity_x = badge_x + badge_size + 20 + 280
        draw.text((severity_x, current_y), severity_label, fill=color_rgb, font=legend_font)

        # Location (if space permits) - LARGER text
        if img_width > 800:
            location_text = f"- {item['location'][:50]}"
            location_x = severity_x + 120
            draw.text((location_x, current_y), location_text, fill='#555555', font=legend_font)

        current_y += line_height

    return new_image

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