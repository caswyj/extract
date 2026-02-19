# Build script for Windows .exe using PyInstaller
# Run this in PowerShell

Write-Host "Building SnapOCR for Windows..."

# Find the correct pip command
$pipCmd = $null
if (Get-Command pip3 -ErrorAction SilentlyContinue) {
    $pipCmd = "pip3"
} elseif (Get-Command pip -ErrorAction SilentlyContinue) {
    $pipCmd = "pip"
} else {
    Write-Host "Error: pip not found. Please install Python first."
    exit 1
}

Write-Host "Using: $pipCmd"

# Check for PyInstaller
$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstaller) {
    Write-Host "PyInstaller not found. Installing..."
    & $pipCmd install pyinstaller
}

# Create executable
pyinstaller `
    --name "SnapOCR" `
    --onefile `
    --windowed `
    --icon resources/icon.ico `
    --add-data "resources/tessdata;resources/tessdata" `
    --hidden-import "PIL._tkinter_finder" `
    --hidden-import "pytesseract" `
    --hidden-import "pynput" `
    --hidden-import "pyautogui" `
    --hidden-import "mss" `
    snapocr/main.py

Write-Host ""
Write-Host "Build complete!"
Write-Host "Output: dist\SnapOCR.exe"
Write-Host ""
Write-Host "Note: For distribution, you may want to:"
Write-Host "  1. Sign the executable with signtool"
Write-Host "  2. Create an installer with NSIS or Inno Setup"
Write-Host ""
Write-Host "Tesseract and tessdata need to be bundled separately or installed on the target machine."