# Social Support AI — Solution Summary

## 1. Problem Statement

Government social security departments process thousands of financial assistance applications manually. Each application requires document verification, cross-referencing with multiple databases, eligibility assessment, and final approval — currently taking **3-7 days per application**. This system automates the entire workflow from application intake to final decision in **under 2 minutes**.

## 2. System Overview

```
Applicant → [Streamlit UI] → [FastAPI REST API] → [LangGraph 7-Node Workflow] → [Decision]
                              ↓                        ↓
                         PostgreSQL               ML Model (RF)
                         MongoDB               + LLM (Qwen2.5)
                         Qdrant                + Rules Engine
                         Neo4j                 + RAG (Policy Retrieval)
```

## 3. Architecture

### Clean Architecture Layers
- **Domain** — Pure Python dataclasses for `Application`, `Applicant`, `Assessment`, 10 domain events, value objects (`Address`, `Money`, `DocumentMetadata`)
- **Ports** — Abstract interfaces: `IApplicationRepository`, `IMLService`, `ILLMService`
- **Infrastructure** — FastAPI, SQLAlchemy (async), Motor (MongoDB), Qdrant client, Neo4j driver, LangGraph, Ollama

### Polyglot Persistence
| Database | Data | Access Pattern |
|----------|------|----------------|
| PostgreSQL | Applications, assessments, users, audit logs, all extracted data | ACID transactions, relational queries |
| MongoDB | Raw OCR text, document images (GridFS) | Schema-less storage, file streaming |
| Qdrant | Policy embeddings (768-dim) | Vector similarity search |
| Neo4j | Entity relationship graph | Cypher graph traversal |

## 4. Multi-Agent Workflow (LangGraph + ReAct)

The workflow follows a **ReAct** (Reasoning + Acting) pattern — each agent node observes state, reasons about it, and acts by producing new state. 7 nodes in sequence, with 2 HITL checkpoints:

```
START → intake → ocr → validation → knowledge → eligibility → decision → recommendation → END
                              ↓                            ↓
                      human_review (HITL)           human_signoff (HITL)
```

- **intake_node**: Load application + documents from PostgreSQL
- **ocr_node**: Process each document, save to MongoDB
- **validation_node**: Cross-document inconsistency detection (hard + soft flags)
- **knowledge_node**: Embed query → Qdrant policy search → top-3 policy context
- **eligibility_node**: Rules engine (5 rules) → Random Forest scoring → SHAP explainability
- **decision_node**: LLM generates natural-language rationale from ML score + policies
- **recommendation_node**: Generate personalized program recommendations

## 5. ML Pipeline

### Why Random Forest?

Random Forest was chosen over deep learning or gradient-boosted trees for this government use case:

| Requirement | How RF meets it |
|-------------|----------------|
| **Interpretability** | SHAP TreeExplainer provides per-feature contribution per prediction. Auditors can understand why any decision was made. |
| **Tabular data** | 8 structured features (income, family size, assets, etc.) — RF handles mixed scales without normalization. |
| **Missing values** | RF can work with incomplete data; split thresholds naturally handle nulls during inference. |
| **Class imbalance** | `class_weight='balanced'` adjusts for ~15% ineligible applicants without manual resampling. |
| **Low data regime** | 100–1000 records is enough for RF to converge; deep learning would require 10× more. |
| **Non-linear interactions** | Captures interactions like `liability_to_income_ratio × family_size` without manual feature engineering. |

### Pipeline Details

- **8 features**: monthly_income, family_size, years_employed, total_assets, total_liabilities, liability_to_income_ratio, has_inconsistencies, num_documents
- **5 business rules**: 4 hard blockers (income, assets, debt ratio, minimum income) + 1 soft flag
- **Model**: Random Forest (200 trees, max_depth=10, class_weight='balanced'); 80/20 stratified split
- **Explainability**: SHAP TreeExplainer — top 3 features per prediction with marginal contribution values
- **Fallback**: If model not loaded, rules-only scoring; workflow never crashes

