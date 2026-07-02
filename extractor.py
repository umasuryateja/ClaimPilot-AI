import os
import pdfplumber
from PIL import Image
from typing import Tuple, Union
from io import BytesIO
from utils import logger

try:
    from pdf2image import convert_from_path, convert_from_bytes
    from pdf2image.exceptions import PDFInfoNotInstalledError
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

def extract_text_from_file(file_input: Union[str, any]) -> Tuple[str, bool]:
    """Extracts text from a TXT or PDF file.
    
    Accepts either a string file path or a Streamlit UploadedFile/BytesIO stream.
    If the file is a PDF and standard text extraction returns empty or near-empty text,
    it falls back to OCR via pdf2image and pytesseract.
    
    Args:
        file_input: The file path (str) or a file-like stream object.
        
    Returns:
        Tuple[str, bool]: A tuple containing (extracted_text, is_ocr_triggered).
        
    Raises:
        ValueError: If file type is unsupported or file is empty/invalid.
        RuntimeError: If OCR fallback was required but dependencies are missing or fail.
    """
    # 1. Determine filename and mode
    if isinstance(file_input, str):
        filename = file_input.lower()
        is_path = True
        if not os.path.exists(file_input):
            raise FileNotFoundError(f"File not found: {file_input}")
    else:
        filename = file_input.name.lower()
        is_path = False

    _, ext = os.path.splitext(filename)
    
    # 2. Extract TXT File
    if ext == ".txt":
        if is_path:
            logger.info(f"Extracting text from TXT file path: {file_input}")
            try:
                with open(file_input, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                if not content:
                    raise ValueError("The text file is empty.")
                return content, False
            except Exception as e:
                raise ValueError(f"Failed to read TXT file path: {str(e)}")
        else:
            logger.info(f"Extracting text from uploaded TXT stream: {filename}")
            try:
                file_input.seek(0)  # Always reset stream pointer
                raw_bytes = file_input.read()
                try:
                    content = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    content = raw_bytes.decode("utf-8", errors="ignore")
                
                content = content.strip()
                if not content:
                    raise ValueError("The text file stream is empty.")
                return content, False
            except Exception as e:
                raise ValueError(f"Failed to decode TXT file stream: {str(e)}")
            
    # 3. Extract PDF File
    elif ext == ".pdf":
        text_parts = []
        if is_path:
            logger.info(f"Attempting standard extraction from PDF file path: {file_input}")
            try:
                with pdfplumber.open(file_input) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
            except Exception as e:
                raise ValueError(f"Failed to read PDF file path with pdfplumber: {str(e)}")
        else:
            logger.info(f"Attempting standard extraction from uploaded PDF stream: {filename}")
            try:
                file_input.seek(0)  # Always reset stream pointer
                with pdfplumber.open(file_input) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
            except Exception as e:
                raise ValueError(f"Failed to read PDF stream with pdfplumber: {str(e)}")
            
        pdf_text = "\n".join(text_parts).strip()
        
        # If text is substantial, return it
        if len(pdf_text) >= 50:
            logger.info("Successfully extracted text using standard PDF parser.")
            return pdf_text, False
            
        # Fall back to OCR
        logger.warning("Standard PDF extraction returned empty or near-empty text. Triggering OCR fallback...")
        return run_ocr_on_pdf(file_input, is_path)
        
    else:
        raise ValueError(f"Unsupported file format: {ext}. Only PDF and TXT files are supported.")

def run_ocr_on_pdf(file_input: Union[str, any], is_path: bool) -> Tuple[str, bool]:
    """Runs OCR on a PDF by converting pages to images and calling pytesseract.
    
    Args:
        file_input: The file path (str) or a file-like stream object.
        is_path (bool): True if file_input is a path string, False if it is a stream.
        
    Returns:
        Tuple[str, bool]: A tuple containing (extracted_text, True).
        
    Raises:
        RuntimeError: If dependencies (poppler, tesseract) are missing or misconfigured.
    """
    if not PDF2IMAGE_AVAILABLE:
        raise RuntimeError(
            "OCR Fallback failed: 'pdf2image' package is not installed. "
            "Please install it using 'pip install pdf2image'."
        )
    if not PYTESSERACT_AVAILABLE:
        raise RuntimeError(
            "OCR Fallback failed: 'pytesseract' package is not installed. "
            "Please install it using 'pip install pytesseract'."
        )
        
    logger.info("Converting PDF pages to images for OCR processing...")
    try:
        if is_path:
            # Convert PDF path to images
            images = convert_from_path(file_input)
        else:
            # Convert PDF binary stream to images
            file_input.seek(0)
            pdf_bytes = file_input.read()
            images = convert_from_bytes(pdf_bytes)
    except PDFInfoNotInstalledError:
        logger.error("Poppler is not installed or not in PATH.")
        raise RuntimeError(
            "OCR Fallback failed: Poppler is not installed on the system, which is required by 'pdf2image' "
            "to process scanned PDFs. Please install Poppler and add its 'bin/' directory to your system PATH."
        )
    except Exception as e:
        logger.error(f"Error during pdf2image conversion: {str(e)}")
        raise RuntimeError(f"OCR Fallback failed during PDF-to-image conversion: {str(e)}")
        
    ocr_text = ""
    for i, img in enumerate(images):
        logger.info(f"Running OCR on page {i+1}/{len(images)}...")
        try:
            page_text = pytesseract.image_to_string(img)
            if page_text:
                ocr_text += page_text + "\n"
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract OCR binary not found.")
            raise RuntimeError(
                "OCR Fallback failed: Tesseract OCR is not installed or not in your system PATH. "
                "Please install Tesseract-OCR and configure your system variables, or set the pytesseract path in the app."
            )
        except Exception as e:
            logger.error(f"Error during pytesseract OCR: {str(e)}")
            raise RuntimeError(f"OCR Fallback failed during text recognition: {str(e)}")
            
    ocr_text = ocr_text.strip()
    if not ocr_text:
        raise RuntimeError("OCR processing completed, but no text could be recognized from the image-based PDF.")
        
    logger.info("OCR fallback completed successfully.")
    return ocr_text, True
