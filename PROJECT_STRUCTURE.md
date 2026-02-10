# 📁 Project Structure

## Overview

Clean, professional structure for an AI-powered book generation system with split-screen React interface.

## Root Directory

```
Book Project/
├── 📄 .env                    # Environment variables (not in git)
├── 📄 .env.example            # Environment template with placeholders
├── 📄 .gitignore              # Git ignore rules (logs, output, env, etc.)
├── 📄 README.md               # Complete documentation
├── 📄 requirements.txt        # Python dependencies
├── 📄 final_schema.sql        # Production database schema (Supabase)
│
├── 📁 backend/                # FastAPI REST API
│   └── api_interactive.py     # Main API with approval workflow
│
├── 📁 frontend/               # React 18 + Vite application
│   ├── package.json           # Node dependencies
│   ├── vite.config.js         # Vite configuration
│   ├── index.html             # HTML entry point
│   └── src/                   # React source code
│       ├── App.jsx            # Main component (split-screen + workflow)
│       ├── App_split.css      # Beige theme styling
│       ├── PDFGenerator.js    # jsPDF wrapper for book generation
│       ├── PDFViewer.jsx      # react-pdf viewer with scrolling
│       ├── main.jsx           # React entry point
│       └── index.css          # Global styles
│
├── 📁 src/                    # Backend Python modules
│   ├── 📁 core/               # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── context_manager.py # Chapter context chaining
│   │   └── state_machine.py   # Workflow state management
│   │
│   ├── 📁 models/             # Data models
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic schemas (Book, Outline, Chapter)
│   │
│   ├── 📁 services/           # Business logic layer
│   │   ├── __init__.py
│   │   ├── llm_service.py     # Gemini API + retry logic
│   │   ├── database_service.py # Supabase operations
│   │   ├── export_service.py  # DOCX/PDF/TXT export
│   │   └── notification_service.py # Email notifications
│   │
│   └── 📁 utils/              # Utilities
│       ├── __init__.py
│       ├── logger.py          # Logging configuration
│       └── validators.py      # Input validation
│
├── 📁 workflows/              # Workflow orchestration
│   ├── __init__.py
│   ├── outline_workflow.py    # Outline generation logic
│   ├── chapter_workflow.py    # Chapter generation logic
│   └── compilation_workflow.py # Final book compilation
│
├── 📁 logs/                   # Application logs (gitignored)
│   └── app.log
│
└── 📁 output/                 # Generated books (gitignored)
    └── Book_Title_UUID.{docx,pdf,txt}
```

## File Counts

| Category | Count | Purpose |
|----------|-------|---------|
| **Backend API** | 1 | FastAPI with 6 endpoints |
| **Frontend Components** | 4 | App, PDFGenerator, PDFViewer, main |
| **Python Services** | 4 | LLM, Database, Export, Notification |
| **Workflows** | 3 | Outline, Chapter, Compilation |
| **Config Files** | 4 | .env, requirements.txt, package.json, vite.config.js |
| **Documentation** | 1 | README.md |
| **Database** | 1 | final_schema.sql |

## Key Features by Directory

### `/backend`
- **api_interactive.py**: 
  - FastAPI REST API
  - 6 endpoints for book workflow
  - CORS configured for frontend
  - Approval workflow with feedback
  - Rate limit handling

### `/frontend/src`
- **App.jsx**: 
  - Split-screen layout (45% / 55%)
  - Workflow state management
  - API integration with Axios
  - Step-by-step book creation

