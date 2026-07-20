# Git Commit Strategy & Milestone Plan

## Repository

- **Platform:** GitHub
- **URL:** https://github.com/nitman07/social-support-ai.git
- **Visibility:** Public (required by client submission guidelines)
- **Branch strategy:** `main` as the single branch with atomic commits (no messy WIP commits)
- **YouTube walkthrough:** A video demo of the application is required for client submission (will be recorded after completion)

---

## Git Commit Philosophy

Every commit should:
1. Be **atomic** — represents one logical change
2. **Compile and run** independently (no broken commits)
3. Follow **Conventional Commits** format
4. Tell a story — the commit log should read like a changelog

### Commit Message Format
```
<type>(<scope>): <short summary>

<optional body explaining WHY, not WHAT>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

**Examples:**
```
feat(domain): add Applicant and Application entities with status machine

feat(ml): implement Random Forest eligibility pipeline with SHAP explainer

docs(adr): add architecture decision record for polyglot persistence

test(agents): add unit tests for validation agent with mocked LLM
```

---

## Milestone Plan (7 Milestones, ~25-30 Commits)

### Milestone 1: Foundation & Infrastructure
**Goal:** Project scaffold, Docker services, configuration, domain skeleton

| # | Commit | Description |
|---|--------|-------------|
| 1.1 | `chore(project): scaffold project structure and configuration` | pyproject.toml, Makefile, .env.example, .gitignore |
| 1.2 | `feat(infra): add Docker Compose with all services` | docker-compose.yml, Dockerfile |
| 1.3 | `feat(core): implement configuration management and logging` | config.py, exceptions.py, logging.py |
| 1.4 | `feat(domain): add domain entities and value objects` | applicant.py, application.py, document.py, assessment.py |
| 1.5 | `feat(domain): define domain ports (repository interfaces)` | application_repo.py, document_store.py, vector_store.py, graph_store.py |
| 1.6 | `feat(domain): implement domain events` | domain_events.py |

**Interview questions for this milestone** → see `personal_interview.md`

---

### Milestone 2: Persistence Layer
**Goal:** All 4 database implementations, migrations, synthetic data

| # | Commit | Description |
|---|--------|-------------|
| 2.1 | `feat(db): implement PostgreSQL models and repositories` | SQLAlchemy models, async repositories |
| 2.2 | `feat(db): implement MongoDB document store` | GridFS storage, Beanie models |
| 2.3 | `feat(db): implement Qdrant vector store` | Collection management, CRUD operations |
| 2.4 | `feat(db): implement Neo4j graph store` | Node/relationship management, Cypher queries |
| 2.5 | `feat(seed): add synthetic data generator and database seeder` | Faker-based generation, seed runner |
| 2.6 | `test(db): add integration tests for all database repositories` | Docker-based integration tests |

---

### Milestone 3: ML & Business Rules
**Goal:** Random Forest pipeline, feature engineering, SHAP, rules engine

| # | Commit | Description |
|---|--------|-------------|
| 3.1 | `feat(ml): implement feature engineering pipeline` | Feature definitions, transformers |
| 3.2 | `feat(ml): train and serialize Random Forest model` | Training script, model artifacts, Calibration |
| 3.3 | `feat(ml): add SHAP explainer for model interpretability` | SHAP integration, feature importance |
| 3.4 | `feat(ml): implement deterministic business rules engine` | Rule definitions, evaluation engine |
| 3.5 | `test(ml): add unit tests for features, model, and rules` | Isolated ML tests |

---

### Milestone 4: Agent Framework & Workflow
**Goal:** LangGraph workflow, all 8 agents, ReAct loops, checkpointing

| # | Commit | Description |
|---|--------|-------------|
| 4.1 | `feat(agents): implement base agent class with ReAct loop` | Abstract base, tool interface, think-act-observe |
| 4.2 | `feat(agents): implement intake and OCR agents` | Agent 1 + Agent 2 |
| 4.3 | `feat(agents): implement validation agent with Reflexion` | Agent 3 (cross-validation, inconsistency detection) |
| 4.4 | `feat(agents): implement knowledge agent with RAG` | Agent 4 (policy retrieval) |
| 4.5 | `feat(agents): implement eligibility and decision agents` | Agent 5 (ML) + Agent 6 (LLM rationale) |
| 4.6 | `feat(agents): implement recommendation and chat agents` | Agent 7 + Agent 8 |
| 4.7 | `feat(workflow): implement LangGraph workflow with checkpointing` | State graph, nodes, edges, orchestrator |
| 4.8 | `feat(workflow): add human-in-the-loop support` | Interruption points, resume mechanism |
| 4.9 | `test(agents): add unit and integration tests for agents` | Mocked LLM tests, workflow tests |

---

### Milestone 5: API Layer
**Goal:** FastAPI endpoints, auth, DI wiring, health checks

| # | Commit | Description |
|---|--------|-------------|
| 5.1 | `feat(api): implement authentication endpoints (JWT)` | login, refresh, middleware |
| 5.2 | `feat(api): implement application endpoints` | CRUD, document upload, status |
| 5.3 | `feat(api): implement workflow control endpoints` | process, resume, checkpoint status |
| 5.4 | `feat(api): implement chat endpoints` | messaging, history |
| 5.5 | `feat(api): implement admin and health endpoints` | dashboard stats, audit, health |
| 5.6 | `feat(core): wire up dependency injection container` | injector wiring, service registration |
| 5.7 | `test(api): add API contract and integration tests` | httpx-based API tests |

---

### Milestone 6: Frontend
**Goal:** Streamlit UI with all pages

| # | Commit | Description |
|---|--------|-------------|
| 6.1 | `feat(ui): implement Streamlit app shell and navigation` | Main entry, sidebar, routing |
| 6.2 | `feat(ui): implement dashboard and new application pages` | Stats view, multi-step form, document upload |
| 6.3 | `feat(ui): implement chat and decision report pages` | Chat interface, assessment visualization |
| 6.4 | `feat(ui): implement admin and analytics pages` | Review queue, charts, filters |

---

### Milestone 7: Observability, Testing & Documentation
**Goal:** LangFuse, audit trail, test suite, ADRs, README

| # | Commit | Description |
|---|--------|-------------|
| 7.1 | `feat(obs): integrate LangFuse observability` | Tracing, spans, metric, LangFuse setup |
| 7.2 | `feat(obs): implement audit trail logging` | Audit table, event recording |
| 7.3 | `test(e2e): add end-to-end workflow test` | Full lifecycle test |
| 7.4 | `docs: add Architecture Decision Records` | ADRs for all key decisions |
| 7.5 | `docs: add system architecture documentation` | Architecture.md with diagrams |
| 7.6 | `docs: add solution summary document` | 10-page deliverable |
| 7.7 | `docs: finalize README with setup instructions` | Complete README |

**Total: ~29 commits across 7 milestones**

---

## Question for you:

**Should I create the GitHub repo on your account, or do you already have one ready?**

If you want me to help set it up, I'll need:
1. Your GitHub username
2. Whether you want me to initialize the repo and push the first commit, or do it yourself

---

## Next Step

I'll wait for your approval before implementing anything. For now, let's discuss:

1. **Milestone structure** — 7 milestones, ~29 commits. Too many? Too few? Merge any?
2. **Repo setup** — Your GitHub account or mine? (I can help create and push)
3. **Starting point** — Once approved, I begin with Milestone 1, commit 1.1 (project scaffold)

Take your time reviewing.
