import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.pdf_extract import extract_pages
from app.chunker import chunk_pages
from app.embed_index import EmbeddingIndex
from app.mcp_client import mcp_generate
from app.storage import save_index, load_index, ensure_data_dir


DATA_DIR = os.getenv("DATA_DIR", "/data")
ensure_data_dir(DATA_DIR)


app = FastAPI(title="PDF Contract QnA")
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


INDEXES = {} # doc_id -> EmbeddingIndex instance (keeps index in memory)


class IngestResponse(BaseModel):
  doc_id: str
  status: str
  pages: int


class QueryRequest(BaseModel):
  doc_id: str
  question: str
  top_k: int = 4


@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
  if not file.filename.lower().endswith(".pdf"):
    raise HTTPException(status_code=400, detail="Only PDF files are supported")


  doc_id = str(uuid.uuid4())
  doc_dir = os.path.join(DATA_DIR, doc_id)
  os.makedirs(doc_dir, exist_ok=True)
  pdf_path = os.path.join(doc_dir, file.filename)


  with open(pdf_path, "wb") as f:
    shutil.copyfileobj(file.file, f)


  pages = extract_pages(pdf_path)
  chunks = chunk_pages(pages)


  emb_index = EmbeddingIndex()
  emb_index.build_from_chunks(chunks)
  save_index(doc_dir, emb_index)
  INDEXES[doc_id] = emb_index


  return {"doc_id": doc_id, "status": "indexed", "pages": len(pages)}

@app.post("/query")
async def query(req: QueryRequest):
  doc_id = req.doc_id
  if doc_id not in INDEXES:
  # try to load from disk
    doc_dir = os.path.join(DATA_DIR, doc_id)
    if not os.path.exists(doc_dir):
      raise HTTPException(status_code=404, detail="Document not found")
    emb_index = load_index(doc_dir)
    INDEXES[doc_id] = emb_index
  else:
    emb_index = INDEXES[doc_id]


  top_k = req.top_k
  results = emb_index.search(req.question, top_k=top_k)


  # Build prompt
  context_lines = []
  for i, r in enumerate(results, start=1):
    snippet = r["text"].strip().replace("\n", " ")
    context_lines.append(f"[{i}] (Page {r['page']}) {snippet}")


  system_instructions = (
    "You are a contract assistant. Use ONLY the provided CONTEXT to answer the user's question. "
    "If the answer cannot be found in the context, reply: \"I don't know.\" "
    "Provide a concise 1-3 sentence answer. Then include a SOURCES section listing page numbers and short snippets used.\n\n")


  prompt = (system_instructions + 
           "CONTEXT:\n" + "\n".join(context_lines) + "\n\n" +
           f"Question: {req.question}\n\nAnswer:")


  mcp_resp = mcp_generate(prompt)
  answer_text = mcp_resp.get("text", "")


  return {
    "answer": answer_text,
    "sources": [{"page": r["page"], "snippet": r["text"]} for r in results],
    "used_chunks": [r["id"] for r in results],
  }