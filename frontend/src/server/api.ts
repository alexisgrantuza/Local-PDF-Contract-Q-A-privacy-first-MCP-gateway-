// API service for backend communication
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export interface IngestResponse {
  doc_id: string;
  status: string;
  pages: number;
}

export interface QueryRequest {
  doc_id: string;
  question: string;
  top_k?: number;
}

export interface QueryResponse {
  answer: string;
  sources: Array<{
    page: number;
    snippet: string;
  }>;
  used_chunks: string[];
}

export class ApiService {
  private static async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;

    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  static async uploadPdf(file: File): Promise<IngestResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/ingest`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload Error: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  static async queryDocument(request: QueryRequest): Promise<QueryResponse> {
    return this.request<QueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }
}
