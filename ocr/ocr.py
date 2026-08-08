"""
OCR Module for Resume Template Builder.

Handles text extraction from PDF resumes:
- Digital PDFs (using PyMuPDF for direct text extraction)
- Scanned PDFs (using EasyOCR on rendered page images)

Only PDF files are supported since the app now focuses on resume uploads.
"""

import os
import fitz  # PyMuPDF
import easyocr
import numpy as np


# Initialize EasyOCR reader (lazy loading — created on first use)
_reader = None


def _get_reader():
    """
    Get or create the EasyOCR reader instance.
    Lazy initialization to avoid loading models until needed.
    Downloads models (~100MB) on first run.
    """
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader


def extract_text_from_pdf(filepath):
    """
    Extract text from a PDF file.

    Strategy:
    1. First try direct text extraction with PyMuPDF (fast, for digital PDFs).
    2. If very little text is found (likely a scanned PDF), fall back to
       rendering each page as an image and running EasyOCR.

    Args:
        filepath (str): Absolute path to the PDF file.

    Returns:
        str: Extracted text from all pages of the PDF.
    """
    doc = fitz.open(filepath)
    all_text = []

    # Step 1: Try direct text extraction (digital PDFs)
    for page in doc:
        text = page.get_text().strip()
        if text:
            all_text.append(text)

    # If we got meaningful text from the digital extraction, return it
    combined = '\n\n'.join(all_text)
    if len(combined.strip()) > 50:
        doc.close()
        return combined

    # Step 2: Fall back to OCR for scanned PDFs
    all_text = []
    reader = _get_reader()

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render page as image at 300 DPI for better OCR accuracy
        pix = page.get_pixmap(dpi=300)

        # Convert pixmap to numpy array for EasyOCR
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )

        # If RGBA, convert to RGB
        if pix.n == 4:
            img = img[:, :, :3]

        results = reader.readtext(img, detail=0, paragraph=True)
        page_text = '\n'.join(results)
        if page_text.strip():
            all_text.append(page_text)

    doc.close()
    return '\n\n'.join(all_text)


def extract_text(filepath):
    """
    Extract text from a PDF resume file.

    Args:
        filepath (str): Absolute path to the PDF file.

    Returns:
        dict: {
            'text': str (extracted text),
            'method': str ('pdf_digital' or 'pdf_ocr'),
            'success': bool,
            'error': str or None
        }
    """
    if not os.path.exists(filepath):
        return {
            'text': '',
            'method': 'none',
            'success': False,
            'error': 'File not found'
        }

    ext = filepath.rsplit('.', 1)[-1].lower()

    if ext != 'pdf':
        return {
            'text': '',
            'method': 'none',
            'success': False,
            'error': f'Unsupported file type: {ext}. Only PDF files are accepted.'
        }

    try:
        text = extract_text_from_pdf(filepath)
        # Determine if it was digital or OCR-based
        method = 'pdf_digital' if len(text) > 50 else 'pdf_ocr'
        return {
            'text': text,
            'method': method,
            'success': True,
            'error': None
        }
    except Exception as e:
        return {
            'text': '',
            'method': 'none',
            'success': False,
            'error': str(e)
        }
