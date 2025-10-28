import os
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


class EmbeddingIndex:
  def __init__(self):
    self.model = SentenceTransformer(MODEL_NAME)
    self.index = None
    self.metadatas = [] # list of chunk dicts


  def build_from_chunks(self, chunks):
    texts = [c["text"] for c in chunks]
    embeddings = self.model.encode(texts, show_progress_bar=False)
    emb = np.array(embeddings).astype('float32')
    d = emb.shape[1]
    self.index = faiss.IndexFlatL2(d)
    self.index.add(emb)
    self.metadatas = chunks


  def search(self, query, top_k=4):
    q_emb = self.model.encode([query]).astype('float32')
    D, I = self.index.search(q_emb, top_k)
    results = []
    for idx in I[0]:
      if idx < 0 or idx >= len(self.metadatas):
        continue
      results.append(self.metadatas[idx])
    return results


  # serialization helpers
  def save(self, path):
    os.makedirs(path, exist_ok=True)
    # save index
    faiss.write_index(self.index, os.path.join(path, "index.faiss"))
    # save metadatas
    np.save(os.path.join(path, "metadatas.npy"), np.array(self.metadatas, dtype=object), allow_pickle=True)


  @classmethod
  def load(cls, path):
    inst = cls()
    inst.index = faiss.read_index(os.path.join(path, "index.faiss"))
    inst.metadatas = list(np.load(os.path.join(path, "metadatas.npy"), allow_pickle=True))
    inst.model = SentenceTransformer(MODEL_NAME)
    return inst