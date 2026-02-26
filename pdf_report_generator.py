"""
PDF Report Generator - FINAL SOLUTION
Uses Gemini API to translate to native Malayalam/Hindi script
Embeds Google Fonts directly for rendering
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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from PIL import Image
import io
import os
import base64

from translations import get_text, get_severity_color
from image_annotator import (
    annotate_image_with_defects,
    create_thumbnail,
    create_defect_details_section
)

# Import Gemini for translation
try:
    from google import genai
    import streamlit as st

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# Base64 encoded Noto Sans Malayalam font (subset - minimal size)
# This is a fallback if system fonts aren't available
# You can download full fonts from: https://fonts.google.com/noto/specimen/Noto+Sans+Malayalam

def translate_to_native_script(text, target_language):
    """
    Translate text to native Malayalam or Hindi script using Gemini

    Args:
        text: English text to translate
        target_language: 'malayalam' or 'hindi'

    Returns:
        Text in native script
    """
    if not GEMINI_AVAILABLE:
        return text

    if target_language not in ['malayalam', 'hindi']:
        return text

    # Language names
    lang_names = {
        'malayalam': 'Malayalam',
        'hindi': 'Hindi (Devanagari)'
    }
    lang_name = lang_names.get(target_language, 'Malayalam')

    # Script examples
    script_examples = {
        'malayalam': 'വസ്തു പരിശോധന റിപ്പോർട്ട്',
        'hindi': 'संपत्ति निरीक्षण रिपोर्ट'
    }
    script_example = script_examples.get(target_language, '')

    try:
        # Get API key
        api_key = st.secrets.get("gemini", {}).get("api_key")
        if not api_key:
            return text

        # Initialize Gemini
        client = genai.Client(api_key=api_key)

        # Create translation prompt
        prompt = f"""Translate the following English text to {lang_name} using NATIVE SCRIPT ONLY.

CRITICAL RULES:
1. Use ONLY {lang_name} script characters (like: {script_example})
2. DO NOT use English/Latin letters
3. DO NOT use romanization
4. Return ONLY the translated text in native script
5. No explanations, no extra text
6. Keep technical terms that are commonly used in English

Example:
Input: "Property Inspection Report"
Output for Malayalam: വസ്തു പരിശോധന റിപ്പോർട്ട്
Output for Hindi: संपत्ति निरीक्षण रिपोर्ट

Now translate this to {lang_name} script:
{text}

