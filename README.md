# Social Support AI

AI-powered workflow automation platform for government social security departments. Automates financial assistance application processing from days to minutes using local LLMs, ML, and multi-agent orchestration.

## Architecture

```
Applicant → [Streamlit UI] → [FastAPI] → [LangGraph Agents] → [Decision]
                ↑                            ↑
          8 Agent Orchestration    ML (Random Forest) + LLM (Mistral)
```

### Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Gateway | FastAPI | REST endpoints, auth, validation |
| Workflow Engine | LangGraph | Multi-agent orchestration with checkpointing |
| ML Pipeline | Scikit-learn (Random Forest) | Eligibility scoring with SHAP explainability |
| RAG | Qdrant + Ollama | Policy retrieval for grounded decisions |
| Document Processing | PaddleOCR + PyMuPDF | Text extraction from images, PDFs, Excel |
| Frontend | Streamlit | Applicant portal + admin dashboard |
| Observability | LangFuse | Agent tracing, LLM monitoring, audit |

### Data Stores

- **PostgreSQL** — Application records, decisions, audit logs (ACID)
- **MongoDB** — Raw documents, OCR output, chat history
- **Qdrant** — Policy embeddings, program vectors
- **Neo4j** — Entity relationships (applicant, family, employers, assets)

## Quick Start

```bash
# Prerequisites: Docker, Docker Compose

# Clone and start
git clone https://github.com/nitman07/social-support-ai.git
cd social-support-ai
make dev

# Seed synthetic data
make seed

# Access
# API:      http://localhost:8000/docs
# Frontend: http://localhost:8501
```

## Development

```bash
make dev       # Start all services
make test      # Run tests
make lint      # Code quality
make seed      # Seed databases
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](http://localhost:8000/docs)
- [Architecture Decisions](docs/decisions/)

## License

MIT
