# PDF Contract Q&A Frontend

A modern React frontend for the PDF Contract Q&A system.

## Features

- 📄 **PDF Upload**: Drag & drop or click to upload PDF contracts
- 🤖 **AI Q&A**: Ask natural language questions about contract contents
- 📚 **Source Citations**: View exact page references and snippets
- 🎨 **Modern UI**: Beautiful, responsive design with smooth animations
- 🔒 **Privacy-First**: Only relevant chunks sent to AI, never full documents

## Quick Start

### Development Mode

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Start development server:

```bash
npm run dev
```

3. Open [http://localhost:5173](http://localhost:5173)

### Production Build

```bash
npm run build
npm run preview
```

## Environment Variables

Create a `.env` file in the root directory:

```env
# Hugging Face Configuration
HF_TOKEN=your_huggingface_token_here
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct

# Embedding Model (optional)
EMBED_MODEL=all-MiniLM-L6-v2
```

## Docker Deployment

Use the provided `docker-compose.yaml`:

```bash
# Copy environment variables
cp .env.example .env
# Edit .env with your HF_TOKEN

# Start services
docker-compose up --build
```

Access the app at [http://localhost:3000](http://localhost:3000)

## API Integration

The frontend communicates with the backend via:

- `POST /ingest` - Upload and process PDF files
- `POST /query` - Ask questions about uploaded documents

See `src/api.ts` for the complete API interface.
