# ADR 001: Clean Architecture

**Date:** 2026-07-20  
**Status:** Accepted  
**Context:** The system requires long-term maintainability and the ability to swap frameworks (e.g., FastAPI → Django, scikit-learn → XGBoost, LangGraph → custom orchestrator) without rewriting business logic.

**Decision:** Use Clean Architecture with strict dependency inversion:

```
Domain (entities, value objects, events)
    ↑
Application (ports/interfaces)
    ↑
Infrastructure (FastAPI, SQLAlchemy, LangGraph, ML models)
```

- Domain layer has zero imports from frameworks
- Ports define interfaces; infrastructure implements them
- DI via `injector` library wires implementations at startup

**Consequences:** Positive: testable business logic, framework independence. Negative: more boilerplate (interfaces, repository pattern) than a flat MVC structure. Tradeoff accepted for a government system with expected 5+ year lifespan.
