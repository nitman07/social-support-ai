# Personal Interview Preparation

## Milestone-specific interview questions and expected answers

---

### Milestone 0: Foundation & Project Scaffold

**Q1: Why did you choose Clean Architecture over a simpler MVC structure?**

*Expected answer:* Government systems require long-term maintainability and the ability to swap frameworks without rewriting business logic. Clean Architecture enforces dependency inversion — domain entities know nothing about FastAPI, SQLAlchemy, or LangChain. This means we can upgrade frameworks independently, test business logic without infrastructure, and onboard new engineers faster because the domain language is consistent.

**Q2: Why 4 databases instead of just PostgreSQL with pgvector?**

*Expected answer:* Each database serves a fundamentally different query pattern. PostgreSQL handles ACID transactions for application records and decisions — these need strict consistency. MongoDB stores unstructured OCR output and raw documents where schema varies per document type. Qdrant is purpose-built for vector similarity search with filtering, offering 10-100x faster approximate nearest neighbor search than pgvector at scale. Neo4j excels at multi-hop graph traversals — finding "all employers connected to this applicant's family members" is a single Cypher query vs. multiple recursive CTEs in PostgreSQL. The operational cost of 4 databases is justified for a reference architecture demonstrating polyglot persistence. In production, you could consolidate to PostgreSQL + pgvector if the graph depth is limited.

**Q3: How did you handle configuration management?**

*Expected answer:* We use pydantic-settings which loads from environment variables with YAML file overrides. Sensible defaults for development, strict validation in production. No secrets in code — everything comes from `.env` or the deployment environment. Config is validated at startup, not lazily, so misconfiguration fails fast.

---

### Milestone 1: Data Layer

**Q1: Why did you separate domain entities from ORM models?**

*Expected answer:* This is the core of Clean Architecture. SQLAlchemy models are infrastructure concerns — they couple us to PostgreSQL specifics like column types, indexes, and migration history. Domain entities are pure business objects. The repository pattern translates between them. This means we can change databases, add caching, or introduce read models without touching business logic. It also makes unit testing trivial — we test against interfaces, not databases.

**Q2: How did you design the application status machine?**

*Expected answer:* The status machine is `draft → submitted → processing → awaiting_review → approved | declined | failed`. Transitions are validated — you can't go from `draft` to `approved` without going through processing. Invalid transitions raise a domain exception. This prevents inconsistent states that plague government systems.

**Q3: Why Neo4j over just foreign keys in PostgreSQL for entity relationships?**

*Expected answer:* For simple one-hop relationships (applicant → family member), foreign keys work fine. But consider: "Find all employers where any family member of this applicant has worked in the last 5 years, and check if those employers have been flagged by other applicants." That's a multi-hop graph traversal that becomes exponentially complex with SQL joins. In Neo4j, it's a linear Cypher query. For a social support system where fraud detection and relationship discovery are critical, a graph database is the right choice.

**Q4: How would you handle database migrations in production?**

*Expected answer:* Alembic with auto-generation from SQLAlchemy models. Migrations are version-controlled, reviewed, and applied with zero-downtime patterns (expand-migrate-contract). Backward-compatible changes only (add columns as nullable, never remove columns without deprecation).

---

### Milestone 2: ML Pipeline

**Q1: Why Random Forest over Gradient Boosting or Neural Networks?**

*Expected answer:* For tabular data with ~10-15 features and ~5,000 synthetic samples, Random Forest offers the best accuracy-to-complexity ratio. It handles outliers well (important with synthetic data imperfections), requires minimal hyperparameter tuning, and provides native feature importance. Gradient Boosting (XGBoost/LightGBM) might outperform with more data but is more prone to overfitting on small datasets. Neural networks are unnecessary for this problem scale and lack interpretability without additional tooling. In production, we'd train multiple models and use cross-validation to select the best.

**Q2: How did you separate business rules from ML predictions?**

*Expected answer:* Business rules are hard constraints applied *before* ML scoring. For example: "If total assets exceed AED 500,000 → auto-decline regardless of ML score" or "If monthly income is below AED 3,000 → auto-qualify for basic support." The ML model only scores applications within the eligible range. This prevents the model from learning spurious correlations and ensures policy-compliant decisions. The ML score determines *how much* support, not *whether* to support.

**Q3: How do you explain individual predictions?**

*Expected answer:* SHAP (SHapley Additive exPlanations) values. For each prediction, we compute the contribution of each feature. This is displayed in the decision report as a bar chart showing which factors pushed the score up (e.g., family size, employment stability) and which pushed it down (e.g., low income, high liabilities). The LLM then translates these SHAP values into natural language: "Your application was approved primarily because your family size of 4 dependents increased your eligibility score by 0.15, while your stable 3-year employment added 0.08."

**Q4: How do you handle imbalanced data?**

