# StandardAssist IN — AI-Powered Intelligent Assistant for Indian Standards & BIS Services

**Smart India Hackathon (SIH) 2026**  
**Problem Statement ID:** 26107  
**Title:** AI-powered Intelligent Assistant for Indian Standards and BIS Services for Industries and Consumers  

---

## Overview

StandardAssist IN is a grounded Retrieval-Augmented Generation (RAG) web application designed to help industries, technical personnel, and consumers query Bureau of Indian Standards (BIS) documents, Indian Standards (IS), certification schemes, and testing guidelines quickly and accurately.

Rather than manually navigating lengthy PDF standards documents, users can ask questions in natural language and receive grounded answers backed by authentic document citations (filename, page number, and relevant text snippet).

---

## Key Capabilities & Supported Use Cases

1. **Indian Standard Discovery**: Find relevant IS codes for products, materials, and procedures (e.g., `IS 10500` for drinking water, `IS 14489:2018` for occupational safety audits).
2. **Certification & Licensing Guidance**: Guidance on ISI mark certification requirements, BIS schemes, and compliance workflows.
3. **Testing & Laboratory Queries**: Information on testing methods, mandatory safety parameters, and laboratory guidelines.
4. **Hallmarking & Consumer Queries**: Clear explanations of hallmarking guidelines and consumer rights regarding certified products.
5. **Multilingual Input Support**: Enter queries in English, Hindi (हिन्दी), or Gujarati (ગુજરાતી).
6. **PDF Document Ingestion**: Upload custom PDF standards for automatic validation, page extraction, chunking, and instant vector indexing.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 React + Vite Frontend (UI)                  │
│       - Chat Interface & Grounded Source Inspector          │
│       - Document Upload & Selection Sidebar                 │
│       - Multilingual Text & Health Status Badge             │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST API (JSON / Multipart)
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend Server                   │
│                                                             │
│  ┌───────────────────────┐       ┌───────────────────────┐  │
│  │ PDF Ingestion Engine  │       │ RAG Hybrid Retriever  │  │
│  │  - PyPDFLoader        │       │  - Dense: MiniLM-L6   │  │
│  │  - SHA-256 Hash       │       │  - Sparse: BM25Okapi  │  │
│  │  - Text Chunking      │       │  - Threshold: 0.35    │  │
│  └───────────┬───────────┘       └───────────┬───────────┘  │
│              │                               │              │
│  ┌───────────▼───────────┐       ┌───────────▼───────────┐  │
│  │ ChromaDB Vector Store │       │  Groq LLM Inference   │  │
│  │  - Cosine Distance    │       │   (gemma2-9b-it)      │  │
│  └───────────────────────┘       └───────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## RAG Workflow

1. **Upload & Validate**: PDF is validated for format, magic bytes (`%PDF`), max file size, and non-empty extractable text. Duplicate files are recognized via SHA-256 hash.
2. **Chunking & Vector Storage**: Pages are split into chunks with full page & filename metadata and embedded into ChromaDB using `SentenceTransformer('all-MiniLM-L6-v2')`.
3. **Hybrid Search**: Query runs dense vector search fused with BM25 keyword matching. Results below `0.35` similarity are filtered out.
4. **Grounded Answer Generation**: Top relevant chunks are formatted into a strict system prompt for `gemma2-9b-it` via Groq LLM. If no relevant context passes the threshold, the system responds with a grounded fallback answer without invoking the LLM.

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+ & npm**

---

### Environment Setup

1. Copy the example environment configuration:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Edit `backend/.env` and add your Groq API key:
   ```env
   GROQ_API_KEY=gsk_your_actual_groq_api_key_here
   GROQ_MODEL=gemma2-9b-it
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   MAX_UPLOAD_SIZE_MB=20
   DEFAULT_TOP_K=5
   DEFAULT_SIMILARITY_THRESHOLD=0.35
   ```

---

### Backend Installation & Run

1. Navigate to project root and install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Start the FastAPI backend server:
   ```bash
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will be available at `http://127.0.0.1:8000`. Access `http://127.0.0.1:8000/api/health` to check system health.

---

### Frontend Installation & Run

1. Navigate to the `Frontend` directory:
   ```bash
   cd Frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

### Running Automated Tests

Run the complete backend test suite (including document ingestion, hybrid retrieval, chat grounding, and hardening tests):

```bash
python -m pytest tests/
```

Run frontend lint and build checks:

```bash
cd Frontend
npm run lint
npm run build
```

---

## Known Limitations

- **Scanned / Image-Only PDFs**: Text extraction relies on PyPDFLoader. Image-only PDFs without embedded OCR text layers will be rejected during upload.
- **API Rate Limits**: LLM responses depend on Groq API quota and connectivity. If the Groq API key is missing or unavailable, the backend gracefully catches the exception.