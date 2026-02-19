#!/bin/bash
# Build script for macOS App Store distribution
# This script creates a properly signed .app bundle for App Store submission

set -e

echo "Building SnapOCR for App Store..."

# Configuration
APP_NAME="SnapOCR"
BUNDLE_ID="com.snapocr.app"
VERSION="2.0.0"
BUILD_NUMBER="200"

# Get the code signing identity from environment or use default
CODESIGN_IDENTITY="${CODESIGN_IDENTITY:-}"

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

# Install dependencies
echo "Installing dependencies..."
$PIP_CMD install -r requirements.txt
$PIP_CMD install pyinstaller

# Clean previous builds
rm -rf build/ dist/

# Create .app bundle with PyInstaller
echo "Building .app bundle..."
python3 -m PyInstaller \
    --name "$APP_NAME" \
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
    --osx-bundle-identifier "$BUNDLE_ID" \
    --target-arch arm64 \
    run.py

# Path to the built app
APP_PATH="dist/$APP_NAME.app"

if [ ! -d "$APP_PATH" ]; then
    echo "Error: Failed to build .app bundle"
    exit 1
fi

# Copy Info.plist
echo "Adding Info.plist..."
cp resources/Info.plist "$APP_PATH/Contents/Info.plist"

# Copy entitlements for later use
ENTITLEMENTS_PATH="resources/SnapOCR.entitlements"

# Code signing (if identity is provided)
if [ -n "$CODESIGN_IDENTITY" ]; then
    echo "Signing application with identity: $CODESIGN_IDENTITY"

    # Sign all frameworks and libraries first
    find "$APP_PATH/Contents/Frameworks" -name "*.dylib" -o -name "*.so" 2>/dev/null | while read lib; do
        codesign --force --sign "$CODESIGN_IDENTITY" --options runtime "$lib"
    done

    # Sign the app bundle
    codesign --deep --force --sign "$CODESIGN_IDENTITY" \
        --options runtime \
        --entitlements "$ENTITLEMENTS_PATH" \
        "$APP_PATH"

    # Verify signature
    echo "Verifying signature..."
    codesign --verify --deep --strict --verbose=2 "$APP_PATH"

    # Check entitlements
    echo "Checking entitlements..."
    codesign --display --entitlements - "$APP_PATH"

    # Create ZIP for notarization
    echo "Creating ZIP for notarization..."
    cd dist
    zip -r "$APP_NAME.zip" "$APP_NAME.app"
    cd ..

    echo ""
    echo "Build complete! Output: $APP_PATH"
    echo "ZIP for notarization: dist/$APP_NAME.zip"
    echo ""
    echo "Next steps for App Store submission:"
    echo "1. Submit for notarization:"
    echo "   xcrun notarytool submit dist/$APP_NAME.zip --apple-id YOUR_APPLE_ID --team-id YOUR_TEAM_ID --password APP_SPECIFIC_PASSWORD"
    echo ""
    echo "2. Wait for notarization to complete, then staple:"
    echo "   xcrun stapler staple $APP_PATH"
    echo ""
    echo "3. Create a signed installer package:"
    echo "   productbuild --component $APP_PATH /Applications --sign YOUR_INSTALLER_CERT dist/$APP_NAME.pkg"
else
    echo ""
    echo "Build complete! Output: $APP_PATH"
    echo ""
    echo "Note: No code signing identity provided. To sign for App Store:"
    echo "  CODESIGN_IDENTITY=\"Your Developer Identity\" ./scripts/build_appstore.sh"
    echo ""
    echo "To find your signing identity, run:"
    echo "  security find-identity -v -p codesigning"
fi

# Verify the app runs
echo ""
echo "To test the built app, run:"
echo "  open $APP_PATH"
