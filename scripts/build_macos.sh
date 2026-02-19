#!/bin/bash
# Build script for macOS .app bundle using PyInstaller

set -e

echo "Building SnapOCR for macOS..."

# Find the correct pip command
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    echo "Error: pip not found. Please install Python first."
    exit 1
fi

echo "Using: $PIP_CMD"

# Check for PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    $PIP_CMD install pyinstaller
fi

# Create .app bundle
# Note: --onedir is recommended for macOS .app bundles (not --onefile)
# Using run.py as entry point to handle imports correctly when bundled
python3 -m PyInstaller \
    --name "SnapOCR" \
    --windowed \
    --onedir \
    --hidden-import "PIL._tkinter_finder" \
    --hidden-import "pytesseract" \
    --hidden-import "mss" \
    --hidden-import "snapocr" \
    --hidden-import "snapocr.main" \
    --hidden-import "snapocr.core.config" \
    --hidden-import "snapocr.core.ocr" \
    --hidden-import "snapocr.core.clipboard" \
    --hidden-import "snapocr.platform.base" \
    --hidden-import "snapocr.platform.macos" \
    --hidden-import "snapocr.platform.macos_native" \
    --add-data "snapocr:snapocr" \
    --osx-bundle-identifier "com.snapocr.app" \
    --target-arch arm64 \
    run.py

# Copy custom Info.plist
echo "Copying custom Info.plist..."
cp resources/Info.plist dist/SnapOCR.app/Contents/Info.plist

echo ""
echo "Build complete!"
echo "Output: dist/SnapOCR.app"
echo ""
echo "Note: You may need to codesign the app for distribution:"
echo "  codesign --deep --force --verify --verbose dist/SnapOCR.app"
