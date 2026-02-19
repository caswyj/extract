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
pyinstaller \
    --name "SnapOCR" \
    --windowed \
    --onefile \
    --icon resources/icon.icns \
    --add-data "resources/tessdata:resources/tessdata" \
    --hidden-import "PIL._tkinter_finder" \
    --hidden-import "pytesseract" \
    --hidden-import "pynput" \
    --hidden-import "pyautogui" \
    --hidden-import "mss" \
    --osx-bundle-identifier "com.snapocr.app" \
    snapocr/main.py

echo ""
echo "Build complete!"
echo "Output: dist/SnapOCR.app"
echo ""
echo "Note: You may need to codesign the app for distribution:"
echo "  codesign --deep --force --verify --verbose dist/SnapOCR.app"