"""Platform-specific implementations."""

from .base import (
    BaseScreenshotCapture,
    BaseClipboardManager,
    BaseHotkeyManager,
    PlatformManager,
)

__all__ = [
    'BaseScreenshotCapture',
    'BaseClipboardManager',
    'BaseHotkeyManager',
    'PlatformManager',
]
