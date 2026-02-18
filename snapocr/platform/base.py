"""
Abstract base classes for platform-specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Callable


class BaseScreenshotCapture(ABC):
    """Abstract base class for screenshot capture functionality."""

    @abstractmethod
    def select_region(self) -> Optional[str]:
        """
        Allow user to select a screen region and capture it.

        Returns:
            Path to the captured image file, or None if cancelled.
        """
        pass

    @abstractmethod
    def capture_full_screen(self) -> Optional[str]:
        """
        Capture the full screen.

        Returns:
            Path to the captured image file, or None if failed.
        """
        pass

    @abstractmethod
    def capture_window(self) -> Optional[str]:
        """
        Capture the currently focused window.

        Returns:
            Path to the captured image file, or None if cancelled.
        """
        pass


class BaseClipboardManager(ABC):
    """Abstract base class for clipboard management."""

    @abstractmethod
    def copy(self, text: str) -> bool:
        """
        Copy text to the system clipboard.

        Args:
            text: The text to copy.

        Returns:
            True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def paste(self) -> str:
        """
        Get text from the system clipboard.

        Returns:
            The clipboard text, or empty string if none.
        """
        pass

    @abstractmethod
    def simulate_paste(self) -> bool:
        """
        Simulate a paste keyboard shortcut (Ctrl+V or Cmd+V).

        Returns:
            True if successful, False otherwise.
        """
        pass


class BaseHotkeyManager(ABC):
    """Abstract base class for hotkey management."""

    @abstractmethod
    def register(self, hotkey: str, callback: Callable[[], None]) -> bool:
        """
        Register a global hotkey.

        Args:
            hotkey: Hotkey string (e.g., "ctrl+shift+o", "cmd+shift+o").
            callback: Function to call when hotkey is pressed.

        Returns:
            True if registration successful, False otherwise.
        """
        pass

    @abstractmethod
    def unregister(self, hotkey: str) -> bool:
        """
        Unregister a previously registered hotkey.

        Args:
            hotkey: The hotkey string to unregister.

        Returns:
            True if unregistration successful, False otherwise.
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """
        Start listening for hotkey events.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        Stop listening for hotkey events.
        """
        pass

    @abstractmethod
    def is_registered(self, hotkey: str) -> bool:
        """
        Check if a hotkey is currently registered.

        Args:
            hotkey: The hotkey string to check.

        Returns:
            True if registered, False otherwise.
        """
        pass


class PlatformManager:
    """
    Factory class to get platform-specific implementations.
    """

    _instance = None
    _platform_name = None

    @classmethod
    def get_platform(cls) -> str:
        """Get the current platform name."""
        if cls._platform_name is None:
            import platform
            system = platform.system().lower()
            if system == 'darwin':
                cls._platform_name = 'macos'
            elif system == 'windows':
                cls._platform_name = 'windows'
            elif system == 'linux':
                cls._platform_name = 'linux'
            else:
                raise RuntimeError(f"Unsupported platform: {system}")
        return cls._platform_name

    @classmethod
    def get_screenshot_capture(cls) -> BaseScreenshotCapture:
        """Get the platform-specific screenshot capture implementation."""
        platform = cls.get_platform()
        if platform == 'macos':
            from .macos import MacOSScreenshotCapture
            return MacOSScreenshotCapture()
        elif platform == 'windows':
            from .windows import WindowsScreenshotCapture
            return WindowsScreenshotCapture()
        elif platform == 'linux':
            from .linux import LinuxScreenshotCapture
            return LinuxScreenshotCapture()

    @classmethod
    def get_clipboard_manager(cls) -> BaseClipboardManager:
        """Get the platform-specific clipboard manager implementation."""
        platform = cls.get_platform()
        if platform == 'macos':
            from .macos import MacOSClipboardManager
            return MacOSClipboardManager()
        elif platform == 'windows':
            from .windows import WindowsClipboardManager
            return WindowsClipboardManager()
        elif platform == 'linux':
            from .linux import LinuxClipboardManager
            return LinuxClipboardManager()

    @classmethod
    def get_hotkey_manager(cls) -> BaseHotkeyManager:
        """Get the platform-specific hotkey manager implementation."""
        platform = cls.get_platform()
        if platform == 'macos':
            from .macos import MacOSHotkeyManager
            return MacOSHotkeyManager()
        elif platform == 'windows':
            from .windows import WindowsHotkeyManager
            return WindowsHotkeyManager()
        elif platform == 'linux':
            from .linux import LinuxHotkeyManager
            return LinuxHotkeyManager()
