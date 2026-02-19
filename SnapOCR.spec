# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[('snapocr', 'snapocr')],
    hiddenimports=[
        'PIL._tkinter_finder',
        'pytesseract',
        'mss',
        'snapocr',
        'snapocr.main',
        'snapocr.core.config',
        'snapocr.core.ocr',
        'snapocr.core.clipboard',
        'snapocr.platform.base',
        'snapocr.platform.macos',
        'snapocr.platform.macos_native',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pynput', 'pyautogui'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SnapOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file='resources/SnapOCR.entitlements',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SnapOCR',
)
app = BUNDLE(
    coll,
    name='SnapOCR.app',
    icon=None,
    bundle_identifier='com.snapocr.app',
    info_plist='resources/Info.plist',
)
