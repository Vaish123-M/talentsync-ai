"""Resume upload and parsing API endpoints."""
from flask import Blueprint, request, jsonify
from pypdf import PdfReader
import io
import traceback


resume_bp = Blueprint('resume', __name__, url_prefix='/api/resumes')


@resume_bp.route('/upload', methods=['POST'])
def upload_resumes():
    """
    Handle multiple PDF resume uploads and extract text.
    
    Expected: multipart/form-data with one or more files
    Returns: JSON with extracted text from each resume
    """
    try:
        # Check if files were included in the request
        if 'files' not in request.files and 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No files provided. Please upload at least one PDF file.'
            }), 400
        
        # Get uploaded files (supports both 'files' and 'file' field names)
        uploaded_files = request.files.getlist('files') or request.files.getlist('file')
        
        if not uploaded_files or uploaded_files[0].filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No files selected for upload.'
            }), 400
        
        results = []
        errors = []
        
        # Process each uploaded file
        for file in uploaded_files:
            try:
                # Validate file type
                if not file.filename.lower().endswith('.pdf'):
                    errors.append({
                        'filename': file.filename,
                        'error': 'Invalid file type. Only PDF files are accepted.'
                    })
                    continue
                
                # Read PDF content
                pdf_bytes = file.read()
                pdf_file = io.BytesIO(pdf_bytes)
                
                # Extract text from PDF
                pdf_reader = PdfReader(pdf_file)
                text_content = []
                
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                
                # Combine all pages
                full_text = '\n\n'.join(text_content)
                
                if not full_text.strip():
                    errors.append({
                        'filename': file.filename,
                        'error': 'No text could be extracted from the PDF.'
                    })
                    continue
                
                # Add successful result
                results.append({
                    'filename': file.filename,
                    'pages': len(pdf_reader.pages),
                    'text': full_text,
                    'status': 'success'
                })
                
            except Exception as e:
                errors.append({
                    'filename': file.filename,
                    'error': f'Failed to process file: {str(e)}'
                })
        
        # Prepare response
        response_data = {
            'status': 'success' if results else 'error',
            'message': f'Processed {len(results)} file(s) successfully.',
            'results': results,
            'total_uploaded': len(uploaded_files),
            'successful': len(results),
            'failed': len(errors)
        }
        
        if errors:
            response_data['errors'] = errors
        
        status_code = 200 if results else 400
        return jsonify(response_data), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred during file upload.',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@resume_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for resume service."""
    return jsonify({
        'status': 'healthy',
        'service': 'resume-parser',
        'version': '1.0.0'
    }), 200
