"""Resume upload and parsing API endpoints."""
import os
from flask import Blueprint, request, jsonify, current_app
import logging

from app.services.resume_service import ResumeService
from app.services.vector_search_service import get_vector_search_service
from app.utils.validators import build_error_response, validate_candidate_contract
from app.utils.resume_format_handler import ResumeFormatHandler


logger = logging.getLogger(__name__)
resume_bp = Blueprint('resume', __name__, url_prefix='/api/resumes')


def get_resume_service():
    """Get or create resume service instance."""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    return ResumeService(upload_folder)


def get_vector_service():
    """Get singleton vector search service from app configuration."""
    return get_vector_search_service(
        persist_directory=current_app.config.get('VECTOR_DB_PATH', 'vector_store'),
        collection_name=current_app.config.get('VECTOR_COLLECTION_NAME', 'candidates'),
        enabled=bool(current_app.config.get('VECTOR_SEARCH_ENABLED', True))
    )


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

        job_description = request.form.get('job_description', '').strip()
        use_semantic_raw = request.form.get('use_semantic', '').strip().lower()
        use_semantic = use_semantic_raw in {'1', 'true', 'yes', 'on'}
        recruiter_id = request.form.get('recruiter_id', 'default').strip() or 'default'
        
        # Process resumes through the service layer
        resume_service = get_resume_service()
        vector_service = get_vector_service()
        result = resume_service.process_uploaded_resumes(
            uploaded_files,
            job_description=job_description,
            use_semantic=use_semantic,
            recruiter_id=recruiter_id,
            vector_search_service=vector_service
        )
        
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
            'upload_folder': current_app.config.get('UPLOAD_FOLDER', 'uploads'),
            'vector_search_enabled': bool(current_app.config.get('VECTOR_SEARCH_ENABLED', True))
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@resume_bp.route('/parse-url', methods=['POST'])
def parse_profile_url():
    """
    Parse candidate profiles from LinkedIn, GitHub URLs or DOCX files.
    
    Accepts JSON payload with:
    - linkedin_url: LinkedIn profile URL (e.g., https://linkedin.com/in/username)
    - github_url: GitHub profile URL (e.g., https://github.com/username)
    
    Returns: Parsed candidate data (skills, experience, projects, etc.)
    """
    try:
        payload = request.get_json(silent=True) or {}
        linkedin_url = str(payload.get('linkedin_url', '')).strip()
        github_url = str(payload.get('github_url', '')).strip()
        job_description = str(payload.get('job_description', '')).strip()
        recruiter_id = str(payload.get('recruiter_id', 'default')).strip() or 'default'
        
        # Validate that at least one URL is provided
        if not linkedin_url and not github_url:
            return jsonify(build_error_response(
                'At least one of linkedin_url or github_url is required.'
            )), 400
        
        logger.info(
            "event=parse_url_request has_linkedin=%s has_github=%s",
            bool(linkedin_url),
            bool(github_url)
        )
        
        resume_service = get_resume_service()
        vector_service = get_vector_service()
        
        # Parse URLs using format handler
        extracted_data = {}
        
        if linkedin_url:
            linkedin_text = ResumeFormatHandler.extract_from_linkedin(linkedin_url)
            if linkedin_text:
                extracted_data['linkedin_profile'] = linkedin_text
                logger.info("event=linkedin_parsing_success")
            else:
                logger.warning("event=linkedin_parsing_failed url=%s", linkedin_url)
        
        if github_url:
            github_text = ResumeFormatHandler.extract_from_github(github_url)
            if github_text:
                extracted_data['github_profile'] = github_text
                logger.info("event=github_parsing_success")
            else:
                logger.warning("event=github_parsing_failed url=%s", github_url)
        
        if not extracted_data:
            return jsonify(build_error_response(
                'Failed to extract data from provided URLs. URLs may be invalid or inaccessible.'
            )), 422
        
        # Combine extracted data for processing
        combined_text = '\n'.join(extracted_data.values())
        
        # Process through resume service pipeline
        result = resume_service.process_raw_text(
            text=combined_text,
            job_description=job_description,
            recruiter_id=recruiter_id,
            vector_search_service=vector_service,
            source_type='urls'
        )
        
        if result.get('status') == 'success':
            candidate = result.get('candidate', {})
            is_valid, validation_error = validate_candidate_contract(candidate)
            if not is_valid:
                logger.error(
                    "event=parse_url_response_validation_failed error=%s",
                    validation_error
                )
                return jsonify(build_error_response('Internal response validation failed.')), 500
            
            return jsonify({
                'status': 'success',
                'candidate': candidate,
                'sources': list(extracted_data.keys())
            }), 200
        
        return jsonify(build_error_response(
            result.get('message', 'Failed to parse candidate profile')
        )), 422
        
    except Exception as e:
        logger.exception("event=parse_url_endpoint_error")
        return jsonify(build_error_response(
            'An error occurred while parsing the profile URL.'
        )), 500


@resume_bp.route('/semantic-search', methods=['POST'])
def semantic_search_candidates():
    """Semantic search for indexed candidates without reprocessing resumes."""
    if not current_app.config.get('VECTOR_SEARCH_ENABLED', True):
        return jsonify(build_error_response('Vector search is disabled by configuration.')), 503

    try:
        payload = request.get_json(silent=True) or {}
        job_description = str(payload.get('job_description', '')).strip()
        recruiter_id = str(payload.get('recruiter_id', 'default')).strip() or 'default'
        top_k = int(payload.get('top_k', 5) or 5)

        if not job_description:
            return jsonify(build_error_response('job_description is required.')), 400

        vector_service = get_vector_service()
        candidates = vector_service.semantic_search(
            job_description=job_description,
            recruiter_id=recruiter_id,
            top_k=top_k
        )

        return jsonify({
            'status': 'success',
            'candidates': candidates
        }), 200
    except Exception:
        logger.exception("event=semantic_search_endpoint_failed")
        return jsonify(build_error_response('Failed to perform semantic search.')), 500


@resume_bp.route('/multi-job-match', methods=['POST'])
def multi_job_match():
    """Match multiple job descriptions against indexed candidates."""
    if not current_app.config.get('VECTOR_SEARCH_ENABLED', True):
        return jsonify(build_error_response('Vector search is disabled by configuration.')), 503

    try:
        payload = request.get_json(silent=True) or {}
        recruiter_id = str(payload.get('recruiter_id', 'default')).strip() or 'default'
        jobs = payload.get('jobs', [])
        default_top_k = int(payload.get('top_k', 5) or 5)

        if not isinstance(jobs, list) or not jobs:
            return jsonify(build_error_response('jobs array is required.')), 400

        vector_service = get_vector_service()
        results = vector_service.multi_job_match(
            recruiter_id=recruiter_id,
            jobs=jobs,
            default_top_k=default_top_k
        )

        return jsonify({
            'status': 'success',
            'jobs': results
        }), 200
    except Exception:
        logger.exception("event=multi_job_match_endpoint_failed")
        return jsonify(build_error_response('Failed to perform multi-job matching.')), 500
