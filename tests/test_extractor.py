import pytest
from unittest.mock import patch, MagicMock
import os
from extractor import extract_text_from_file

def test_extract_text_from_txt(tmp_path):
    # Create temporary txt file
    txt_file = tmp_path / "claim.txt"
    sample_content = "Policy: POL-100\nName: Alice Vance\nIncident: Collision on highway."
    txt_file.write_text(sample_content, encoding="utf-8")
    
    text, is_ocr = extract_text_from_file(str(txt_file))
    assert text == sample_content
    assert not is_ocr

@patch("pdfplumber.open")
def test_extract_text_from_pdf_standard(mock_open, tmp_path):
    # Mock pdfplumber open to return a mock pdf page with text
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = (
        "POLICY NUMBER: POL-999\n"
        "This is a standard PDF document with enough characters in the text layer "
        "to satisfy the minimum character count of 50 characters, meaning that "
        "standard extraction will succeed without triggering the OCR fallback."
    )
    mock_pdf.pages = [mock_page]
    mock_open.return_value.__enter__.return_value = mock_pdf
    
    # Create empty mock file
    pdf_file = tmp_path / "claim.pdf"
    pdf_file.touch()
    
    text, is_ocr = extract_text_from_file(str(pdf_file))
    assert "POLICY NUMBER: POL-999" in text
    assert not is_ocr
    mock_open.assert_called_once_with(str(pdf_file))

@patch("pdfplumber.open")
@patch("extractor.run_ocr_on_pdf")
def test_extract_text_from_pdf_fallback_to_ocr(mock_run_ocr, mock_open, tmp_path):
    # Mock pdfplumber open to return a page with empty text (scanned page)
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "   "  # whitespace only (triggers OCR)
    mock_pdf.pages = [mock_page]
    mock_open.return_value.__enter__.return_value = mock_pdf
    
    # Mock OCR execution
    mock_run_ocr.return_value = ("OCR TEXT: Policy POL-777", True)
    
    # Create empty mock file
    pdf_file = tmp_path / "scanned_claim.pdf"
    pdf_file.touch()
    
    text, is_ocr = extract_text_from_file(str(pdf_file))
    assert text == "OCR TEXT: Policy POL-777"
    assert is_ocr
    mock_run_ocr.assert_called_once_with(str(pdf_file), True)
    mock_open.assert_called_once_with(str(pdf_file))
