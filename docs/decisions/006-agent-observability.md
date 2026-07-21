# ADR 006: Agent Observability (LangFuse + Audit Trail)

**Date:** 2026-07-21  
**Status:** Accepted  
**Context:** Government AI systems must provide full audit trails for every decision. Each workflow step must be traceable, including LLM prompts/responses, ML scores, and human interventions.

**Decision:** Three-layer observability:

**1. LangFuse (external tracing):**
- Each workflow node wrapped with `@trace_node` decorator
- Captures: node name, input state, output state, duration, errors
- LLM prompts and responses captured via LangChain callbacks
- Can be disabled when LangFuse server is not running

**2. PostgreSQL audit_logs (internal audit):**
- Every state transition logged: `workflow_started`, `flag_accepted`, `signoff_approved`, `workflow_resumed`
- Stores: application_id, action, actor (user or system), details (JSONB), ip_address, timestamp
- Immutable append-only (no UPDATE, only INSERT)

**3. Prometheus metrics (operational):**
- Request count, average duration, total duration via `GET /metrics`
- Can be scraped by Prometheus + visualized in Grafana

**Consequences:** Positive: full audit trail for every decision, meets government compliance requirements. Negative: additional storage for audit logs (negligible, ~1KB per event). LangFuse requires a self-hosted server for production trace visualization.
