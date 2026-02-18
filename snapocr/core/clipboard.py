"""
Cross-platform clipboard management with auto-paste support.
"""

import time
from typing import Optional

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    import pyautogui
except ImportError:
    pyautogui = None


class ClipboardManager:
    """
    Cross-platform clipboard manager with auto-paste functionality.
    """

    def __init__(self, auto_paste: bool = False, paste_delay_ms: int = 500):
        """
        Initialize clipboard manager.

        Args:
            auto_paste: Whether to automatically paste after copying.
            paste_delay_ms: Delay in milliseconds before auto-paste.
        """
        self._auto_paste = auto_paste
        self._paste_delay_ms = paste_delay_ms
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

    def simulate_paste(self) -> bool:
        """
        Simulate paste keyboard shortcut (Ctrl+V or Cmd+V).

        Returns:
            True if successful, False otherwise.
        """
        if pyautogui is None:
            print("Error: pyautogui not installed. Auto-paste unavailable.")
            return False

        try:
            import platform
            system = platform.system().lower()

            if system == 'darwin':
                # macOS: Cmd+V
                pyautogui.hotkey('command', 'v')
            else:
                # Windows/Linux: Ctrl+V
                pyautogui.hotkey('ctrl', 'v')

            return True
        except Exception as e:
            print(f"Error simulating paste: {e}")
            return False

    def copy_and_paste(self, text: str, delay_ms: Optional[int] = None) -> bool:
        """
        Copy text to clipboard and optionally auto-paste.

        Args:
            text: Text to copy.
            delay_ms: Optional override for paste delay.

        Returns:
            True if copy successful (paste is best-effort).
        """
        # Copy to clipboard
        if not self.copy(text):
            return False

        # Auto-paste if enabled
        should_paste = self._auto_paste
        paste_delay = delay_ms if delay_ms is not None else self._paste_delay_ms

        if should_paste:
            # Small delay to ensure clipboard is updated
            time.sleep(paste_delay / 1000.0)
            self.simulate_paste()

        return True

    @property
    def auto_paste(self) -> bool:
        """Get auto-paste setting."""
        return self._auto_paste

    @auto_paste.setter
    def auto_paste(self, value: bool) -> None:
        """Set auto-paste setting."""
        self._auto_paste = value

    @property
    def paste_delay_ms(self) -> int:
        """Get paste delay in milliseconds."""
        return self._paste_delay_ms

    @paste_delay_ms.setter
    def paste_delay_ms(self, value: int) -> None:
        """Set paste delay in milliseconds."""
        self._paste_delay_ms = value