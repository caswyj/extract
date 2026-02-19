"""
macOS platform-specific implementations.
"""

import os
import subprocess
import tempfile
from typing import Optional

from .base import (
    BaseScreenshotCapture,
    BaseClipboardManager,
)


class MacOSScreenshotCapture(BaseScreenshotCapture):
    """macOS screenshot capture using built-in screencapture command."""

    def __init__(self):
        """Initialize macOS screenshot capture."""
        self._temp_dir = tempfile.gettempdir()

    def _get_temp_path(self) -> str:
        """Get a temporary file path for screenshot."""
        return os.path.join(self._temp_dir, 'snapocr_temp.png')

    def select_region(self) -> Optional[str]:
        """
        Capture a selected screen region using screencapture.

        Returns:
            Path to captured image or None if cancelled.
        """
        temp_path = self._get_temp_path()

        # Remove existing temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        print("Select a region with your mouse (drag to select, Esc to cancel)...")

        # Use macOS screencapture command
        # -i: interactive mode (user selects region)
        # -r: don't play sound
        # -x: don't play sound (alternative flag)
        result = subprocess.run(
            ['screencapture', '-i', '-r', temp_path],
            capture_output=True
        )

        # screencapture returns 0 on success, non-zero if cancelled
        if result.returncode != 0:
            return None

        if os.path.exists(temp_path):
            return temp_path
        return None

    def capture_full_screen(self) -> Optional[str]:
        """Capture the full screen."""
        temp_path = self._get_temp_path()

        if os.path.exists(temp_path):
            os.remove(temp_path)

        # -x: don't play sound
        result = subprocess.run(
            ['screencapture', '-x', temp_path],
            capture_output=True
        )

        if result.returncode == 0 and os.path.exists(temp_path):
            return temp_path
        return None

    def capture_window(self) -> Optional[str]:
        """Capture the currently focused window."""
        temp_path = self._get_temp_path()

        if os.path.exists(temp_path):
            os.remove(temp_path)

        # -l: capture window by ID (0 for focused window doesn't work, need to get window ID)
        # -o: capture window only (no shadow)
        # -w: select window interactively
        result = subprocess.run(
            ['screencapture', '-o', '-w', '-x', temp_path],
            capture_output=True
        )

        if result.returncode == 0 and os.path.exists(temp_path):
            return temp_path
        return None


class MacOSClipboardManager(BaseClipboardManager):
    """macOS clipboard manager using pbcopy and pbpaste."""

    def copy(self, text: str) -> bool:
        """Copy text to clipboard using pbcopy."""
        try:
            process = subprocess.Popen(
                ['pbcopy', 'w'],
                stdin=subprocess.PIPE,
                env={**os.environ, 'LANG': 'en_US.UTF-8'}
            )
            process.communicate(text.encode('utf-8'))
            return process.returncode == 0
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            return False

    def paste(self) -> str:
        """Get text from clipboard using pbpaste."""
        try:
            result = subprocess.run(
                ['pbpaste'],
                capture_output=True,
                text=True,
                env={**os.environ, 'LANG': 'en_US.UTF-8'}
            )
            return result.stdout
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            return ""