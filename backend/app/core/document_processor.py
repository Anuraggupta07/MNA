import fitz  # PyMuPDF
import pdfplumber
import io
import logging
from typing import Optional, Dict, Any
from google.cloud import vision
from PIL import Image
import os
from config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles PDF text extraction using multiple methods
    """
    
    def __init__(self):
        # Initialize Google Cloud Vision client if credentials are available
        self.vision_client = None
        if settings.GOOGLE_CLOUD_CREDENTIALS_PATH and os.path.exists(settings.GOOGLE_CLOUD_CREDENTIALS_PATH):
            try:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GOOGLE_CLOUD_CREDENTIALS_PATH
                self.vision_client = vision.ImageAnnotatorClient()
                logger.info("Google Cloud Vision client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Cloud Vision: {e}")
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF using multiple methods
        """
        try:
            # Method 1: Try pdfplumber first (best for text-based PDFs)
            text = self._extract_with_pdfplumber(pdf_path)
            
            # If pdfplumber didn't extract much text, try PyMuPDF
            if len(text.strip()) < 100:
                logger.info("pdfplumber extracted minimal text, trying PyMuPDF")
                text = self._extract_with_pymupdf(pdf_path)
            
            # If still minimal text and OCR is available, try OCR
            if len(text.strip()) < 100 and self.vision_client:
                logger.info("Minimal text extracted, attempting OCR")
                text = self._extract_with_ocr(pdf_path)
            
            # Clean up the extracted text
            text = self._clean_text(text)
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
        return text
    
    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF"""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
        return text
    
    def _extract_with_ocr(self, pdf_path: str) -> str:
        """Extract text using Google Cloud Vision OCR"""
        if not self.vision_client:
            logger.warning("Google Cloud Vision client not available")
            return ""
        
        text = ""
        try:
            # Convert PDF pages to images and run OCR
            doc = fitz.open(pdf_path)
            for page_num in range(min(5, len(doc))):  # Limit to first 5 pages for cost
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Run OCR on the image
                image = vision.Image(content=img_data)
                response = self.vision_client.text_detection(image=image)
                
                if response.text_annotations:
                    text += response.text_annotations[0].description + "\n"
                
                if response.error.message:
                    logger.error(f"OCR error: {response.error.message}")
            
            doc.close()
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
        
        return text
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                cleaned_lines.append(line)
        
        # Join lines with single newlines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove multiple consecutive newlines
        while '\n\n\n' in cleaned_text:
            cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
        
        return cleaned_text
    
    def get_document_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract document metadata"""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            doc.close()
            
            return {
                "page_count": len(doc),
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", "")
            }
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}