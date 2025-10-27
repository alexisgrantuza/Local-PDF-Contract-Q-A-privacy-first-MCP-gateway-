import uuid


def chunk_pages(pages, chunk_size=1200, overlap=200):
  chunks = []
  for p in pages:
    text = p.get("text", "")
    start = 0
    L = len(text)
    while start < L:
      end = start + chunk_size
      chunk_text = text[start:end]
      if not chunk_text.strip():
        break
      chunk_id = str(uuid.uuid4())
      chunks.append({"id": chunk_id, "page": p.get("page"), "text": chunk_text})
      start = end - overlap
  return chunks