"""
Linux platform-specific implementations.
"""

import os
import subprocess
import tempfile
from typing import Optional

from .base import (
    BaseScreenshotCapture,
    BaseClipboardManager,
)


class LinuxScreenshotCapture(BaseScreenshotCapture):
    """Linux screenshot capture using scrot or ImageMagick import."""

    def __init__(self):
        """Initialize and detect available screenshot tool."""
        self._capture_tool = self._detect_capture_tool()
        self._temp_dir = tempfile.gettempdir()

    def _detect_capture_tool(self) -> Optional[str]:
        """Detect available screenshot tool."""
        # Prefer scrot for its selection mode
        result = subprocess.run(['which', 'scrot'], capture_output=True)
        if result.returncode == 0:
            return 'scrot'

        # Fall back to ImageMagick import
        result = subprocess.run(['which', 'import'], capture_output=True)
        if result.returncode == 0:
            return 'import'

        # Use mss as Python-based fallback
        return 'mss'

    def _get_temp_path(self) -> str:
        """Get a temporary file path for screenshot."""
        return os.path.join(self._temp_dir, 'snapocr_temp.png')

    def select_region(self) -> Optional[str]:
        """
        Capture a selected screen region.

        Returns:
            Path to captured image or None if cancelled.
        """
        temp_path = self._get_temp_path()

        # Remove existing temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        print("Select a region with your mouse (drag to select, Esc to cancel)...")

        if self._capture_tool == 'scrot':
            # scrot -s: selection mode, -z: silent (no output)
            result = subprocess.run(
                ['scrot', '-s', '-z', temp_path],
                capture_output=True
            )
            if result.returncode != 0:
                return None

        elif self._capture_tool == 'import':
            # ImageMagick import with interactive selection
            result = subprocess.run(
                ['import', temp_path],
                capture_output=True
            )
            if result.returncode != 0:
                return None

        else:
            # Use mss with tkinter overlay for region selection
            return self._capture_with_mss_selection()

        if os.path.exists(temp_path):
            return temp_path
        return None

    def _capture_with_mss_selection(self) -> Optional[str]:
        """Capture region using mss with tkinter selection overlay."""
        try:
            import mss
            import tkinter as tk
            from PIL import ImageGrab
        except ImportError:
            print("Error: mss and tkinter required for region selection")
            return None

        # Selection state
        selection = {'start': None, 'end': None, 'done': False}

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
                    outline='red', width=2, tag="selection"
                )

        # Create fullscreen transparent window
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-alpha', 0.3)
        root.attributes('-topmost', True)
        root.configure(bg='black')

        canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<ButtonRelease-1>', on_release)
        canvas.bind('<B1-Motion>', on_motion)
        canvas.bind('<Escape>', lambda e: root.destroy())

        root.mainloop()

        if not selection['done'] or not selection['start'] or not selection['end']:
            return None

        # Calculate region bounds
        x1, y1 = selection['start']
        x2, y2 = selection['end']
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)

        if right - left < 5 or bottom - top < 5:
            return None

        # Capture the region
        temp_path = self._get_temp_path()
        try:
            with mss.mss() as sct:
                monitor = {'left': left, 'top': top, 'width': right - left, 'height': bottom - top}
                screenshot = sct.grab(monitor)
                from PIL import Image
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                img.save(temp_path)
            return temp_path
        except Exception as e:
            print(f"Error capturing region: {e}")
            return None

    def capture_full_screen(self) -> Optional[str]:
        """Capture the full screen."""
        temp_path = self._get_temp_path()

        if os.path.exists(temp_path):
            os.remove(temp_path)

        if self._capture_tool == 'scrot':
            result = subprocess.run(
                ['scrot', '-z', temp_path],
                capture_output=True
            )
        elif self._capture_tool == 'import':
            result = subprocess.run(
                ['import', '-window', 'root', temp_path],
                capture_output=True
            )
        else:
            try:
                import mss
                with mss.mss() as sct:
                    monitor = sct.monitors[1]  # Primary monitor
                    screenshot = sct.grab(monitor)
                    from PIL import Image
                    img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                    img.save(temp_path)
                result = subprocess.CompletedProcess(args=[], returncode=0)
            except Exception as e:
                print(f"Error capturing screen: {e}")
                return None

        if result.returncode == 0 and os.path.exists(temp_path):
            return temp_path
        return None

    def capture_window(self) -> Optional[str]:
        """Capture the currently focused window."""
        temp_path = self._get_temp_path()

        if os.path.exists(temp_path):
            os.remove(temp_path)

        if self._capture_tool == 'scrot':
            # scrot -u: focused window
            result = subprocess.run(
                ['scrot', '-u', '-z', temp_path],
                capture_output=True
            )
        elif self._capture_tool == 'import':
            # Select window by clicking
            result = subprocess.run(
                ['import', temp_path],
                capture_output=True
            )
        else:
            # Not supported with mss alone
            print("Window capture not supported. Use full screen or region selection.")
            return None

        if result.returncode == 0 and os.path.exists(temp_path):
            return temp_path
        return None


class LinuxClipboardManager(BaseClipboardManager):
    """Linux clipboard manager using xclip, xsel, or pyperclip."""

    def copy(self, text: str) -> bool:
        """Copy text to clipboard."""
        # Try xclip first (most reliable)
        result = subprocess.run(['which', 'xclip'], capture_output=True)
        if result.returncode == 0:
            try:
                subprocess.run(
                    ['xclip', '-selection', 'clipboard'],
                    input=text.encode('utf-8'),
                    check=True
                )
                return True
            except Exception:
                pass

        # Try xsel
        result = subprocess.run(['which', 'xsel'], capture_output=True)
        if result.returncode == 0:
            try:
                subprocess.run(
                    ['xsel', '--clipboard', '--input'],
                    input=text.encode('utf-8'),
                    check=True
                )
                return True
            except Exception:
                pass

        # Fall back to pyperclip
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except Exception:
            pass

        print("Error: Could not copy to clipboard. Install xclip or xsel.")
        return False

    def paste(self) -> str:
        """Get text from clipboard."""
        # Try xclip
        result = subprocess.run(['which', 'xclip'], capture_output=True)
        if result.returncode == 0:
            try:
                result = subprocess.run(
                    ['xclip', '-selection', 'clipboard', '-o'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout
            except Exception:
                pass

        # Try xsel
        result = subprocess.run(['which', 'xsel'], capture_output=True)
        if result.returncode == 0:
            try:
                result = subprocess.run(
                    ['xsel', '--clipboard', '--output'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout
            except Exception:
                pass

        # Fall back to pyperclip
        try:
            import pyperclip
            return pyperclip.paste()
        except Exception:
            pass

        return ""