"""
PDF Report Generator for Defactra AI - WORKAROUND VERSION
Uses romanization for Malayalam/Hindi when Unicode fonts are unavailable
This allows PDFs to generate even without system fonts installed
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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from PIL import Image
import io
import os

from translations import get_text, get_severity_color
from image_annotator import (
    annotate_image_with_defects,
    create_thumbnail,
    create_defect_details_section
)

# Romanization mappings for when Unicode fonts are unavailable
ROMANIZATION = {
    'malayalam': {
        'വസ്തു പരിശോധന റിപ്പോർട്ട്': 'Vasthu Parishodhana Report',
        'ഡിഫാക്ട്ര AI നിർമ്മിച്ചത്': 'Difaktra AI nirmichath',
        'പരിശോധന തീയതി': 'Parishodhana Thiyathi',
        'വസ്തുവിന്റെ വിശദാംശങ്ങൾ': 'Vasthuvin്റെ Vishadhamshangal',
        'എക്സിക്യൂട്ടീവ് സംഗ്രഹം': 'Executive Summary',
        'കേടുപാടുകളുടെ വിശകലനം': 'Kedupadukalu്റെ Vishakallanam',
        'അപകട വിലയിരുത്തൽ': 'Apakada Vilayiruthal',
        'ശുപാർശകൾ': 'Shuparshakal',
        'വസ്തു ഐഡി': 'Vasthu ID',
        'വിലാസം': 'Vilasam',
        'നഗരം': 'Nagaram',
        'തരം': 'Tharam',
        'കിടപ്പുമുറികൾ': 'Kidappumurikal',
        'വിസ്തീർണ്ണം (ചതുരശ്ര അടി)': 'Vistheernam (sq ft)',
        'നിർമ്മിച്ച വർഷം': 'Nirmmicha Varsham',
        'മുറി': 'Muri',
        'മൊത്തം അവസ്ഥ സ്കോർ': 'Mottham Avastha Score',
        'ആകെ കേടുപാടുകൾ': 'Aake Kedupadukal',
        'ഗുരുതര പ്രശ്നങ്ങൾ': 'Guruthara Prashnnangal',
        'ഉയർന്ന മുൻഗണന': 'Uyarnna Mungadana',
        'ഇടത്തരം മുൻഗണന': 'Idattharam Mungadana',
        'കുറഞ്ഞ മുൻഗണന': 'Kuranja Mungadana',
        'ഉപയോഗക്ഷമത റേറ്റിംഗ്': 'Upayogakshamatha Rating',
        'പേജ്': 'Page',
    },
    'hindi': {
        'संपत्ति निरीक्षण रिपोर्ट': 'Sampatti Nirikshan Report',
        'डिफैक्ट्रा AI द्वारा निर्मित': 'Difaktra AI dwara nirmit',
        'निरीक्षण तिथि': 'Nirikshan Tithi',
        'संपत्ति विवरण': 'Sampatti Vivaran',
        'कार्यकारी सारांश': 'Executive Summary',
        'दोष विश्लेषण': 'Dosh Vishleshan',
        'जोखिम मूल्यांकन': 'Jokhim Mulyakan',
        'सिफारिशें': 'Sifarishen',
        'संपत्ति आईडी': 'Sampatti ID',
        'पता': 'Pata',
        'शहर': 'Shahar',
        'प्रकार': 'Prakar',
        'शयनकक्ष': 'Shayanakaksh',
        'क्षेत्रफल (वर्ग फुट)': 'Kshetrafal (sq ft)',
        'निर्माण वर्ष': 'Nirman Varsh',
        'कमरा': 'Kamra',
        'समग्र स्थिति स्कोर': 'Samagra Sthiti Score',
        'कुल दोष पाए गए': 'Kul Dosh Paye Gaye',
        'गंभीर समस्याएं': 'Gambhir Samasyayen',
        'उच्च प्राथमिकता': 'Uchch Prathmikta',
        'मध्यम प्राथमिकता': 'Madhyam Prathmikta',
        'कम प्राथमिकता': 'Kam Prathmikta',
        'उपयोगिता रेटिंग': 'Upyogita Rating',
        'पृष्ठ': 'Prishth',
    }
}


def romanize_text(text, language):
    """
    Romanize Malayalam/Hindi text when Unicode fonts are unavailable

    Args:
        text: Text to romanize
        language: Language code

    Returns:
        Romanized text or original if not found
    """
    if language not in ['malayalam', 'hindi']:
        return text

    if language in ROMANIZATION and text in ROMANIZATION[language]:
        romanized = ROMANIZATION[language][text]
        return f"{romanized} [{text}]"  # Show both versions

    return text


def try_register_unicode_fonts():
    """
    Try to register Unicode fonts if available
    Returns dict of successfully registered fonts
    """
    fonts_registered = {}

    try:
        # Common font locations
        font_paths = [
            '/usr/share/fonts/truetype/noto/',
            '/usr/share/fonts/truetype/liberation/',
            '/usr/share/fonts/truetype/dejavu/',
            '/usr/share/fonts/truetype/freefont/',
            '/usr/local/share/fonts/',
        ]

        # Malayalam fonts to try
        malayalam_fonts = [
            'NotoSansMalayalam-Regular.ttf',
            'NotoSansMalayalam.ttf',
            'Meera-Regular.ttf',
            'FreeSerif.ttf',  # Has some Unicode support
        ]

        # Hindi fonts to try
        hindi_fonts = [
            'NotoSansDevanagari-Regular.ttf',
            'NotoSansDevanagari.ttf',
            'Lohit-Devanagari.ttf',
            'FreeSerif.ttf',  # Has some Unicode support
        ]

        # Try to register Malayalam font
        for font_dir in font_paths:
            if not os.path.exists(font_dir):
                continue
            for font_file in malayalam_fonts:
                full_path = os.path.join(font_dir, font_file)
                if os.path.exists(full_path):
                    try:
                        pdfmetrics.registerFont(TTFont('Malayalam', full_path))
                        fonts_registered['malayalam'] = True
                        print(f"✅ Malayalam font registered: {font_file}")
                        break
                    except:
                        continue
            if 'malayalam' in fonts_registered:
                break

        # Try to register Hindi font
        for font_dir in font_paths:
            if not os.path.exists(font_dir):
                continue
            for font_file in hindi_fonts:
                full_path = os.path.join(font_dir, font_file)
                if os.path.exists(full_path):
                    try:
                        pdfmetrics.registerFont(TTFont('Hindi', full_path))
                        fonts_registered['hindi'] = True
                        print(f"✅ Hindi font registered: {font_file}")
                        break
                    except:
                        continue
            if 'hindi' in fonts_registered:
                break

    except Exception as e:
        print(f"⚠️ Font registration warning: {e}")

    return fonts_registered


def get_font_for_language(language, fonts_available):
    """
    Get appropriate font name for language with fallback

    Args:
        language: Language code
        fonts_available: Dict of available fonts

    Returns:
        Font name string
    """
    if language == 'malayalam' and fonts_available.get('malayalam'):
        return 'Malayalam'
    elif language == 'hindi' and fonts_available.get('hindi'):
        return 'Hindi'
    else:
        return 'Helvetica'


class DefactraReportTemplate:
    """Custom PDF template with Defactra branding"""

    def __init__(self, language='english', fonts_available=None):
        self.language = language
        self.fonts_available = fonts_available or {}
        self.font = get_font_for_language(language, self.fonts_available)
        self.use_romanization = language in ['malayalam', 'hindi'] and not self.fonts_available.get(language)

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

        # Subtitle
        canvas.setFillColorRGB(0.63, 0.63, 1)
        try:
            canvas.setFont(self.font, 10)
        except:
            canvas.setFont("Helvetica", 10)

        subtitle_text = get_text('generated_by', self.language)
        if self.use_romanization:
            subtitle_text = romanize_text(subtitle_text, self.language)
        canvas.drawString(40, A4[1] - 65, subtitle_text)

        canvas.restoreState()

    def footer(self, canvas, doc):
        """Draw footer on each page"""
        canvas.saveState()

        # Footer background
        canvas.setFillColorRGB(0.06, 0.05, 0.16)
        canvas.rect(0, 0, A4[0], 50, fill=1, stroke=0)

        # Page number - always use English
        canvas.setFillColorRGB(0.63, 0.63, 1)
        canvas.setFont("Helvetica-Bold", 9)
        page_text = f"Page {doc.page}"
        canvas.drawRightString(A4[0] - 40, 15, page_text)

        canvas.restoreState()


def create_custom_styles(language='english', fonts_available=None):
    """Create custom paragraph styles"""
    styles = getSampleStyleSheet()
    fonts_available = fonts_available or {}

    base_font = get_font_for_language(language, fonts_available)

    # Use Helvetica-Bold for English, same font for others
    if language == 'english':
        title_font = 'Helvetica-Bold'
        header_font = 'Helvetica-Bold'
    else:
        title_font = base_font
        header_font = base_font

    normal_font = base_font

    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,  # Slightly smaller to fit romanized text
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
        fontName=normal_font,
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
        fontName=normal_font,
        leading=11
    ))

    styles.add(ParagraphStyle(
        name='DefectDesc',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#404040'),
        spaceAfter=4,
        leftIndent=20,
        fontName=normal_font,
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
    Generate PDF report with Unicode support and romanization fallback
    """

    # Try to register Unicode fonts
    fonts_available = try_register_unicode_fonts()

    use_romanization = language in ['malayalam', 'hindi'] and not fonts_available.get(language)

    if use_romanization:
        print(f"⚠️ Unicode fonts for {language} not available - using romanization")
        print("   Install fonts for better rendering: apt-get install fonts-noto")

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

    template = DefactraReportTemplate(language, fonts_available)
    story = []
    styles = create_custom_styles(language, fonts_available)

    # Helper function to get text
    def get_localized_text(key):
        text = get_text(key, language)
        if use_romanization:
            text = romanize_text(text, language)
        return text

    # TITLE PAGE
    title_text = get_localized_text('report_title')
    title = Paragraph(title_text, styles['CustomTitle'])
    story.append(title)
    story.append(Spacer(1, 20))

    # Date and property ID
    inspection_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    date_text = f"{get_localized_text('inspection_date')}: {inspection_date}"
    story.append(Paragraph(date_text, styles['CustomNormal']))
    story.append(Spacer(1, 10))

    property_id = property_data.get('property_id', 'N/A')
    id_text = f"{get_localized_text('property_id')}: <b>{property_id}</b>"
    story.append(Paragraph(id_text, styles['CustomNormal']))
    story.append(Spacer(1, 30))

    # PROPERTY DETAILS
    story.append(Paragraph(get_localized_text('property_details'), styles['SectionHeader']))
    story.append(Spacer(1, 10))

    table_font = get_font_for_language(language, fonts_available)

    property_details = [
        [get_localized_text('address'), property_data.get('address', 'N/A')],
        [get_localized_text('city'), property_data.get('city', 'N/A')],
        [get_localized_text('property_type'), property_data.get('property_type', 'N/A')],
        [get_localized_text('bedrooms'), str(property_data.get('bedrooms', 'N/A'))],
        [get_localized_text('area'), f"{property_data.get('area_sqft', 'N/A')} sq ft"],
        [get_localized_text('year_built'), str(property_data.get('year_built', 'N/A'))],
        [get_localized_text('room_name'), property_data.get('room_name', 'N/A')],
    ]

    prop_table = Table(property_details, colWidths=[2.5 * inch, 3 * inch])
    prop_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F4FF')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0080FF')),
        ('FONTNAME', (0, 0), (-1, -1), table_font),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(prop_table)
    story.append(Spacer(1, 20))

    # EXECUTIVE SUMMARY
    story.append(Paragraph(get_localized_text('executive_summary'), styles['SectionHeader']))
    story.append(Spacer(1, 10))

    total_defects = len(defects)
    critical_count = len([d for d in defects if d.get('severity', '').lower() == 'critical'])
    high_count = len([d for d in defects if d.get('severity', '').lower() == 'high'])
    medium_count = len([d for d in defects if d.get('severity', '').lower() == 'medium'])
    low_count = len([d for d in defects if d.get('severity', '').lower() == 'low'])

    overall_score = property_data.get('overall_score', 75)
    usability = property_data.get('usability', 'good')

    summary_data = [
        [get_localized_text('overall_condition'), f"{overall_score}/100"],
        [get_localized_text('usability_rating'), usability.upper()],
        [get_localized_text('total_defects'), str(total_defects)],
        [get_localized_text('critical_issues'), str(critical_count)],
        [get_localized_text('high_priority'), str(high_count)],
        [get_localized_text('medium_priority'), str(medium_count)],
        [get_localized_text('low_priority'), str(low_count)],
    ]

    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F8FF')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#00F5FF')),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), table_font),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))

    # Color coding
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

    # ANNOTATED IMAGES
    if images:
        story.append(PageBreak())
        story.append(Paragraph(get_localized_text('defect_analysis'), styles['SectionHeader']))
        story.append(Spacer(1, 10))

        for idx, img in enumerate(images, 1):
            annotated_img, legend_data = annotate_image_with_defects(img, defects, language)

            img_thumbnail = create_thumbnail(annotated_img, max_size=(600, 500))
            img_buffer = io.BytesIO()
            img_thumbnail.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            rl_img = RLImage(img_buffer, width=6 * inch, height=4.5 * inch, kind='proportional')

            caption = Paragraph(f"<b>{get_localized_text('defect_analysis')} - {idx}</b>", styles['CustomNormal'])

            story.append(KeepTogether([caption, Spacer(1, 5), rl_img]))
            story.append(Spacer(1, 15))

            if legend_data is not None and len(legend_data) > 0:
                defect_elements = create_defect_details_section(legend_data, styles)
                for element in defect_elements:
                    story.append(element)

                if idx < len(images):
                    story.append(PageBreak())

    # RECOMMENDATIONS
    story.append(PageBreak())
    story.append(Paragraph(get_localized_text('recommendations'), styles['SectionHeader']))
    story.append(Spacer(1, 10))

    recommendations = []
    if critical_count > 0:
        recommendations.append(f"• {get_localized_text('rec_critical')}")
    if high_count > 0:
        recommendations.append(f"• {get_localized_text('rec_high')}")
    if medium_count > 0:
        recommendations.append(f"• {get_localized_text('rec_medium')}")
    if low_count > 0:
        recommendations.append(f"• {get_localized_text('rec_low')}")
    recommendations.append(f"• {get_localized_text('rec_general')}")

    for rec in recommendations:
        story.append(Paragraph(rec, styles['CustomNormal']))
        story.append(Spacer(1, 6))

    # BUILD PDF
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