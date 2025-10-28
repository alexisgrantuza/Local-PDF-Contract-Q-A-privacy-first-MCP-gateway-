from pydantic import BaseModel


class IngestResponse(BaseModel):
  doc_id: str
  status: str
  pages: int


class QueryRequest(BaseModel):
  doc_id: str
  question: str
  top_k: int = 4