## Features

### 1. **Multi-Document PDF Processing**
   - Upload multiple PDF files simultaneously
   - Extract text from PDFs with PyPDF2
   - Semantic section detection (Abstract, numbered sections, etc.)

### 2. **Intelligent Text Chunking**
   - RecursiveCharacterTextSplitter with 1000-char chunks and 200-char overlap
   - Semantic section-based splitting (preserves document structure)
   - Duplicate detection using SHA-256 hashing (prevents re-processing)

### 3. **Hybrid Retrieval System**
   - **Semantic Search**: FAISS vector store similarity search (k=10)
   - **Keyword Extraction**: Extracts error codes, numbers, uppercase tokens (ORA, HTTP, etc.)
   - **Keyword Re-ranking**: Filters and ranks results by keyword score
   - Fallback mechanism for missing keyword hits

### 4. **Vector Store Management**
   - Persistent FAISS vector store with incremental updates
   - Chunk hashing to avoid duplication
   - Automatic deletion of stale chunks when documents change
   - Support for metadata tracking (PDF hash, chunk hash, source file)

### 5. **Prompt Engineering**
   - Strict document-grounded prompts (no external knowledge allowed)
   - Context-based Q&A with exact value reproduction
   - Guard rails: Returns "The document does not contain this information" when needed

### 6. **LLM Integration**
   - Google Gemini 2.5 Flash Lite model
   - Zero temperature (deterministic responses)
   - Google Generative AI embeddings

### 7. **Streamlit UI**
   - Sidebar for PDF uploads with multi-file support
   - Text input for user queries
   - Real-time processing feedback (success/info messages)
   - Response display with BlobSha 80ce885edb71141dde3bff32b2dbe97c2e5c4481