*Expected answer:* In synthetic data, we can control the balance. In production, government data may be imbalanced (more approvals than declines). We use class weighting in Random Forest, stratified cross-validation, and threshold tuning via precision-recall curves. The decision threshold is calibrated to the policy team's risk appetite.

---

### Milestone 3: Agents + Workflow

**Q1: Why LangGraph over CrewAI or AutoGen?**

*Expected answer:* LangGraph provides three critical capabilities for government workflows: (1) **Stateful graphs** — we can pause, resume, and inspect workflow state at any point. CrewAI is stateless — once agents finish, the context is lost. (2) **Conditional branching** — the graph can route to different nodes based on validation results or ML scores. (3) **Built-in checkpointing** with LangGraph's `interrupt` mechanism enables human-in-the-loop without custom infrastructure. AutoGen is more flexible for open-ended agent conversations but less suitable for deterministic government workflows. CrewAI is easier to get started with but lacks the observability and control needed for auditability.

**Q2: How did you design the agent tool access?**

*Expected answer:* Each agent has a restricted tool set relevant to its function. The OCR agent can only call OCR tools and document store APIs. The Validation agent can only query databases and flag inconsistencies. This follows the Principle of Least Privilege applied to AI agents — an agent cannot execute tools outside its domain. The Master Orchestrator has broader visibility but only routes work; it doesn't directly modify data.

**Q3: How do you handle agent failures and retries?**

*Expected answer:* Each node in the LangGraph has a retry policy defined in `workflows/config.py`. OCR failures retry up to 3 times with exponential backoff. If all retries fail, the document is flagged and the workflow continues with partial data (best-effort extraction). Validation failures retry once, then flag for human review. ML prediction failures fall back to rule-based scoring. The key principle: a single agent failure should not fail the entire application.

**Q4: How does Human-in-the-Loop work technically?**

*Expected answer:* LangGraph's `interrupt` mechanism pauses the graph execution and persists state to PostgreSQL via PostgresSaver. The API provides endpoints for reviewers to view flags (`GET /applications/{id}/flags`), resolve them (`POST /applications/{id}/resolve-flag`), and resume the workflow (`POST /applications/{id}/resume`). When resumed, the graph receives the human's decision as input and continues from the exact checkpoint. The entire interaction is logged in the audit trail.

**Q5: How does the ReAct loop work in your agents?**

*Expected answer:* Each agent has a constrained ReAct loop: (1) **Think** — analyze current state and available data, decide what needs to happen next. (2) **Act** — call a specific tool (e.g., `extract_from_image`, `query_graph_db`, `compute_ml_score`). (3) **Observe** — interpret the tool's output. (4) **Repeat** — continue until the agent's task is complete or max iterations reached. The loop is constrained to prevent infinite loops — max 5 iterations per agent invocation.

---

### Milestone 4: API Layer

**Q1: Why FastAPI over Django REST Framework or Flask?**

*Expected answer:* FastAPI offers native async support, automatic OpenAPI/Swagger documentation, and Pydantic-based request validation — all critical for an AI platform. Async is essential because we call LLMs, databases, and external services concurrently. Django REST Framework would require Django ORM coupling, which conflicts with Clean Architecture. Flask would need significant additional tooling for validation and documentation. FastAPI also leads in performance benchmarks due to Starlette's async foundation.

**Q2: How did you design the API for async workflow processing?**

*Expected answer:* The `POST /applications/{id}/process` endpoint returns `202 Accepted` immediately with a `workflow_id`. The LangGraph workflow runs as a background task. The client polls `GET /applications/{id}/status` to check progress. This prevents HTTP timeout issues (LLM calls can take 10-30 seconds) and allows the client to show progress to the user.

**Q3: How do you handle authentication and authorization?**

*Expected answer:* JWT-based with short-lived access tokens (15 minutes) and refresh tokens (7 days). Role-based access control with four roles: `applicant`, `reviewer`, `decision_maker`, `admin`. Middleware validates tokens on every request and injects the current user into the request context. For production, this would integrate with UAE PASS or Azure AD/Keycloak via OAuth2.

**Q4: How do you version your API?**

*Expected answer:* URL-based versioning (`/api/v1/`). When breaking changes are needed, we create `/api/v2/` and maintain backward compatibility for a deprecation period. This is simpler and more explicit than header-based versioning for government APIs where external integrators need clear contracts.

---

### Milestone 5: RAG + Knowledge

**Q1: Why did you choose nomic-embed-text / BGE-M3 for embeddings?**

*Expected answer:* BGE-M3 supports multi-language (Arabic + English for UAE context) and handles multiple granularities (document, passage, sentence). It's available via Ollama, keeping everything local. OpenAI's text-embedding-3 would violate the local-only requirement. nomic-embed-text is a lighter alternative but doesn't handle Arabic as well. For production, we'd benchmark both on a labeled retrieval set.

**Q2: How do you ensure the LLM cites the correct policy documents?**

