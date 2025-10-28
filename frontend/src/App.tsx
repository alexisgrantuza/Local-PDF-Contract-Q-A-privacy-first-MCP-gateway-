import { useState } from "react";
import { ApiService } from "./server/api";
import type { IngestResponse } from "./server/api";
import type { AppState } from "./types/index";
import "./App.css";

function App() {
  const [state, setState] = useState<AppState>({
    docId: null,
    isLoading: false,
    error: null,
    uploadProgress: null,
    query: "",
    response: null,
    isQuerying: false,
  });

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setState((prev) => ({ ...prev, error: "Please upload a PDF file" }));
      return;
    }

    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
      uploadProgress: "Uploading and processing PDF...",
      response: null,
    }));

    try {
      const result: IngestResponse = await ApiService.uploadPdf(file);
      setState((prev) => ({
        ...prev,
        docId: result.doc_id,
        isLoading: false,
        uploadProgress: `Successfully processed ${result.pages} pages!`,
        error: null,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : "Upload failed",
        uploadProgress: null,
      }));
    }
  };

  const handleQuery = async () => {
    if (!state.docId || !state.query.trim()) return;

    setState((prev) => ({ ...prev, isQuerying: true, error: null }));

    try {
      const result = await ApiService.queryDocument({
        doc_id: state.docId,
        question: state.query,
        top_k: 4,
      });
      setState((prev) => ({ ...prev, response: result, isQuerying: false }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isQuerying: false,
        error: error instanceof Error ? error.message : "Query failed",
      }));
    }
  };

  const resetApp = () => {
    setState({
      docId: null,
      isLoading: false,
      error: null,
      uploadProgress: null,
      query: "",
      response: null,
      isQuerying: false,
    });
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>📄 PDF Contract Q&A</h1>
        <p>Upload a PDF contract and ask questions about its contents</p>
      </header>

      <main className="app-main">
        {!state.docId ? (
          <div className="upload-section">
            <div className="upload-area">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                disabled={state.isLoading}
                id="pdf-upload"
                style={{ display: "none" }}
              />
              <label htmlFor="pdf-upload" className="upload-button">
                {state.isLoading ? "Processing..." : "📁 Upload PDF Contract"}
              </label>
            </div>

            {state.uploadProgress && (
              <div className="progress-message">{state.uploadProgress}</div>
            )}
          </div>
        ) : (
          <div className="qa-section">
            <div className="document-info">
              <h3>✅ Document Ready</h3>
              <p>Document ID: {state.docId}</p>
              <button onClick={resetApp} className="reset-button">
                Upload New Document
              </button>
            </div>

            <div className="query-section">
              <div className="query-input">
                <textarea
                  value={state.query}
                  onChange={(e) =>
                    setState((prev) => ({ ...prev, query: e.target.value }))
                  }
                  placeholder="Ask a question about the contract..."
                  rows={3}
                  disabled={state.isQuerying}
                />
                <button
                  onClick={handleQuery}
                  disabled={!state.query.trim() || state.isQuerying}
                  className="query-button"
                >
                  {state.isQuerying ? "🤔 Thinking..." : "❓ Ask Question"}
                </button>
              </div>
            </div>

            {state.response && (
              <div className="response-section">
                <div className="answer">
                  <h3>💡 Answer</h3>
                  <div className="answer-text">{state.response.answer}</div>
                </div>

                <div className="sources">
                  <h3>📚 Sources</h3>
                  {state.response.sources.map((source, index) => (
                    <div key={index} className="source-item">
                      <div className="source-header">
                        <span className="page-number">Page {source.page}</span>
                        <button
                          className="copy-button"
                          onClick={() =>
                            navigator.clipboard.writeText(source.snippet)
                          }
                        >
                          📋 Copy
                        </button>
                      </div>
                      <div className="source-text">{source.snippet}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {state.error && <div className="error-message">❌ {state.error}</div>}
      </main>
    </div>
  );
}

export default App;
