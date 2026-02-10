import { useState, useEffect } from 'react'
import axios from 'axios'
import PDFViewer from './PDFViewer'
import BookPDFGenerator from './PDFGenerator'
import './App_split.css'

const API_BASE = 'http://localhost:8000'

function App() {
  // Workflow steps: create -> outline_review -> chapter_review -> final -> completed
  const [step, setStep] = useState('create')
  
  // Book data
  const [title, setTitle] = useState('')
  const [requirements, setRequirements] = useState('')
  const [numChapters, setNumChapters] = useState(5)
  const [bookId, setBookId] = useState(null)
  
  // Outline data
  const [outline, setOutline] = useState(null)
  const [chapters, setChapters] = useState([])
  
  // Chapter review data
  const [currentChapter, setCurrentChapter] = useState(1)
  const [chapterData, setChapterData] = useState(null)
  const [approvedChapters, setApprovedChapters] = useState([])
  const [allChapterContents, setAllChapterContents] = useState([]) // Store all chapter contents
  
  // Feedback & Rating
  const [feedback, setFeedback] = useState('')
  const [rating, setRating] = useState(null)
  
  // UI states
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // PDF states
  const [pdfDataUrl, setPdfDataUrl] = useState(null)
  const [pdfGenerator] = useState(() => new BookPDFGenerator())

  // Update PDF whenever data changes
  useEffect(() => {
    updatePDF()
  }, [title, chapters, allChapterContents, step])

  const updatePDF = () => {
    if (!title && chapters.length === 0) {
      setPdfDataUrl(null)
      return
    }

    try {
      // Build chapters array with content
      const chaptersForPDF = chapters.map((ch, index) => ({
        number: ch.number,
        title: ch.title,
        content: allChapterContents[index]?.content || ''
      }))

      const pdf = pdfGenerator.generatePDF(title, chaptersForPDF)
      const dataUrl = pdf.output('dataurlstring')
      setPdfDataUrl(dataUrl)
    } catch (err) {
      console.error('PDF generation error:', err)
    }
  }

  const handleCreateBook = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/books`, {
        title,
        requirements,
        num_chapters: numChapters
      })
      
      setBookId(response.data.id)
      
      // Automatically generate outline
      await generateOutline(response.data.id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create book')
    } finally {
      setLoading(false)
    }
  }

  const generateOutline = async (id) => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/books/${id}/generate-outline`)
      
      setOutline(response.data.outline)
      setChapters(response.data.chapters)
      setStep('outline_review')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate outline')
    } finally {
      setLoading(false)
    }
  }

  const handleApproveOutline = async (approved) => {
    if (!approved && !feedback) {
      setError('Please provide feedback for changes')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/books/${bookId}/approve-outline`, {
        approved,
        feedback: approved ? null : feedback,
        rating: rating
      })

      if (approved) {
        setStep('chapter_review')
        setCurrentChapter(1)
        // Generate first chapter
        await generateChapter(1)
      } else {
        // Regenerate outline with feedback
        await regenerateOutline()
      }
      
      // Reset feedback and rating
      setFeedback('')
      setRating(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to approve outline')
    } finally {
      setLoading(false)
    }
  }

  const regenerateOutline = async () => {
    setLoading(true)
    try {
      const response = await axios.post(`${API_BASE}/books/${bookId}/regenerate-outline`)
      setOutline(response.data.outline)
      setChapters(response.data.chapters)
      setFeedback('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to regenerate outline')
    } finally {
      setLoading(false)
    }
  }

  const generateChapter = async (chapterNum) => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/books/${bookId}/generate-chapter/${chapterNum}`)
      
      setChapterData(response.data)
      
      // Store chapter content for PDF
      setAllChapterContents(prev => {
        const updated = [...prev]
        updated[chapterNum - 1] = {
          number: chapterNum,
          title: response.data.title,
          content: response.data.content
        }
        return updated
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate chapter')
    } finally {
      setLoading(false)
    }
  }

  const handleApproveChapter = async (approved) => {
    if (!approved && !feedback) {
      setError('Please provide feedback for changes')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/books/${bookId}/approve-chapter/${currentChapter}`, {
        approved,
        feedback: approved ? null : feedback,
        rating: rating
      })

      if (approved) {
        setApprovedChapters([...approvedChapters, currentChapter])
        
        // Check if more chapters to generate
        if (currentChapter < chapters.length) {
          const nextChapter = currentChapter + 1
          setCurrentChapter(nextChapter)
          await generateChapter(nextChapter)
        } else {
          // All chapters done!
          setStep('final')
        }
      } else {
        // Regenerate chapter with feedback
        await regenerateChapter(currentChapter, feedback)
      }
      
      setFeedback('')
      setRating(null)
    } catch (err) {
      console.error('Chapter approval error:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to process chapter approval'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const regenerateChapter = async (chapterNum, fb) => {
    setLoading(true)
    try {
      const response = await axios.post(
        `${API_BASE}/books/${bookId}/regenerate-chapter/${chapterNum}?feedback=${encodeURIComponent(fb)}`
      )
      setChapterData(response.data)
      
      // Update chapter content for PDF
      setAllChapterContents(prev => {
        const updated = [...prev]
        updated[chapterNum - 1] = {
          number: chapterNum,
          title: response.data.title,
          content: response.data.content
        }
        return updated
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to regenerate chapter')
    } finally {
      setLoading(false)
    }
  }

  const handleCompile = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/books/${bookId}/compile`)
      setStep('completed')
      
      // Download final PDF
      if (pdfGenerator && title) {
        const sanitizedTitle = title.replace(/[^a-zA-Z0-9]/g, '_')
        pdfGenerator.download(`${sanitizedTitle}.pdf`)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to compile book')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setStep('create')
    setTitle('')
    setRequirements('')
    setNumChapters(5)
    setBookId(null)
    setOutline(null)
    setChapters([])
    setCurrentChapter(1)
    setChapterData(null)
    setApprovedChapters([])
    setAllChapterContents([])
    setFeedback('')
    setRating(null)
    setError(null)
    setPdfDataUrl(null)
  }

  return (
    <div className="app">
      <div className="split-container">
        {/* LEFT PANEL - Form/Controls */}
        <div className="left-panel">
          <header className="header">
            <h1>📚 AI Book Generator</h1>
            <p>Interactive book creation with AI & live preview</p>
          </header>

          {error && (
            <div className="error-banner">
              <span>⚠️ {error}</span>
              <button onClick={() => setError(null)}>×</button>
            </div>
          )}

          {/* STEP 1: Create Book */}
          {step === 'create' && (
            <div className="card">
              <h2>📖 Create Your Book</h2>
              <form onSubmit={handleCreateBook}>
                <div className="form-group">
                  <label>Book Title</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g., The Future of AI in Healthcare"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Requirements & Topics</label>
                  <textarea
                    value={requirements}
                    onChange={(e) => setRequirements(e.target.value)}
                    placeholder="Describe what you want the book to cover..."
                    rows="6"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Number of Chapters</label>
                  <input
                    type="number"
                    value={numChapters}
                    onChange={(e) => setNumChapters(parseInt(e.target.value) || 5)}
                    min="1"
                    max="10"
                    placeholder="5"
                    required
                  />
                  <small className="help-text" style={{display: 'block', marginTop: '0.5rem', color: '#5D4E37'}}>
                    Recommended: 3-5 chapters (to avoid API rate limits)
                  </small>
                </div>

                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? '⏳ Generating Outline...' : '✨ Generate Outline'}
                </button>
              </form>
            </div>
          )}

          {/* STEP 2: Review Outline */}
          {step === 'outline_review' && outline && (
            <div className="card">
              <h2>📋 Review Book Outline</h2>
              
              <div className="outline-box">
                <h3>Outline</h3>
                <pre className="outline-text">{outline}</pre>
              </div>

              <div className="chapters-list">
                <h3>Chapters ({chapters.length})</h3>
                <ul>
                  {chapters.map((ch, idx) => (
                    <li key={`chapter-${idx}-${ch.number}`}>
                      <span className="chapter-num">{ch.number}</span>
                      <span className="chapter-title">{ch.title}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="approval-section">
                <div className="form-group">
                  <label>📝 Feedback (optional if approving, required for changes)</label>
                  <textarea
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Any changes you'd like to make?"
                    rows="3"
                  />
                </div>

                <div className="rating-section">
                  <label>⭐ Rate this outline (optional)</label>
                  <div className="rating-buttons">
                    {[0,1,2,3,4,5,6,7,8,9,10].map(num => (
                      <button
                        key={num}
                        type="button"
                        className={`rating-btn ${rating === num ? 'active' : ''}`}
                        onClick={() => setRating(num)}
                      >
                        {num}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="action-buttons">
                  <button
                    onClick={() => handleApproveOutline(false)}
                    className="btn-secondary"
                    disabled={loading}
                  >
                    ✏️ Request Changes
                  </button>
                  <button
                    onClick={() => handleApproveOutline(true)}
                    className="btn-primary"
                    disabled={loading}
                  >
                    {loading ? '⏳ Processing...' : '✅ Approve & Continue'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Review Chapters */}
          {step === 'chapter_review' && chapterData && (
            <div className="card">
              <div className="progress-header">
                <h2>📘 Chapter {currentChapter} of {chapters.length}</h2>
                <span className="chapter-progress">{approvedChapters.length} approved</span>
              </div>

              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{width: `${(approvedChapters.length / chapters.length) * 100}%`}}
                />
              </div>

              <div className="chapter-box">
                <h3>{chapterData.title}</h3>
                <div className="chapter-content">{chapterData.content}</div>
              </div>

              <div className="approval-section">
                <div className="form-group">
                  <label>📝 Feedback (optional if approving, required for changes)</label>
                  <textarea
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Any changes you'd like to make?"
                    rows="3"
                  />
                </div>

                <div className="rating-section">
                  <label>⭐ Rate this chapter (optional)</label>
                  <div className="rating-buttons">
                    {[0,1,2,3,4,5,6,7,8,9,10].map(num => (
                      <button
                        key={num}
                        type="button"
                        className={`rating-btn ${rating === num ? 'active' : ''}`}
                        onClick={() => setRating(num)}
                      >
                        {num}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="action-buttons">
                  <button
                    onClick={() => handleApproveChapter(false)}
                    className="btn-secondary"
                    disabled={loading}
                  >
                    ✏️ Request Changes
                  </button>
                  <button
                    onClick={() => handleApproveChapter(true)}
                    className="btn-primary"
                    disabled={loading}
                  >
                    {loading ? '⏳ Processing...' : currentChapter < chapters.length ? '✅ Approve & Next Chapter' : '✅ Approve & Finish'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: Final Review */}
          {step === 'final' && (
            <div className="card">
              <div className="success-icon">🎉</div>
              <h2>All Chapters Complete!</h2>
              <p className="subtitle">Ready to download your book?</p>

              <div className="summary-box">
                <h3>📊 Summary</h3>
                <ul>
                  <li>📚 Title: <strong>{title}</strong></li>
                  <li>📖 Chapters: <strong>{chapters.length}</strong></li>
                  <li>✅ Approved: <strong>{approvedChapters.length}</strong></li>
                </ul>
              </div>

              <div className="action-buttons">
                <button onClick={handleReset} className="btn-secondary">
                  Start New Book
                </button>
                <button onClick={handleCompile} className="btn-primary" disabled={loading}>
                  {loading ? '⏳ Compiling...' : '📥 Download PDF'}
                </button>
              </div>
            </div>
          )}

          {/* STEP 5: Completed */}
          {step === 'completed' && (
            <div className="card success-card">
              <div className="success-icon">🎊</div>
              <h2>Book Generated Successfully!</h2>
              <p className="subtitle">Your PDF has been downloaded and saved</p>

              <div className="download-section">
                <h3>📁 Files saved in:</h3>
                <code className="path-box">Downloads folder + output/</code>
                <p className="help-text">Check your Downloads and the output folder for all formats (.docx, .pdf, .txt)</p>
              </div>

              <button onClick={handleReset} className="btn-primary">
                Create Another Book
              </button>
            </div>
          )}
        </div>

        {/* RIGHT PANEL - PDF Preview */}
        <div className="right-panel">
          <PDFViewer pdfDataUrl={pdfDataUrl} />
        </div>
      </div>
    </div>
  )
}

export default App