- **App_split.css**: 
  - Beige theme (#F5F5DC)
  - Responsive design
  - Dark PDF viewer styling

- **PDFGenerator.js**: 
  - Client-side PDF creation
  - Title page, TOC, chapters
  - Automatic page breaks
  - jsPDF wrapper

- **PDFViewer.jsx**: 
  - Continuous scrolling
  - Zoom controls (50-200%)
  - react-pdf integration
  - Page counter

### `/src/services`
- **llm_service.py**: 
  - Google Gemini Flash integration
  - Auto-retry with exponential backoff
  - Rate limit handling
  - Chapter count enforcement

- **database_service.py**: 
  - Supabase CRUD operations
  - Books, outlines, chapters tables
  - Error handling
  - Connection management

- **export_service.py**: 
  - Multi-format export (DOCX, PDF, TXT)
  - Formatting and styling
  - File management

### `/workflows`
- **outline_workflow.py**: 
  - Outline generation from requirements
  - Feedback incorporation
  - Regeneration logic

- **chapter_workflow.py**: 
  - Sequential chapter generation
  - Context chaining
  - Summary creation

- **compilation_workflow.py**: 
  - Final book assembly
  - Multi-format export orchestration

## Dependencies

### Backend (Python)
- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `google-generativeai` - Gemini API
- `supabase` - Database client
- `python-docx` - DOCX generation
- `pydantic` - Data validation

### Frontend (JavaScript)
- `react` + `react-dom` - UI framework
- `vite` - Build tool
- `axios` - HTTP client
- `jspdf` - PDF generation
- `react-pdf` - PDF viewing
- `pdfjs-dist` - PDF.js library

## Database Schema

### Tables (4 total)

1. **books** - Main book records
   - Metadata, title, requirements
   - Timestamps

2. **outlines** - Generated outlines
   - Book reference
   - Content, chapter count
   - Version tracking

3. **chapters** - Individual chapters
   - Book and chapter number references
   - Title and content
   - Unique constraint

4. **final_state** - Compilation status
   - Book reference (primary key FK)
   - Status flags
   - File paths

## Code Organization Principles

### ✅ What We Have

1. **Modular Architecture**
   - Clear separation: API, services, workflows
   - Each service has single responsibility
   - Easy to test and maintain

2. **Clean File Structure**
   - No duplicate or backup files
   - No unnecessary documentation files
   - Only production-ready code

3. **Logical Grouping**
   - Backend vs Frontend clear separation
   - Services grouped by functionality
   - Workflows isolated from services

4. **Configuration Management**
   - Environment variables in .env
   - Example template provided
   - No hardcoded credentials

5. **Documentation**
   - Single comprehensive README
   - Code comments where needed
   - Clear naming conventions

### ❌ What We Don't Have

1. **No Dead Code**
   - Removed all backup files
   - No commented-out sections
   - No unused imports

2. **No Redundancy**
   - Single README (removed 18 .md files)
   - One CSS file (removed old styles)
   - No duplicate scripts

3. **No Legacy Files**
   - Removed CLI version (main.py)
   - Removed old SQL scripts
   - Removed test/demo scripts

## For Interviewers

### Quick Navigation

Need to see...
- **API endpoints?** → `backend/api_interactive.py`
- **React UI?** → `frontend/src/App.jsx`
- **PDF generation?** → `frontend/src/PDFGenerator.js`
- **AI integration?** → `src/services/llm_service.py`
- **Database?** → `final_schema.sql` or `src/services/database_service.py`
- **Styling?** → `frontend/src/App_split.css`

### Code Quality Indicators

- ✅ **No warnings in terminal**
- ✅ **No console errors**
- ✅ **Clean git status**
- ✅ **Organized imports**
- ✅ **Consistent naming**
- ✅ **Proper error handling**
- ✅ **Comprehensive logging**

### Architecture Highlights

1. **RESTful API Design** - Standard HTTP methods, clear endpoints
2. **Component-Based UI** - Reusable React components
3. **Service Layer Pattern** - Business logic separated from API
4. **Client-Side PDF** - No server overhead, instant updates
5. **Responsive Design** - Works on desktop and mobile

### Scalability Considerations

- Easy to add new LLM providers (extend `llm_service.py`)
- Easy to add export formats (extend `export_service.py`)
- Easy to add UI features (React component model)
- Database schema supports versioning
- API versioning ready (`/api/v1` prefix possible)

## Running the Project

```bash
# Terminal 1 - Backend
python -m uvicorn backend.api_interactive:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend && npm run dev

# Browser
http://localhost:5173
```

---

**Clean. Professional. Ready for production.**
