"""
Result panel for displaying OCR text and LaTeX results.

This module provides a panel that:
- Displays next to the selected region
- Shows OCR text with optional LaTeX
- Supports scrolling for long content
- Includes a copy button
"""

from typing import Optional, Tuple, Callable
from PIL import Image, ImageTk


class ResultPanel:
    """
    Panel for displaying OCR results next to the selection region.

    The panel automatically positions itself based on available screen space:
    Priority: right > left > below > above
    """

    # Gap between selection and panel in pixels
    GAP = 10
    # Panel padding in pixels
    PADDING = 10
    # Minimum panel size
    MIN_WIDTH = 200
    MIN_HEIGHT = 100
    # Maximum panel size
    MAX_WIDTH = 400
    MAX_HEIGHT = 300
    # Background color
    BG_COLOR = '#2D2D2D'
    # Text color
    TEXT_COLOR = '#FFFFFF'
    # Border color
    BORDER_COLOR = '#00BFFF'
    # Font
    FONT_FAMILY = ('Arial', 11)

    def __init__(self):
        """Initialize the result panel."""
        self._window = None
        self._text_widget = None
        self._result_text = ''
        self._latex_text = ''
        self._copy_callback: Optional[Callable[[], None]] = None
        self._accept_callback: Optional[Callable[[], None]] = None
        self._cancel_callback: Optional[Callable[[], None]] = None

    def calculate_position(
        self,
        selection_rect: Tuple[int, int, int, int],
        panel_size: Tuple[int, int],
        screen_bounds: Tuple[int, int]
    ) -> Tuple[int, int]:
        """
        Calculate the best position for the panel.

        Args:
            selection_rect: (x, y, width, height) of the selection
            panel_size: (width, height) of the panel
            screen_bounds: (width, height) of the screen

        Returns:
            (x, y) position for the top-left corner of the panel
        """
        sx, sy, sw, sh = selection_rect
        pw, ph = panel_size
        scr_w, scr_h = screen_bounds

        # 1. Try right side
        if sx + sw + self.GAP + pw <= scr_w:
            return (sx + sw + self.GAP, sy)

        # 2. Try left side
        if sx - self.GAP - pw >= 0:
            return (sx - self.GAP - pw, sy)

        # 3. Try below
        if sy + sh + self.GAP + ph <= scr_h:
            return (sx, sy + sh + self.GAP)

        # 4. Try above
        if sy - self.GAP - ph >= 0:
            return (sx, sy - self.GAP - ph)

        # 5. Fallback - position at right edge of screen
        return (scr_w - pw - self.GAP, sy)

    def show(
        self,
        text: str,
        latex: Optional[str],
        selection_rect: Tuple[int, int, int, int],
        screen_bounds: Tuple[int, int],
        on_copy: Optional[Callable[[], None]] = None,
        on_accept: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None
    ):
        """
        Show the result panel.

        Args:
            text: OCR text to display
            latex: Optional LaTeX result
            selection_rect: (x, y, width, height) of the selection
            screen_bounds: (width, height) of the screen
            on_copy: Callback when copy button is clicked
            on_accept: Callback when accept button is clicked
            on_cancel: Callback when cancel button is clicked
        """
        self._result_text = text
        self._latex_text = latex or ''
        self._copy_callback = on_copy
        self._accept_callback = on_accept
        self._cancel_callback = on_cancel

        try:
            import tkinter as tk
            import tkinter.scrolledtext as scrolledtext
        except ImportError:
            print("Error: tkinter not available")
            return

        # Calculate content to determine size
        full_text = text
        if latex:
            full_text += f"\n\n[LaTeX]:\n{latex}"

        # Estimate panel size based on content
        lines = full_text.split('\n')
        max_line_len = max(len(line) for line in lines) if lines else 0
        num_lines = len(lines)

        # Estimate dimensions (rough approximation)
        char_width = 8  # Approximate character width in pixels
        line_height = 18  # Approximate line height in pixels

        panel_width = min(self.MAX_WIDTH, max(self.MIN_WIDTH, max_line_len * char_width + self.PADDING * 2))
        panel_height = min(self.MAX_HEIGHT, max(self.MIN_HEIGHT, num_lines * line_height + self.PADDING * 2 + 40))

        # Calculate position
        panel_x, panel_y = self.calculate_position(
            selection_rect,
            (panel_width, panel_height),
            screen_bounds
        )

        # Create the window
        self._window = tk.Toplevel()
        self._window.title("OCR Result")
        self._window.geometry(f"{panel_width}x{panel_height}+{panel_x}+{panel_y}")
        self._window.attributes('-topmost', True)
        self._window.configure(bg=self.BG_COLOR)
        self._window.overrideredirect(True)  # Remove window decorations

        # Create border frame
        border_frame = tk.Frame(
            self._window,
            bg=self.BORDER_COLOR,
            padx=1,
            pady=1
        )
        border_frame.pack(fill=tk.BOTH, expand=True)

        # Main content frame
        content_frame = tk.Frame(border_frame, bg=self.BG_COLOR)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Text display area
        self._text_widget = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            font=self.FONT_FAMILY,
            bg='#1E1E1E',
            fg=self.TEXT_COLOR,
            insertbackground=self.TEXT_COLOR,
            selectbackground=self.BORDER_COLOR,
            relief=tk.FLAT,
            padx=self.PADDING,
            pady=self.PADDING
        )
        self._text_widget.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self._text_widget.insert(tk.END, full_text)
        self._text_widget.config(state=tk.DISABLED)  # Make read-only

        # Button frame
        button_frame = tk.Frame(content_frame, bg=self.BG_COLOR)
        button_frame.pack(fill=tk.X, padx=self.PADDING, pady=(0, self.PADDING))

        # Copy button
        copy_btn = tk.Button(
            button_frame,
            text="Copy",
            command=self._on_copy,
            bg='#4A4A4A',
            fg=self.TEXT_COLOR,
            activebackground='#5A5A5A',
            activeforeground=self.TEXT_COLOR,
            relief=tk.FLAT,
            padx=10
        )
        copy_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Accept button
        accept_btn = tk.Button(
            button_frame,
            text="Accept",
            command=self._on_accept,
            bg='#2E7D32',  # Green
            fg=self.TEXT_COLOR,
            activebackground='#388E3C',
            activeforeground=self.TEXT_COLOR,
            relief=tk.FLAT,
            padx=10
        )
        accept_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            bg='#C62828',  # Red
            fg=self.TEXT_COLOR,
            activebackground='#D32F2F',
            activeforeground=self.TEXT_COLOR,
            relief=tk.FLAT,
            padx=10
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Bind escape key
        self._window.bind('<Escape>', lambda e: self._on_cancel())

        # Focus on window
        self._window.focus_set()

    def _on_copy(self):
        """Handle copy button click."""
        if self._copy_callback:
            self._copy_callback()

    def _on_accept(self):
        """Handle accept button click."""
        if self._accept_callback:
            self._accept_callback()
        self.close()

    def _on_cancel(self):
        """Handle cancel button click."""
        if self._cancel_callback:
            self._cancel_callback()
        self.close()

    def close(self):
        """Close the result panel."""
        if self._window:
            self._window.destroy()
            self._window = None

    def is_visible(self) -> bool:
        """Check if the panel is currently visible."""
        return self._window is not None and self._window.winfo_exists()


def show_result_panel(
    text: str,
    latex: Optional[str],
    selection_rect: Tuple[int, int, int, int],
    screen_bounds: Tuple[int, int],
    on_copy: Optional[Callable[[], None]] = None,
    on_accept: Optional[Callable[[], None]] = None,
    on_cancel: Optional[Callable[[], None]] = None
) -> ResultPanel:
    """
    Convenience function to show a result panel.

    Returns:
        The ResultPanel instance.
    """
    panel = ResultPanel()
    panel.show(text, latex, selection_rect, screen_bounds, on_copy, on_accept, on_cancel)
    return panel
