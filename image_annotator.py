"""
Image Annotation Module for Defactra AI
Marks and labels defects on property images
"""

from PIL import Image, ImageDraw, ImageFont
import io

def annotate_image_with_defects(image, defects, language='english'):
    """
    Annotate image with defect markers and labels

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

    # Define colors for severity levels
    severity_colors = {
        'critical': '#FF0066',
        'high': '#FF6600',
        'medium': '#FFCC00',
        'low': '#00FF99'
    }

    # Try to load a font, fallback to default if not available
    try:
        # Use a larger font for better visibility
        font_size = max(20, min(image.width, image.height) // 40)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size - 4)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Image dimensions
    img_width, img_height = annotated.size

    # If no defects, add a watermark showing the image was analyzed
    if not defects:
        # Add "No Defects Detected" watermark
        watermark_text = "✓ Analyzed - No Major Defects"
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Position at top center
        x = (img_width - text_width) // 2
        y = 30

        # Draw semi-transparent background
        padding = 10
        draw.rectangle(
            [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
            fill='#00FF9980',
            outline='#00FF99',
            width=2
        )
        draw.text((x, y), watermark_text, fill='#FFFFFF', font=font)

        return annotated

    # Estimate locations and mark defects
    # Since we don't have exact coordinates, we'll distribute markers intelligently

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

    # Draw markers for each defect
    marker_positions = []
    marker_number = 1

    for zone, zone_defects in location_zones.items():
        if not zone_defects:
            continue

        # Determine base position for this zone
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

        base_x, base_y = zone_positions.get(zone, (img_width // 2, img_height // 2))

        # Distribute defects in this zone
        for j, (defect_idx, defect) in enumerate(zone_defects):
            # Calculate position with slight offset for multiple defects in same zone
            offset = (j - len(zone_defects) // 2) * 80
            x = base_x + offset
            y = base_y + (j * 30 if len(zone_defects) > 1 else 0)

            # Ensure marker stays within image bounds
            x = max(60, min(x, img_width - 60))
            y = max(60, min(y, img_height - 60))

            severity = defect.get('severity', 'medium').lower()
            color = severity_colors.get(severity, '#808080')

            # Convert hex color to RGB
            color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

            # Draw marker circle
            marker_radius = 25
            draw.ellipse(
                [x - marker_radius, y - marker_radius, x + marker_radius, y + marker_radius],
                fill=color_rgb,
                outline='#FFFFFF',
                width=3
            )

            # Draw number in circle
            number_text = str(marker_number)
            bbox = draw.textbbox((0, 0), number_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw.text(
                (x - text_width // 2, y - text_height // 2),
                number_text,
                fill='#FFFFFF',
                font=font
            )

            # Draw line to label
            label_x = x + marker_radius + 10
            label_y = y

            # Adjust label position if too close to edge
            if label_x > img_width - 200:
                label_x = x - marker_radius - 10
                label_y = y

            draw.line([x + marker_radius, y, label_x, label_y], fill=color_rgb, width=2)

            # Create label text
            defect_name = defect.get('detected_object', 'Defect')
            if len(defect_name) > 25:
                defect_name = defect_name[:22] + '...'

            label_text = f"{marker_number}. {defect_name}"
            severity_text = defect.get('severity', 'medium').upper()

            # Draw label background
            bbox = draw.textbbox((0, 0), label_text, font=small_font)
            label_width = bbox[2] - bbox[0] + 20
            label_height = bbox[3] - bbox[1] + 30

            # Adjust if label goes out of bounds
            if label_x + label_width > img_width:
                label_x = img_width - label_width - 10
            if label_y + label_height > img_height:
                label_y = img_height - label_height - 10

            # Draw label box
            draw.rectangle(
                [label_x, label_y - 15, label_x + label_width, label_y + label_height - 15],
                fill=(*color_rgb, 200),
                outline='#FFFFFF',
                width=2
            )

            # Draw text
            draw.text((label_x + 10, label_y - 10), label_text, fill='#FFFFFF', font=small_font)
            draw.text((label_x + 10, label_y + 10), severity_text, fill='#FFFFFF', font=small_font)

            marker_positions.append((x, y))
            marker_number += 1

    # Add legend at bottom
    legend_y = img_height - 120
    legend_x = 20

    # Draw legend background
    draw.rectangle(
        [10, legend_y - 10, img_width - 10, img_height - 10],
        fill='#00000080',
        outline='#FFFFFF',
        width=2
    )

    # Draw legend title
    draw.text((legend_x, legend_y), "Severity Levels:", fill='#FFFFFF', font=font)

    # Draw severity indicators
    legend_items = [
        ('critical', 'CRITICAL'),
        ('high', 'HIGH'),
        ('medium', 'MEDIUM'),
        ('low', 'LOW')
    ]

    item_width = (img_width - 40) // len(legend_items)
    for i, (severity, label) in enumerate(legend_items):
        color = severity_colors[severity]
        color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

        item_x = legend_x + (i * item_width)
        item_y = legend_y + 30

        # Draw color box
        draw.rectangle(
            [item_x, item_y, item_x + 30, item_y + 20],
            fill=color_rgb,
            outline='#FFFFFF',
            width=1
        )

        # Draw label
        draw.text((item_x + 40, item_y), label, fill='#FFFFFF', font=small_font)

    return annotated

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