# TalentSync AI - Frontend

A production-ready React dashboard for an AI-powered hiring assistant.

## Features

### 🎯 Core Functionality
- **Dashboard**: Overview with stats and quick actions
- **Resume Upload**: Drag-and-drop multi-file upload with progress tracking
- **Candidate Search**: AI-powered semantic search with natural language queries
- **Email Automation**: Automated candidate outreach with customizable templates

### 🎨 UI/UX
- Clean, modern design with TailwindCSS
- Responsive layout for all screen sizes
- Smooth animations and transitions
- Toast notifications for user feedback
- Loading states and progress indicators

### 🏗️ Architecture
```
src/
├── components/          # Reusable UI components
│   ├── Header.js
│   ├── Sidebar.js
│   ├── Footer.js
│   ├── FileUploader.js
│   ├── CandidateCard.js
│   ├── LoadingSpinner.js
│   ├── ProgressBar.js
│   └── NotificationToast.js
├── pages/              # Main application pages
│   ├── Dashboard.js
│   ├── UploadResumes.js
│   ├── CandidateSearch.js
│   └── Automation.js
├── services/           # API communication layer
│   ├── api.js
│   └── resumeService.js
├── hooks/              # Custom React hooks
│   └── useResumeUpload.js
├── App.js              # Main application with routing
└── index.js            # Application entry point
```

## Tech Stack

- **React 18.2** - UI framework
- **React Router 6** - Navigation
- **Axios** - HTTP client
- **TailwindCSS 3** - Styling
- **Functional Components** - Modern React patterns

## Getting Started

### Prerequisites
- Node.js 14+ and npm
- Backend API running on `http://localhost:5000`

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API URL
```

3. Start development server:
```bash
npm start
```

The application will open at `http://localhost:3000`

## Available Scripts

- `npm start` - Start development server
- `npm build` - Create production build
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

## API Integration

### Backend Endpoints

#### Upload Resumes
```
POST /api/upload-resumes
Content-Type: multipart/form-data
Body: FormData with 'files' key containing PDF files

Response:
{
  "candidates": [
    {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "123-456-7890",
      "skills": ["React", "Node.js"],
      "experience": "5 years",
      "education": "BS Computer Science",
      "summary": "Experienced developer..."
    }
  ]
}
```

#### Search Candidates (Placeholder)
```
POST /api/search-candidates
Content-Type: application/json
Body: { "query": "React developers with 2+ years" }
```

## Components

### FileUploader
Drag-and-drop file upload component with visual feedback.

```jsx
<FileUploader 
  onFilesSelected={handleFiles}
  accept=".pdf"
  multiple={true}
/>
```

### CandidateCard
Display candidate information in a card layout.

```jsx
<CandidateCard candidate={candidateData} />
```

### NotificationToast
Show success/error notifications.

```jsx
<NotificationToast
  type="success"
  message="Upload successful!"
  onClose={() => {}}
/>
```

### ProgressBar
Visual progress indicator.

```jsx
<ProgressBar progress={75} showPercentage={true} />
```

### LoadingSpinner
Loading state indicator.

```jsx
<LoadingSpinner size="lg" text="Processing..." />
```

## Custom Hooks

### useResumeUpload
Manages resume upload state and operations.

```jsx
const {
  selectedFiles,
  loading,
  progress,
  error,
  results,
  handleFileSelection,
  uploadResumes,
  reset
} = useResumeUpload();
```

## Styling

TailwindCSS is configured with custom theme extensions:

- Custom color palette (`primary.50` - `primary.900`)
- Soft shadow utility (`shadow-soft`)
- Custom animations
- Responsive breakpoints

## Configuration

### Environment Variables

Create a `.env` file:

```env
REACT_APP_API_URL=http://localhost:5000/api
```

### TailwindCSS

Configuration in `tailwind.config.js`:
- Content paths
- Theme extensions
- Custom colors
- Utilities

## Future Enhancements

- [ ] Real-time notifications with WebSockets
- [ ] Advanced candidate filtering
- [ ] Bulk email scheduling
- [ ] Analytics dashboard
- [ ] Dark mode support
- [ ] Candidate profile pages
- [ ] Interview scheduling
- [ ] Notes and comments system

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Code splitting with React.lazy
- Optimized bundle size
- Lazy loading for images
- Memoized components where appropriate

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## License

MIT License - see LICENSE file for details
