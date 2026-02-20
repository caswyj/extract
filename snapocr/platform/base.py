"""
Abstract base classes for platform-specific implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple, Any


@dataclass
class SelectionResult:
    """Result of a screen region selection."""

    image_path: str                              # Path to the captured image file
    rect: Tuple[int, int, int, int]              # (x, y, width, height) of selection
    screen_image: Optional[Any] = None           # PIL Image of full screen (for overlay)
    screen_width: int = 0                        # Full screen width
    screen_height: int = 0                       # Full screen height


class BaseScreenshotCapture(ABC):
    """Abstract base class for screenshot capture functionality."""

    @abstractmethod
    def select_region(self) -> Optional[SelectionResult]:
        """
        Allow user to select a screen region and capture it.

        Returns:
            SelectionResult with image path and region info, or None if cancelled.
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
