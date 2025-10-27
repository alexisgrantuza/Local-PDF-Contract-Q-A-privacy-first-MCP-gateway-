Nice — let’s fully flesh out the **Local PDF / Contract Q&A (privacy-first, MCP gateway)** project so you can build a working MVP in one day. I’ll give: goal, architecture, exact stack choices, step-by-step implementation plan with runnable snippets, folder layout, API design, prompt templates, privacy/security notes, testing checklist, and a tight 1-day timeline.

# 1) Project goal (one-sentence)

A privacy-first single-page app where a user uploads a PDF contract locally, the app extracts and indexes the contract text (locally), and a small LLM behind an MCP gateway answers natural-language questions using retrieved relevant chunks with citation snippets.

# 2) High-level architecture

1. **Frontend (web)** — upload PDF, ask question, show answer + source snippet(s). (React or Streamlit)
2. **Ingestion service (local)** — extract text from PDF, chunk, produce embeddings, store vector index (FAISS/Chroma).
3. **Search endpoint (local)** — accept query, embed query, retrieve top-k chunks from vector DB.
4. **MCP gateway call (hosted)** — send retrieved chunks + user question to the LLM via the MCP gateway (so the LLM runs remotely but never receives whole doc; only retrieved context), get final answer.
5. **Return & display** — frontend shows answer with snippet citations and confidence metadata.

# 3) Tech stack (recommended)

- Backend / ingestion & search: **Python** (fast to prototype)

  - PDF extraction: `pdfplumber` or `PyMuPDF` (`fitz`)
  - Chunking & embeddings: `sentence-transformers` (`all-MiniLM-L6-v2` or similar)
  - Vector DB: **FAISS** (local) or **Chroma** (file-backed)
  - Web server: **FastAPI** or Streamlit (Streamlit for fastest one-file UI)
  - Optional: `langchain` for glue code (but not required)

- LLM access: **MCP / hosted gateway** — simple HTTP API endpoint that proxies to the model you choose; treat as external LLM provider.
- Frontend: Streamlit (fast) or React + simple fetch (if you prefer separate UI)
- Containerization: optional `docker-compose` to run locally.

# 4) Privacy model

- **Local storage of PDF & vectors**: store locally (encrypted if persisted), or ephemeral in memory.
- **What is sent to LLM (MCP gateway)**: only _retrieved chunks_ relevant to the question + the question (never the full doc).
- **MCP settings**: set `log=false` or equivalent on gateway calls, and restrict gateway API keys to this app.
- **Redaction**: if documents include PHI you may add a pre-check to redact sensitive fields before embeddings or before sending contexts.

# 5) Deliverable

Single-page app where:

- User uploads a contract (PDF).
- App displays uploaded file name, index progress.
- User enters a question → app returns a short answer + source snippet(s) (with page numbers or chunk id).
- Optionally show “confidence” and top-k supporting snippets.

# 6) Implementation plan (step-by-step) — one-day friendly

## Prep (30–45 minutes)

1. Create project folder and virtualenv.
2. Install packages: `pip install fastapi uvicorn sentence-transformers faiss-cpu pdfplumber requests streamlit` (or `chromadb` instead of faiss).
3. Obtain MCP gateway API key / endpoint (or use any LLM endpoint).

## Step A — PDF → text (30–45 minutes)

- Extract text with `pdfplumber` or `PyMuPDF`.
- Also capture page numbers for citation.

### Example (Python)

```python
# pdf_extract.py
import pdfplumber

def extract_pages(path):
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"page": i, "text": text})
    return pages
```

## Step B — Chunking (15–30 minutes)

- Chunk by sliding window. Keep map of chunk_id → (page_start,page_end,text).
- Example: chunk size 800 tokens (or ~1000 chars), overlap 200 chars.

### Simple chunker

```python
def chunk_pages(pages, chunk_size=1200, overlap=200):
    chunks = []
    for p in pages:
        text = p["text"]
        i = 0
        while i < len(text):
            chunk = text[i:i+chunk_size]
            chunks.append({"page": p["page"], "text": chunk})
            i += chunk_size - overlap
    return chunks
```

