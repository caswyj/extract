"""
Button bar for OCR actions (Pin, Accept, Cancel).

This module provides a button bar that:
- Appears at the bottom of the selection region
- Provides three action buttons: Pin, Accept, Cancel
- Can be shown independently or integrated with other components
"""

from typing import Optional, Callable
from PIL import Image, ImageTk


class ButtonBar:
    """
    Action button bar for OCR operations.

    Buttons:
    - Pin: Create a floating pinned window with the screenshot
    - Accept: Accept OCR result and copy to clipboard
    - Cancel: Cancel the operation
    """

    # Button bar height
    HEIGHT = 40
    # Button padding
    BUTTON_PADDING = 10
    # Background color
    BG_COLOR = '#2D2D2D'
    # Text color
    TEXT_COLOR = '#FFFFFF'

    def __init__(self):
        """Initialize the button bar."""
        self._window = None
        self._frame = None
        self._on_pin: Optional[Callable[[], None]] = None
        self._on_accept: Optional[Callable[[], None]] = None
        self._on_cancel: Optional[Callable[[], None]] = None

    def show(
        self,
        x: int,
        y: int,
        width: int,
        on_pin: Optional[Callable[[], None]] = None,
        on_accept: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None
    ):
        """
        Show the button bar at the specified position.

        Args:
            x: X position for the button bar
            y: Y position for the button bar
            width: Width of the button bar
            on_pin: Callback for Pin button
            on_accept: Callback for Accept button
            on_cancel: Callback for Cancel button
        """
        self._on_pin = on_pin
        self._on_accept = on_accept
        self._on_cancel = on_cancel

        try:
            import tkinter as tk
        except ImportError:
            print("Error: tkinter not available")
            return

        # Create the window
        self._window = tk.Toplevel()
        self._window.title("Actions")
        self._window.geometry(f"{width}x{self.HEIGHT}+{x}+{y}")
        self._window.attributes('-topmost', True)
        self._window.configure(bg=self.BG_COLOR)
        self._window.overrideredirect(True)  # Remove window decorations

        # Create frame for buttons
        self._frame = tk.Frame(self._window, bg=self.BG_COLOR)
        self._frame.pack(fill=tk.BOTH, expand=True)

        # Pin button
        pin_btn = tk.Button(
            self._frame,
            text="Pin",
            command=self._handle_pin,
            bg='#1565C0',  # Blue
            fg=self.TEXT_COLOR,
            activebackground='#1976D2',
            activeforeground=self.TEXT_COLOR,
            relief=tk.FLAT,
            padx=15,
            font=('Arial', 10, 'bold')
        )
        pin_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Accept button
        accept_btn = tk.Button(
            self._frame,
            text="Accept",
            command=self._handle_accept,
            bg='#2E7D32',  # Green
            fg=self.TEXT_COLOR,
            activebackground='#388E3C',
            activeforeground=self.TEXT_COLOR,
            relief=tk.FLAT,
            padx=15,
            font=('Arial', 10, 'bold')
        )
        accept_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Cancel button
        cancel_btn = tk.Button(
            self._frame,
            text="Cancel",
            command=self._handle_cancel,
            bg='#C62828',  # Red
            fg=self.TEXT_COLOR,
            activebackground='#D32F2F',
            activeforeground=self.TEXT_COLOR,
            relief=tk.FLAT,
            padx=15,
            font=('Arial', 10, 'bold')
        )
        cancel_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Bind escape key for cancel
        self._window.bind('<Escape>', lambda e: self._handle_cancel())

        # Focus on window
        self._window.focus_set()

    def _handle_pin(self):
        """Handle Pin button click."""
        if self._on_pin:
            self._on_pin()

    def _handle_accept(self):
        """Handle Accept button click."""
        if self._on_accept:
            self._on_accept()
        self.close()

    def _handle_cancel(self):
        """Handle Cancel button click."""
        if self._on_cancel:
            self._on_cancel()
        self.close()

    def close(self):
        """Close the button bar."""
        if self._window:
            self._window.destroy()
            self._window = None

    def is_visible(self) -> bool:
        """Check if the button bar is currently visible."""
        return self._window is not None and self._window.winfo_exists()


def show_button_bar(
    x: int,
    y: int,
    width: int,
    on_pin: Optional[Callable[[], None]] = None,
    on_accept: Optional[Callable[[], None]] = None,
    on_cancel: Optional[Callable[[], None]] = None
) -> ButtonBar:
    """
    Convenience function to show a button bar.

    Returns:
        The ButtonBar instance.
    """
    bar = ButtonBar()
    bar.show(x, y, width, on_pin, on_accept, on_cancel)
    return bar
