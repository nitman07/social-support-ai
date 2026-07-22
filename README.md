# Social Support AI

AI-powered workflow automation for government social security departments. Processes financial assistance applications in **minutes** instead of days using local LLMs, ML scoring, and multi-agent orchestration.

## Quick Start

```bash
git clone https://github.com/nitman07/social-support-ai.git
cd social-support-ai
cp .env.example .env
make dev          # start all 8 Docker services
make seed         # populate 4 databases with 100 synthetic applicants
make train        # train the Random Forest eligibility model
```

**Access:**
- **API + Swagger UI:** http://localhost:8001/docs
- **Streamlit Dashboard:** http://localhost:8501 (login: `admin` / `admin123`)
- **Redoc:** http://localhost:8001/redoc

## Architecture

```
                      ┌─────────────────────────────┐
                      │    Streamlit Dashboard      │
                      │   (localhost:8501)           │
                      └──────────────┬──────────────┘
                                     │ HTTP (JWT)
                      ┌──────────────▼──────────────┐
                      │     FastAPI REST API        │
                      │   (localhost:8001)           │
                      │   - Auth (JWT)              │
                      │   - Applications CRUD       │
                      │   - Workflow Trigger        │
                      │   - HITL Signoff            │
                      └──────────────┬──────────────┘
                                     │
                      ┌──────────────▼──────────────┐
                      │   LangGraph 7-Node Workflow │
                      │   (asyncio background task) │
                      │                             │
                      │  intake → ocr → validation │
                      │     → knowledge → eligib.  │
                      │     → decision → recomm.   │
                      └──────┬─────┬────┬─────┬────┘
                             │     │    │     │
                 ┌───────────┘     │    │     └───────────┐
                 ▼                 ▼    ▼                 ▼
           PostgreSQL          MongoDB Qdrant          Neo4j
        (applications,       (OCR text,  (policy      (entity
         assessments,         document   embeddings)   graph)
         users, audit)        images)
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.11+ | Async-native, AI/ML ecosystem |
| API | FastAPI | Async endpoints, Pydantic validation, auto-docs |
| Workflow | LangGraph | Stateful 7-node agent graph with checkpointing |
| ML | scikit-learn (Random Forest) | Eligibility scoring + SHAP explainability |
| LLM | Ollama (Qwen2.5:0.5b) | Local decision rationale generation |
| Frontend | Streamlit | Admin dashboard + process UI |
| Auth | JWT (HS256) + PBKDF2 | Stateless authentication |
| Container | Docker Compose | 8 services, single-command start |

## Project Structure

```
social-support-ai/
├── backend/
│   ├── api/v1/               # REST endpoints (auth, applications, decisions)
│   ├── core/                 # Config, DI, logging, metrics, observability
│   ├── database/
│   │   ├── postgres/         # ORM models, Alembic, repositories
│   │   ├── mongodb/          # Document store (Motor + GridFS)
│   │   ├── qdrant/           # Vector store client
│   │   └── neo4j/            # Graph store client
│   ├── domain/               # Entities, value objects, events, ports
│   ├── ml/                   # Feature engineering, rules, model, pipeline
│   ├── rag/                  # Policy retriever (Qdrant + Ollama embeddings)
│   ├── services/             # Auth (JWT), LLM (Ollama), audit
│   └── workflows/            # LangGraph state, nodes, edges, graph
├── frontend/
│   ├── streamlit_app.py      # Entry point (login + navigation)
│   ├── api_client.py         # Typed httpx API wrapper
│   └── utils/               # Page modules (dashboard, applications, etc.)
├── configs/                  # Feature definitions (YAML)
├── data/                     # Model artifacts (eligibility_rf.pkl)
├── docker/                   # Shared Dockerfile
├── docs/
│   ├── decisions/            # Architecture Decision Records (6 ADRs)
│   ├── architecture-m*.mmd  # Mermaid flow diagrams (M2–M6)
│   └── solution-summary.md  # Comprehensive solution overview
└── tests/                    # Unit + integration tests
    ├── unit/                 # 21 tests (domain, ML, auth)
    └── integration/          # API + audit + metrics tests
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login` | — | Login, returns JWT |
| GET | `/api/v1/auth/me` | JWT | Current user profile |
| GET | `/api/v1/applications` | JWT | Paginated list (status filter) |
| GET | `/api/v1/applications/{id}` | JWT | Full application detail |
| POST | `/api/v1/applications/{id}/process` | JWT | Trigger workflow (202 Accepted) |
| GET | `/api/v1/applications/{id}/status` | JWT | Workflow progress + decision |
| GET | `/api/v1/applications/{id}/flags` | JWT | Inconsistency flags |
| POST | `/api/v1/applications/{id}/resolve-flag/{fid}` | JWT | Accept/reject flag |
| POST | `/api/v1/applications/{id}/signoff` | JWT | Human approve/decline |
| POST | `/api/v1/applications/{id}/resume` | JWT | Resume paused workflow |
| GET | `/health` | — | Health check |
| GET | `/metrics` | — | Request count + durations |

Full interactive docs at http://localhost:8001/docs

## Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start all 8 Docker services |
| `make down` | Stop all services |
| `make seed` | Populate databases with 100 synthetic applicants |
| `make train` | Train Random Forest eligibility model |
| `make test` | Run tests with coverage |
| `make lint` | Ruff code quality check |
| `make clean` | Clean Python caches |

## Architecture Decisions

Six ADRs document key design choices:
1. [Clean Architecture](docs/decisions/001-clean-architecture.md)
2. [LangGraph over CrewAI](docs/decisions/002-langgraph-over-crewai.md)
3. [Local LLM Strategy](docs/decisions/003-local-llm-strategy.md)
4. [Polyglot Persistence](docs/decisions/004-polyglot-persistence.md)
5. [ML-LLM Separation](docs/decisions/005-ml-llm-boundary.md)
6. [Agent Observability](docs/decisions/006-agent-observability.md)

## Design Highlights

- **ML owns the score, LLM owns the explanation** — Random Forest computes deterministic eligibility; LLM only writes rationale. Legally defensible.
- **7-node LangGraph workflow** with 2 HITL checkpoints (validation flags + decision signoff). State is checkpointed at every node.
- **Polyglot persistence** — PostgreSQL (ACID), MongoDB (documents), Qdrant (vectors), Neo4j (graph). Each optimized for its query pattern.
- **Graceful degradation** — If Ollama is down, templated rationale. If ML model not loaded, rules-only scoring. A single failure never crashes the workflow.
- **202 + async pattern** — Workflow runs as background task; client polls status. API stays responsive.
- **No cloud dependencies** — All models run locally via Ollama. No citizen data leaves the premises.

## End-to-End Example

Applicant *Samantha Duncan* processed through the full workflow:

```
           Input                              ↓                          Output
┌─────────────────────────┐          ┌──────────────────┐      ┌──────────────────────────┐
│ Monthly Income: AED 13,923│   →     │ ML Score: 0.986  │  →   │ Decision: ✅ Approved     │
│ Family Size: 3           │         │ Confidence: 0.986 │      │ LLM Rationale: Generated  │
│ Employed: 19 yrs         │         │ SHAP Top-3:       │      │ Recommendation:           │
│ Total Assets: AED 60K    │         │  income, liab.,   │      │  UAE Digital Skills Prog. │
│ Total Liab.: AED 43K     │         │  assets           │      │                          │
│ No inconsistencies       │         │                   │      │                          │
└─────────────────────────┘          └──────────────────┘      └──────────────────────────┘
```

The workflow completed in ~98 seconds across all 7 LangGraph nodes with Ollama generating the decision rationale locally.

## License

MIT
