"""Resume upload and parsing API endpoints."""
import os
from flask import Blueprint, request, jsonify, current_app
import logging

from app.services.resume_service import ResumeService
from app.utils.validators import build_error_response, validate_candidate_contract


logger = logging.getLogger(__name__)
resume_bp = Blueprint('resume', __name__, url_prefix='/api/resumes')


def get_resume_service():
    """Get or create resume service instance."""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    return ResumeService(upload_folder)


@resume_bp.route('/upload', methods=['POST'])
def upload_resumes():
    """
    Handle multiple PDF resume uploads and process them through the complete pipeline.
    
    Pipeline stages:
    1. Validate and save PDF files
    2. Extract text from PDFs
    3. Parse resumes using AI (LangChain + OpenAI)
    4. Return structured candidate data
    
    Expected: multipart/form-data with 'files' or 'file' field containing PDF(s)
    Returns: JSON with parsed candidate data including name, skills, experience, etc.
    """
    try:
        # Check if files were included in the request
        if 'files' not in request.files and 'file' not in request.files:
            return jsonify(build_error_response(
                'No files provided. Please upload at least one PDF file using "files" or "file" field.'
            )), 400
        
        # Get uploaded files (supports both 'files' and 'file' field names)
        uploaded_files = request.files.getlist('files') or request.files.getlist('file')
        
        # Validate that files were actually selected
        if not uploaded_files or uploaded_files[0].filename == '':
            return jsonify(build_error_response('No files selected for upload.')), 400
        
        logger.info("event=upload_request_received file_count=%s", len(uploaded_files))
        
        # Process resumes through the service layer
        resume_service = get_resume_service()
        result = resume_service.process_uploaded_resumes(uploaded_files)
        
        if result.get('status') == 'success':
            for candidate in result.get('candidates', []):
                is_valid, validation_error = validate_candidate_contract(candidate)
                if not is_valid:
                    logger.error(
                        "event=upload_response_validation_failed error=%s",
                        validation_error
                    )
                    return jsonify(build_error_response('Internal response validation failed.')), 500

            return jsonify(result), 200

        message = result.get('message', 'Resume upload failed')
        lowered = message.lower()
        status_code = 400 if 'invalid file type' in lowered or 'no files' in lowered else 422

        return jsonify(build_error_response(message)), status_code
        
    except Exception as e:
        logger.exception("event=upload_endpoint_unexpected_error")
        return jsonify(build_error_response('An unexpected error occurred during file upload.')), 500


@resume_bp.route('/validate', methods=['POST'])
def validate_resumes():
    """
    Validate uploaded files without processing them.
    
    Useful for checking files before full processing.
    """
    try:
        if 'files' not in request.files and 'file' not in request.files:
            return jsonify(build_error_response('No files provided.')), 400
        
        uploaded_files = request.files.getlist('files') or request.files.getlist('file')
        
        if not uploaded_files or uploaded_files[0].filename == '':
            return jsonify(build_error_response('No files selected.')), 400
        
        resume_service = get_resume_service()
        validation_result = resume_service.validate_files(uploaded_files)
        
        return jsonify({
            'status': 'success',
            **validation_result
        }), 200
        
    except Exception as e:
        logger.exception("event=validation_endpoint_error")
        return jsonify(build_error_response('Failed to validate uploaded files.')), 500


@resume_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for resume service."""
    try:
        # Check if OpenAI API key is configured
        openai_configured = bool(os.getenv('OPENAI_API_KEY'))
        
        return jsonify({
            'status': 'healthy',
            'service': 'resume-parser',
            'version': '1.0.0',
            'ai_configured': openai_configured,
            'upload_folder': current_app.config.get('UPLOAD_FOLDER', 'uploads')
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
