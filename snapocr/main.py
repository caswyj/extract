"""
SnapOCR Main Entry Point

Cross-platform screenshot OCR tool with LaTeX conversion support.
"""

import argparse
import os
import sys
from typing import Optional

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
        image_path = self._screenshot_capture.select_region()
        if not image_path:
            return None

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

    def run_once(self) -> Optional[str]:
        """Run a single capture and extraction."""
        return self.capture_and_extract()

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
    result = app.run_once()
    if result is None:
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
