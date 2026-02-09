"""PDF text extraction utility for resume processing."""
import io
import logging
from typing import Optional, Dict
from pypdf import PdfReader


logger = logging.getLogger(__name__)


class PDFExtractor:
    """Handles PDF text extraction with error handling."""
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> Dict[str, any]:
        """
        Extract text from a PDF file path.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text, page count, and status
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                return PDFExtractor._extract_from_reader(pdf_reader, file_path)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return {
                'success': False,
                'error': 'File not found',
                'text': '',
                'pages': 0
            }
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'pages': 0
            }
    
    @staticmethod
    def extract_text_from_bytes(pdf_bytes: bytes, filename: str = 'unknown') -> Dict[str, any]:
        """
        Extract text from PDF bytes.
        
        Args:
            pdf_bytes: PDF file content as bytes
            filename: Original filename for logging
            
        Returns:
            Dictionary containing extracted text, page count, and status
        """
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PdfReader(pdf_file)
            return PDFExtractor._extract_from_reader(pdf_reader, filename)
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'pages': 0
            }
    
    @staticmethod
    def _extract_from_reader(pdf_reader: PdfReader, source: str) -> Dict[str, any]:
        """
        Internal method to extract text from PdfReader object.
        
        Args:
            pdf_reader: PdfReader instance
            source: Source identifier for logging
            
        Returns:
            Dictionary containing extraction results
        """
        try:
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                logger.warning(f"PDF is encrypted: {source}")
                return {
                    'success': False,
                    'error': 'PDF is encrypted and cannot be processed',
                    'text': '',
                    'pages': 0
                }
            
            # Extract text from all pages
            text_content = []
            page_count = len(pdf_reader.pages)
            
            if page_count == 0:
                return {
                    'success': False,
                    'error': 'PDF has no pages',
                    'text': '',
                    'pages': 0
                }
            
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        # Clean up the text
                        cleaned_text = PDFExtractor._clean_text(page_text)
                        if cleaned_text:
                            text_content.append(cleaned_text)
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num} from {source}: {str(e)}")
                    continue
            
            # Combine all pages
            full_text = '\n\n'.join(text_content)
            
            if not full_text.strip():
                return {
                    'success': False,
                    'error': 'No text could be extracted from PDF',
                    'text': '',
                    'pages': page_count
                }
            
            return {
                'success': True,
                'text': full_text,
                'pages': page_count,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF reader for {source}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'pages': 0
            }
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean extracted text by removing excessive whitespace and special characters.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        # Remove empty lines
        lines = [line for line in lines if line]
        # Join with single newline
        cleaned = '\n'.join(lines)
        return cleaned
    
    @staticmethod
    def validate_pdf(file_bytes: bytes) -> bool:
        """
        Validate if bytes represent a valid PDF file.
        
        Args:
            file_bytes: File content as bytes
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            # Check PDF header
            if not file_bytes.startswith(b'%PDF'):
                return False
            
            # Try to read it
            pdf_file = io.BytesIO(file_bytes)
            pdf_reader = PdfReader(pdf_file)
            
            # Check if it has at least one page
            return len(pdf_reader.pages) > 0
        except Exception:
            return False
