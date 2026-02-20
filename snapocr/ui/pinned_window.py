"""
Pinned floating window for keeping screenshots visible.

This module provides a floating window that:
- Stays always on top
- Can be dragged around the screen
- Displays the screenshot and OCR text
- Has a context menu for actions
"""

from typing import Optional, Callable
from PIL import Image, ImageTk
import tkinter as tk


class PinnedWindow:
    """
    A floating always-on-top window for pinned screenshots.

    Features:
    - Draggable by clicking anywhere
    - Right-click context menu
    - Resizable image display
    - Shows OCR text
    """

    # Window title
    TITLE = "Pinned Screenshot"
    # Background color
    BG_COLOR = '#2D2D2D'
    # Text color
    TEXT_COLOR = '#FFFFFF'
    # Default thumbnail size
    DEFAULT_WIDTH = 300
    DEFAULT_HEIGHT = 200
    # Minimum size
    MIN_WIDTH = 100
    MIN_HEIGHT = 80

    # Class variable to track all pinned windows
    _pinned_windows = []

    def __init__(self):
        """Initialize the pinned window."""
        self._window: Optional[tk.Toplevel] = None
        self._image: Optional[Image.Image] = None
        self._text: str = ''
        self._latex: Optional[str] = None
        self._on_copy: Optional[Callable[[], None]] = None
        self._drag_start: Optional[tuple] = None

    def show(
        self,
        image: Image.Image,
        text: str = '',
        latex: Optional[str] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        on_copy: Optional[Callable[[], None]] = None
    ):
        """
        Show the pinned window with the given image.

        Args:
            image: PIL Image to display
            text: OCR text (optional)
            latex: LaTeX result (optional)
            x: Initial X position (optional)
            y: Initial Y position (optional)
            on_copy: Callback for copy action
        """
        self._image = image
        self._text = text
        self._latex = latex
        self._on_copy = on_copy

        # Create the window
        self._window = tk.Toplevel()
        self._window.title(self.TITLE)
        self._window.attributes('-topmost', True)
        self._window.configure(bg=self.BG_COLOR)
        self._window.overrideredirect(True)  # Remove window decorations

        # Calculate window size based on image
        img_width, img_height = image.size
        aspect = img_width / img_height

        # Scale to fit default size while maintaining aspect ratio
        if img_width > self.DEFAULT_WIDTH:
            display_width = self.DEFAULT_WIDTH
            display_height = int(display_width / aspect)
        elif img_height > self.DEFAULT_HEIGHT:
            display_height = self.DEFAULT_HEIGHT
            display_width = int(display_height * aspect)
        else:
            display_width = min(img_width, self.DEFAULT_WIDTH)
            display_height = min(img_height, self.DEFAULT_HEIGHT)

        display_height = max(self.MIN_HEIGHT, display_height)
        display_width = max(self.MIN_WIDTH, display_width)

        # Set initial position (default to center of screen)
        if x is None or y is None:
            screen_width = self._window.winfo_screenwidth()
            screen_height = self._window.winfo_screenheight()
            x = (screen_width - display_width) // 2
            y = (screen_height - display_height) // 2

        self._window.geometry(f"{display_width}x{display_height}+{x}+{y}")

        # Create border frame
        border_frame = tk.Frame(
            self._window,
            bg='#00BFFF',
            padx=2,
            pady=2
        )
        border_frame.pack(fill=tk.BOTH, expand=True)

        # Create content frame
        content_frame = tk.Frame(border_frame, bg=self.BG_COLOR)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Title bar (draggable)
        title_bar = tk.Frame(
            content_frame,
            bg='#3D3D3D',
            height=20
        )
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)

        # Title label
        title_label = tk.Label(
            title_bar,
            text="SnapOCR",
            bg='#3D3D3D',
            fg=self.TEXT_COLOR,
            font=('Arial', 9)
        )
        title_label.pack(side=tk.LEFT, padx=5)

        # Close button in title bar
        close_btn = tk.Button(
            title_bar,
            text="x",
            command=self.close,
            bg='#C62828',
            fg=self.TEXT_COLOR,
            relief=tk.FLAT,
            padx=5,
            font=('Arial', 8, 'bold')
        )
        close_btn.pack(side=tk.RIGHT, padx=2, pady=2)

        # Image label
        self._photo = ImageTk.PhotoImage(image.resize((display_width, display_height - 20), Image.LANCZOS))
        image_label = tk.Label(
            content_frame,
            image=self._photo,
            bg=self.BG_COLOR
        )
        image_label.pack(fill=tk.BOTH, expand=True)
        image_label.image = self._photo  # Keep reference

        # Bind drag events to title bar and image
        title_bar.bind('<ButtonPress-1>', self._on_drag_start)
        title_bar.bind('<B1-Motion>', self._on_drag_motion)
        title_label.bind('<ButtonPress-1>', self._on_drag_start)
        title_label.bind('<B1-Motion>', self._on_drag_motion)
        image_label.bind('<ButtonPress-1>', self._on_drag_start)
        image_label.bind('<B1-Motion>', self._on_drag_motion)

        # Create context menu
        self._menu = tk.Menu(self._window, tearoff=0)
        self._menu.add_command(label="Copy Text", command=self._copy_text)
        if latex:
            self._menu.add_command(label="Copy LaTeX", command=self._copy_latex)
        self._menu.add_separator()
        self._menu.add_command(label="Close", command=self.close)

        # Bind right-click for context menu
        self._window.bind('<ButtonPress-3>', self._show_context_menu)
        title_bar.bind('<ButtonPress-3>', self._show_context_menu)
        image_label.bind('<ButtonPress-3>', self._show_context_menu)

        # Track this window
        PinnedWindow._pinned_windows.append(self)

    def _on_drag_start(self, event):
        """Handle drag start."""
        self._drag_start = (event.x_root, event.y_root)

    def _on_drag_motion(self, event):
        """Handle drag motion to move window."""
        if self._drag_start:
            dx = event.x_root - self._drag_start[0]
            dy = event.y_root - self._drag_start[1]
            x = self._window.winfo_x() + dx
            y = self._window.winfo_y() + dy
            self._window.geometry(f"+{x}+{y}")
            self._drag_start = (event.x_root, event.y_root)

    def _show_context_menu(self, event):
        """Show the context menu."""
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()

    def _copy_text(self):
        """Copy the OCR text to clipboard."""
        if self._on_copy:
            self._on_copy()
        elif self._text:
            # Copy directly to clipboard
            self._window.clipboard_clear()
            self._window.clipboard_append(self._text)

    def _copy_latex(self):
        """Copy the LaTeX result to clipboard."""
        if self._latex:
            self._window.clipboard_clear()
            self._window.clipboard_append(self._latex)

    def close(self):
        """Close the pinned window."""
        if self._window:
            # Remove from tracking list
            if self in PinnedWindow._pinned_windows:
                PinnedWindow._pinned_windows.remove(self)
            self._window.destroy()
            self._window = None

    def is_visible(self) -> bool:
        """Check if the window is currently visible."""
        return self._window is not None and self._window.winfo_exists()

    @classmethod
    def get_all_windows(cls):
        """Get all active pinned windows."""
        return [w for w in cls._pinned_windows if w.is_visible()]

    @classmethod
    def close_all(cls):
        """Close all pinned windows."""
        for window in cls._pinned_windows[:]:
            window.close()
        cls._pinned_windows.clear()


def create_pinned_window(
    image: Image.Image,
    text: str = '',
    latex: Optional[str] = None,
    x: Optional[int] = None,
    y: Optional[int] = None,
    on_copy: Optional[Callable[[], None]] = None
) -> PinnedWindow:
    """
    Convenience function to create and show a pinned window.

    Returns:
        The PinnedWindow instance.
    """
    window = PinnedWindow()
    window.show(image, text, latex, x, y, on_copy)
    return window
