"""
SnapOCR Main Entry Point

Cross-platform screenshot OCR tool with LaTeX conversion support.
"""

import argparse
import os
import sys
from typing import Optional


def _setup_windows_dpi():
    """Setup Windows DPI awareness for correct screen coordinates."""
    if sys.platform == 'win32':
        try:
            import ctypes
            # Try to set Per-Monitor DPI Aware (Windows 8.1+)
            # This ensures correct coordinates on scaled displays
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except (AttributeError, OSError):
            # Fallback for older Windows versions
            try:
                import ctypes
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
        except Exception:
            pass


# Setup DPI awareness before any UI operations
_setup_windows_dpi()

from .core.config import Config
from .core.ocr import extract_text, format_result
from .core.clipboard import ClipboardManager
from .platform.base import PlatformManager


class SnapOCR:
    """Main SnapOCR application class."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize SnapOCR.

        Args:
            config: Optional config instance. Creates new one if not provided.
        """
        self._config = config or Config()
        self._screenshot_capture = PlatformManager.get_screenshot_capture()
        self._clipboard_manager = ClipboardManager()

    def capture_and_extract(self, show_result: bool = True) -> Optional[str]:
        """
        Capture a screenshot region and extract text.

        Args:
            show_result: Whether to print the result.

        Returns:
            Extracted text or None if cancelled/failed.
        """
        # Capture screenshot region
        selection_result = self._screenshot_capture.select_region()
        if not selection_result:
            return None

        image_path = selection_result.image_path

        try:
            # Extract text
            if show_result:
                print("Extracting text...")

            text, latex = extract_text(
                image_path,
                language=self._config.language,
                tesseract_path=self._config.tesseract_path,
                latex_mode=self._config.latex_conversion,
                auto_detect_math=True
            )

            # Format result
            result = format_result(text, latex)

            if not result:
                if show_result:
                    print("No text detected in the selected region.")
                return None

            # Copy to clipboard
            self._clipboard_manager.copy(result)

            if show_result:
                print(f"Text copied to clipboard ({len(result)} characters)")
                print("-" * 40)
                preview = result[:200] + "..." if len(result) > 200 else result
                print(preview)
                print("-" * 40)

            return result

        finally:
            # Cleanup temp file
            try:
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)
            except Exception:
                pass

    def capture_with_ui(self, show_result: bool = True) -> Optional[str]:
        """
        Capture a screenshot region with interactive UI.

        Shows selection overlay, result panel, and action buttons.

        Args:
            show_result: Whether to print the result.

        Returns:
            Extracted text or None if cancelled/failed.
        """
        try:
            import tkinter as tk
            from tkinter import simpledialog
            from PIL import Image
        except ImportError as e:
            print(f"Error: UI requires tkinter and PIL: {e}")
            return self.capture_and_extract(show_result)

        # Capture screenshot region
        selection_result = self._screenshot_capture.select_region()
        if not selection_result:
            return None

        image_path = selection_result.image_path
        rect = selection_result.rect
        screen_width = selection_result.screen_width
        screen_height = selection_result.screen_height

        try:
            # Extract text
            if show_result:
                print("Extracting text...")

            text, latex = extract_text(
                image_path,
                language=self._config.language,
                tesseract_path=self._config.tesseract_path,
                latex_mode=self._config.latex_conversion,
                auto_detect_math=True
            )

            # Format result
            result = format_result(text, latex)

            if not result:
                if show_result:
                    print("No text detected in the selected region.")
                # Show a notification anyway
                self._show_no_text_dialog()
                return None

            # Load the captured image for potential pinning
            captured_image = Image.open(image_path)

            # Show the interactive result UI
            final_result = self._show_result_ui(
                text=text,
                latex=latex,
                result=result,
                captured_image=captured_image,
                rect=rect,
                screen_bounds=(screen_width, screen_height),
                show_result=show_result
            )

            return final_result

        finally:
            # Cleanup temp file
            try:
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)
            except Exception:
                pass

    def _show_no_text_dialog(self):
        """Show a dialog when no text is detected."""
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()  # Hide the main window
            root.attributes('-topmost', True)
            messagebox.showinfo("SnapOCR", "No text detected in the selected region.")
            root.destroy()
        except Exception:
            pass

    def _show_result_ui(
        self,
        text: str,
        latex: Optional[str],
        result: str,
        captured_image,
        rect: tuple,
        screen_bounds: tuple,
        show_result: bool = True
    ) -> Optional[str]:
        """
        Show the interactive result UI with Pin/Accept/Cancel buttons.

        Returns:
            The final result if accepted, None if cancelled.
        """
        import tkinter as tk
        from tkinter import scrolledtext
        from PIL import ImageTk

        from .ui.pinned_window import PinnedWindow

        final_result = [None]  # Use list to allow modification in nested function

        # Create main window
        root = tk.Tk()
        root.title("SnapOCR Result")
        root.attributes('-topmost', True)
        root.configure(bg='#2D2D2D')

        # Calculate window position
        sx, sy, sw, sh = rect
        screen_w, screen_h = screen_bounds
        GAP = 10

        # Panel size
        panel_width = 350
        panel_height = 200

        # Calculate position (try right first, then left, then below)
        if sx + sw + GAP + panel_width <= screen_w:
            panel_x = sx + sw + GAP
            panel_y = sy
        elif sx - GAP - panel_width >= 0:
            panel_x = sx - GAP - panel_width
            panel_y = sy
        else:
            panel_x = sx
            panel_y = sy + sh + GAP

        root.geometry(f"{panel_width}x{panel_height}+{panel_x}+{panel_y}")

        # Create border frame
        border_frame = tk.Frame(root, bg='#00BFFF', padx=2, pady=2)
        border_frame.pack(fill=tk.BOTH, expand=True)

        # Main content frame
        content_frame = tk.Frame(border_frame, bg='#2D2D2D')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Text display area
        text_widget = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            font=('Arial', 11),
            bg='#1E1E1E',
            fg='#FFFFFF',
            insertbackground='#FFFFFF',
            selectbackground='#00BFFF',
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, result)
        text_widget.config(state=tk.DISABLED)

        # Button frame
        button_frame = tk.Frame(content_frame, bg='#2D2D2D')
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def on_pin():
            """Handle Pin button - create a floating window."""
            pinned = PinnedWindow()
            pinned.show(
                image=captured_image,
                text=text,
                latex=latex,
                x=root.winfo_x() + 50,
                y=root.winfo_y() + 50,
                on_copy=lambda: self._clipboard_manager.copy(result)
            )
            if show_result:
                print("Screenshot pinned to floating window.")

        def on_accept():
            """Handle Accept button - copy and close."""
            self._clipboard_manager.copy(result)
            final_result[0] = result
            if show_result:
                print(f"Text copied to clipboard ({len(result)} characters)")
            root.destroy()

        def on_cancel():
            """Handle Cancel button - just close."""
            root.destroy()

        # Pin button
        pin_btn = tk.Button(
            button_frame,
            text="Pin",
            command=on_pin,
            bg='#1565C0',
            fg='#FFFFFF',
            activebackground='#1976D2',
            activeforeground='#FFFFFF',
            relief=tk.FLAT,
            padx=15,
            font=('Arial', 10, 'bold')
        )
        pin_btn.pack(side=tk.LEFT, padx=5)

        # Accept button
        accept_btn = tk.Button(
            button_frame,
            text="Accept",
            command=on_accept,
            bg='#2E7D32',
            fg='#FFFFFF',
            activebackground='#388E3C',
            activeforeground='#FFFFFF',
            relief=tk.FLAT,
            padx=15,
            font=('Arial', 10, 'bold')
        )
        accept_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=on_cancel,
            bg='#C62828',
            fg='#FFFFFF',
            activebackground='#D32F2F',
            activeforeground='#FFFFFF',
            relief=tk.FLAT,
            padx=15,
            font=('Arial', 10, 'bold')
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Bind escape for cancel
        root.bind('<Escape>', lambda e: on_cancel())

        # Focus on window
        root.focus_set()

        # Run the UI
        root.mainloop()

        return final_result[0]

    def run_once(self) -> Optional[str]:
        """Run a single capture and extraction."""
        return self.capture_and_extract()

    def run_with_ui(self) -> Optional[str]:
        """Run a single capture with interactive UI."""
        return self.capture_with_ui()

    @property
    def config(self) -> Config:
        """Get the configuration."""
        return self._config


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='SnapOCR - Cross-platform screenshot OCR tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  snapocr                    Capture region and extract text
  snapocr --ui               Capture with interactive UI (Pin/Accept/Cancel)
  snapocr --latex            Enable LaTeX conversion for math
  snapocr --lang eng         Use English only OCR

Config file location:
  macOS:   ~/Library/Application Support/SnapOCR/config.json
  Windows: %APPDATA%/SnapOCR/config.json
  Linux:   ~/.config/snapocr/config.json
        """
    )

    parser.add_argument(
        '--lang', '-l',
        type=str,
        help='OCR language (e.g., "eng", "chi_sim", "eng+chi_sim")'
    )

    parser.add_argument(
        '--latex',
        action='store_true',
        help='Enable LaTeX conversion for math formulas'
    )

    parser.add_argument(
        '--no-latex',
        action='store_true',
        help='Disable LaTeX conversion'
    )

    parser.add_argument(
        '--ui',
        action='store_true',
        help='Show interactive UI with Pin/Accept/Cancel buttons'
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to config file'
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version='%(prog)s 2.0.0'
    )

    args = parser.parse_args()

    # Load config
    config = Config(args.config) if args.config else Config()

    # Apply command line overrides
    if args.lang:
        config.language = args.lang
    if args.latex:
        config.latex_conversion = True
    if args.no_latex:
        config.latex_conversion = False

    # Create app instance and run
    app = SnapOCR(config)

    if args.ui:
        result = app.run_with_ui()
    else:
        result = app.run_once()

    if result is None:
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
