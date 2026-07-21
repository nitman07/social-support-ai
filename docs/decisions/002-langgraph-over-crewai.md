# ADR 002: LangGraph over CrewAI / AutoGen

**Date:** 2026-07-20  
**Status:** Accepted  
**Context:** Need an agent orchestration framework for the 7-node application processing workflow (Intake → OCR → Validation → Knowledge → Eligibility → Decision → Recommendation).

**Decision:** Use LangGraph (LangChain's graph-based orchestration framework).

**Why not CrewAI:** Stateless — once agents finish, context is lost. No checkpointing for human-in-the-loop. No conditional routing.

**Why not AutoGen:** More flexible for open-ended agent conversations but less suitable for deterministic government workflows with strict state machines.

**LangGraph advantages for this context:**
1. Stateful graphs with checkpointing via `MemorySaver`/`PostgresSaver`
2. Conditional branching (`add_conditional_edges`) for HITL routing
3. `interrupt` mechanism enables native human-in-the-loop without custom infrastructure
4. Typed state (`ApplicationState` TypedDict) ensures type safety across nodes

**Consequences:** Positive: built-in checkpointing, conditional routing, HITL support. Negative: tied to LangChain ecosystem (but framework-agnostic via port interfaces). Negative: `langgraph-checkpoint-postgres` package needed for production persistence.
