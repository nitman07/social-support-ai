# Implementation Roadmap

## Milestone Overview

```
Milestone 0: Foundation (Day 1 – AM)
  Project scaffold, Docker, config, core infrastructure

Milestone 1: Data Layer (Day 1 – PM)
  Database schemas, repositories, synthetic data seeding

Milestone 2: ML Pipeline (Day 2 – AM)
  Feature engineering, Random Forest training, SHAP explainer, business rules

Milestone 3: Agents + Workflow (Day 2 – PM)
  LangGraph graph, all 8 agents, ReAct loops, checkpointing

Milestone 4: API Layer (Day 2 – PM)
  FastAPI endpoints, auth, validation, DI wiring

Milestone 5: RAG + Knowledge (Day 3 – AM)
  Qdrant collections, embedding pipeline, policy retrieval

Milestone 6: Frontend (Day 3 – AM)
  Streamlit pages, chat UI, dashboard

Milestone 7: Observability + Testing (Day 3 – PM)
  LangFuse integration, audit trail, test suite

Milestone 8: Documentation (Day 3 – PM)
  ADRs, architecture doc, solution summary, README
```

---

## Milestone 0: Foundation

### Deliverables
- `pyproject.toml` with all dependencies
- `docker-compose.yml` with all services (Postgres, Mongo, Qdrant, Neo4j, Ollama, Redis)
- `Dockerfile` (multi-stage: dev + prod)
- `Makefile` with commands: `make dev`, `make test`, `make lint`, `make seed`
- `.env.example` with all configuration variables
- `backend/core/config.py` — pydantic-settings configuration
- `backend/core/exceptions.py` — domain exception hierarchy
- `backend/core/logging.py` — structured JSON logging (loguru)
- `.gitignore`, `README.md` (skeleton)

### Architecture Decisions Established
- Configuration management strategy (env vars + YAML configs)
- Error handling pattern (domain exceptions → HTTP mapping)
- Logging standard (structured JSON, correlation IDs)

### Testing
- Integration test verifying all Docker services are reachable
- Unit test for config loading from env

---

## Milestone 1: Data Layer

### Deliverables

**Domain Layer**
- `backend/domain/entities/applicant.py` — Applicant aggregate
- `backend/domain/entities/application.py` — Application aggregate (status machine)
- `backend/domain/entities/document.py` — Document entity
- `backend/domain/entities/assessment.py` — Assessment
- `backend/domain/values/income.py` — Income VO with validation
- `backend/domain/values/address.py` — Address VO
- `backend/domain/values/eligibility_score.py` — Score VO (0-1 range)
- `backend/domain/ports/application_repo.py` — Repository interface
- `backend/domain/ports/document_store.py` — Document store interface
- `backend/domain/ports/vector_store.py` — Vector store interface
- `backend/domain/ports/graph_store.py` — Graph store interface
- `backend/domain/events/domain_events.py` — Event definitions

**Infrastructure Layer**
- `backend/database/postgres/models.py` — SQLAlchemy ORM models (all tables from schema)
- `backend/database/postgres/repositories.py` — Repository implementations
- `backend/database/mongodb/document_store.py` — GridFS document storage
- `backend/database/qdrant/vector_store.py` — Qdrant collection management
- `backend/database/neo4j/graph_store.py` — Neo4j node/relationship management

**Seed Data**
- `backend/seed/synthetic_data.py` — Faker-based applicant + document generator
- `backend/seed/policy_documents/` — 10-15 synthetic policy documents
- `backend/seed/seed_runner.py` — Populates all 4 databases

