"""
Windows platform-specific implementations.
"""

import os
import tempfile
from typing import Optional, Callable

from .base import (
    BaseScreenshotCapture,
    BaseClipboardManager,
    BaseHotkeyManager,
)


class WindowsScreenshotCapture(BaseScreenshotCapture):
    """Windows screenshot capture using mss with tkinter selection overlay."""

    def __init__(self):
        """Initialize Windows screenshot capture."""
        self._temp_dir = tempfile.gettempdir()

    def _get_temp_path(self) -> str:
        """Get a temporary file path for screenshot."""
        return os.path.join(self._temp_dir, 'snapocr_temp.png')

    def select_region(self) -> Optional[str]:
        """
        Capture a selected screen region using mss with tkinter overlay.

        Returns:
            Path to captured image or None if cancelled.
        """
        try:
            import mss
            import tkinter as tk
            from PIL import Image
        except ImportError:
            print("Error: mss, tkinter, and Pillow required for region selection")
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

        def on_escape(event):
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

        print("Select a region with your mouse (drag to select, Esc to cancel)...")

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
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                img.save(temp_path)
            return temp_path
        except Exception as e:
            print(f"Error capturing region: {e}")
            return None

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
            import win32gui

            # Get foreground window
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None

            # Get window rect
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            with mss.mss() as sct:
                monitor = {'left': left, 'top': top, 'width': width, 'height': height}
                screenshot = sct.grab(monitor)
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                img.save(temp_path)
            return temp_path
        except ImportError:
            print("Error: win32gui required for window capture. Install with: pip install pywin32")
            return None
        except Exception as e:
            print(f"Error capturing window: {e}")
            return None


class WindowsClipboardManager(BaseClipboardManager):
    """Windows clipboard manager using pyperclip."""

    def __init__(self):
        """Initialize Windows clipboard manager."""
        try:
            import pyperclip
            self._pyperclip = pyperclip
        except ImportError:
            self._pyperclip = None

    def copy(self, text: str) -> bool:
        """Copy text to clipboard."""
        if self._pyperclip:
            try:
                self._pyperclip.copy(text)
                return True
            except Exception as e:
                print(f"Error copying to clipboard: {e}")

        # Fallback to ctypes
        try:
            import ctypes

            # Open clipboard
            if not ctypes.windll.user32.OpenClipboard(0):
                return False

            try:
                # Empty clipboard
                ctypes.windll.user32.EmptyClipboard()

                # Set clipboard data
                CF_UNICODETEXT = 13
                text_bytes = text.encode('utf-16le') + b'\x00\x00'

                # Allocate global memory
                GMEM_MOVEABLE = 0x0002
                h_mem = ctypes.windll.kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes))
                if not h_mem:
                    return False

                p_mem = ctypes.windll.kernel32.GlobalLock(h_mem)
                if not p_mem:
                    ctypes.windll.kernel32.GlobalFree(h_mem)
                    return False

                ctypes.memmove(p_mem, text_bytes, len(text_bytes))
                ctypes.windll.kernel32.GlobalUnlock(h_mem)

                if not ctypes.windll.user32.SetClipboardData(CF_UNICODETEXT, h_mem):
                    ctypes.windll.kernel32.GlobalFree(h_mem)
                    return False

                return True
            finally:
                ctypes.windll.user32.CloseClipboard()
        except Exception as e:
            print(f"Error with ctypes clipboard: {e}")
            return False

    def paste(self) -> str:
        """Get text from clipboard."""
        if self._pyperclip:
            try:
                return self._pyperclip.paste()
            except Exception:
                pass

        # Fallback to ctypes
        try:
            import ctypes

            if not ctypes.windll.user32.OpenClipboard(0):
                return ""

            try:
                CF_UNICODETEXT = 13
                h_mem = ctypes.windll.user32.GetClipboardData(CF_UNICODETEXT)
                if not h_mem:
                    return ""

                p_mem = ctypes.windll.kernel32.GlobalLock(h_mem)
                if not p_mem:
                    return ""

                # Read the data
                text = ctypes.wstring_at(p_mem)
                ctypes.windll.kernel32.GlobalUnlock(h_mem)
                return text
            finally:
                ctypes.windll.user32.CloseClipboard()
        except Exception:
            return ""

    def simulate_paste(self) -> bool:
        """Simulate Ctrl+V paste."""
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 'v')
            return True
        except Exception as e:
            print(f"Error simulating paste: {e}")
            return False


class WindowsHotkeyManager(BaseHotkeyManager):
    """Windows hotkey manager using pynput."""

    def __init__(self):
        """Initialize hotkey manager."""
        self._hotkeys = {}
        self._listener = None
        self._running = False

    def _normalize_hotkey(self, hotkey: str) -> str:
        """Normalize hotkey string for pynput format."""
        hotkey = hotkey.lower().strip()

        # Windows-specific replacements
        replacements = {
            'ctrl': '<ctrl>',
            'alt': '<alt>',
            'shift': '<shift>',
            'win': '<cmd>',
            'windows': '<cmd>',
            'super': '<cmd>',
            'meta': '<cmd>',
        }

        parts = hotkey.replace(' ', '').split('+')
        normalized_parts = []

        for part in parts:
            if part in replacements:
                normalized_parts.append(replacements[part])
            elif len(part) == 1:
                normalized_parts.append(part)
            else:
                normalized_parts.append(f'<{part}>')

        return '+'.join(normalized_parts)

    def register(self, hotkey: str, callback: Callable[[], None]) -> bool:
        """Register a global hotkey."""
        try:
            normalized = self._normalize_hotkey(hotkey)
            self._hotkeys[normalized] = callback

            # Restart listener if running
            if self._running:
                self.stop()
                self.start()

            return True
        except Exception as e:
            print(f"Error registering hotkey: {e}")
            return False

    def unregister(self, hotkey: str) -> bool:
        """Unregister a hotkey."""
        try:
            normalized = self._normalize_hotkey(hotkey)
            if normalized in self._hotkeys:
                del self._hotkeys[normalized]

                # Restart listener if running
                if self._running:
                    self.stop()
                    self.start()

            return True
        except Exception as e:
            print(f"Error unregistering hotkey: {e}")
            return False

    def start(self) -> None:
        """Start listening for hotkeys."""
        if self._running:
            return

        try:
            from pynput import keyboard

            # Create hotkey listeners
            if self._hotkeys:
                self._listener = keyboard.GlobalHotKeys(self._hotkeys)
                self._listener.start()
                self._running = True
        except Exception as e:
            print(f"Error starting hotkey listener: {e}")

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._running = False

    def is_registered(self, hotkey: str) -> bool:
        """Check if hotkey is registered."""
        normalized = self._normalize_hotkey(hotkey)
        return normalized in self._hotkeys