*Expected answer:* We use a two-step approach: (1) retrieve the top-k policy chunks with relevance scores, (2) instruct the LLM to only answer from the retrieved context and cite specific document IDs. The prompt explicitly states: "If the retrieved context doesn't contain enough information to answer, say 'I cannot find this information in the current policy documents.' Do not make up policies." We also log the retrieved context IDs with every generation for audit.

**Q3: How do you handle conflicting or outdated policies?**

*Expected answer:* Each policy document has `effective_from` and `effective_to` dates. The retriever filters to only active policies at query time. When policies conflict (two active policies with contradictory statements), the system surfaces both to the decision agent and flags the conflict for manual review. In production, a policy management workflow would handle versioning and deprecation.

---

### Milestone 6: Frontend

**Q1: Why Streamlit over React/Next.js?**

*Expected answer:* For a prototype and reference implementation, Streamlit provides the fastest iteration speed — full application in Python without a separate frontend build pipeline. The API-first design means the frontend is a thin client; if this goes to production, React/Vue can replace Streamlit without any backend changes. Streamlit is also familiar to data scientists and AI engineers who may need to extend the UI.

**Q2: How do you handle real-time updates for application status?**

*Expected answer:* Polling with exponential backoff. The frontend polls `GET /applications/{id}/status` every 2 seconds for the first 30 seconds, then every 10 seconds. When status changes, the UI updates. For production, we'd add WebSocket support via FastAPI's WebSocket endpoints, but polling is simpler and more reliable for a prototype.

**Q3: What's the decision report page showing?**

*Expected answer:* The decision report has four sections: (1) **ML Assessment** — eligibility score as a gauge, feature importance bar chart (SHAP values), confidence score. (2) **LLM Rationale** — natural language explanation of the decision. (3) **Inconsistency Flags** — any data discrepancies found during validation and their resolution status. (4) **Recommendations** — personalized training programs, job matches, and government support programs with relevance scores.

---

### Milestone 7: Observability + Testing

**Q1: Why LangFuse over MLflow or Weights & Biases?**

*Expected answer:* LangFuse is purpose-built for LLM observability — it traces prompts, responses, token usage, latency, and cost natively. MLflow is a general MLOps platform that requires significant customization for LLM tracing. Weights & Biases is cloud-only, violating our local-first requirement. LangFuse can be self-hosted and captures the specific metrics we need for AI auditing: prompt version, model used, hallucination scores, and retry counts.

**Q2: How do you test LLM-dependent code?**

*Expected answer:* Three-layer strategy: (1) **Unit tests** — mock the LLM service entirely, test the agent logic and state transitions with predefined LLM responses. (2) **Integration tests** — use a real Ollama instance with a small model (Phi-2 or Qwen2.5:0.5B) to test the full pipeline, but with simplified prompts to keep responses deterministic. (3) **Evaluation tests** — use LangFuse to compare LLM outputs against golden answers for key scenarios, tracking accuracy over time.

**Q3: What metrics do you track for the AI system?**

*Expected answer:* Operational: request latency (p50/p95/p99), error rate, token usage per application. Business: approval rate, average processing time, human intervention rate, inconsistency detection rate. ML: model accuracy, precision/recall, feature stability over time. LLM: response relevance, citation accuracy, hallucination rate. All exported as Prometheus metrics and visualized in Grafana.

---

### Milestone 8: Documentation

**Q1: How do you keep documentation synchronized with code?**

*Expected answer:* Documentation is checked into the repository alongside code. ADRs document why decisions were made, not what the code does (the code documents that). API documentation is auto-generated by FastAPI/Swagger. Architecture diagrams are maintained in Mermaid (as code) so they're version-controlled and diffable. README has a "last reviewed" date.

**Q2: What's the most important architectural decision you made and why?**

*Expected answer:* The separation of ML from LLM for financial decisions. In a government social support system, eligibility determinations must be deterministic, reproducible, and defensible in court. An ML model's decision can be explained through SHAP values and business rules. An LLM's "reasoning" is probabilistic — it could give different answers for the same input. By having the ML model produce the numeric score and the LLM only interpret it, we get the best of both: reliable computation with human-readable explanation. This separation is the most important design choice because it directly impacts the system's legal and ethical defensibility.

**Q3: How would this system scale to handle 100,000 applications per day?**

*Expected answer:* (1) Stateless API layer behind a load balancer, horizontal scaling of FastAPI instances. (2) Celery workers for agent execution, with Redis as the message broker and PostgreSQL for results. (3) Read replicas for PostgreSQL, sharded MongoDB, Qdrant cluster with replication, Neo4j causal cluster. (4) LLM inference scaled via Ollama's built-in batching or vLLM for higher throughput. (5) Caching layer (Redis) for frequently accessed policies and chat responses. The current architecture supports this with config changes and Kubernetes deployment — no code changes needed.
