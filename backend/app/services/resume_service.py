"""Resume processing service orchestrating the full pipeline."""
import os
import logging
from typing import Dict, List, Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from app.utils.pdf_extractor import PDFExtractor
from app.ai.resume_parser import get_parser


logger = logging.getLogger(__name__)


class ResumeService:
    """Service for processing resume uploads through the complete pipeline."""
    
    def __init__(self, upload_folder: str):
        """
        Initialize resume service.
        
        Args:
            upload_folder: Directory path for storing uploaded files
        """
        self.upload_folder = upload_folder
        self.pdf_extractor = PDFExtractor()
        self.resume_parser = get_parser()
        
        # Ensure upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
    
    def process_uploaded_resumes(self, files: List[FileStorage]) -> Dict[str, any]:
        """
        Process multiple uploaded resume files through the complete pipeline.
        
        Args:
            files: List of uploaded file objects
            
        Returns:
            Dictionary containing processed results and errors
        """
        results = []
        errors = []
        
        for file in files:
            try:
                result = self._process_single_resume(file)
                
                if result['success']:
                    results.append(result)
                else:
                    errors.append({
                        'filename': file.filename,
                        'error': result.get('error', 'Unknown error')
                    })
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {str(e)}")
                errors.append({
                    'filename': file.filename,
                    'error': str(e)
                })
        
        return {
            'status': 'success' if results else 'error',
            'message': f'Successfully processed {len(results)} out of {len(files)} file(s)',
            'results': results,
            'total_uploaded': len(files),
            'successful': len(results),
            'failed': len(errors),
            'errors': errors if errors else None
        }
    
    def _process_single_resume(self, file: FileStorage) -> Dict[str, any]:
        """
        Process a single resume file through the pipeline.
        
        Steps:
        1. Validate file type
        2. Save file to uploads directory
        3. Extract text from PDF
        4. Parse text using AI
        5. Return structured data
        
        Args:
            file: Uploaded file object
            
        Returns:
            Dictionary containing processing result
        """
        filename = file.filename
        
        # Step 1: Validate file type
        if not self._is_allowed_file(filename):
            return {
                'success': False,
                'filename': filename,
                'error': 'Invalid file type. Only PDF files are accepted.'
            }
        
        # Step 2: Save file
        try:
            saved_path = self._save_file(file)
        except Exception as e:
            logger.error(f"Error saving file {filename}: {str(e)}")
            return {
                'success': False,
                'filename': filename,
                'error': f'Failed to save file: {str(e)}'
            }
        
        # Step 3: Extract text from PDF
        try:
            extraction_result = self.pdf_extractor.extract_text_from_file(saved_path)
            
            if not extraction_result['success']:
                return {
                    'success': False,
                    'filename': filename,
                    'saved_path': saved_path,
                    'error': f"Text extraction failed: {extraction_result['error']}"
                }
            
            extracted_text = extraction_result['text']
            page_count = extraction_result['pages']
            
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            return {
                'success': False,
                'filename': filename,
                'saved_path': saved_path,
                'error': f'Text extraction error: {str(e)}'
            }
        
        # Step 4: Parse resume using AI
        try:
            parse_result = self.resume_parser.parse_resume(extracted_text)
            
            if not parse_result['success']:
                return {
                    'success': False,
                    'filename': filename,
                    'saved_path': saved_path,
                    'extracted_text': extracted_text[:500] + '...',  # Include snippet
                    'error': f"Resume parsing failed: {parse_result['error']}"
                }
            
            candidate_data = parse_result['data']
            
        except Exception as e:
            logger.error(f"Error parsing resume {filename}: {str(e)}")
            return {
                'success': False,
                'filename': filename,
                'saved_path': saved_path,
                'extracted_text': extracted_text[:500] + '...',
                'error': f'Resume parsing error: {str(e)}'
            }
        
        # Step 5: Return complete result
        return {
            'success': True,
            'filename': filename,
            'saved_path': saved_path,
            'pages': page_count,
            'candidate_data': candidate_data,
            'text_length': len(extracted_text)
        }
    
    def _save_file(self, file: FileStorage) -> str:
        """
        Save uploaded file to the uploads directory.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Path where file was saved
        """
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Handle duplicate filenames
        base_name, extension = os.path.splitext(filename)
        counter = 1
        save_path = os.path.join(self.upload_folder, filename)
        
        while os.path.exists(save_path):
            filename = f"{base_name}_{counter}{extension}"
            save_path = os.path.join(self.upload_folder, filename)
            counter += 1
        
        # Save the file
        file.save(save_path)
        logger.info(f"File saved: {save_path}")
        
        return save_path
    
    def _is_allowed_file(self, filename: str) -> bool:
        """
        Check if filename has an allowed extension.
        
        Args:
            filename: Name of the file
            
        Returns:
            True if allowed, False otherwise
        """
        if not filename:
            return False
        
        return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'
    
    def get_upload_folder(self) -> str:
        """Get the upload folder path."""
        return self.upload_folder
    
    def validate_files(self, files: List[FileStorage]) -> Dict[str, any]:
        """
        Validate uploaded files without processing them.
        
        Args:
            files: List of uploaded file objects
            
        Returns:
            Validation results
        """
        valid_files = []
        invalid_files = []
        
        for file in files:
            if not file or not file.filename:
                continue
            
            if self._is_allowed_file(file.filename):
                valid_files.append(file.filename)
            else:
                invalid_files.append({
                    'filename': file.filename,
                    'reason': 'Invalid file type. Only PDF files are accepted.'
                })
        
        return {
            'valid_count': len(valid_files),
            'invalid_count': len(invalid_files),
            'valid_files': valid_files,
            'invalid_files': invalid_files
        }
