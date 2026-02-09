"""Resume upload and parsing API endpoints."""
import os
from flask import Blueprint, request, jsonify, current_app
import logging

from app.services.resume_service import ResumeService


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
            return jsonify({
                'status': 'error',
                'message': 'No files provided. Please upload at least one PDF file using "files" or "file" field.'
            }), 400
        
        # Get uploaded files (supports both 'files' and 'file' field names)
        uploaded_files = request.files.getlist('files') or request.files.getlist('file')
        
        # Validate that files were actually selected
        if not uploaded_files or uploaded_files[0].filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No files selected for upload.'
            }), 400
        
        logger.info(f"Processing {len(uploaded_files)} uploaded file(s)")
        
        # Process resumes through the service layer
        resume_service = get_resume_service()
        result = resume_service.process_uploaded_resumes(uploaded_files)
        
        # Determine HTTP status code
        if result['successful'] > 0:
            status_code = 200
        elif result['failed'] > 0:
            status_code = 400
        else:
            status_code = 500
        
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred during file upload.',
            'error': str(e)
        }), 500


@resume_bp.route('/validate', methods=['POST'])
def validate_resumes():
    """
    Validate uploaded files without processing them.
    
    Useful for checking files before full processing.
    """
    try:
        if 'files' not in request.files and 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No files provided.'
            }), 400
        
        uploaded_files = request.files.getlist('files') or request.files.getlist('file')
        
        if not uploaded_files or uploaded_files[0].filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No files selected.'
            }), 400
        
        resume_service = get_resume_service()
        validation_result = resume_service.validate_files(uploaded_files)
        
        return jsonify({
            'status': 'success',
            **validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in validation endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


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
