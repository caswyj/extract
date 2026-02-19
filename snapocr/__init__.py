"""
SnapOCR - Cross-platform screenshot OCR tool

A simple tool that captures a screenshot region, extracts text using OCR,
and copies the result to clipboard. Supports English, Chinese, and LaTeX
conversion for mathematical formulas.

Usage:
    from snapocr import SnapOCR

    app = SnapOCR()
    text = app.capture_and_extract()
"""

__version__ = '2.0.0'
__author__ = 'SnapOCR Contributors'

from .main import SnapOCR, main
from .core.config import Config
from .core.ocr import extract_text, format_result
from .core.clipboard import ClipboardManager
from .platform.base import PlatformManager

__all__ = [
    'SnapOCR',
    'Config',
    'extract_text',
    'format_result',
    'ClipboardManager',
    'PlatformManager',
    'main',
]