## Step C — Embeddings + vector DB (30–45 minutes)

- Use `sentence-transformers` to embed each chunk.
- Index with FAISS or Chroma.

### Embedding + FAISS example

```python
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_chunks(chunks):
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    return np.array(embeddings).astype("float32")

# create faiss index
def build_index(embeddings):
    d = embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embeddings)
    return index
```

- Save chunk metadata mapping (IDs → page/text) with `pickle` or JSON.

## Step D — Search endpoint (10–20 minutes)

- FastAPI endpoint `/query`:

  - Accepts question text.
  - Embed question locally with same model.
  - Query FAISS for top_k (e.g., k=4).
  - Retrieve corresponding chunk texts and metadata.

### Example (search snippet)

```python
def search_query(index, q_text, chunks, top_k=4):
    q_emb = model.encode([q_text]).astype("float32")
    D, I = index.search(q_emb, top_k)
    results = [chunks[i] for i in I[0]]
    return results
```

## Step E — Call LLM via MCP gateway (10–20 minutes)

- Compose a prompt combining: short system instruction, retrieved chunks (with chunk ids/page numbers), and the user question.
- Send to MCP gateway endpoint (HTTP POST) and return the model reply.

### Example payload (pseudocode)

```
POST https://mcp-gateway.example/v1/generate
Headers: Authorization: Bearer <API_KEY>
Body: {
  "model": "small-llm-1",
  "input": "<system prompt + context chunks + question>",
  "max_tokens": 300,
  "logprobs": null,
  "user": "<user id>",
  "metadata": {"doc_id": "..."}
}
```

### Prompt template (concise & safe)

```
System: You are a contract assistant. Use ONLY the supplied context to answer. Provide a short answer and list which pages or snippets you used.

Context:
[1] (Page 3) "Lease term is 12 months..."
[2] (Page 5) "Late fee 2% per month..."
...

Question: <user question>

Answer concisely with a 1-2 sentence answer. Then include "SOURCES:" with the chunk/page references used.
```

**Important**: always instruct the LLM to cite specific chunks/pages and to say "I don't know" if not answerable.

## Step F — Frontend (Streamlit) (30–45 minutes)

- Quick Streamlit UI:

  - File uploader → triggers ingestion.
  - Text input for question → hits backend `/query` endpoint.
  - Show answer, and below it show supporting snippets with page numbers and “copy” button.

### Streamlit minimal

```python
# app.py
import streamlit as st
import requests

uploaded = st.file_uploader("Upload contract (PDF)", type="pdf")
if uploaded:
    # save to temp, call /ingest or ingest inline
    st.write("Indexed. Ask a question:")
    q = st.text_input("Question")
    if q:
        resp = requests.post("http://localhost:8000/query", json={"question": q})
        data = resp.json()
        st.write("Answer:", data["answer"])
        for s in data["sources"]:
            st.markdown(f"**Page {s['page']}**: {s['text'][:300]}...")
```

## Step G — Test & polish (30–60 minutes)

- Upload sample contracts (NDAs, lease, employment) and try questions.
- Check citations, ensure LLM does not hallucinate (force “use only supplied context”).
- Add UI progress indicators for indexing.

# 7) Folder structure (suggested)

```
pdf-qna/
├─ backend/
│  ├─ app.py            # FastAPI app: /ingest, /query endpoints
│  ├─ pdf_extract.py
│  ├─ chunker.py
│  ├─ embed_index.py
│  └─ data/             # saved indices and metadata
├─ frontend/
│  └─ app.py            # streamlit single-file UI (or react)
├─ requirements.txt
└─ docker-compose.yml
```

# 8) API design (minimal)

- `POST /ingest` — multipart upload `{file: pdf}` → returns `{doc_id, status}`
- `POST /query` — `{doc_id, question}` → returns `{answer, sources:[{page, snippet, chunk_id}], used_chunks: [...]}`

# 9) Example flow (end-to-end)

