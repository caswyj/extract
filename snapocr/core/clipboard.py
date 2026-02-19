"""
Cross-platform clipboard management.
"""

from typing import Optional

try:
    import pyperclip
except ImportError:
    pyperclip = None


class ClipboardManager:
    """
    Cross-platform clipboard manager.
    """

    def __init__(self):
        """Initialize clipboard manager."""
        self._platform_clipboard = None

    def _get_platform_clipboard(self):
        """Get platform-specific clipboard implementation."""
        if self._platform_clipboard is None:
            import platform
            system = platform.system().lower()

            if system == 'darwin':
                from ..platform.macos import MacOSClipboardManager
                self._platform_clipboard = MacOSClipboardManager()
            elif system == 'windows':
                from ..platform.windows import WindowsClipboardManager
                self._platform_clipboard = WindowsClipboardManager()
            else:
                from ..platform.linux import LinuxClipboardManager
                self._platform_clipboard = LinuxClipboardManager()

        return self._platform_clipboard

    def copy(self, text: str) -> bool:
        """
        Copy text to clipboard.

        Args:
            text: Text to copy.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Try pyperclip first as it's cross-platform
            if pyperclip is not None:
                pyperclip.copy(text)
            else:
                # Fall back to platform-specific implementation
                clipboard = self._get_platform_clipboard()
                return clipboard.copy(text)
            return True
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            # Try platform-specific as fallback
            try:
                clipboard = self._get_platform_clipboard()
                return clipboard.copy(text)
            except Exception as e2:
                print(f"Platform clipboard also failed: {e2}")
                return False

    def paste(self) -> str:
        """
        Get text from clipboard.

        Returns:
            Clipboard text or empty string.
        """
        try:
            if pyperclip is not None:
                return pyperclip.paste()
            else:
                clipboard = self._get_platform_clipboard()
                return clipboard.paste()
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            try:
                clipboard = self._get_platform_clipboard()
                return clipboard.paste()
            except Exception:
                return ""
