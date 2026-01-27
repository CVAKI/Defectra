"""
Demo: PDF Report Generation for Defactra AI
This demonstrates the PDF generation with sample data
"""

from PIL import Image, ImageDraw, ImageFont
from pdf_report_generator import generate_pdf_report
from translations import get_text
import io

# Create sample property data
property_data = {
    'property_id': 'P12ABC',
    'address': '123 Main Street, Downtown',
    'city': 'Trivandrum',
    'property_type': 'Villa',
    'bedrooms': 4,
    'area_sqft': 2500,
    'year_built': 2015,
    'room_name': 'Master Bedroom',
    'overall_score': 65,
    'usability': 'fair - needs repairs'
}

# Create sample defects
defects = [
    {
        'detected_object': 'Major wall crack',
        'severity': 'critical',
        'confidence_score': 92.5,
        'location': 'North wall, upper right corner',
        'description': 'A significant vertical crack measuring approximately 2 feet in length has been detected on the north wall. This appears to be a structural issue that could indicate foundation settlement or seismic activity. The crack shows signs of recent expansion.',
        'repair_priority': 'immediate',
        'estimated_impact': 'Critical safety concern. May affect structural integrity. Property value significantly impacted. Immediate professional assessment required.'
    },
    {
        'detected_object': 'Water damage and staining',
        'severity': 'high',
        'confidence_score': 88.3,
        'location': 'Ceiling, center area near window',
        'description': 'Extensive water staining covering approximately 3 square feet on the ceiling suggests an active or recent leak. Discoloration pattern indicates water intrusion from above, possibly from roof or plumbing issues.',
        'repair_priority': 'urgent',
        'estimated_impact': 'High priority issue. Could lead to mold growth, ceiling collapse, or extensive water damage. Repair required within 7 days to prevent escalation.'
    },
    {
        'detected_object': 'Peeling paint',
        'severity': 'medium',
        'confidence_score': 76.2,
        'location': 'East wall, lower section',
        'description': 'Paint is peeling and bubbling on the lower section of the east wall, likely due to moisture infiltration or poor surface preparation. The affected area is approximately 4 square feet.',
        'repair_priority': 'routine',
        'estimated_impact': 'Moderate concern. Affects aesthetics and could worsen if left unattended. Should be addressed within 30 days to maintain property appearance.'
    },
    {
        'detected_object': 'Minor floor scratches',
        'severity': 'low',
        'confidence_score': 65.0,
        'location': 'Hardwood floor, near entrance',
        'description': 'Surface scratches visible on hardwood flooring near the room entrance. These appear to be from normal wear and tear and do not affect structural integrity.',
        'repair_priority': 'cosmetic',
        'estimated_impact': 'Minor cosmetic issue. Does not affect functionality or safety. Can be addressed during regular maintenance or renovation.'
    },
    {
        'detected_object': 'Electrical outlet damage',
        'severity': 'high',
        'confidence_score': 85.7,
        'location': 'West wall, bottom outlet',
        'description': 'The electrical outlet shows signs of heat damage or burning around the edges. This indicates potential electrical issues such as loose connections, overloading, or faulty wiring.',
        'repair_priority': 'urgent',
        'estimated_impact': 'Safety hazard. Fire risk present. Professional electrician inspection required immediately. Do not use this outlet until repaired.'
    }
]

# Create sample annotated images (simulated property images)
def create_sample_room_image():
    """Create a sample room image for demonstration"""
    img = Image.new('RGB', (800, 600), color='#f5f5f5')
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    # Draw simulated room
    # Walls
    draw.rectangle([50, 100, 750, 500], fill='#e8e8e8', outline='#333', width=3)

    # Floor
    draw.rectangle([50, 400, 750, 500], fill='#c4a57b', outline='#333', width=2)

    # Window
    draw.rectangle([300, 120, 500, 300], fill='#87CEEB', outline='#333', width=3)
    draw.line([400, 120, 400, 300], fill='#333', width=3)
    draw.line([300, 210, 500, 210], fill='#333', width=3)

    # Door
    draw.rectangle([620, 250, 720, 500], fill='#8B4513', outline='#333', width=3)
    draw.ellipse([640, 350, 650, 360], fill='#FFD700')

    # Defect markers (approximate locations)
    # Critical crack
    draw.line([680, 150, 690, 250], fill='#FF0066', width=5)

    # Water stain
    draw.ellipse([350, 130, 450, 180], fill='#8B7355', outline='#FF6600', width=3)

    # Peeling paint
    for i in range(5):
        draw.rectangle([100 + i*15, 420 + i*10, 115 + i*15, 440 + i*10],
                      fill='#FFCC00', outline='#FFB300', width=2)

    # Add title
    draw.text((250, 30), "Master Bedroom - Inspection View", fill='#1a1a1a', font=title_font)
    draw.text((280, 530), "Defactra AI Analysis", fill='#00f5ff', font=text_font)

    return img

# Generate sample images
images = [create_sample_room_image()]

# Generate PDF in all three languages
print("=" * 70)
print("Defactra AI - PDF Report Generation Demo")
print("=" * 70)
print()

languages = ['english', 'malayalam', 'hindi']
language_names = {
    'english': 'English',
    'malayalam': 'Malayalam (മലയാളം)',
    'hindi': 'Hindi (हिंदी)'
}

for lang in languages:
    print(f"Generating report in {language_names[lang]}...")

    try:
        # Generate PDF
        pdf_path = f"/mnt/user-data/outputs/Defactra_Report_{lang.upper()}.pdf"
        generate_pdf_report(
            property_data=property_data,
            defects=defects,
            images=images,
            language=lang,
            output_path=pdf_path
        )

        print(f"✅ {language_names[lang]} report generated: {pdf_path}")
        print()

    except Exception as e:
        print(f"❌ Error generating {language_names[lang]} report: {e}")
        import traceback
        print(traceback.format_exc())
        print()

print("=" * 70)
print("Demo Complete!")
print("=" * 70)
print()
print("📁 Generated Reports:")
print("   1. English:   /mnt/user-data/outputs/Defactra_Report_ENGLISH.pdf")
print("   2. Malayalam: /mnt/user-data/outputs/Defactra_Report_MALAYALAM.pdf")
print("   3. Hindi:     /mnt/user-data/outputs/Defactra_Report_HINDI.pdf")
print()
print("Features included:")
print("   ✅ Multi-language support (English, Malayalam, Hindi)")
print("   ✅ Professional design matching web theme")
print("   ✅ Annotated images with defect markers")
print("   ✅ Detailed defect analysis")
print("   ✅ Severity color coding")
print("   ✅ Risk assessment")
print("   ✅ Recommendations")
print()