"""
Windows platform-specific implementations.
"""

import os
import tempfile
from typing import Optional

from .base import (
    BaseScreenshotCapture,
    BaseClipboardManager,
    SelectionResult,
)


class WindowsScreenshotCapture(BaseScreenshotCapture):
    """Windows screenshot capture using mss with tkinter selection overlay."""

    def __init__(self):
        """Initialize Windows screenshot capture."""
        self._temp_dir = tempfile.gettempdir()

    def _get_temp_path(self) -> str:
        """Get a temporary file path for screenshot."""
        return os.path.join(self._temp_dir, 'snapocr_temp.png')

    def _get_dpi_scale(self):
        """Get the DPI scaling factor for the primary monitor."""
        try:
            import ctypes
            # Get the DPI for the primary monitor
            user32 = ctypes.windll.user32
            dc = user32.GetDC(0)
            LOGPIXELSX = 88
            dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, LOGPIXELSX)
            user32.ReleaseDC(0, dc)
            # Standard DPI is 96, scale factor is dpi/96
            return dpi / 96.0
        except Exception:
            return 1.0

    def select_region(self) -> Optional[SelectionResult]:
        """
        Capture a selected screen region using mss with tkinter overlay.

        Returns:
            SelectionResult with image path and region info, or None if cancelled.
        """
        try:
            import mss
            import tkinter as tk
            from PIL import Image
            import ctypes
        except ImportError:
            print("Error: mss, tkinter, and Pillow required for region selection")
            return None

        # Get DPI scaling factor
        dpi_scale = self._get_dpi_scale()

        # Make the process DPI aware to get correct coordinates
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        # Capture full screen first for overlay
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[0]  # All monitors combined
                screenshot = sct.grab(monitor)
                screen_img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                screen_width, screen_height = screenshot.size
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None

        # Selection state
        selection = {'start': None, 'end': None, 'done': False, 'cancelled': False}

        def on_press(event):
            selection['start'] = (event.x_root, event.y_root)

        def on_release(event):
            selection['end'] = (event.x_root, event.y_root)
            selection['done'] = True
            root.destroy()

        def on_motion(event):
            if selection['start']:
                # Update selection rectangle
                canvas.delete("selection")
                x1, y1 = selection['start']
                x2, y2 = event.x_root, event.y_root
                canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline='#00BFFF', width=2, tag="selection"
                )

        def on_escape(event):
            selection['cancelled'] = True
            root.destroy()

        # Create fullscreen transparent window
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-alpha', 0.3)
        root.attributes('-topmost', True)
        root.configure(bg='black', cursor='cross')

        canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<ButtonRelease-1>', on_release)
        canvas.bind('<B1-Motion>', on_motion)
        canvas.bind('<Escape>', on_escape)
        root.bind('<Escape>', on_escape)

        print("Select a region with your mouse (drag to select, Esc to cancel)...")

        root.mainloop()

        if selection['cancelled'] or not selection['done'] or not selection['start'] or not selection['end']:
            return None

        # Calculate region bounds (coordinates from tkinter should be in physical pixels)
        x1, y1 = selection['start']
        x2, y2 = selection['end']
        left = int(min(x1, x2))
        top = int(min(y1, y2))
        right = int(max(x1, x2))
        bottom = int(max(y1, y2))

        if right - left < 5 or bottom - top < 5:
            return None

        width = right - left
        height = bottom - top

        # Crop the selected region from the full screen capture
        temp_path = self._get_temp_path()
        try:
            region_img = screen_img.crop((left, top, right, bottom))
            region_img.save(temp_path)
        except Exception as e:
            print(f"Error saving selection: {e}")
            return None

        return SelectionResult(
            image_path=temp_path,
            rect=(left, top, width, height),
            screen_image=screen_img,
            screen_width=screen_width,
            screen_height=screen_height
        )

    def capture_full_screen(self) -> Optional[str]:
        """Capture the full screen."""
        temp_path = self._get_temp_path()

        try:
            import mss
            from PIL import Image

            with mss.mss() as sct:
                # Get primary monitor (index 1 in mss)
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                img.save(temp_path)
            return temp_path
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None

    def capture_window(self) -> Optional[str]:
        """Capture the currently focused window."""
        temp_path = self._get_temp_path()

        try:
            import mss
            from PIL import Image
            import ctypes

            # Get foreground window
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            # Get window rect
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
            width = right - left
            height = bottom - top

            with mss.mss() as sct:
                monitor = {'left': left, 'top': top, 'width': width, 'height': height}
                screenshot = sct.grab(monitor)
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                img.save(temp_path)
            return temp_path
        except Exception as e:
            print(f"Error capturing window: {e}")
            return None


class WindowsClipboardManager(BaseClipboardManager):
    """Windows clipboard manager using Windows API directly."""

    def __init__(self):
        """Initialize Windows clipboard manager."""
        pass

    def copy(self, text: str) -> bool:
        """Copy text to clipboard using Windows API."""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            # Ensure clipboard is closed first
            user32.CloseClipboard()

            # Try multiple times in case clipboard is locked by another app
            for attempt in range(3):
                if user32.OpenClipboard(0):
                    break
                import time
                time.sleep(0.05)
            else:
                print("Error: Could not open clipboard after 3 attempts")
                return False

            try:
                # Empty clipboard first
                user32.EmptyClipboard()

                # Set clipboard data
                CF_UNICODETEXT = 13
                text_bytes = text.encode('utf-16le') + b'\x00\x00'

                # Allocate global memory
                GMEM_MOVEABLE = 0x0002
                h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes))
                if not h_mem:
                    return False

                p_mem = kernel32.GlobalLock(h_mem)
                if not p_mem:
                    kernel32.GlobalFree(h_mem)
                    return False

                ctypes.memmove(p_mem, text_bytes, len(text_bytes))
                kernel32.GlobalUnlock(h_mem)

                if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
                    kernel32.GlobalFree(h_mem)
                    return False

                return True
            finally:
                user32.CloseClipboard()

        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            return False

    def paste(self) -> str:
        """Get text from clipboard using Windows API."""
        try:
            import ctypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            # Try multiple times in case clipboard is locked
            for attempt in range(3):
                if user32.OpenClipboard(0):
                    break
                import time
                time.sleep(0.05)
            else:
                return ""

            try:
                CF_UNICODETEXT = 13
                h_mem = user32.GetClipboardData(CF_UNICODETEXT)
                if not h_mem:
                    return ""

                p_mem = kernel32.GlobalLock(h_mem)
                if not p_mem:
                    return ""

                # Read the data
                text = ctypes.wstring_at(p_mem)
                kernel32.GlobalUnlock(h_mem)
                return text
            finally:
                user32.CloseClipboard()
        except Exception:
            return ""
