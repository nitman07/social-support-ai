# Folder Structure

```
social-support-ai/
│
├── backend/                              # FastAPI application
│   ├── api/                              # Interface adapters (controllers)
│   │   ├── v1/                           # Versioned API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── applications.py           # Application CRUD + document upload
│   │   │   ├── auth.py                   # Login, refresh, registration
│   │   │   ├── chat.py                   # Chat sessions
│   │   │   ├── admin.py                  # Admin dashboard + audit
│   │   │   └── health.py                 # Health checks
│   │   ├── __init__.py
│   │   ├── deps.py                       # FastAPI dependency injection
│   │   └── middleware.py                 # Auth, logging, rate limiting
│   │
│   ├── core/                             # Cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── config.py                     # App configuration (pydantic-settings)
│   │   ├── container.py                  # DI container (injector)
│   │   ├── security.py                   # JWT, password hashing
│   │   ├── exceptions.py                 # Domain + HTTP exceptions
│   │   └── logging.py                    # Structured logging setup
│   │
│   ├── domain/                           # Enterprise business rules (framework-free)
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── applicant.py              # Applicant aggregate root
│   │   │   ├── application.py            # Application aggregate
│   │   │   ├── document.py               # Document entity
│   │   │   ├── assessment.py             # Assessment entity
│   │   │   └── user.py                   # System user entity
│   │   ├── values/
│   │   │   ├── __init__.py
│   │   │   ├── income.py                 # Income value object
│   │   │   ├── address.py                # Address VO
│   │   │   ├── eligibility_score.py      # Score VO (range 0-1)
│   │   │   └── document_type.py          # Enum of supported types
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   └── domain_events.py          # ApplicationSubmitted, DecisionMade, etc.
│   │   └── ports/                        # Interface boundaries (contracts)
│   │       ├── __init__.py
│   │       ├── application_repo.py       # IApplicationRepository
│   │       ├── document_store.py         # IDocumentStore
│   │       ├── vector_store.py           # IVectorStore
│   │       ├── graph_store.py            # IGraphStore
│   │       ├── llm_service.py            # ILLMService
│   │       ├── ml_service.py             # IMLService
│   │       └── observability.py          # IObservabilityService
│   │
│   ├── services/                         # Application use cases
│   │   ├── __init__.py
│   │   ├── application_service.py        # Orchestrates application lifecycle
│   │   ├── document_service.py           # Document upload + processing
│   │   ├── assessment_service.py         # Manages assessment flow
│   │   ├── recommendation_service.py     # Generates recommendations
│   │   ├── chat_service.py               # Chat session management
│   │   └── audit_service.py             # Audit trail recording
│   │
│   ├── agents/                           # AI agent implementations
│   │   ├── __init__.py
│   │   ├── base.py                       # Abstract base agent
│   │   ├── orchestrator.py               # Master orchestrator (supervisor)
│   │   ├── intake_agent.py               # Agent 1: Application intake
│   │   ├── ocr_agent.py                  # Agent 2: Document OCR
│   │   ├── validation_agent.py           # Agent 3: Cross-validation
│   │   ├── knowledge_agent.py            # Agent 4: RAG policy queries
│   │   ├── eligibility_agent.py          # Agent 5: ML + rules
│   │   ├── decision_agent.py             # Agent 6: LLM reasoning
│   │   ├── recommendation_agent.py       # Agent 7: Recommendations
│   │   └── chat_agent.py                 # Agent 8: Interactive assistant
│   │
│   ├── workflows/                        # LangGraph workflow definitions
│   │   ├── __init__.py
│   │   ├── state.py                      # ApplicationState TypedDict
│   │   ├── graph.py                      # Graph builder
│   │   ├── nodes.py                      # Node function implementations
│   │   ├── edges.py                      # Conditional edge logic
│   │   └── config.py                     # Retry, timeout, checkpoint configs
│   │
│   ├── ml/                               # Machine learning pipeline
│   │   ├── __init__.py
│   │   ├── pipeline.py                   # Feature engineering + training pipeline
│   │   ├── features.py                   # Feature definitions and transformers
│   │   ├── model.py                      # Random Forest model wrapper
│   │   ├── explainer.py                  # SHAP explanation
│   │   └── rules.py                      # Deterministic business rules
│   │
│   ├── rag/                              # Retrieval Augmented Generation
│   │   ├── __init__.py
│   │   ├── embeddings.py                 # Embedding model integration
│   │   ├── retriever.py                  # Vector search + hybrid search
│   │   ├── generator.py                  # Context-grounded generation
│   │   └── documents.py                  # Policy/program document management
│   │
│   ├── database/                         # Data access implementations
│   │   ├── postgres/
│   │   │   ├── __init__.py
│   │   │   ├── models.py                 # SQLAlchemy ORM models
│   │   │   ├── repositories.py           # Repository implementations
│   │   │   └── migrations/              # Alembic migrations
│   │   ├── mongodb/
│   │   │   ├── __init__.py
│   │   │   ├── repository.py            # MongoDB repository
│   │   │   └── document_store.py        # GridFS document storage
│   │   ├── qdrant/
│   │   │   ├── __init__.py
│   │   │   └── vector_store.py          # Qdrant client wrapper
│   │   ├── neo4j/
│   │   │   ├── __init__.py
│   │   │   └── graph_store.py           # Neo4j client wrapper
│   │   └── redis/
│   │       ├── __init__.py
│   │       └── cache.py                 # Redis caching layer
│   │
│   ├── prompts/                          # Prompt templates (versioned)
│   │   ├── __init__.py
│   │   ├── extraction/                   # OCR extraction prompts
│   │   │   ├── emirates_id.txt
│   │   │   ├── bank_statement.txt
│   │   │   ├── resume.txt
│   │   │   └── ...
│   │   ├── validation/                   # Cross-validation prompts
│   │   │   ├── income_check.txt
│   │   │   ├── address_check.txt
│   │   │   └── family_check.txt
│   │   ├── decision/                     # Decision reasoning prompts
│   │   │   ├── eligibility.txt
│   │   │   └── final_decision.txt
│   │   └── chat/                         # Chat interaction prompts
│   │       └── assistant.txt
│   │
│   └── seed/                             # Synthetic data generation
│       ├── __init__.py
│       ├── synthetic_data.py             # Faker-based data generator
│       ├── seed_runner.py                # Orchestrates seeding
│       └── policy_documents/            # Fake policy PDFs for RAG
│
├── frontend/                             # Streamlit application
│   ├── __init__.py
│   ├── streamlit_app.py                  # Main entry + navigation
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── dashboard.py                  # Overview stats
│   │   ├── new_application.py            # Application form + upload
│   │   ├── chat.py                       # Chat interface
│   │   ├── decision_report.py            # Decision + recommendations view
│   │   ├── admin.py                      # Admin panel
│   │   └── analytics.py                  # Analytics dashboard
│   ├── components/                       # Reusable UI components
│   │   ├── __init__.py
│   │   ├── document_uploader.py
│   │   ├── assessment_card.py
│   │   ├── recommendation_list.py
│   │   └── chat_bubble.py
│   └── utils/
│       ├── __init__.py
│       ├── api_client.py                 # FastAPI client wrapper
│       └── session.py                    # Streamlit session state
│
├── tests/                                # Test suite
│   ├── __init__.py
│   ├── conftest.py                       # Global fixtures
│   ├── unit/                             # Fast, isolated tests
│   │   ├── domain/
│   │   │   ├── test_applicant.py
│   │   │   ├── test_application.py
│   │   │   └── test_values.py
│   │   ├── agents/
│   │   │   ├── test_intake_agent.py
│   │   │   ├── test_validation_agent.py
│   │   │   └── test_eligibility_agent.py
│   │   ├── ml/
│   │   │   ├── test_features.py
│   │   │   └── test_rules.py
│   │   └── services/
│   │       ├── test_application_service.py
│   │       └── test_document_service.py
│   ├── integration/                      # Tests with real DBs
│   │   ├── test_postgres_repo.py
│   │   ├── test_qdrant_store.py
│   │   ├── test_neo4j_store.py
│   │   └── test_workflow.py
│   └── e2e/                              # Full end-to-end tests
│       └── test_full_application.py
│
├── docker/                               # Docker configuration
│   ├── Dockerfile                        # Multi-stage build
│   └── docker-compose.yml                # All services
│
├── docs/                                 # Documentation
│   ├── architecture.md                   # System architecture overview
│   ├── decisions/                        # Architecture Decision Records
│   │   ├── 001-clean-architecture.md
│   │   ├── 002-langgraph-over-crewai.md
│   │   ├── 003-local-llm-strategy.md
│   │   ├── 004-polyglot-persistence.md
│   │   ├── 005-ml-llm-boundary.md
│   │   └── 006-agent-observability.md
│   └── solution-summary.md              # 10-page deliverable
│
├── scripts/                              # DevOps scripts
│   ├── setup.sh                          # Initial setup
│   ├── pull-models.sh                    # Download Ollama models
│   └── seed-db.sh                        # Seed databases
│
├── configs/                              # Environment configs
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
│
├── pyproject.toml                        # Python project configuration
├── Makefile                              # Development commands
├── .env.example                          # Environment variable template
├── .gitignore
└── README.md                             # Project README
```

## Design Rationale for Key Structural Decisions

| Decision | Why |
|---|---|
| `backend/` and `frontend/` separate | Clean separation of concerns. Different deploy, scale, and test strategies. |
| `domain/` has zero external dependencies | No FastAPI, no SQLAlchemy, no LangChain imports in domain. Pure Python + stdlib. This is the heart of Clean Architecture. |
| `ports/` are abstract interfaces | Any database, LLM, or ML framework can be swapped without touching business logic. |
| `agents/` separate from `services/` | Services orchestrate business logic. Agents encapsulate AI behavior. They call services, not the other way around. |
| `prompts/` as text files (not inline strings) | Version control, diffing, and review of prompts. Also enables A/B testing different prompt versions. |
| `tests/` mirrors `src/` structure | Easy to find tests for any module. Tests are co-located by concern, not by type. |
| `docs/decisions/` (ADRs) | Every architectural choice documented with context, options considered, and rationale. Critical for government procurement audits. |
