# Commercial Real Estate PDF Extractor - Web Application

Full-stack web application for extracting structured data from commercial real estate listing PDFs using LLM-powered processing.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                Frontend (Next.js + React)                │
│  - File upload with drag & drop                          │
│  - Real-time progress tracking (SSE)                     │
│  - Results table with sorting & filtering                │
│  - CSV export (individual or combined)                   │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST + SSE
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Backend (Flask + Python)                    │
│  - RESTful API endpoints                                 │
│  - Server-Sent Events for progress                       │
│  - PDF extraction service                                │
│  - LLM processing service                                │
│  - Local file storage (S3-ready abstraction)             │
└─────────────────────────────────────────────────────────┘
```

## Features

### MVP Features
- ✅ Multi-file PDF upload (drag & drop supported)
- ✅ Real-time extraction progress with SSE
- ✅ LLM-powered data extraction (Claude, GPT, Gemini)
- ✅ Results table with sorting and row expansion
- ✅ CSV export (download all or selected)
- ✅ Error handling and display
- ✅ Session-based processing (temporary storage)

### Future Features (Phase 3)
- 🔄 User authentication & accounts
- 🔄 Database persistence (PostgreSQL)
- 🔄 Cloud storage (S3/GCS)
- 🔄 Extraction history
- 🔄 Usage quotas/limits

## Project Structure

```
.
├── backend/
│   ├── api/
│   │   └── routes.py              # REST API endpoints
│   ├── config/
│   │   └── settings.py            # Configuration management
│   ├── services/
│   │   ├── extractor_service.py   # PDF extraction
│   │   ├── llm_service.py         # LLM processing
│   │   ├── storage_service.py     # File storage abstraction
│   │   └── progress_tracker.py    # SSE progress tracking
│   ├── models/
│   │   └── schemas.py             # Data models
│   ├── app.py                     # Flask app entry point
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # Backend Docker image
│   └── .env.example               # Environment template
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx               # Main application page
│   │   └── layout.tsx             # Root layout
│   ├── components/
│   │   ├── FileUploader.tsx       # Drag & drop file upload
│   │   ├── ProgressIndicator.tsx  # Progress bar with SSE
│   │   └── ResultsTable.tsx       # Results display & export
│   ├── hooks/
│   │   ├── useFileUpload.ts       # Upload logic
│   │   └── useExtraction.ts       # Extraction with SSE
│   ├── lib/
│   │   └── api.ts                 # API client
│   ├── types/
│   │   └── index.ts               # TypeScript definitions
│   ├── Dockerfile                 # Frontend Docker image
│   └── .env.local.example         # Environment template
│
├── src/                           # Original CLI code (reused)
│   ├── extractor.py
│   ├── llm_processor.py
│   ├── calculator.py
│   └── utils.py
│
├── docker-compose.yml             # Local development setup
├── config.yaml                    # LLM configuration
└── WEBAPP_README.md               # This file
```

## Getting Started

### Prerequisites

- **Docker & Docker Compose** (recommended for easy setup)
- OR:
  - Python 3.11+
  - Node.js 20+
  - Java Runtime (for PDF processing)

### Option 1: Docker Setup (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   cd listing_extractor
   ```

2. **Set up environment variables:**
   ```bash
   # Copy backend environment template
   cp backend/.env.example .env

   # Edit .env and add your API keys
   nano .env
   ```

   Required API keys in `.env`:
   ```
   ANTHROPIC_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   GOOGLE_API_KEY=your_key_here
   ```

3. **Start the application:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000/api/health

5. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Option 2: Local Development Setup

#### Backend Setup

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   ```

3. **Run the backend:**
   ```bash
   python backend/app.py
   # OR with gunicorn:
   gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 300 "backend.app:create_app()"
   ```

#### Frontend Setup

1. **Install Node dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment:**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local if needed (default: http://localhost:5000/api)
   ```

