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
    # Check if running as a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS

        # Platform-specific executable name
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

    # First, check for bundled Tesseract
    bundled_path = get_bundled_tesseract_path()
    if bundled_path:
        pytesseract.pytesseract.tesseract_cmd = bundled_path

        # Set tessdata path for bundled installation
        tessdata_path = get_bundled_tessdata_path()
        if tessdata_path:
            os.environ['TESSDATA_PREFIX'] = tessdata_path + os.sep

        return bundled_path

    # Fall back to system Tesseract
    return None


# Lazy-loaded LaTeX OCR model
_latex_model = None


def _get_latex_model():
    """
    Lazy load the UniMERNet LaTeX OCR model.

    Returns:
        UniMERNet model instance or None if unavailable.
    """
    global _latex_model
    if _latex_model is None:
        try:
            from unimernet.tasks import uni_mernet_task
            from unimernet.common.config import Config

            # Set model path for bundled or system
            if getattr(sys, 'frozen', False):
                model_path = os.path.join(sys._MEIPASS, 'models', 'unimernet')
                if os.path.exists(model_path):
                    os.environ['UNIMERNET_MODEL_PATH'] = model_path

            # Initialize the model
            _latex_model = uni_mernet_task(
                model_name='unimernet',
                device='cpu'  # Use CPU for compatibility, can be changed to 'cuda'
            )
        except ImportError:
            print("Warning: unimernet not installed. LaTeX conversion unavailable.")
            print("Install with: pip install unimernet-small")
            return None
        except Exception as e:
            print(f"Warning: Could not load UniMERNet model: {e}")
            return None
    return _latex_model


def detect_math_content(text: str) -> bool:
    """
    Detect if text contains mathematical content.

    Args:
        text: The extracted text to analyze.

    Returns:
        True if mathematical content is detected.
    """
    # Common mathematical symbols and patterns
    math_patterns = [
        r'[=+\-*/^]',  # Basic operators
        r'[∑∫∏∂∇]',    # Calculus symbols
        r'[α-ωΑ-Ω]',   # Greek letters
        r'[<>≤≥≠±×÷]',  # Comparison and special operators
        r'\d+\s*[xy]\s*=',  # Equations
        r'[xy]\s*\^',  # Powers
        r'\\frac',     # LaTeX fractions
        r'\\sqrt',     # Square roots
        r'\\sum',      # Summation
        r'\\int',      # Integral
        r'\[[^\]]+\]',  # Brackets often used in math
        r'\{[^}]+\}',   # Braces
    ]

    for pattern in math_patterns:
        if re.search(pattern, text):
            return True
    return False


def contains_math_symbols(image: Image.Image) -> bool:
    """
    Heuristic check if image likely contains mathematical formulas.

    Args:
        image: PIL Image to analyze.

    Returns:
        True if image likely contains math.
    """
    # Convert to grayscale for analysis
    gray = image.convert('L')

    # Quick OCR to check for math symbols
    if pytesseract is None:
        return False

    try:
        # Quick scan with basic config
        text = pytesseract.image_to_string(gray, config='--psm 6')
        return detect_math_content(text)
    except Exception:
        return False


def preprocess_for_latex(image: Image.Image) -> Image.Image:
    """
    Preprocess image for better LaTeX OCR results.

    Args:
        image: PIL Image to preprocess.

    Returns:
        Preprocessed image.
    """
    import numpy as np

    # Convert to grayscale
    if image.mode != 'L':
        gray = image.convert('L')
    else:
        gray = image

    # Convert to numpy for processing
    img_array = np.array(gray)

    # Binarization using Otsu's method
    from PIL import ImageOps
    threshold = ImageOps.autocontrast(gray).point(lambda x: 0 if x < 128 else 255, '1')

    return threshold.convert('L')


def extract_text(
    image_path: str,
    language: str = 'eng+chi_sim',
    tesseract_path: Optional[str] = None,
    latex_mode: bool = False,
    auto_detect_math: bool = True
) -> Tuple[str, Optional[str]]:
    """
    Extract text from an image using OCR with optional LaTeX conversion.

    Args:
        image_path: Path to the image file.
        language: Tesseract language code(s), e.g., 'eng', 'chi_sim', 'eng+chi_sim'.
        tesseract_path: Optional path to Tesseract executable.
        latex_mode: Force LaTeX conversion for the entire image.
        auto_detect_math: Automatically detect and convert math regions.

    Returns:
        Tuple of (extracted_text, latex_result) where latex_result may be None.
    """
    if pytesseract is None:
        raise ImportError("pytesseract is not installed. Install with: pip install pytesseract")

    # Setup bundled Tesseract first (if available)
    setup_tesseract()

    # Set Tesseract path if explicitly provided
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    # Load image
    image = Image.open(image_path)

    # Configure Tesseract for optimal text extraction
    # --oem 3: Use LSTM neural net engine
    # --psm 6: Assume single uniform block of text
    custom_config = r'--oem 3 --psm 6'

    # Check if requested language is available
    try:
        available_langs = pytesseract.get_languages()
        requested_langs = language.split('+')
        missing_langs = [lang for lang in requested_langs if lang not in available_langs]

        if missing_langs:
            print(f"Warning: Language data not found: {missing_langs}")
            print(f"Available languages: {available_langs}")
            # Fall back to available languages
            available_requested = [lang for lang in requested_langs if lang in available_langs]
            if available_requested:
                language = '+'.join(available_requested)
            else:
                language = 'eng' if 'eng' in available_langs else available_langs[0]
                print(f"Using fallback language: {language}")
    except Exception:
        pass  # Continue with requested language

    # Extract text
    try:
        text = pytesseract.image_to_string(
            image,
            lang=language,
            config=custom_config
        )
        text = text.strip()
    except Exception as e:
        print(f"Error during OCR: {e}")
        text = ""

    # LaTeX conversion using UniMERNet
    latex_result = None

    if latex_mode or (auto_detect_math and contains_math_symbols(image)):
        model = _get_latex_model()
        if model is not None:
            try:
                # Use UniMERNet to convert image to LaTeX
                latex_result = model.inference(image)
                if latex_result:
                    latex_result = latex_result.strip()
            except Exception as e:
                print(f"Warning: LaTeX conversion failed: {e}")

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
