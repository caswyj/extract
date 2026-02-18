"""Core modules for SnapOCR."""

from .config import Config
from .ocr import extract_text, format_result
from .clipboard import ClipboardManager

__all__ = ['Config', 'extract_text', 'format_result', 'ClipboardManager']
