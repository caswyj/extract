"""
macOS native screenshot implementation using PyObjC for App Store sandbox compatibility.

This module provides screenshot capture using native macOS APIs through PyObjC,
which is compatible with App Store sandbox requirements.
"""

import os
import tempfile
from typing import Optional, Tuple

try:
    from Cocoa import NSPasteboard, NSStringPboardType
    from Quartz import (
        CGWindowListCreateImage,
        kCGNullWindowID,
        kCGWindowListOptionOnScreenOnly,
        kCGWindowImageDefault,
        CGRectNull,
        CGRectMake,
        CGMainDisplayID,
        CGDisplayBounds,
    )
    PYOBJC_AVAILABLE = True
except ImportError:
    PYOBJC_AVAILABLE = False

try:
    from PIL import Image
    import io
except ImportError:
    Image = None


class MacOSNativeScreenshotCapture:
    """
    macOS screenshot capture using native Quartz APIs.

    This implementation uses PyObjC to call native macOS APIs,
    making it compatible with App Store sandbox requirements.
    """

    def __init__(self):
        """Initialize native screenshot capture."""
        if not PYOBJC_AVAILABLE:
            raise ImportError(
                "PyObjC is required for native macOS screenshot capture. "
                "Install with: pip install pyobjc-framework-Quartz pyobjc-framework-Cocoa"
            )
        self._temp_dir = tempfile.gettempdir()

    def _get_temp_path(self) -> str:
        """Get a temporary file path for screenshot."""
        return os.path.join(self._temp_dir, 'snapocr_temp.png')

    def capture_screen_rect(self, x: int, y: int, width: int, height: int) -> Optional[bytes]:
        """
        Capture a rectangular region of the screen.

        Args:
            x: Left coordinate of the region.
            y: Top coordinate of the region.
            width: Width of the region.
            height: Height of the region.

        Returns:
            PNG image bytes or None if failed.
        """
        try:
            rect = CGRectMake(x, y, width, height)
            image_ref = CGWindowListCreateImage(
                rect,
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID,
                kCGWindowImageDefault
            )

            if image_ref is None:
                return None

            # Convert CGImage to PIL Image and then to PNG bytes
            if Image is None:
                return None

            # Get image dimensions
            width = image_ref.getWidth()
            height = image_ref.getHeight()

            # Create a bitmap representation
            from Quartz import CGImageDestinationCreateWithData, CGImageDestinationAddImage, CGImageDestinationFinalize
            from Cocoa import NSMutableData

            data = NSMutableData.data()
            destination = CGImageDestinationCreateWithData(data, 'public.png', 1, None)
            CGImageDestinationAddImage(destination, image_ref, None)
            CGImageDestinationFinalize(destination)

            return bytes(data)

        except Exception as e:
            print(f"Error capturing screen region: {e}")
            return None

    def select_region(self) -> Optional[str]:
        """
        Allow user to select a screen region and capture it.

        Note: For App Store compatibility, region selection requires
        a custom NSPanel overlay or using the system screenshot utility.

        Returns:
            Path to captured image or None if cancelled.
        """
        # For App Store sandbox compatibility, we use the system
        # screencapture utility which handles region selection
        import subprocess

        temp_path = self._get_temp_path()

        if os.path.exists(temp_path):
            os.remove(temp_path)

        print("Select a region with your mouse (drag to select, Esc to cancel)...")

        result = subprocess.run(
            ['screencapture', '-i', '-r', temp_path],
            capture_output=True
        )

        if result.returncode != 0:
            return None

        if os.path.exists(temp_path):
            return temp_path
        return None

    def capture_full_screen(self) -> Optional[str]:
        """Capture the full screen."""
        try:
            temp_path = self._get_temp_path()

            # Get main display bounds
            main_display = CGMainDisplayID()
            bounds = CGDisplayBounds(main_display)

            # Capture full screen
            image_bytes = self.capture_screen_rect(
                int(bounds.origin.x),
                int(bounds.origin.y),
                int(bounds.size.width),
                int(bounds.size.height)
            )

            if image_bytes:
                with open(temp_path, 'wb') as f:
                    f.write(image_bytes)
                return temp_path
            return None

        except Exception as e:
            print(f"Error capturing full screen: {e}")
            return None

    def capture_window(self) -> Optional[str]:
        """Capture the currently focused window."""
        import subprocess

        temp_path = self._get_temp_path()

        if os.path.exists(temp_path):
            os.remove(temp_path)

        result = subprocess.run(
            ['screencapture', '-o', '-w', '-x', temp_path],
            capture_output=True
        )

        if result.returncode == 0 and os.path.exists(temp_path):
            return temp_path
        return None


class MacOSNativeClipboardManager:
    """
    macOS clipboard manager using native Cocoa APIs.

    This implementation uses PyObjC for App Store sandbox compatibility.
    """

    def __init__(self):
        """Initialize native clipboard manager."""
        if not PYOBJC_AVAILABLE:
            raise ImportError(
                "PyObjC is required for native macOS clipboard. "
                "Install with: pip install pyobjc-framework-Cocoa"
            )
        self._pasteboard = NSPasteboard.generalPasteboard()

    def copy(self, text: str) -> bool:
        """Copy text to clipboard using native Cocoa APIs."""
        try:
            self._pasteboard.clearContents()
            self._pasteboard.setString_forType_(text, NSStringPboardType)
            return True
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            return False

    def paste(self) -> str:
        """Get text from clipboard using native Cocoa APIs."""
        try:
            text = self._pasteboard.stringForType_(NSStringPboardType)
            return text if text else ""
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            return ""
