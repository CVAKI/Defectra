#!/bin/bash

echo "=========================================="
echo "Installing Unicode Fonts for Defactra AI"
echo "Malayalam and Hindi PDF Support"
echo "=========================================="
echo ""

# Update package list
echo "📦 Updating package list..."
sudo apt-get update

echo ""
echo "📥 Installing Noto Fonts (Best for Indian Languages)..."
sudo apt-get install -y fonts-noto fonts-noto-core fonts-noto-ui-core

echo ""
echo "📥 Installing Additional Malayalam Fonts..."
sudo apt-get install -y fonts-malayalam fonts-mlym fonts-smc-anjalioldlipi fonts-smc-meera

echo ""
echo "📥 Installing Additional Hindi/Devanagari Fonts..."
sudo apt-get install -y fonts-devanagari fonts-lohit-deva fonts-nakula

echo ""
echo "📥 Installing Liberation Fonts (Fallback)..."
sudo apt-get install -y fonts-liberation fonts-liberation2

echo ""
echo "🔄 Refreshing font cache..."
sudo fc-cache -f -v

echo ""
echo "=========================================="
echo "✅ Font Installation Complete!"
echo "=========================================="
echo ""
echo "Installed fonts:"
echo "  ✅ Noto Sans (Universal Unicode)"
echo "  ✅ Noto Sans Malayalam"
echo "  ✅ Noto Sans Devanagari (Hindi)"
echo "  ✅ Meera, Anjali Old Lipi (Malayalam)"
echo "  ✅ Lohit Devanagari (Hindi)"
echo ""
echo "Verifying installation..."
fc-list | grep -i "noto\|malayalam\|devanagari" | head -10
echo ""
echo "🎉 Ready to generate PDFs in Malayalam and Hindi!"
echo ""
echo "Next steps:"
echo "1. Replace pdf_report_generator.py with pdf_report_generator_fixed.py"
echo "2. Run your Streamlit app: streamlit run app.py"
echo "3. Generate reports in Malayalam or Hindi"
echo ""