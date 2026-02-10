# 📚 AI Book Generator

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg) ![React](https://img.shields.io/badge/React-18-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)

A full-stack automated book generation system with interactive approval workflow and live PDF preview. Built for professional content creation with AI assistance.

## ✨ Key Features

- **🎨 Split-Screen Interface**: Professional beige-themed UI with 45% form / 55% PDF viewer
- **📄 Live PDF Preview**: Real-time PDF generation as you create content
- **✅ Interactive Workflow**: Step-by-step creation with approval gates at each stage
- **🤖 AI-Powered**: Google Gemini Flash for high-quality content generation
- **🔄 Smart Error Handling**: Automatic retry with exponential backoff for rate limits
- **⭐ Quality Control**: Rate and provide feedback at outline and chapter level
- **📥 Multi-Format Export**: Download as PDF, DOCX, or TXT

## 🏗️ Architecture

### Tech Stack

**Backend:**
- FastAPI (Python REST API)
- Google Gemini Flash 2.0 (AI)
- Supabase (PostgreSQL database)
- Modular service architecture

**Frontend:**
- React 18 + Vite
- jsPDF (client-side PDF generation)
- react-pdf (PDF viewing)
- Axios (HTTP client)

### Project Structure

```
Book Project/
├── backend/
│   └── api_interactive.py      # FastAPI REST API with approval workflow
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React component (split-screen)
│   │   ├── App_split.css       # Beige theme styling
│   │   ├── PDFGenerator.js     # jsPDF wrapper for book generation
│   │   ├── PDFViewer.jsx       # react-pdf viewer component
│   │   ├── main.jsx            # React entry point
│   │   └── index.css           # Global styles
│   ├── package.json
│   └── vite.config.js
├── src/
│   ├── core/                   # Config, context, state management
│   ├── models/                 # Pydantic data schemas
│   ├── services/               # Business logic (LLM, Database, Export)
│   └── utils/                  # Logging, validation utilities
├── workflows/                  # Outline, chapter, compilation workflows
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template
├── final_schema.sql            # Production database schema
├── requirements.txt            # Python dependencies
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- Supabase account (free tier)
- Google Gemini API key (free tier)

### 1. Environment Setup

```bash
# Navigate to project
cd "Book Project"

# Create .env file from example
cp .env.example .env

# Edit .env and add your credentials:
# GEMINI_API_KEY=your_gemini_key
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_supabase_anon_key
```

### 2. Database Setup

In Supabase SQL Editor, run the contents of `final_schema.sql`:

```sql
-- Creates 4 tables: books, outlines, chapters, final_state
-- See final_schema.sql for complete schema
```

### 3. Install Dependencies

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 4. Run the Application

**Terminal 1 - Start Backend:**
```bash
python -m uvicorn backend.api_interactive:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```

**Browser:**
Open `http://localhost:5173` (or the port shown in terminal)

## 📖 How to Use

### Step-by-Step Workflow

**1. Create Book**
- Enter book title (e.g., "AI in Healthcare")
- Describe requirements and topics
- Set number of chapters (3-5 recommended for demo)
- Click "Generate Outline"

**2. Review Outline**
- View AI-generated outline and chapter list
- **PDF Preview**: Title page and table of contents appear
- Add feedback if changes needed (optional)
- Rate the outline 0-10 (optional)
- Click "Approve & Continue" or "Request Changes"

**3. Review Chapters (Iterative)**
- Read each generated chapter
- **PDF Preview**: Chapters appear progressively in scrollable viewer
- Add feedback for improvements (optional)
- Rate each chapter (optional)
- Click "Approve & Next Chapter" or "Request Changes"
- Repeat for all chapters

**4. Download Final Book**
- Review complete book in PDF viewer
- Click "Download PDF"
- Book saved to Downloads folder

## 🎨 UI Features

### Split-Screen Layout

**Left Panel (45%):**
- Form inputs and controls
- Step-by-step workflow
- Approval interface
- Feedback textarea
- Rating system (0-10)
- Progress tracking

**Right Panel (55%):**
- Live PDF preview
- Continuous scrolling through all pages
- Zoom controls (50% - 200%)
- Auto-updates when content changes

### PDF Structure

1. **Page 1**: Title page with book title
2. **Page 2**: Table of contents with chapter list
3. **Page 3+**: Full chapters with formatted content

### Color Scheme

- **Primary**: `#F5F5DC` (Beige/Cream)
- **Accents**: `#8B7355`, `#5D4E37` (Browns)
- **PDF Viewer**: Dark theme `#1a1a1a`

## 🔧 Technical Details

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/books` | POST | Create new book project |
| `/books/{id}/generate-outline` | POST | Generate outline with AI |
| `/books/{id}/approve-outline` | POST | Approve or request outline changes |
| `/books/{id}/generate-chapter/{num}` | POST | Generate specific chapter |
| `/books/{id}/approve-chapter/{num}` | POST | Approve or request chapter changes |
| `/books/{id}/compile` | POST | Compile final book and download PDF |

### Backend Services

**llm_service.py** - Gemini API integration
- Auto-retry with exponential backoff
- Rate limit handling (429 errors)
- Chapter count enforcement
- Context-aware generation

**database_service.py** - Supabase operations
- CRUD for books, outlines, chapters
- Transaction management
- Error handling

**export_service.py** - Multi-format export
- PDF generation (python-docx + docx2pdf)
- DOCX with proper formatting
- TXT plaintext export

### Frontend Components

**App.jsx** - Main application
- Workflow state management
- API integration with Axios
- Split-screen layout orchestration

**PDFGenerator.js** - Client-side PDF creation
- Title page generation
- Table of contents with page numbers
- Chapter formatting with page breaks
- Automatic paragraph handling

**PDFViewer.jsx** - PDF preview
- Continuous scrolling (all pages)
- Zoom controls
- react-pdf integration

### Database Schema

**books** - Main book records
- id (UUID primary key)
- title, requirements
- num_chapters
- timestamps

**outlines** - Generated outlines
- id, book_id (foreign key)
- content, chapter_count
- version tracking

**chapters** - Individual chapters
- id, book_id, chapter_number
- title, content
- Unique constraint on (book_id, chapter_number)

**final_state** - Compilation status
- book_id (primary key foreign key)
- compilation status
- file paths (docx, pdf, txt)

## ⚡ Performance & Limits

### API Rate Limits

**Google Gemini Free Tier:**
- 15 requests per minute
- 1,500 requests per day

**Request Estimates:**
- Outline generation: 1-2 requests
- Per chapter: 1-2 requests
- 3-chapter book: ~8-10 total requests
- 5-chapter book: ~12-16 total requests

### Recommended Settings

- **Demo/Test**: 3 chapters (~5 minutes)
- **Production**: 5-7 chapters (~10-15 minutes)
- **Maximum**: Avoid 10+ chapters (rate limit risk)

### Auto-Retry Logic

System automatically handles rate limits:
1. Detects 429 error
2. Extracts retry delay from error
3. Waits with exponential backoff
4. Retries up to 3 times
5. User sees "Processing..." during retry

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check dependencies installed
pip list | grep -E "fastapi|uvicorn|supabase"

# Verify .env file
cat .env

# Check port availability
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Linux/Mac
```

### Frontend Build Errors

```bash
# Clear and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 16+
```

### PDF Not Loading

- Open browser console (F12) for errors
- Verify `pdfjs-dist` installed: `npm list pdfjs-dist`
- Check PDF.js worker URL in PDFViewer.jsx
- Clear browser cache

### Database Connection Issues

- Verify Supabase URL and key in .env
- Check Supabase project is not paused
- Confirm tables exist (run final_schema.sql)
- Check network connection

### Rate Limit Errors

- System auto-retries automatically
- Wait 10-60 seconds for retry
- Consider fewer chapters for demo
- Check Gemini API quota in console

## 📚 Project Best Practices

### For Development

- Use 3 chapters for quick testing
- Check browser console for errors
- Monitor backend terminal for logs
- Test approval workflow with feedback

### For Demo/Interview

- Prepare with dry run beforehand
- Use 3-5 chapters maximum
- Have compelling book title ready
- Show PDF updates in real-time
- Demonstrate approval workflow
- Highlight error handling
- Discuss architecture decisions

### Code Quality

- Modular service layer
- Comprehensive error handling
- Logging throughout
- Clean separation of concerns
- RESTful API design
- Responsive UI design

## 📄 File Outputs

Generated files are saved in:

```
output/
├── Book_Title_UUID.docx   # Formatted Word document
├── Book_Title_UUID.pdf    # PDF version
└── Book_Title_UUID.txt    # Plain text version
```

Downloads from browser saved to system Downloads folder.

## 🎓 Interview Highlights

### Technical Skills Demonstrated

1. **Full-Stack Development**
   - FastAPI backend (Python)
   - React frontend (JavaScript)
   - REST API design
   - Database integration

2. **AI Integration**
   - Google Gemini API
   - Prompt engineering
   - Error handling & retries
   - Rate limit management

3. **User Experience**
   - Split-screen interface
   - Real-time updates
   - Interactive workflow
   - Visual feedback
   - Responsive design

4. **Architecture**
   - Modular service layer
   - Clear separation of concerns
   - Scalable structure
   - Clean code organization

5. **Production Readiness**
   - Comprehensive error handling
   - Logging for debugging
   - Environment configuration
   - Database migrations
   - Documentation

## 📝 License

This project is for demonstration and portfolio purposes.

---

**Built for professional demonstration | Full-Stack AI Application**
    title="AI Ethics",
    notes_on_outline_before="Cover fairness, transparency, accountability",
    status_outline_notes="no_notes_needed"
)

# Run full workflow
generator.run_full_workflow(book_id)

# Or run stages separately
generator.generate_outline_only(book_id)
generator.generate_chapters(book_id)
generator.compile_book(book_id, formats=['docx', 'pdf'])
```

#### Handling Feedback Loops

