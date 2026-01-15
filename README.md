# Product Manual Bot

An AI-driven Product Manual Bot using RAG (Retrieval-Augmented Generation) to answer questions about product manuals with accurate, cited responses.

## Architecture

The system uses:
- **Backend**: FastAPI with async support
- **LLM**: Groq via LangChain
- **Vector DB**: Neon DB (PostgreSQL with pgvector)
- **Frontend**: Streamlit with streaming support
- **Text Splitting**: Recursive character splitting with ParentDocumentRetriever pattern

## Features

- **Fine-grained Retrieval**: Child chunks (200-400 chars) for precise search
- **Context-rich Answers**: Parent chunks (2000 chars) for complete context
- **Streaming Responses**: Real-time token-by-token generation
- **Source Citations**: Transparent display of source documents
- **Background Processing**: Async document ingestion

## Prerequisites

- Python 3.12+
- Poetry for dependency management
- Neon DB account with PostgreSQL database
- Groq API key
- Docker (optional, for containerized deployment)

## Setup

### 1. Install Dependencies

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
NEON_DB_URL=postgresql://user:password@host:5432/database?sslmode=require
```

### 3. Set Up Database

Ensure your Neon DB database has the pgvector extension enabled. The application will automatically create the required tables on first run.

### 4. Run the Application

#### Development Mode

**Backend:**
```bash
poetry run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
poetry run streamlit run src/ui/app.py --server.port 8501
```

#### Docker Compose

```bash
docker-compose up --build
```

This will start both backend (port 8000) and frontend (port 8501).

## Usage

1. **Upload Documents**: Use the sidebar in the Streamlit UI to upload PDF product manuals
2. **Ask Questions**: Type your question in the chat interface
3. **View Sources**: Expand the "View Sources" section to see which documents were used

## API Endpoints

### Health Check
```
GET /health
```

### Upload Document
```
POST /api/v1/ingestion/upload
Content-Type: multipart/form-data
Body: file (PDF)
```

### Chat (Streaming)
```
POST /api/v1/chat/stream
Content-Type: application/json
Body: {
  "messages": [{"role": "user", "content": "..."}],
  "query": "your question"
}
```

### Chat (Non-streaming)
```
POST /api/v1/chat/chat
Content-Type: application/json
Body: {
  "messages": [{"role": "user", "content": "..."}],
  "query": "your question"
}
```

## Testing

```bash
# Run unit tests
poetry run pytest tests/unit/ -v

# Run integration tests
poetry run pytest tests/integration/ -v

# Run all tests
poetry run pytest tests/ -v
```

## Code Quality

```bash
# Lint code
poetry run ruff check src/ tests/

# Format code
poetry run ruff format src/ tests/
```

## Project Structure

```
product-manual-bot/
├── src/
│   ├── app/              # FastAPI backend
│   │   ├── api/          # API routes
│   │   ├── core/         # Configuration
│   │   ├── services/     # Business logic
│   │   └── schemas/      # Pydantic models
│   └── ui/               # Streamlit frontend
├── tests/                # Test suite
├── data/                 # Local data storage
└── pyproject.toml        # Poetry configuration
```

## Development Standards

- **Dependency Management**: Poetry with lockfile
- **Code Quality**: Ruff for linting and formatting
- **Testing**: pytest with unit and integration tests
- **Type Safety**: Pydantic models for all data contracts
- **Async Architecture**: FastAPI async/await throughout
