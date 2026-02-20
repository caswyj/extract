"""
OCR text extraction with LaTeX conversion support.
"""

import os
import re
import sys
from typing import Optional, Tuple
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None


def get_bundled_tesseract_path() -> Optional[str]:
    """
    Get the path to bundled Tesseract executable if running as a packaged app.

    Returns:
        Path to tesseract executable or None if not found.
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        if sys.platform == 'win32':
            tesseract_exe = os.path.join(base_path, 'tesseract', 'tesseract.exe')
        else:
            tesseract_exe = os.path.join(base_path, 'tesseract', 'tesseract')
        if os.path.exists(tesseract_exe):
            return tesseract_exe
    return None


def get_bundled_tessdata_path() -> Optional[str]:
    """
    Get the path to bundled tessdata directory if running as a packaged app.

    Returns:
        Path to tessdata directory or None if not found.
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        tessdata_path = os.path.join(base_path, 'tessdata')
        if os.path.exists(tessdata_path):
            return tessdata_path
    return None


def setup_tesseract() -> Optional[str]:
    """
    Setup Tesseract paths for bundled or system installation.

    Returns:
        Path to Tesseract executable or None.
    """
    if pytesseract is None:
        return None

    bundled_path = get_bundled_tesseract_path()
    if bundled_path:
        pytesseract.pytesseract.tesseract_cmd = bundled_path
        tessdata_path = get_bundled_tessdata_path()
        if tessdata_path:
            os.environ['TESSDATA_PREFIX'] = tessdata_path + os.sep
        return bundled_path
    return None


# Lazy-loaded LaTeX OCR model
_latex_model = None


def _get_latex_model():
    """
    Lazy load the RapidLatexOCR model.

    Returns:
        LatexOCR instance or None if unavailable.
    """
    global _latex_model
    if _latex_model is None:
        try:
            from rapid_latex_ocr import LatexOCR
            print("Loading LaTeX OCR model...")
            _latex_model = LatexOCR()
            print("LaTeX OCR model loaded successfully")
        except ImportError as e:
            print(f"Warning: rapid-latex-ocr not installed: {e}")
            print("Install with: pip install rapid-latex-ocr")
            return None
        except Exception as e:
            print(f"Warning: Could not load LaTeX OCR model: {e}")
            return None
    return _latex_model


def detect_math_content(image: Image.Image) -> bool:
    """
    Detect if image contains mathematical content by analyzing the image.

    Args:
        image: PIL Image to analyze.

    Returns:
        True if mathematical content is detected.
    """
    if pytesseract is None:
        return False

    try:
        # Try to get text with basic config to detect math
        text = pytesseract.image_to_string(image, config='--psm 6')

        # Check for math patterns
        math_patterns = [
            r'[=+\-*/^]',
            r'[∑∫∏∂∇]',
            r'[α-ωΑ-Ω]',
            r'[<>≤≥≠±×÷]',
            r'\d+\s*[xy]\s*=',
            r'[xy]\s*\^',
            r'\d+\^',  # Powers like 2^3
            r'\\frac',
            r'\\sqrt',
            r'\\sum',
            r'\\int',
            r'\d+\s*[+\-*/]\s*\d+',  # Simple equations
        ]

        for pattern in math_patterns:
            if re.search(pattern, text):
                return True
        return False
    except Exception:
        return False


def extract_text(
    image_path: str,
    language: str = 'chi_sim+eng',
    tesseract_path: Optional[str] = None,
    latex_mode: bool = False,
    auto_detect_math: bool = True
) -> Tuple[str, Optional[str]]:
    """
    Extract text from an image using OCR with optional LaTeX conversion.

    Args:
        image_path: Path to the image file.
        language: Tesseract language code(s), e.g., 'eng', 'chi_sim', 'chi_sim+eng'.
        tesseract_path: Optional path to Tesseract executable.
        latex_mode: Force LaTeX conversion for the entire image.
        auto_detect_math: Automatically detect and convert math regions.

    Returns:
        Tuple of (extracted_text, latex_result) where latex_result may be None.
    """
    if pytesseract is None:
        raise ImportError("pytesseract is not installed. Install with: pip install pytesseract")

    setup_tesseract()

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    image = Image.open(image_path)

    # Check available languages and select the best combination
    try:
        available_langs = pytesseract.get_languages()
        print(f"Available languages: {available_langs}")

        # Try to use Chinese + English for better results
        if 'chi_sim' in available_langs and 'eng' in available_langs:
            language = 'chi_sim+eng'
        elif 'chi_sim' in available_langs:
            language = 'chi_sim'
        elif 'eng' in available_langs:
            language = 'eng'
        else:
            language = available_langs[0] if available_langs else 'eng'

        print(f"Using language: {language}")
    except Exception as e:
        print(f"Could not get available languages: {e}")

    # Improved OCR configuration for better Chinese recognition
    # --oem 3: Use LSTM neural net engine (best for Chinese)
    # --psm 6: Assume single uniform block of text
    # -c preserve_interword_spaces=1: Keep spaces
    custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'

    try:
        text = pytesseract.image_to_string(
            image,
            lang=language,
            config=custom_config
        )
        text = text.strip()
    except Exception as e:
        print(f"Error during OCR: {e}")
        # Fallback to basic config
        try:
            text = pytesseract.image_to_string(image, lang=language)
            text = text.strip()
        except Exception as e2:
            print(f"Fallback OCR also failed: {e2}")
            text = ""

    latex_result = None

    # LaTeX conversion
    if latex_mode or (auto_detect_math and detect_math_content(image)):
        model = _get_latex_model()
        if model is not None:
            try:
                print("Converting to LaTeX...")
                # RapidLatexOCR expects PIL Image
                result = model(image)
                if result:
                    # result might be a tuple or string depending on version
                    if isinstance(result, tuple):
                        latex_result = result[0] if result[0] else None
                    else:
                        latex_result = str(result).strip()
                    if latex_result:
                        print(f"LaTeX result: {latex_result[:100]}...")
            except Exception as e:
                print(f"Warning: LaTeX conversion failed: {e}")
                import traceback
                traceback.print_exc()

    return text, latex_result


def format_result(text: str, latex: Optional[str] = None) -> str:
    """
    Format the OCR result with optional LaTeX.

    Args:
        text: The extracted text.
        latex: Optional LaTeX result.

    Returns:
        Formatted result string.
    """
    result_parts = []

    if text:
        result_parts.append(text)

    if latex:
        result_parts.append(f"\n[LaTeX]: {latex}")

    return '\n'.join(result_parts).strip()
