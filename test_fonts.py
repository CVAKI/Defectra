"""
Test Script: Verify Malayalam and Hindi PDF Rendering
Tests if the fonts are properly installed and working
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import io
import os

print("=" * 70)
print("Testing Malayalam and Hindi Font Rendering for Defactra AI")
print("=" * 70)
print()

# Test text samples
test_texts = {
    'english': 'Property Inspection Report - Defactra AI',
    'malayalam': 'വസ്തു പരിശോധന റിപ്പോർട്ട് - ഡിഫാക്ട്ര AI',
    'hindi': 'संपत्ति निरीक्षण रिपोर्ट - डिफैक्ट्रा AI'
}


def find_and_register_fonts():
    """Find and register Unicode fonts"""
    font_paths = [
        '/usr/share/fonts/truetype/noto/',
        '/usr/share/fonts/truetype/liberation/',
        '/usr/share/fonts/truetype/dejavu/',
    ]

    fonts_found = {}

    # Try Malayalam fonts
    malayalam_fonts = [
        'NotoSansMalayalam-Regular.ttf',
        'NotoSansMalayalam.ttf',
        'Meera-Regular.ttf',
    ]

    for font_dir in font_paths:
        if not os.path.exists(font_dir):
            continue
        for font_file in malayalam_fonts:
            full_path = os.path.join(font_dir, font_file)
            if os.path.exists(full_path):
                try:
                    pdfmetrics.registerFont(TTFont('Malayalam', full_path))
                    fonts_found['malayalam'] = full_path
                    print(f"✅ Malayalam font registered: {font_file}")
                    break
                except Exception as e:
                    print(f"⚠️  Failed to register {font_file}: {e}")
        if 'malayalam' in fonts_found:
            break

    # Try Hindi fonts
    hindi_fonts = [
        'NotoSansDevanagari-Regular.ttf',
        'NotoSansDevanagari.ttf',
        'Lohit-Devanagari.ttf',
    ]

    for font_dir in font_paths:
        if not os.path.exists(font_dir):
            continue
        for font_file in hindi_fonts:
            full_path = os.path.join(font_dir, font_file)
            if os.path.exists(full_path):
                try:
                    pdfmetrics.registerFont(TTFont('Hindi', full_path))
                    fonts_found['hindi'] = full_path
                    print(f"✅ Hindi font registered: {font_file}")
                    break
                except Exception as e:
                    print(f"⚠️  Failed to register {font_file}: {e}")
        if 'hindi' in fonts_found:
            break

    return fonts_found


# Register fonts
print("1. Searching for Unicode fonts...")
print()
fonts_found = find_and_register_fonts()
print()

if not fonts_found:
    print("❌ No Unicode fonts found!")
    print()
    print("Please install fonts by running:")
    print("   chmod +x install_fonts.sh")
    print("   ./install_fonts.sh")
    print()
    exit(1)

# Create test PDFs
print("2. Generating test PDFs...")
print()

for lang, text in test_texts.items():
    try:
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        story = []

        # Create style
        styles = getSampleStyleSheet()

        if lang == 'malayalam' and 'malayalam' in fonts_found:
            font_name = 'Malayalam'
        elif lang == 'hindi' and 'hindi' in fonts_found:
            font_name = 'Hindi'
        else:
            font_name = 'Helvetica'

        custom_style = ParagraphStyle(
            name='CustomStyle',
            parent=styles['Normal'],
            fontSize=16,
            fontName=font_name,
            textColor=colors.HexColor('#00F5FF'),
            leading=20
        )

        # Add test text
        story.append(Spacer(1, 100))
        story.append(Paragraph(text, custom_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Language: {lang.title()}", custom_style))
        story.append(Paragraph(f"Font: {font_name}", custom_style))

        # Build PDF
        doc.build(story)

        # Save to file
        filename = f'/mnt/user-data/outputs/test_{lang}.pdf'
        with open(filename, 'wb') as f:
            f.write(output.getvalue())

        print(f"   ✅ {lang.title()}: {filename}")

    except Exception as e:
        print(f"   ❌ {lang.title()}: {str(e)}")

print()
print("=" * 70)
print("✅ Font Test Complete!")
print("=" * 70)
print()
print("Results:")
for lang, font_path in fonts_found.items():
    print(f"   ✅ {lang.title()}: {os.path.basename(font_path)}")
print()

if len(fonts_found) == 2:
    print("🎉 All fonts working! Your PDFs should render correctly.")
    print()
    print("Next steps:")
    print("   1. Backup your current pdf_report_generator.py")
    print("   2. Replace it with pdf_report_generator_fixed.py:")
    print("      cp pdf_report_generator_fixed.py pdf_report_generator.py")
    print("   3. Run your Streamlit app: streamlit run app.py")
else:
    print("⚠️  Some fonts are missing. Run install_fonts.sh to install them.")
print()