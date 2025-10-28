import type { QueryResponse } from "../server/api";

export interface AppState {
  docId: string | null;
  isLoading: boolean;
  error: string | null;
  uploadProgress: string | null;
  query: string;
  response: QueryResponse | null;
  isQuerying: boolean;
}
