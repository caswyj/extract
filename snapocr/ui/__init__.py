"""
SnapOCR UI components for interactive screenshot OCR.

This module provides:
- SelectionOverlay: Full-screen overlay for region selection with dimming
- ResultPanel: Panel to display OCR results next to selection
- ButtonBar: Action buttons (Pin, Accept, Cancel)
- PinnedWindow: Floating always-on-top window for pinned screenshots
"""

from .selection_overlay import SelectionOverlay
from .result_panel import ResultPanel
from .button_bar import ButtonBar
from .pinned_window import PinnedWindow

__all__ = [
    'SelectionOverlay',
    'ResultPanel',
    'ButtonBar',
    'PinnedWindow',
]
