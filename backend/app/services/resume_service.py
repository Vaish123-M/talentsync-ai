"""Resume processing service orchestrating the full pipeline."""
import os
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List
from pathlib import Path
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from app.utils.pdf_extractor import PDFExtractor
from app.services.job_matcher import calculate_match_scores


logger = logging.getLogger(__name__)


def get_resume_parser():
    """Lazily import and return parser instance to avoid hard AI dependency at import time."""
    from app.ai.resume_parser import get_parser
    return get_parser()


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
        self.resume_parser = None
        self.vector_search_service = None
        
        # Ensure upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
    
    def process_uploaded_resumes(
        self,
        files: List[FileStorage],
        job_description: str = '',
        use_semantic: bool = False,
        recruiter_id: str = 'default',
        vector_search_service: Any = None
    ) -> Dict[str, Any]:
        """
        Process multiple uploaded resume files through the complete pipeline.
        
        Args:
            files: List of uploaded file objects
            
        Returns:
            Dictionary containing processed results and errors
        """
        candidates = []
        errors = []
        self.vector_search_service = vector_search_service

        logger.info("event=resume_upload_started total_files=%s", len(files))
        
        worker_count = int(os.getenv('RESUME_PARSE_WORKERS', '1') or 1)
        if worker_count > 1 and len(files) > 1:
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                future_map = {executor.submit(self._process_single_resume, file): file for file in files}
                for future in as_completed(future_map):
                    file = future_map[future]
                    try:
                        result = future.result()
                        if result['success']:
                            candidates.append(result['candidate'])
                        else:
                            errors.append({
                                'filename': file.filename,
                                'message': result.get('error', 'Unknown error')
                            })
                    except Exception as e:
                        logger.exception("event=resume_processing_failed filename=%s", file.filename)
                        errors.append({
                            'filename': file.filename,
                            'message': str(e)
                        })
        else:
            for file in files:
                try:
                    result = self._process_single_resume(file)
                    
                    if result['success']:
                        candidates.append(result['candidate'])
                    else:
                        errors.append({
                            'filename': file.filename,
                            'message': result.get('error', 'Unknown error')
                        })
                except Exception as e:
                    logger.exception("event=resume_processing_failed filename=%s", file.filename)
                    errors.append({
                        'filename': file.filename,
                        'message': str(e)
                    })

        if candidates:
            if self.vector_search_service is not None:
                try:
                    indexed_count = self.vector_search_service.index_candidates(
                        candidates,
                        recruiter_id=recruiter_id or 'default'
                    )
                    logger.info("event=resume_vector_indexing_completed indexed_count=%s", indexed_count)
                except Exception:
                    logger.exception("event=resume_vector_indexing_failed")

            if job_description and job_description.strip():
                logger.info(
                    "event=resume_matching_started candidate_count=%s use_semantic=%s",
                    len(candidates),
                    use_semantic
                )
                ranked_candidates = calculate_match_scores(
                    job_description,
                    candidates,
                    use_semantic=use_semantic
                )
                candidates = ranked_candidates

            logger.info(
                "event=resume_upload_completed processed=%s failed=%s",
                len(candidates),
                len(errors)
            )
            response: Dict[str, Any] = {
                'status': 'success',
                'candidates': candidates
            }

            if errors:
                response['message'] = f"Processed {len(candidates)} file(s), {len(errors)} failed"

            return response

        error_message = errors[0]['message'] if errors else 'No files were processed'
        logger.error("event=resume_upload_no_successes total_files=%s", len(files))
        return {
            'status': 'error',
            'message': error_message,
            'candidates': []
        }
    
    def _process_single_resume(self, file: FileStorage) -> Dict[str, Any]:
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
        logger.debug("event=resume_file_received filename=%s", filename)
        
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
            logger.exception("event=resume_file_save_failed filename=%s", filename)
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
            logger.debug(
                "event=resume_text_extracted filename=%s pages=%s text_length=%s",
                filename,
                page_count,
                len(extracted_text)
            )
            
        except Exception as e:
            logger.exception("event=resume_text_extraction_failed filename=%s", filename)
            return {
                'success': False,
                'filename': filename,
                'saved_path': saved_path,
                'error': f'Text extraction error: {str(e)}'
            }
        
        # Step 4: Parse resume using AI
        try:
            if self.resume_parser is None:
                self.resume_parser = get_resume_parser()

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
            candidate = self._to_candidate_payload(filename, candidate_data)
            
        except Exception as e:
            logger.exception("event=resume_parsing_failed filename=%s", filename)
            return {
                'success': False,
                'filename': filename,
                'saved_path': saved_path,
                'error': f'Resume parsing error: {str(e)}'
            }
        
        # Step 5: Return complete result
        return {
            'success': True,
            'candidate': candidate
        }

    def _to_candidate_payload(self, filename: str, parser_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform parser output into standardized business candidate contract."""
        fallback_name = Path(filename).stem.replace('_', ' ').strip().title() if filename else 'Unknown Candidate'

        raw_name = parser_data.get('name') if isinstance(parser_data, dict) else None
        name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else fallback_name

        raw_summary = parser_data.get('professional_summary') if isinstance(parser_data, dict) else None
        summary = raw_summary.strip() if isinstance(raw_summary, str) else ''

        raw_experience = parser_data.get('experience_years', 0) if isinstance(parser_data, dict) else 0
        experience_years = self._safe_number(raw_experience)

        raw_skills = parser_data.get('skills', []) if isinstance(parser_data, dict) else []
        skills = self._normalize_skills(raw_skills)

        return {
            'id': str(uuid.uuid4()),
            'name': name,
            'summary': summary,
            'experience_years': experience_years,
            'skills': skills,
            'match_score': None
        }

    @staticmethod
    def _safe_number(value: Any) -> float:
        """Convert numeric-like value to non-negative number."""
        try:
            parsed = float(value)
            return max(0.0, parsed)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _normalize_skills(skills: Any) -> List[str]:
        """Normalize skills into de-duplicated list of strings."""
        if isinstance(skills, str):
            raw_skills = [segment.strip() for segment in skills.split(',')]
        elif isinstance(skills, list):
            raw_skills = [str(skill).strip() for skill in skills]
        else:
            raw_skills = []

        normalized = []
        seen = set()

        for skill in raw_skills:
            if not skill:
                continue
            lowered = skill.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            normalized.append(skill)

        return normalized
    
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
