import { useState, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

// Set up worker for react-pdf using jsdelivr CDN
pdfjs.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

function PDFViewer({ pdfDataUrl }) {
  const [numPages, setNumPages] = useState(null)
  const [scale, setScale] = useState(1.0)

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages)
  }

  useEffect(() => {
    // Reset scroll position when PDF changes
    const container = document.querySelector('.pdf-viewer-container')
    if (container) {
      container.scrollTop = 0
    }
  }, [pdfDataUrl])

  if (!pdfDataUrl) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem', color: '#F5F5DC' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📄</div>
        <h3>PDF Preview</h3>
        <p style={{ color: '#D4C5A9' }}>Your book will appear here as you create it</p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="pdf-header">
        <h2>📖 Live Preview</h2>
        <div className="pdf-page-info">
          {numPages ? `${numPages} page${numPages > 1 ? 's' : ''}` : 'Loading...'}
        </div>
      </div>

      <div className="pdf-controls" style={{
        display: 'flex',
        justifyContent: 'center',
        gap: '1rem',
        padding: '1rem',
        background: '#1a1a1a',
        borderBottom: '1px solid #8B7355'
      }}>
        <button
          onClick={() => setScale(prev => Math.max(0.5, prev - 0.1))}
          style={{
            padding: '0.5rem 1rem',
            background: '#5D4E37',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          Zoom Out
        </button>
        
        <span style={{ color: '#F5F5DC', lineHeight: '2.5' }}>
          {Math.round(scale * 100)}%
        </span>
        
        <button
          onClick={() => setScale(prev => Math.min(2, prev + 0.1))}
          style={{
            padding: '0.5rem 1rem',
            background: '#5D4E37',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          Zoom In
        </button>
      </div>

      <div className="pdf-viewer-container" style={{ 
        flex: 1, 
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '1rem',
        padding: '1rem 0'
      }}>
        <Document
          file={pdfDataUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div style={{ color: '#F5F5DC', textAlign: 'center', padding: '2rem' }}>
              Loading PDF...
            </div>
          }
          error={
            <div style={{ color: '#ef5350', textAlign: 'center', padding: '2rem' }}>
              Error loading PDF. Please try again.
            </div>
          }
        >
          {Array.from(new Array(numPages), (el, index) => (
            <Page
              key={`page_${index + 1}`}
              pageNumber={index + 1}
              scale={scale}
              className="pdf-canvas"
              renderTextLayer={true}
              renderAnnotationLayer={true}
              style={{ marginBottom: '1rem' }}
            />
          ))}
        </Document>
      </div>
    </div>
  )
}

export default PDFViewer