3. **Run the frontend:**
   ```bash
   npm run dev
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:5000

## API Documentation

### Backend Endpoints

#### `POST /api/upload`
Upload PDF files for extraction.

**Request:** `multipart/form-data` with `files` field
**Response:**
```json
{
  "session_id": "uuid",
  "files": [
    {
      "file_id": "uuid",
      "filename": "listing.pdf",
      "size": 1024000,
      "upload_time": "2025-01-01T00:00:00",
      "path": "/tmp/uploads/session_id/listing.pdf"
    }
  ],
  "total_files": 1
}
```

#### `POST /api/extract`
Start extraction process.

**Request:**
```json
{
  "session_id": "uuid",
  "files": [
    {
      "file_id": "uuid",
      "filename": "listing.pdf",
      "path": "/path/to/file"
    }
  ]
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "total_files": 1,
  "successful": 1,
  "failed": 0,
  "results": [
    {
      "file_id": "uuid",
      "filename": "listing.pdf",
      "success": true,
      "csv_row": "...",
      "data": {
        "File Name": "listing.pdf",
        "Address": "123 Main St",
        ...
      }
    }
  ],
  "errors": []
}
```

#### `GET /api/progress/:session_id` (Server-Sent Events)
Real-time progress updates.

**Response:** SSE stream
```
data: {"session_id":"uuid","overall_progress":50,"current_file":{...}}

data: {"session_id":"uuid","overall_progress":100,"status":"completed"}
```

#### `DELETE /api/session/:session_id`
Delete session and associated files.

## Configuration

### LLM Settings (`config.yaml`)

```yaml
llm:
  default_provider: "anthropic"
  anthropic:
    model: "claude-3-5-haiku-20241022"
    max_tokens: 1000
  openai:
    model: "gpt-4o-mini"
    max_tokens: 1000
  google:
    model: "gemini-1.5-flash"
    max_tokens: 1000
```

### File Upload Limits

- Maximum file size: **20MB** per file
- Allowed formats: **PDF only**
- Multiple files: **Unlimited** (within reasonable limits)

## Deployment

### Frontend Deployment (Vercel)

1. **Push code to GitHub**

2. **Import project in Vercel:**
   - Select `frontend` directory as root
   - Set build command: `npm run build`
   - Set output directory: `.next`

3. **Set environment variables:**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com/api
   ```

### Backend Deployment Options

#### Railway (Recommended)
1. Create new project in Railway
2. Connect GitHub repo
3. Set root directory: `backend`
4. Add environment variables from `.env.example`
5. Deploy

#### Fly.io
```bash
fly launch
fly deploy
```

#### Google Cloud Run
```bash
gcloud run deploy backend --source .
```

## Development Workflow

### Adding New Features

1. **Backend changes:**
   - Add service logic in `backend/services/`
   - Add API endpoints in `backend/api/routes.py`
   - Update schemas in `backend/models/schemas.py`

2. **Frontend changes:**
   - Add components in `frontend/components/`
   - Add hooks in `frontend/hooks/`
   - Update types in `frontend/types/index.ts`

### Testing

```bash
# Backend (from project root)
python -m pytest backend/tests/

# Frontend (from frontend directory)
npm run test

# E2E testing
npm run test:e2e
```

## Troubleshooting

### Common Issues

**Issue:** Backend can't find PDF extraction modules
**Solution:** Ensure `src/` directory is in PYTHONPATH:
```bash
export PYTHONPATH=/path/to/project:$PYTHONPATH
```

**Issue:** CORS errors in browser
**Solution:** Check `CORS_ORIGINS` in backend `.env` matches frontend URL

**Issue:** SSE connection drops
**Solution:** Ensure proxy/load balancer supports SSE (e.g., nginx: `proxy_buffering off`)

**Issue:** File upload fails
**Solution:** Check file size limit and disk space in `/tmp` directory

## Future Enhancements

### Phase 2: Polish & Deployment ✅
- [x] Docker containerization
- [x] Production-ready configs
- [x] Deployment documentation

### Phase 3: Auth & Persistence (Planned)
- [ ] User authentication (JWT)
- [ ] PostgreSQL database
- [ ] S3/GCS storage integration
- [ ] Extraction history
- [ ] User quotas and rate limiting
- [ ] Admin dashboard

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Contact: [Your Contact Info]
