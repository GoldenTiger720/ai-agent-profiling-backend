import os
import tempfile
import fitz  # PyMuPDF
import pdfplumber
import PyPDF2
import pytesseract
from PIL import Image
import logging
from typing import List, Optional, Tuple
import io
from app.config import settings
from app.utils.text_cleaning import clean_text, process_text_for_ai

logger = logging.getLogger(__name__)

# Set Tesseract command if specified in settings
if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

def extract_text_with_pymupdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF using PyMuPDF.
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        Extracted text as string
    """
    text = ""
    try:
        # Open PDF from memory
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            # Iterate through pages
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Extract text from page
                page_text = page.get_text()
                text += page_text + "\n\n"
    except Exception as e:
        logger.error(f"Error extracting text with PyMuPDF: {str(e)}")
    
    return text

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF, trying multiple methods and using OCR if necessary.
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        Extracted text as string
    """
    # First, try the fastest methods to extract text
    text = extract_text_with_pymupdf(pdf_bytes)
    
    # If PyMuPDF didn't extract much text, try pdfplumber
    if not text or len(text.strip()) < 100:
        text = extract_text_with_pdfplumber(pdf_bytes)
    
    # If pdfplumber didn't work well, try PyPDF2
    if not text or len(text.strip()) < 100:
        text = extract_text_with_pypdf2(pdf_bytes)
    
    # If we still don't have much text, it's likely a scanned PDF
    if not text or len(text.strip()) < 100:
        # Check if it's scanned
        if is_scanned_pdf(pdf_bytes):
            # Perform OCR
            text = perform_ocr_on_pdf(pdf_bytes)
    
    return text

def process_pdf_for_profile(pdf_bytes: bytes) -> List[str]:
    """
    Process a PDF file to extract text chunks suitable for AI processing.
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        List of processed text chunks
    """
    # Extract text from PDF
    raw_text = extract_text_from_pdf(pdf_bytes)
    
    # Process text for AI
    processed_chunks = process_text_for_ai(raw_text)
    
    return processed_chunks

def extract_text_with_pdfplumber(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF using pdfplumber.
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        Extracted text as string
    """
    text = ""
    try:
        # Create a file-like object from bytes
        pdf_io = io.BytesIO(pdf_bytes)
        
        # Extract text with pdfplumber
        with pdfplumber.open(pdf_io) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n\n"
    except Exception as e:
        logger.error(f"Error extracting text with pdfplumber: {str(e)}")
    
    return text

def extract_text_with_pypdf2(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF using PyPDF2.
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        Extracted text as string
    """
    text = ""
    try:
        # Create a file-like object from bytes
        pdf_io = io.BytesIO(pdf_bytes)
        
        # Extract text with PyPDF2
        reader = PyPDF2.PdfReader(pdf_io)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n\n"
    except Exception as e:
        logger.error(f"Error extracting text with PyPDF2: {str(e)}")
    
    return text

def perform_ocr_on_pdf(pdf_bytes: bytes) -> str:
    """
    Perform OCR on a scanned PDF to extract text.
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        Extracted text as string
    """
    text = ""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_bytes)
            temp_file_path = temp_file.name
        
        # Open PDF with PyMuPDF
        doc = fitz.open(temp_file_path)
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get page as an image
            pix = page.get_pixmap(alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Perform OCR
            page_text = pytesseract.image_to_string(img)
            text += page_text + "\n\n"
        
        doc.close()
    except Exception as e:
        logger.error(f"Error performing OCR: {str(e)}")
    finally:
        # Clean up temporary file
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
    
    return text

def is_scanned_pdf(pdf_bytes: bytes) -> bool:
    """
    Check if a PDF is scanned (image-based) or contains extractable text.
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        True if PDF is scanned (needs OCR), False if text can be extracted directly
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_bytes)
            temp_file_path = temp_file.name
        
        # Try to extract text using PyPDF2
        with open(temp_file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text and len(page_text.strip()) > 100:  # If substantial text is found
                    text += page_text
            
            # If we found substantial text, it's not a scanned PDF
            if text and len(text.strip()) > 100:
                return False
            
        # If PyPDF2 didn't find text, check with PyMuPDF as a backup
        doc = fitz.open(temp_file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text and len(text.strip()) > 100:
                doc.close()
                return False
        doc.close()
        
        # If we got here, the PDF is likely scanned and needs OCR
        return True
    except Exception as e:
        logger.error(f"Error checking if PDF is scanned: {str(e)}")
        # If we can't determine, assume it might need OCR
        return True
    finally:
        # Clean up temporary file
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)