import os
from app.embed_index import EmbeddingIndex




def ensure_data_dir(path: str):
  os.makedirs(path, exist_ok=True)




def save_index(doc_dir: str, emb_index: EmbeddingIndex):
  emb_index.save(doc_dir)




def load_index(doc_dir: str) -> EmbeddingIndex:
  return EmbeddingIndex.load(doc_dir)