### Design Decisions
- SQLAlchemy async with asyncpg for PostgreSQL
- Beanie ODM for MongoDB (async, Pydantic-native)
- Qdrant client with filtering payloads
- Neo4j Python driver (not py2neo — it's unmaintained)

### Testing
- Repository integration tests against real Docker containers
- Domain entity unit tests (especially status machine transitions)
- Seed data verification test

---

## Milestone 2: ML Pipeline

### Deliverables
- `backend/ml/features.py` — Feature definitions (income, family_size, employment_stability, assets_ratio, credit_score, etc.)
- `backend/ml/pipeline.py` — `sklearn.pipeline.Pipeline` with preprocessing + Random Forest
- `backend/ml/model.py` — Model wrapper with `predict()` and `predict_proba()`
- `backend/ml/explainer.py` — SHAP explainer for feature importance
- `backend/ml/rules.py` — Deterministic business rules (separate from ML):
  - If income < poverty_threshold → auto-eligible for basic support
  - If total_assets > wealth_threshold → auto-decline
  - If family_size > dependent_threshold → additional allowance
  - If employment_gap > 2 years → flag for training recommendation

### Training Strategy
1. Generate 5,000 synthetic labeled records
2. Train/test split (80/20)
3. Random Forest with 100 estimators, max_depth=10
4. Cross-validation (5-fold)
5. Feature importance analysis
6. Calibration curve for confidence scoring

### Design Decisions
- **Random Forest over Gradient Boosting**: More robust to outliers in synthetic data, fewer hyperparameters to tune. If real data shows systematic bias, switch to XGBoost.
- **Business rules before ML**: Hard constraints applied first (e.g., asset threshold). ML only scores within the eligible population. This prevents the model from learning spurious correlations between protected attributes and eligibility.
- **SHAP over LIME**: SHAP offers theoretically guaranteed feature attribution (Shapley values). LIME is faster but unstable across runs.

### Testing
- Feature computation tests (edge cases: missing income, zero assets)
- Model serialization/deserialization (joblib)
- Rule precedence tests
- SHAP output format test

---

## Milestone 3: Agents + Workflow

### Deliverables

**Workflow Core**
- `backend/workflows/state.py` — `ApplicationState` TypedDict
- `backend/workflows/graph.py` — LangGraph StateGraph construction
- `backend/workflows/nodes.py` — All node functions
- `backend/workflows/edges.py` — Conditional edge routing
- `backend/workflows/config.py` — Retry, timeout, checkpoint configurations

**Agents**
- `backend/agents/base.py` — `BaseAgent` abstract class (think-act-observe loop)
- `backend/agents/orchestrator.py` — Supervisor agent with ReAct
- `backend/agents/intake_agent.py` — Creates app record, stores metadata, spawns workflow
- `backend/agents/ocr_agent.py` — Routes docs to handlers, calls PaddleOCR + vision model
- `backend/agents/validation_agent.py` — Cross-field validation with Reflexion
- `backend/agents/knowledge_agent.py` — RAG pipeline: embed query → retrieve → ground
- `backend/agents/eligibility_agent.py` — Calls ML model + applies rules + generates structured output
- `backend/agents/decision_agent.py` — LLM synthesizes ML output + policies + rationale
- `backend/agents/recommendation_agent.py` — Matches applicant profile to programs
- `backend/agents/chat_agent.py` — Stateful conversational agent (subgraph)

### Agent Implementation Detail

Each agent follows this contract:

```python
class BaseAgent(ABC):
    agent_name: str
    tools: list[Tool]

    @abstractmethod
    async def process(self, state: ApplicationState) -> dict:
        """Execute agent's responsibility and return state updates."""

    async def _think(self, context: dict) -> str:
        """ReAct: analyze current context and decide next action."""

    async def _act(self, thought: str, state: ApplicationState) -> ActionResult:
        """ReAct: execute the decided action using available tools."""

    async def _observe(self, result: ActionResult) -> str:
        """ReAct: interpret the result and update reasoning."""

    def _log_trace(self, span: Span, action: str, result: Any) -> None:
        """Log every step to LangFuse."""
```

### LangGraph Integration

```python
def build_application_graph() -> CompiledGraph:
    workflow = StateGraph(ApplicationState)

    # Add nodes
    workflow.add_node("intake", intake_agent.process)
    workflow.add_node("ocr", ocr_agent.process)
    workflow.add_node("validation", validation_agent.process)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("knowledge", knowledge_agent.process)
    workflow.add_node("eligibility", eligibility_agent.process)
    workflow.add_node("decision", decision_agent.process)
    workflow.add_node("human_signoff", human_signoff_node)
    workflow.add_node("recommendation", recommendation_agent.process)
    workflow.add_node("finalize", finalize_node)

    # Add edges
    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "ocr")
    workflow.add_edge("ocr", "validation")
    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {"human_review": "human_review", "knowledge": "knowledge"}
    )
    workflow.add_edge("human_review", "knowledge")
    workflow.add_edge("knowledge", "eligibility")
    workflow.add_edge("eligibility", "decision")
    workflow.add_conditional_edges(
        "decision",
        route_after_decision,
        {"human_signoff": "human_signoff", "recommendation": "recommendation"}
    )
    workflow.add_edge("human_signoff", "recommendation")
    workflow.add_edge("recommendation", "finalize")
    workflow.add_edge("finalize", END)

    # Compile with checkpointing
    return workflow.compile(checkpointer=PostgresSaver())
```

### Design Decisions
- **PostgresSaver for checkpoints** (not MemorySaver): Government apps need persistent, durable state. If the server restarts mid-workflow, the graph resumes from the last checkpoint.
- **Reflexion in Validation Agent**: After the initial validation pass, the agent reviews its own findings for false positives before flagging. This reduces noisy HITL interruptions.
- **Chat as a subgraph**: Not part of the main workflow. Runs independently with its own state and can be triggered at any point during the application lifecycle.

### Testing
- Unit tests for each agent (mocked LLM, mocked DB)
- Integration test for full workflow (all 8 agents, real DBs, mocked LLM responses)
- Checkpoint resume test: interrupt at validation → resume → verify state
- Retry test: force OCR failure → verify retry → verify escalation on max retries

---

## Milestone 4: API Layer

### Deliverables
- `backend/api/v1/applications.py` — All application endpoints
- `backend/api/v1/auth.py` — JWT auth endpoints
- `backend/api/v1/chat.py` — Chat endpoints
- `backend/api/v1/admin.py` — Admin endpoints
- `backend/api/v1/health.py` — Health check
- `backend/api/deps.py` — FastAPI dependency injection
- `backend/api/middleware.py` — Auth middleware, request ID, logging
- `backend/core/security.py` — JWT encode/decode, password hashing

### Key Endpoint Detail

```
POST /api/v1/applications/{id}/process
  - Triggers LangGraph workflow asynchronously
  - Returns 202 Accepted with workflow_id
  - Workflow runs via background task (asyncio.create_task or Celery)
  - Status can be polled via GET /applications/{id}/status

POST /api/v1/applications/{id}/resume
  - Provides human decision for checkpoint
  - Body: { "action": "approve_flags" | "override_inconsistency", "notes": "..." }
  - Resumes workflow from checkpoint with injected state
```

### Design Decisions
- **Async endpoints everywhere**: All database drivers are async. LangGraph supports async natively.
- **Background task for workflow** (not blocking request): Users don't wait for the full workflow to complete. They upload → get `202 Accepted` → poll status → see result.
- **Pydantic models for all request/response**: Auto-documented via Swagger. Strict validation at the boundary.
- **Versioned API (`/api/v1/`)**: Future versions (v2) can coexist. Old clients aren't broken.

### Testing
- API contract tests (using `httpx.AsyncClient` + `TestClient`)
- Auth middleware tests (valid token, expired token, missing token)
- Multipart upload test
- Pagination test
- Error response format tests

---

## Milestone 5: RAG + Knowledge

### Deliverables
- `backend/rag/embeddings.py` — BGE-M3/nomic-embed-text integration for embeddings
- `backend/rag/retriever.py` — Hybrid search (dense + keyword) with Qdrant
- `backend/rag/generator.py` — Context-grounded LLM generation for policy answers
- Qdrant collections with seeded policy/test documents

### RAG Pipeline
```
User Query (e.g., "What is the eligibility for a family of 4?")
    │
    ▼
1. Generate query embedding (Ollama: nomic-embed-text)
    │
    ▼
2. Hybrid search: dense (Qdrant) + keyword (BM25 via Qdrant filter)
    │
    ▼
3. Retrieve top-k policy chunks
    │
    ▼
4. Filter by recency (only active policies)
    │
    ▼
5. LLM generates grounded response with citations
```

### Testing
- Embedding generation test
- Retrieval relevance test (precision@k)
- Citation accuracy test (does the LLM response actually match the retrieved chunk?)

---

## Milestone 6: Frontend

### Deliverables
- `frontend/streamlit_app.py` — Main app with sidebar navigation
- `frontend/pages/dashboard.py` — Application stats (total, pending, approved, avg processing time)
- `frontend/pages/new_application.py` — Multi-step form + document upload drag-and-drop
- `frontend/pages/chat.py` — Chat interface for applicant assistant
- `frontend/pages/decision_report.py` — View assessment results, feature importance chart, recommendations
- `frontend/pages/admin.py` — All applications table, human review queue, flag resolution
- `frontend/pages/analytics.py` — Charts (approval rate over time, processing time distribution)
- `frontend/components/` — Reusable Streamlit components

### Design Decisions
- **Streamlit over React**: Faster to build for a prototype. If this goes to production, the API-first design means the frontend can be swapped to React/Vue without backend changes.
- **Page-per-view navigation**: Each major function is a separate page. Simpler than complex multi-tab layouts.
- **API client as a separate module**: Streamlit calls the FastAPI backend — it's not directly calling DB or agents. This enforces the API as the contract.

### Testing
- UI smoke tests (each page renders without errors)
- API integration (frontend calls → backend responses are correct)

---

## Milestone 7: Observability + Testing

### Deliverables
- `backend/core/observability.py` — LangFuse SDK initialization
- LangFuse integration in every agent (trace parent spans, child spans per tool call)
- Audit trail: every state transition logged to `audit_logs` table
- Prometheus metrics endpoint (`/metrics`)

### Observability Events
```
WorkflowStarted     → trace_id, application_id
AgentInvoked        → agent_name, input_state_hash
ToolCalled          → tool_name, duration_ms, success/failure
LLMInvocation       → model, prompt_tokens, response_tokens, latency
CheckpointReached   → node_name, state_hash
HumanIntervention   → action, user_id, notes
WorkflowCompleted   → total_duration_ms, decision, confidence
WorkflowFailed      → error_type, stack_trace, retry_count
```

### LangFuse-Specific

```python
# In each agent's process method:
@observe(name="ocr_agent")
async def process(self, state: ApplicationState) -> dict:
    span = langfuse.span(
        name="ocr_agent.run",
        input=state,
        metadata={"application_id": state["application_id"]}
    )

    # ... agent logic ...

    span.end(output=result)
```

### Testing
- Unit tests: 80%+ coverage for domain and services
- Integration tests: all database operations, workflow execution
- E2E test: full application lifecycle (submit → process → assess → decide → recommend)
- Performance test: workflow completes under 5 minutes for a standard application

---

## Milestone 8: Documentation

### Deliverables
- `docs/architecture.md` — System architecture with C4 diagrams (Context, Container, Component)
- `docs/decisions/001-clean-architecture.md` — ADR: Why Clean Architecture
- `docs/decisions/002-langgraph-over-crewai.md` — ADR: Agent framework choice
- `docs/decisions/003-local-llm-strategy.md` — ADR: Ollama + model selection
- `docs/decisions/004-polyglot-persistence.md` — ADR: Multi-database choice
- `docs/decisions/005-ml-llm-boundary.md` — ADR: Separation of ML and LLM
- `docs/decisions/006-agent-observability.md` — ADR: LangFuse for tracing
- `docs/solution-summary.md` — 10-page solution summary (the assessment deliverable)
- `README.md` — Full setup instructions, architecture overview, project walkthrough

### README Structure
1. Project Overview
2. Architecture (high-level diagram)
3. Tech Stack
4. Quick Start (with `make dev`)
5. API Documentation (link to Swagger)
6. Project Structure
7. Design Decisions Summary
8. Testing
9. Deployment
10. Future Improvements

---

## Future Improvements (Post-MVP)

| Area | Improvement | Priority |
|---|---|---|
| Scale | Kubernetes deployment with Helm charts | High |
| Scale | Horizontal scaling for agents (Celery workers + Redis queues) | High |
| Security | OAuth2/OIDC integration (Azure AD, Keycloak) | High |
| Security | Document encryption at rest (MongoDB encryption) | Medium |
| ML | Online learning from human decisions | Medium |
| ML | A/B testing framework for model versions | Medium |
| Data | Incremental embedding updates (CDC from Postgres → Qdrant) | Low |
| Agent | Self-improving prompts (LangFuse prompt management) | Low |
| Agent | Multi-language support (Arabic, English) | Low |
| Integration | Integration with UAE's national digital identity (UAE PASS) | Medium |
| Integration | MOI (Ministry of Interior) systems integration | Medium |