1. User uploads `contract.pdf` → backend extracts N pages, chunks them, computes embeddings, builds FAISS index, stores metadata → returns `doc_id`.
2. User submits question "When does the lease end?" → backend embeds query, finds top 3 chunks, builds prompt with those chunks, calls MCP gateway for answer.
3. Gateway returns: "Lease term is 12 months starting Jan 1, 2025 and ends Dec 31, 2025." Backend returns this plus sources like `(page 1, chunk 2)`.

# 10) Safety & anti-hallucination rules

- Always include a system instruction: **“Only use the provided context; if answer not in context, say 'I don't know'.”**
- Limit response length and require explicit citations.
- Optionally verify factual claims: run a simple exact-match search on citations for phrases that LLM claims.

# 11) Quick code snippets (packable)

### FastAPI skeleton (very short)

```python
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
app = FastAPI()

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    # save file, extract pages, chunk, embed, index
    return {"doc_id": "doc123", "status":"indexed"}

class Q(BaseModel):
    doc_id: str
    question: str

@app.post("/query")
def query(q: Q):
    # embed question, search index, call MCP gateway, return answer + sources
    return {"answer":"...", "sources":[...]}
```

### MCP gateway call (requests)

```python
import requests, os
MCP_URL = "https://mcp-gateway.example/v1/generate"
API_KEY = os.environ.get("MCP_API_KEY")

def call_mcp(prompt):
    payload = {"model":"small-llm-1","input":prompt,"max_tokens":300}
    r = requests.post(MCP_URL, json=payload, headers={"Authorization":f"Bearer {API_KEY}"})
    return r.json()["text"]
```

# 12) 1-day timeline (hour-by-hour realistic)

- 00:00–00:30 — scaffold repo, install deps, create virtualenv.
- 00:30–01:15 — implement PDF extraction + test on sample.
- 01:15–02:00 — implement chunker + metadata mapping.
- 02:00–03:00 — integrate sentence-transformers + build FAISS index; save index.
- 03:00–03:30 — add search endpoint to load index and return top-k chunks.
- 03:30–04:00 — craft simple prompt template and integrate MCP gateway call.
- 04:00–05:00 — build Streamlit UI + wire to backend endpoints.
- 05:00–05:30 — test on sample contracts, tweak chunk size and system prompt.
- 05:30–06:00 — add small polish: citation display, index progress, environment variables, README.

(If using the single-file Streamlit approach you can shave time off — do ingestion in-process so you avoid separate FastAPI wiring.)

# 13) Testing & validation checklist

- [ ] Indexing works for multi-page PDF and preserves page numbers.
- [ ] Query returns top-k supporting snippets and page numbers.
- [ ] LLM refuses to answer when context doesn't contain answer (or says “I don't know”).
- [ ] No full document is ever sent to MCP gateway — only retrieved chunks.
- [ ] API keys set via env vars, not committed.
- [ ] If saving indices to disk, encrypted or in temp folder with TTL.

# 14) Optional improvements (post-MVP)

- Add **semantic search re-ranking**: call LLM for cross-encoder reranking of retrieved chunks (improves accuracy).
- Integrate **document OCR** (Tesseract) for scanned PDFs.
- Add **access control** / per-user isolation.
- Add **explainability**: highlight phrases in the original PDF viewer via page coordinates.
- Add **browser extension** to ask questions while viewing the PDF in browser.

# 15) Quick pitfalls & how to avoid them

- **Hallucinations** — fix by strict system prompts + require citations.
- **Poor retrieval** — tune chunk size and overlap; store page numbers; consider sentence-level chunking for legal docs.
- **Slow embeddings** — cache embeddings per doc; run offline batching.
- **Large PDFs** — limit file size for MVP (e.g., under 10MB).

# 16) Final checklist to hand you a working repo

If you want, I’ll immediately scaffold a ready-to-run **single-file Streamlit app** or a small FastAPI+Streamlit repo that:

- ingests a PDF,
- builds FAISS index locally with `sentence-transformers`,
- runs queries and calls a configurable MCP gateway,
- displays answers with sources.

Which do you prefer right now — **Streamlit single-file** (fastest) or **FastAPI backend + React frontend** (more production-y)? I’ll generate the starter repo code instantly.