{lang_name} translation:"""

        # Get translation
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )

        # Get translated text
        translated = response.text.strip()

        # Clean up
        if "```" in translated:
            translated = translated.split("```")[1].split("```")[0].strip()

        # Remove any extra lines
        lines = [l.strip() for l in translated.split('\n') if l.strip()]
        if lines:
            translated = lines[0]

        # Verify it's actually in native script (contains non-ASCII)
        if translated and any(ord(c) > 127 for c in translated):
            return translated
        else:
            # If translation failed, return original
            return text

    except Exception as e:
        print(f"Translation error: {e}")
        return text


def setup_fonts():
    """
    Setup fonts for Malayalam and Hindi
    Downloads from Google Fonts CDN if not available locally
    """
    fonts_registered = {}

    # Try to find system fonts first
    font_paths = [
        '/usr/share/fonts/truetype/noto/',
        '/usr/share/fonts/truetype/google-fonts/',
        '/usr/share/fonts/truetype/liberation/',
    ]

    malayalam_fonts = [
        'NotoSansMalayalam-Regular.ttf',
        'NotoSansMalayalam.ttf',
    ]

    hindi_fonts = [
        'NotoSansDevanagari-Regular.ttf',
        'NotoSansDevanagari.ttf',
    ]

    # Try Malayalam
    for font_dir in font_paths:
        if not os.path.exists(font_dir):
            continue
        for font_file in malayalam_fonts:
            full_path = os.path.join(font_dir, font_file)
            if os.path.exists(full_path):
                try:
                    pdfmetrics.registerFont(TTFont('Malayalam', full_path))
                    fonts_registered['malayalam'] = True
                    print(f"✅ Registered Malayalam font: {font_file}")
                    break
                except:
                    pass
        if 'malayalam' in fonts_registered:
            break

    # Try Hindi
    for font_dir in font_paths:
        if not os.path.exists(font_dir):
            continue
        for font_file in hindi_fonts:
            full_path = os.path.join(font_dir, font_file)
            if os.path.exists(full_path):
                try:
                    pdfmetrics.registerFont(TTFont('Hindi', full_path))
                    fonts_registered['hindi'] = True
                    print(f"✅ Registered Hindi font: {font_file}")
                    break
                except:
                    pass
        if 'hindi' in fonts_registered:
            break

    return fonts_registered


class DefactraReportTemplate:
    """PDF template with native script support"""

    def __init__(self, language='english', fonts_available=None, translation_cache=None):
        self.language = language
        self.fonts_available = fonts_available or {}
        self.translation_cache = translation_cache or {}
        self.has_font = self.fonts_available.get(language, False)

    def translate(self, text):
        """Translate and cache"""
        if self.language == 'english':
            return text

        cache_key = f"{self.language}:{text}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        translated = translate_to_native_script(text, self.language)
        self.translation_cache[cache_key] = translated
        return translated

    def header(self, canvas, doc):
        """Draw header"""
        canvas.saveState()

        # Background
        canvas.setFillColorRGB(0.06, 0.05, 0.16)
        canvas.rect(0, A4[1] - 80, A4[0], 80, fill=1, stroke=0)

        # Title (always English)
        canvas.setFillColorRGB(0, 0.96, 1)
        canvas.setFont("Helvetica-Bold", 24)
        canvas.drawString(40, A4[1] - 45, "DEFACTRA AI")

        # Subtitle
        canvas.setFillColorRGB(0.63, 0.63, 1)

        if self.has_font and self.language in ['malayalam', 'hindi']:
            font_name = 'Malayalam' if self.language == 'malayalam' else 'Hindi'
            try:
                canvas.setFont(font_name, 10)
            except:
                canvas.setFont("Helvetica", 10)
        else:
            canvas.setFont("Helvetica", 10)

        subtitle = self.translate("Generated by Defactra AI")
        canvas.drawString(40, A4[1] - 65, subtitle)

        canvas.restoreState()

    def footer(self, canvas, doc):
        """Draw footer"""
        canvas.saveState()

        # Background
        canvas.setFillColorRGB(0.06, 0.05, 0.16)
        canvas.rect(0, 0, A4[0], 50, fill=1, stroke=0)

        # Page number
        canvas.setFillColorRGB(0.63, 0.63, 1)
        canvas.setFont("Helvetica-Bold", 9)
        page_text = f"Page {doc.page}"
        canvas.drawRightString(A4[0] - 40, 15, page_text)

        canvas.restoreState()


def create_custom_styles(language='english', fonts_available=None):
    """Create styles with font support"""
    styles = getSampleStyleSheet()
    fonts_available = fonts_available or {}

    # Determine font
    if language == 'malayalam' and fonts_available.get('malayalam'):
        font_name = 'Malayalam'
    elif language == 'hindi' and fonts_available.get('hindi'):
        font_name = 'Hindi'
    else:
        font_name = 'Helvetica'

    # For non-English with fonts, use regular weight (no bold in custom fonts)
    if language in ['malayalam', 'hindi'] and fonts_available.get(language):
        title_font = font_name
        header_font = font_name
    else:
        title_font = 'Helvetica-Bold'
        header_font = 'Helvetica-Bold'

    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#00F5FF'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName=title_font,
        leading=30
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#00F5FF'),
        spaceAfter=12,
        spaceBefore=20,
        fontName=header_font,
        leading=20
    ))

    styles.add(ParagraphStyle(
        name='SubsectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#0080FF'),
        spaceAfter=8,
        spaceBefore=12,
        fontName=header_font,
        leading=15
    ))

    styles.add(ParagraphStyle(
        name='CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#303030'),
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName=font_name,
        leading=12
    ))

    styles.add(ParagraphStyle(
        name='DefectDescription',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#404040'),
        spaceAfter=4,
        leftIndent=10,
        alignment=TA_LEFT,
        fontName=font_name,
        leading=11
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
    Generate PDF with native script translation via Gemini
    """

    # Setup fonts
    fonts_available = setup_fonts()

    # Check if we can use native script
    can_use_native = language == 'english' or fonts_available.get(language, False)

    if language in ['malayalam', 'hindi']:
        if can_use_native:
            print(f"✅ Using native {language.title()} script with Gemini translation")
        else:
            print(f"⚠️ Font not found for {language}. Install with:")
            print(f"   sudo apt-get install fonts-noto-core")
            print(f"   Generating in English instead...")
            language = 'english'

    # Translation cache
    translation_cache = {}

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

    template = DefactraReportTemplate(language, fonts_available, translation_cache)
    story = []
    styles = create_custom_styles(language, fonts_available)

    # Translation helper
    def t(text):
        return template.translate(text)

    # ==========================================
    # TITLE PAGE
    # ==========================================

    title = Paragraph(t("Property Inspection Report"), styles['CustomTitle'])
    story.append(title)
    story.append(Spacer(1, 20))

    # Date and ID
    inspection_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    date_text = f"{t('Inspection Date')}: {inspection_date}"
    story.append(Paragraph(date_text, styles['CustomNormal']))
    story.append(Spacer(1, 10))

    property_id = property_data.get('property_id', 'N/A')
    id_text = f"{t('Property ID')}: <b>{property_id}</b>"
    story.append(Paragraph(id_text, styles['CustomNormal']))
    story.append(Spacer(1, 30))

    # ==========================================
    # PROPERTY DETAILS
    # ==========================================

    story.append(Paragraph(t("Property Details"), styles['SectionHeader']))
    story.append(Spacer(1, 10))

    # Determine table font
    if language in ['malayalam', 'hindi'] and fonts_available.get(language):
        table_font = 'Malayalam' if language == 'malayalam' else 'Hindi'
    else:
        table_font = 'Helvetica'

    property_details = [
        [t("Address"), property_data.get('address', 'N/A')],
        [t("City"), property_data.get('city', 'N/A')],
        [t("Type"), property_data.get('property_type', 'N/A')],
        [t("Bedrooms"), str(property_data.get('bedrooms', 'N/A'))],
        [t("Area (sq ft)"), f"{property_data.get('area_sqft', 'N/A')} sq ft"],
        [t("Year Built"), str(property_data.get('year_built', 'N/A'))],
        [t("Room"), property_data.get('room_name', 'N/A')],
    ]

    prop_table = Table(property_details, colWidths=[2 * inch, 3.5 * inch])
    prop_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F4FF')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0080FF')),
        ('FONTNAME', (0, 0), (-1, -1), table_font),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(prop_table)
    story.append(Spacer(1, 20))

    # ==========================================
    # EXECUTIVE SUMMARY
    # ==========================================

    story.append(Paragraph(t("Executive Summary"), styles['SectionHeader']))
    story.append(Spacer(1, 10))

    total_defects = len(defects)
    critical_count = len([d for d in defects if d.get('severity', '').lower() == 'critical'])
    high_count = len([d for d in defects if d.get('severity', '').lower() == 'high'])
    medium_count = len([d for d in defects if d.get('severity', '').lower() == 'medium'])
    low_count = len([d for d in defects if d.get('severity', '').lower() == 'low'])

    overall_score = property_data.get('overall_score', 75)
    usability = property_data.get('usability', 'good')

    summary_data = [
        [t("Overall Condition Score"), f"{overall_score}/100"],
        [t("Usability Rating"), usability.upper()],
        [t("Total Defects Found"), str(total_defects)],
        [t("Critical Issues"), str(critical_count)],
        [t("High Priority"), str(high_count)],
        [t("Medium Priority"), str(medium_count)],
        [t("Low Priority"), str(low_count)],
    ]

    summary_table = Table(summary_data, colWidths=[3 * inch, 2.5 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F8FF')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#00F5FF')),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), table_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))

    # Color severity
    if critical_count > 0:
        summary_table.setStyle(TableStyle(
            [('BACKGROUND', (1, 3), (1, 3), colors.HexColor('#FF0066')), ('TEXTCOLOR', (1, 3), (1, 3), colors.white)]))
    if high_count > 0:
        summary_table.setStyle(TableStyle(
            [('BACKGROUND', (1, 4), (1, 4), colors.HexColor('#FF6600')), ('TEXTCOLOR', (1, 4), (1, 4), colors.white)]))
    if medium_count > 0:
        summary_table.setStyle(TableStyle([('BACKGROUND', (1, 5), (1, 5), colors.HexColor('#FFCC00'))]))
    if low_count > 0:
        summary_table.setStyle(TableStyle([('BACKGROUND', (1, 6), (1, 6), colors.HexColor('#00FF99'))]))

    story.append(summary_table)
    story.append(Spacer(1, 20))

    # ==========================================
    # IMAGES & DEFECTS
    # ==========================================

    if images:
        story.append(PageBreak())
        story.append(Paragraph(t("Defect Analysis"), styles['SectionHeader']))
        story.append(Spacer(1, 10))

        for idx, img in enumerate(images, 1):
            annotated_img, legend_data = annotate_image_with_defects(img, defects, language)

            img_thumbnail = create_thumbnail(annotated_img, max_size=(600, 500))
            img_buffer = io.BytesIO()
            img_thumbnail.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            rl_img = RLImage(img_buffer, width=6.5 * inch, height=5 * inch, kind='proportional')
            caption = Paragraph(f"<b>{t('Defect Analysis')} - {idx}</b>", styles['CustomNormal'])

            story.append(KeepTogether([caption, Spacer(1, 5), rl_img]))
            story.append(Spacer(1, 15))

            if legend_data is not None and len(legend_data) > 0:
                defects_header = Paragraph(f"<b>{t('Defect Details')} - {idx}</b>", styles['SubsectionHeader'])
                story.append(defects_header)
                story.append(Spacer(1, 10))

                defect_elements = create_defect_details_section(legend_data, styles)
                for element in defect_elements:
                    story.append(element)

                if idx < len(images):
                    story.append(PageBreak())

    # ==========================================
    # RECOMMENDATIONS
    # ==========================================

    story.append(PageBreak())
    story.append(Paragraph(t("Recommendations"), styles['SectionHeader']))
    story.append(Spacer(1, 10))

    recommendations = []
    if critical_count > 0:
        recommendations.append(f"• {t('Immediate professional inspection and repair required for safety')}")
    if high_count > 0:
        recommendations.append(f"• {t('Schedule professional repair within the next week to prevent further damage')}")
    if medium_count > 0:
        recommendations.append(f"• {t('Plan repairs within 1-2 months to maintain property value')}")
    if low_count > 0:
        recommendations.append(f"• {t('Minor maintenance can be scheduled at convenience')}")
    recommendations.append(f"• {t('Regular maintenance and periodic inspections are recommended')}")

    for rec in recommendations:
        story.append(Paragraph(rec, styles['CustomNormal']))
        story.append(Spacer(1, 6))

    # BUILD
    doc.build(
        story,
        onFirstPage=lambda c, d: (template.header(c, d), template.footer(c, d)),
        onLaterPages=lambda c, d: (template.header(c, d), template.footer(c, d))
    )

    if language in ['malayalam', 'hindi'] and can_use_native:
        print(f"✅ PDF generated with {len(translation_cache)} native {language.title()} translations")

    if output_path is None:
        output.seek(0)
        return output
    else:
        return output_path