## 6. API Layer

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | JWT authentication (HS256, 15min expiry) |
| `/api/v1/auth/me` | GET | Current user profile |
| `/api/v1/applications` | GET | Paginated list with status filter |
| `/api/v1/applications/{id}` | GET | Full detail (applicant, docs, assessment, flags, recs) |
| `/api/v1/applications/{id}/process` | POST | Trigger workflow (202 Accepted, async) |
| `/api/v1/applications/{id}/status` | GET | Poll workflow progress |
| `/api/v1/applications/{id}/flags` | GET | List inconsistencies |
| `/api/v1/applications/{id}/resolve-flag/{flag_id}` | POST | Accept/reject flag |
| `/api/v1/applications/{id}/signoff` | POST | Human approve/decline |
| `/api/v1/applications/{id}/resume` | POST | Resume paused workflow |

## 7. Frontend (Streamlit Dashboard)

4 pages:
1. **Dashboard** — Metric cards (total/draft/approved/declined), recent applications
2. **Applications** — Filterable table with pagination, Detail + Process buttons
3. **Process** — Select draft app → Start Workflow → Live status polling until decision
4. **Admin** — Flag Queue tab (accept/reject inconsistencies), Awaiting Review tab (approve/decline/resume)

## 8. Observability

- **LangFuse**: `@trace_node` decorator on all 7 nodes; traces input/output/duration/errors
- **Audit Logs**: Every state transition logged to `audit_logs` table (action, actor, details JSONB)
- **Metrics**: `GET /metrics` — request count, average/total duration

## 9. Tech Stack

| Category | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.11+ | AI/ML ecosystem, async support |
| API Framework | FastAPI | Async-native, auto-docs, Pydantic validation |
| Workflow Engine | LangGraph | Stateful graphs, checkpointing, HITL |
| ML | scikit-learn (Random Forest) | Interpretable, low data requirements |
| LLM | Ollama (Qwen2.5:0.5b) | Local inference, data sovereignty |
| Frontend | Streamlit | Fast prototyping, Python-only |
| Databases | PostgreSQL + MongoDB + Qdrant + Neo4j | Polyglot per query pattern |
| Auth | JWT (HS256) + PBKDF2-SHA256 | Stateless, no session store |
| Containerization | Docker Compose | 8 services, single `make dev` |

## 10. Setup & Deployment

```bash
# Prerequisites: Docker, Docker Compose, Git

git clone https://github.com/nitman07/social-support-ai.git
cd social-support-ai
cp .env.example .env    # review and adjust if needed
make dev                # start all 8 services (~2 min)
make seed               # populate databases
make train              # train ML model

# Access:
# API + Swagger:         http://localhost:8001/docs
# Streamlit Dashboard:   http://localhost:8501
# Login:                 admin / admin123

# Run tests:
make test               # 20 unit tests + integration tests

# Stop:
make down
```

## 11. Key Design Decisions

1. **ML ≠ LLM** — ML computes scores deterministically; LLM only explains. Legal defensibility.
2. **Clean Architecture** — Framework independence for 5+ year government system lifespan.
3. **LangGraph over CrewAI** — Stateful graphs with checkpointing for HITL workflows.
4. **Polyglot Persistence** — 4 databases optimized for specific query patterns.
5. **Local LLM only** — Data sovereignty; no citizen data sent to cloud providers.
6. **Async everywhere** — All DB drivers async; workflow runs as background task.
7. **Versioned API** — `/api/v1/` prefix allows coexistence of future API versions.

## 12. Future Improvements

| Area | Improvement | Priority |
|------|-------------|----------|
| Scale | Kubernetes deployment with Helm | High |
| Scale | Celery workers for agent execution | High |
| Security | OAuth2/OIDC integration | High |
| ML | Online learning from human decisions | Medium |
| RAG | Multi-language (Arabic) policy retrieval | Medium |
| Frontend | React/Vue SPA replacing Streamlit | Low |
| Observability | Grafana dashboards for Prometheus metrics | Low |
