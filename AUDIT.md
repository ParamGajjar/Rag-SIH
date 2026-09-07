# Codebase Audit Report: Rag-SIH

**Repository:** [https://github.com/ParamGajjar/Rag-SIH](https://github.com/ParamGajjar/Rag-SIH)  
**Audit Date:** September 7, 2026  
**Auditor:** Antigravity AI Assistant  

---

## 1. Executive Summary

`Rag-SIH` is a hackathon project aimed at providing an AI-powered assistant for Indian Standards (BIS compliance, certification, testing, and guidelines). The repository currently consists of two disconnected parts:
1. **Python RAG Script (`rag_main.py`)**: A monolithic Python script containing document loading, text splitting, embedding generation, ChromaDB vector storage, vector retrieval, and Groq LLM integration logic.
2. **Frontend SPA (`Frontend/`)**: A React 19 + Vite application providing a polished search and chat UI, but currently relying entirely on hardcoded dummy responses.

The application is in an early prototype stage with **no integration between the frontend and backend**, **no API server layer**, **no Python dependency management files**, and **no automated tests**.

---

## 2. Current Architecture

```
                                CURRENT STATE ARCHITECTURE
                                
   +---------------------------------------+      +---------------------------------------+
   |             Frontend (SPA)            |      |            Backend (Script)           |
   |                                       |      |                                       |
   |   React 19 + Vite 8 + Tailwind CSS    |      |  rag_main.py (Monolithic Execution)   |
   |   - Mock chat interface               |      |  - PyPDFLoader (scanning ../data)     |
   |   - Hardcoded ISI/BIS answers          |      |  - RecursiveCharacterTextSplitter     |
   |   - Zero API network calls            |      |  - SentenceTransformer                |
   |                                       |      |  - ChromaDB (at ../data/vector_store) |
   +---------------------------------------+      |  - RAGRetriever                       |
                                                  |  - ChatGroq (gemma2-9b-it)            |
                                                  +---------------------------------------+
                                                                      
                                        NO API BRIDGE EXISTS
```

### Data Flow & Component Breakdown

1. **PDF Document Ingestion**:
   - **Loader**: `PyPDFLoader` from `langchain_community.document_loaders`.
   - **Source Directory**: Hardcoded path `../data` (outside repository root).
   - **Metadata**: Attaches `source_file` and `file_type`.

2. **Text Chunking**:
   - **Splitter**: `RecursiveCharacterTextSplitter` from `langchain_text_splitters`.
   - **Configuration**: `chunk_size = 400`, `chunk_overlap = 90`, separators `["\n\n", "\n", " ", ""]`.

3. **Embedding Generation**:
   - **Framework**: `SentenceTransformer` via custom `EmbeddingManager` class.
   - **Model**: `all-MiniLM-L6-v2` (384-dimensional dense vectors).

4. **Vector Database**:
   - **Store**: `chromadb.PersistentClient`.
   - **Persist Path**: Hardcoded path `../data/vector_store`.
   - **Collection Name**: `pdf_documents`.
   - **Storage**: Custom IDs (`doc_<uuid>_<index>`), metadatas, document page content, and floating-point embedding vectors.

5. **Retrieval Mechanism**:
   - **Class**: `RAGRetriever`.
   - **Query Pipeline**: Encodes user query string using `EmbeddingManager`, runs vector distance query on ChromaDB for `top_k` (default 5).
   - **Score Calculation**: Converts cosine distance to similarity score (`1 - distance`) and filters by `score_threshold`.

6. **LLM Integration**:
   - **Provider**: Groq via `langchain_groq.ChatGroq`.
   - **Model**: `gemma2-9b-it` (temperature 0.1, max_tokens 1024).
   - **Prompt**: Standard RAG system prompt requiring answers based strictly on retrieved context.

7. **Frontend Implementation**:
   - **Tech Stack**: React 19, Vite 8, Tailwind CSS v4, Lucide React icons.
   - **UI Flow**: Toggleable search landing page and chat screen.
   - **Data Handling**: Purely local React state (`useState`). `handleSearch` submits user input and appends a static canned response referencing "IS 14489:2018".

8. **Frontend/Backend Integration**:
   - **Status**: **Disconnected**. No backend web server (e.g. FastAPI / Flask) exists to expose RAG endpoints to the frontend.

---

## 3. Current Features

| Feature Component | Status | Implementation Details |
| :--- | :--- | :--- |
| **PDF Ingestion & Chunking** | Prototype | Functional script logic; hardcoded to `../data` |
| **Vector Indexing & Storage** | Prototype | ChromaDB setup exists; re-indexes everything on every script run |
| **Similarity Retrieval** | Prototype | Dense vector similarity retrieval implemented in Python |
| **Groq LLM Generation** | Prototype | Prompt formatting and ChatGroq setup present |
| **User Interface** | UI Shell | Responsive React UI with query input and chat template |
| **REST API Server** | **Missing** | No HTTP server exists to connect frontend and backend |
| **Environment Config** | **Missing** | No `.env.example` or configuration schema |
| **Dependency Specs** | **Missing** | No `requirements.txt` or `pyproject.toml` |

---

## 4. Problem Identification & Classification

### 🚨 Critical Errors (Preventing App Execution)
1. **Missing Backend Dependencies Specification**: No `requirements.txt` or `pyproject.toml` exists. Python imports for `langchain_community`, `chromadb`, `sentence_transformers`, `langchain_groq`, etc., fail in a standard python environment.
2. **Missing API Server**: No HTTP API backend (e.g., FastAPI) exists. The React frontend cannot communicate with `rag_main.py`.
3. **Hardcoded External Directory Paths**: `rag_main.py` attempts to read from `../data` and persist ChromaDB to `../data/vector_store`. If these directories do not exist outside `Rag-SIH`, execution crashes.
4. **Top-Level Execution Side-Effects**: `rag_main.py` executes document loading, embedding generation, ChromaDB insertion, and LLM initialization at the top level during module load.

### ⚙️ Backend Issues
1. **Unused Imports & Dead Code**: `rank_bm25.BM25Okapi`, `sklearn.metrics.pairwise.cosine_similarity`, and `PyMuPDFLoader` are imported in `rag_main.py` but never used.
2. **Brittle Error Handling**: `GroqLLM` returns string error descriptions instead of raising handled exceptions or structured responses.
3. **Static Model Configuration**: Groq model name (`gemma2-9b-it`) and embedding model name (`all-MiniLM-L6-v2`) are hardcoded without configuration fallback.

### 🎨 Frontend Issues
1. **Unused Imports**: `Mic` and `Building2` imported in `App.jsx` but unused (flagged by `oxlint`).
2. **Dummy Static Responses**: Frontend returns the exact same hardcoded text for every query.
3. **Lack of Integration Layer**: No API service, HTTP client (fetch/axios), loading state, or error handling UI for network requests.
4. **Template Boilerplate**: `App.css` contains default Vite starter styles unrelated to the application.

### 🏛️ Architecture Issues
1. **Lack of Separation of Concerns**: RAG logic, configuration, script execution, vector storage, and model initialization are crammed into one 462-line file (`rag_main.py`).
2. **Missing Backend Application Layer**: Needs a web framework (FastAPI) with structured routing, request/response models (Pydantic), and lifecycle management.
3. **Tight Coupling to File Paths**: Ingestion process hardcodes local paths instead of offering configurable data directories or file upload endpoints.

### 🔒 Security Issues
1. **Missing Root `.gitignore`**: No root `.gitignore` file exists (only `Frontend/.gitignore`). Risk of accidentally committing `.env`, secrets, or database stores.
2. **Unvalidated API Key Access**: `GROQ_API_KEY` is accessed directly from environment without schema validation.
3. **No Input Sanitization**: Prompt templates directly format un-sanitized user strings into the prompt.

### ⚡ Performance Issues
1. **Repeated Heavy Computations**: `rag_main.py` re-loads all PDFs, re-chunks text, re-generates embeddings, and re-writes to ChromaDB *on every execution*.
2. **No Embeddings Caching**: Deduplication checks are missing before adding documents to ChromaDB.

### 🧪 Testing Gaps
1. **Zero Test Coverage**: No Python unit/integration tests exist (`unittest` / `pytest`).
2. **No Frontend Tests**: No Component or E2E tests exist for React components.

---

## 5. Exact Verification Commands Executed & Baseline Results

All checks were executed from `d:\Projects\SIH 2026\Rag-SIH` on September 7, 2026.

### 1. Backend Python Syntax Compilation
- **Command:** `python -m py_compile rag_main.py`
- **Exit Code:** `0`
- **Result:** Success. `rag_main.py` contains valid Python syntax.

### 2. Backend Python Dependency Import Audit
- **Command:**
  ```powershell
  python -c "
  mods = ['langchain_community', 'langchain_text_splitters', 'rank_bm25', 'numpy', 'sentence_transformers', 'chromadb', 'sklearn', 'dotenv', 'langchain_groq', 'langchain']
  for m in mods:
      try:
          __import__(m)
          print(f'{m}: INSTALLED')
      except ImportError as e:
          print(f'{m}: MISSING ({e})')
  "
  ```
- **Exit Code:** `0`
- **Result:**
  ```text
  langchain_community: MISSING
  langchain_text_splitters: MISSING
  rank_bm25: MISSING
  numpy: MISSING
  sentence_transformers: MISSING
  chromadb: MISSING
  sklearn: MISSING
  dotenv: MISSING
  langchain_groq: MISSING
  langchain: MISSING
  ```

### 3. Backend Test Suite Discovery
- **Command:** `python -m unittest discover`
- **Exit Code:** `1`
- **Result:** `NO TESTS RAN` (0 tests found).

### 4. Frontend Package Installation
- **Command:** `cmd /c "npm install"` (Executed inside `Frontend/`)
- **Exit Code:** `0`
- **Result:** Success. 54 packages installed in 4 seconds, 0 vulnerabilities found.

### 5. Frontend Code Linting
- **Command:** `cmd /c "npm run lint"` (Executed inside `Frontend/`)
- **Exit Code:** `0`
- **Result:** Passed with 2 warnings (Oxlint):
  - Warning 1: `Identifier 'Mic' is imported but never used` in `src/App.jsx:2:18`
  - Warning 2: `Identifier 'Building2' is imported but never used` in `src/App.jsx:2:100`

### 6. Frontend Build Bundle Check
- **Command:** `cmd /c "npm run build"` (Executed inside `Frontend/`)
- **Exit Code:** `0`
- **Result:** Success. Vite compiled production bundle in 2.26s:
  - `dist/index.html` (0.47 kB)
  - `dist/assets/index-ZoJEgSae.css` (21.29 kB)
  - `dist/assets/index-C8hu0fMS.js` (202.37 kB)

---

## 6. Recommended Implementation Order (for Subsequent Phases)

1. **Phase 2: Environment & Foundation Setup**
   - Create root `.gitignore` (ignore `.env`, `node_modules`, `__pycache__`, vector store files, `.venv`).
   - Create `requirements.txt` specifying exact backend package versions.
   - Create `.env.example` defining environment variables (`GROQ_API_KEY`, `CHROMA_DB_DIR`, `DATA_DIR`, `PORT`).

2. **Phase 3: Backend Refactoring & FastAPI Server**
   - Refactor `rag_main.py` into modular service modules (`config.py`, `ingestion.py`, `vectorstore.py`, `retriever.py`, `llm.py`).
   - Remove top-level script side-effects and duplicate imports.
   - Build a FastAPI backend (`app.py`) with CORS middleware and endpoints (`POST /api/query`, `POST /api/ingest`, `GET /api/health`).

3. **Phase 4: Frontend API Integration & UI Polish**
   - Add API client service in React (`src/services/api.js`).
   - Connect `App.jsx` search & chat handlers to FastAPI backend `/api/query`.
   - Remove unused Lucide React icon imports and clean up Vite boilerplate CSS.
   - Add loading indicators, error toast notifications, and source citation links.

4. **Phase 5: Verification & Testing**
   - Add unit tests for RAG pipeline and FastAPI endpoints (`pytest`).
   - Verify end-to-end user query flow from React UI through FastAPI + ChromaDB + Groq LLM.
