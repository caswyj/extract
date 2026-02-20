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
    SelectionResult,
)


class MacOSScreenshotCapture(BaseScreenshotCapture):
    """macOS screenshot capture using mss with tkinter selection overlay."""

    def __init__(self):
        """Initialize macOS screenshot capture."""
        self._temp_dir = tempfile.gettempdir()

    def _get_temp_path(self) -> str:
        """Get a temporary file path for screenshot."""
        return os.path.join(self._temp_dir, 'snapocr_temp.png')

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
        except ImportError:
            print("Error: mss, tkinter, and Pillow required for region selection")
            return None

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
            selection['start'] = (event.x, event.y)

        def on_release(event):
            selection['end'] = (event.x, event.y)
            selection['done'] = True
            root.destroy()

        def on_motion(event):
            if selection['start']:
                # Update selection rectangle
                canvas.delete("selection")
                x1, y1 = selection['start']
                x2, y2 = event.x, event.y
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

        # Calculate region bounds
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

        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Use mss for consistency
        try:
            import mss
            from PIL import Image

            with mss.mss() as sct:
                monitor = sct.monitors[0]  # All monitors
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

        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Use screencapture for window selection on macOS
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
