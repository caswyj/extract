"""
Full-screen overlay for region selection with dimming effect.

This module provides an interactive selection overlay that:
- Captures the full screen as background
- Creates a semi-transparent dimmed overlay
- Highlights the selected region in real-time
- Returns selection coordinates and captured image
"""

import os
import tempfile
from typing import Optional, Tuple, Callable

from ..platform.base import SelectionResult


class SelectionOverlay:
    """
    Full-screen overlay for interactive region selection.

    Features:
    - Screen dimming with clear selection area
    - Real-time selection rectangle
    - Cross-platform tkinter implementation
    """

    # Dimming opacity (0.0 to 1.0)
    DIM_OPACITY = 0.4
    # Selection border color
    SELECTION_COLOR = '#00BFFF'  # Deep sky blue
    # Selection border width
    SELECTION_WIDTH = 2
    # Minimum selection size
    MIN_SELECTION_SIZE = 5

    def __init__(self):
        """Initialize the selection overlay."""
        self._temp_dir = tempfile.gettempdir()
        self._result: Optional[SelectionResult] = None
        self._callback: Optional[Callable[[SelectionResult], None]] = None

    def _get_temp_path(self) -> str:
        """Get a temporary file path for screenshot."""
        return os.path.join(self._temp_dir, 'snapocr_selection.png')

    def select(self, callback: Optional[Callable[[SelectionResult], None]] = None) -> Optional[SelectionResult]:
        """
        Show the selection overlay and wait for user to select a region.

        Args:
            callback: Optional callback to receive the selection result.

        Returns:
            SelectionResult with the captured region, or None if cancelled.
        """
        self._callback = callback
        self._result = None

        try:
            import mss
            import tkinter as tk
            from PIL import Image, ImageTk
        except ImportError as e:
            print(f"Error: Required libraries not available: {e}")
            return None

        # Capture full screen
        try:
            with mss.mss() as sct:
                # Get combined virtual screen (all monitors)
                monitor = sct.monitors[0]  # All monitors combined
                screenshot = sct.grab(monitor)
                screen_img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                screen_width, screen_height = screenshot.size
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None

        # Selection state
        selection = {
            'start': None,
            'end': None,
            'done': False,
            'cancelled': False
        }

        # Create fullscreen window
        root = tk.Tk()
        root.title("SnapOCR Selection")
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(bg='black', cursor='cross')

        # Platform-specific transparency
        if hasattr(root, 'attributes'):
            # On macOS, use -transparent to allow click-through in dimmed areas
            # On Windows/Linux, we use alpha blending
            import platform
            if platform.system() == 'Darwin':
                # macOS: use standard alpha
                root.attributes('-alpha', 0.3)
            else:
                root.attributes('-alpha', self.DIM_OPACITY)

        # Create canvas covering the entire screen
        canvas = tk.Canvas(
            root,
            width=screen_width,
            height=screen_height,
            bg='black',
            highlightthickness=0
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        # Selection rectangle ID
        selection_rect_id = [None]
        dim_rect_ids = []  # IDs for dimmed areas

        def draw_dimmed_overlay():
            """Draw dimmed overlay outside selection area."""
            # Clear previous dim rects
            for rect_id in dim_rect_ids:
                canvas.delete(rect_id)
            dim_rect_ids.clear()

            # If no selection yet, entire screen is dimmed
            if not selection['start'] or not selection['end']:
                return

            x1, y1 = selection['start']
            x2, y2 = selection['end']
            left, top = min(x1, x2), min(y1, y2)
            right, bottom = max(x1, x2), max(y1, y2)

            # Draw semi-transparent overlay on areas outside selection
            # Top strip
            if top > 0:
                rect = canvas.create_rectangle(
                    0, 0, screen_width, top,
                    fill='#000000',
                    stipple='gray50',  # Creates semi-transparent effect
                    outline='',
                    tags='dim'
                )
                dim_rect_ids.append(rect)

            # Bottom strip
            if bottom < screen_height:
                rect = canvas.create_rectangle(
                    0, bottom, screen_width, screen_height,
                    fill='#000000',
                    stipple='gray50',
                    outline='',
                    tags='dim'
                )
                dim_rect_ids.append(rect)

            # Left strip
            if left > 0:
                rect = canvas.create_rectangle(
                    0, top, left, bottom,
                    fill='#000000',
                    stipple='gray50',
                    outline='',
                    tags='dim'
                )
                dim_rect_ids.append(rect)

            # Right strip
            if right < screen_width:
                rect = canvas.create_rectangle(
                    right, top, screen_width, bottom,
                    fill='#000000',
                    stipple='gray50',
                    outline='',
                    tags='dim'
                )
                dim_rect_ids.append(rect)

        def on_press(event):
            """Handle mouse press - start selection."""
            selection['start'] = (event.x, event.y)
            selection['end'] = None

        def on_motion(event):
            """Handle mouse motion - update selection rectangle."""
            if selection['start']:
                selection['end'] = (event.x, event.y)

                # Delete previous selection rectangle
                if selection_rect_id[0]:
                    canvas.delete(selection_rect_id[0])

                # Draw new selection rectangle
                x1, y1 = selection['start']
                x2, y2 = selection['end']

                # Draw selection border
                selection_rect_id[0] = canvas.create_rectangle(
                    min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2),
                    outline=self.SELECTION_COLOR,
                    width=self.SELECTION_WIDTH,
                    tags='selection'
                )

                # Update dimmed overlay
                draw_dimmed_overlay()

        def on_release(event):
            """Handle mouse release - complete selection."""
            if selection['start']:
                selection['end'] = (event.x, event.y)
                selection['done'] = True
                root.destroy()

        def on_escape(event):
            """Handle escape key - cancel selection."""
            selection['cancelled'] = True
            root.destroy()

        def on_right_click(event):
            """Handle right-click - cancel selection."""
            selection['cancelled'] = True
            root.destroy()

        # Bind events
        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<B1-Motion>', on_motion)
        canvas.bind('<ButtonRelease-1>', on_release)
        canvas.bind('<Escape>', on_escape)
        canvas.bind('<ButtonPress-3>', on_right_click)  # Right-click

        # Also bind on the root for escape key
        root.bind('<Escape>', on_escape)

        # Run the selection loop
        root.mainloop()

        # Check if cancelled or invalid
        if selection['cancelled'] or not selection['done']:
            return None

        if not selection['start'] or not selection['end']:
            return None

        # Calculate selection bounds
        x1, y1 = selection['start']
        x2, y2 = selection['end']
        left = int(min(x1, x2))
        top = int(min(y1, y2))
        right = int(max(x1, x2))
        bottom = int(max(y1, y2))

        width = right - left
        height = bottom - top

        # Check minimum size
        if width < self.MIN_SELECTION_SIZE or height < self.MIN_SELECTION_SIZE:
            return None

        # Crop the selected region from the full screen capture
        try:
            region_img = screen_img.crop((left, top, right, bottom))
            temp_path = self._get_temp_path()
            region_img.save(temp_path)
        except Exception as e:
            print(f"Error saving selection: {e}")
            return None

        # Create result
        self._result = SelectionResult(
            image_path=temp_path,
            rect=(left, top, width, height),
            screen_image=screen_img,
            screen_width=screen_width,
            screen_height=screen_height
        )

        if self._callback:
            self._callback(self._result)

        return self._result

    @property
    def result(self) -> Optional[SelectionResult]:
        """Get the last selection result."""
        return self._result


def select_region() -> Optional[SelectionResult]:
    """
    Convenience function to show selection overlay and get result.

    Returns:
        SelectionResult or None if cancelled.
    """
    overlay = SelectionOverlay()
    return overlay.select()
