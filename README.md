# TalentSync AI

An AI-powered hiring assistant that streamlines the recruitment process using advanced artificial intelligence, natural language processing, and intelligent candidate matching.

## 🚀 Features

- **AI-Powered Resume Parsing**: Automatically extract and structure information from resumes
- **Intelligent Job Matching**: Match candidates to jobs using vector similarity search
- **Smart Candidate Screening**: AI-driven candidate evaluation and ranking
- **Interactive AI Assistant**: LangChain-powered chatbot for recruitment queries
- **Vector Database Integration**: Efficient semantic search using embeddings

## 📁 Project Structure

```
talentsync-ai/
├── backend/                    # Python Flask Backend
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   │   ├── users.py
│   │   │   ├── jobs.py
│   │   │   ├── candidates.py
│   │   │   └── ai_assistant.py
│   │   ├── models/            # Database models
│   │   │   ├── user.py
│   │   │   ├── job.py
│   │   │   └── candidate.py
│   │   ├── services/          # Business logic
│   │   │   ├── user_service.py
│   │   │   ├── job_service.py
│   │   │   └── candidate_service.py
│   │   ├── ai/                # AI & LangChain integration
│   │   │   ├── langchain_service.py
│   │   │   ├── resume_parser.py
│   │   │   └── job_matcher.py
│   │   ├── vector_db/         # Vector database operations
│   │   │   ├── client.py
│   │   │   └── embeddings.py
│   │   ├── utils/             # Utility functions
│   │   │   ├── helpers.py
│   │   │   └── validators.py
│   │   └── config/            # Configuration
│   │       ├── development.py
│   │       └── production.py
│   ├── tests/                 # Backend tests
│   ├── migrations/            # Database migrations
│   ├── app.py                 # Application entry point
│   ├── config.py              # Main configuration
│   └── requirements.txt       # Python dependencies
│
├── frontend/                  # React Frontend
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── Header.js
│   │   │   ├── Footer.js
│   │   │   ├── JobCard.js
│   │   │   ├── CandidateCard.js
│   │   │   └── AIChat.js
│   │   ├── pages/             # Page components
│   │   │   ├── Home.js
│   │   │   ├── Dashboard.js
│   │   │   ├── Jobs.js
│   │   │   └── Candidates.js
│   │   ├── services/          # API service layer
│   │   │   ├── api.js
│   │   │   ├── aiService.js
│   │   │   └── authService.js
│   │   ├── hooks/             # Custom React hooks
│   │   │   ├── useAuth.js
│   │   │   └── useFetch.js
│   │   ├── utils/             # Utility functions
│   │   │   ├── helpers.js
│   │   │   └── constants.js
│   │   ├── contexts/          # React contexts
│   │   │   ├── AuthContext.js
│   │   │   └── AppContext.js
│   │   ├── assets/            # Images, fonts, etc.
│   │   ├── App.js             # Main App component
│   │   ├── App.css
│   │   ├── index.js           # React entry point
│   │   └── index.css
│   └── package.json           # Node.js dependencies
│
├── .gitignore
└── README.md
```

## 🛠️ Tech Stack

### Backend
- **Framework**: Flask (Python)
- **AI/ML**: LangChain, OpenAI API
- **Vector Database**: Pinecone/Chroma/FAISS
- **Database**: PostgreSQL/SQLite
- **Authentication**: JWT

### Frontend
- **Framework**: React
- **State Management**: Context API / Redux
- **Styling**: CSS / Tailwind CSS
- **HTTP Client**: Axios
- **Routing**: React Router

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 🔧 Configuration

Create a `.env` file in the backend directory:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
OPENAI_API_KEY=your-openai-api-key
VECTOR_DB_URL=your-vector-db-url
```

## 🚦 Usage

1. Start the backend server (runs on http://localhost:5000)
2. Start the frontend development server (runs on http://localhost:3000)
3. Access the application in your browser

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- TalentSync AI Team

## 🙏 Acknowledgments

- LangChain for AI capabilities
- OpenAI for language models
- The open-source community