# TalentSync AI - Phase 1: Resume Ingestion & Parsing Pipeline

## Overview

Phase 1 implements a complete resume processing pipeline that:
- Accepts multiple PDF resume uploads
- Extracts text from PDFs using PyPDF
- Parses resumes using AI (LangChain + OpenAI)
- Returns structured candidate data

## Architecture

```
┌─────────────────┐
│   Flask API     │
│   (Routes)      │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Service Layer  │
│ (Resume Service)│
└────────┬────────┘
         │
         ├─────────────────┐
         v                 v
┌──────────────┐   ┌───────────────┐
│ PDF Extractor│   │ Resume Parser │
│  (PyPDF)     │   │ (LangChain)   │
└──────────────┘   └───────────────┘
```

## Project Structure

```
backend/
├── app/
│   ├── ai/
│   │   └── resume_parser.py      # LangChain-based AI parser
│   ├── routes/
│   │   └── resume.py              # API endpoints
│   ├── services/
│   │   └── resume_service.py     # Business logic layer
│   ├── utils/
│   │   └── pdf_extractor.py      # PDF text extraction
│   └── main.py                    # App factory
├── uploads/                       # Uploaded PDF storage
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
└── app.py                         # Application entry point
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- OpenAI API key (get from https://platform.openai.com)

### 2. Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 4. Run the Application

```bash
# Start the Flask development server
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### 1. Upload and Parse Resumes

**POST** `/api/resumes/upload`

Upload multiple PDF resumes and get structured candidate data.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Field: `files` (multiple PDFs) or `file` (single PDF)

**Example using cURL:**
```bash
curl -X POST http://localhost:5000/api/resumes/upload \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.pdf"
```

**Example using Python:**
```python
import requests

url = "http://localhost:5000/api/resumes/upload"
files = [
    ('files', open('resume1.pdf', 'rb')),
    ('files', open('resume2.pdf', 'rb'))
]
response = requests.post(url, files=files)
print(response.json())
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully processed 2 out of 2 file(s)",
  "total_uploaded": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "success": true,
      "filename": "resume1.pdf",
      "saved_path": "uploads/resume1.pdf",
      "pages": 2,
      "text_length": 1234,
      "candidate_data": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0100",
        "skills": ["Python", "Flask", "LangChain", "Machine Learning"],
        "experience_years": 5,
        "education": "Bachelor's in Computer Science from MIT",
        "professional_summary": "Experienced software engineer with 5 years in AI/ML development...",
        "current_role": "Senior Software Engineer",
        "location": "San Francisco, CA"
      }
    }
  ],
  "errors": null
}
```

### 2. Validate Files

**POST** `/api/resumes/validate`

Validate uploaded files without processing them.

**Request:**
```bash
curl -X POST http://localhost:5000/api/resumes/validate \
  -F "files=@resume.pdf"
```

**Response:**
```json
{
  "status": "success",
  "valid_count": 1,
  "invalid_count": 0,
  "valid_files": ["resume.pdf"],
  "invalid_files": []
}
```

### 3. Health Check

**GET** `/api/resumes/health`

Check service health and configuration status.

**Request:**
```bash
curl http://localhost:5000/api/resumes/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "resume-parser",
  "version": "1.0.0",
  "ai_configured": true,
  "upload_folder": "uploads"
}
```

### 4. Root Health Check

**GET** `/`

Check if the API is running.

**Request:**
```bash
curl http://localhost:5000/
```

**Response:**
```json
{
  "status": "success",
  "message": "TalentSync AI Hiring Assistant API is running",
  "version": "1.0.0",
  "environment": "development"
}
```

## Structured Output Format

The AI parser extracts the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Full name of the candidate |
| `email` | string | Email address |
| `phone` | string | Phone number |
| `skills` | array | List of technical and professional skills |
| `experience_years` | integer | Total years of professional experience |
| `education` | string | Highest education degree and institution |
| `professional_summary` | string | Brief 2-3 sentence career summary |
| `current_role` | string | Most recent job title |
| `location` | string | Current location/city |

## Error Handling

The API handles various error scenarios:

1. **Invalid file type**: Only PDF files are accepted
2. **Corrupted PDFs**: Gracefully handles unreadable PDFs
3. **Empty PDFs**: Detects and reports PDFs with no extractable text
4. **Missing API key**: Returns clear error if OpenAI key not configured
5. **Parsing failures**: Falls back to alternative parsing methods

## Testing

### Test with Sample Resume

```bash
# Create a test script
cat > test_upload.py << 'EOF'
import requests

url = "http://localhost:5000/api/resumes/upload"
files = {'files': open('sample_resume.pdf', 'rb')}
response = requests.post(url, files=files)

print("Status Code:", response.status_code)
print("Response:", response.json())
EOF

# Run the test
python test_upload.py
```

## Troubleshooting

### Issue: "OpenAI API key not configured"
**Solution**: Ensure `.env` file exists and contains valid `OPENAI_API_KEY`

### Issue: "No text could be extracted from PDF"
**Solution**: PDF may be image-based or corrupted. Try with a text-based PDF.

### Issue: "File not found" errors
**Solution**: Ensure `uploads/` directory exists and has write permissions.

### Issue: Import errors
**Solution**: Ensure all dependencies are installed: `pip install -r requirements.txt`

## Limitations (Phase 1)

- No database persistence (Phase 2)
- No vector DB for semantic search (Phase 2)
- No authentication/authorization (Future)
- Single AI provider (OpenAI only)
- No batch processing optimization

## Next Steps (Phase 2)

- Implement ChromaDB for vector storage
- Add job matching functionality
- Create candidate database models
- Implement semantic search
- Add AI assistant chatbot

## Dependencies

Key libraries used:
- **Flask**: Web framework
- **LangChain**: AI orchestration
- **OpenAI**: Language model
- **PyPDF**: PDF text extraction
- **python-dotenv**: Environment management

## License

See main project LICENSE file.

## Support

For issues or questions, please create an issue in the GitHub repository.
