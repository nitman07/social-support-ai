# ADR 004: Polyglot Persistence (4 Databases)

**Date:** 2026-07-20  
**Status:** Accepted  
**Context:** Different data types in the system have fundamentally different query patterns — ACID transactions, document storage, vector search, and graph traversal.

**Decision:** Use 4 specialized databases instead of PostgreSQL + pgvector.

| Database | Purpose | Why Not a Single DB |
|----------|---------|---------------------|
| **PostgreSQL** | Application records, decisions, users, audit logs | ACID transactions, complex relational queries, reporting |
| **MongoDB** | Raw OCR output, document images (GridFS), chat history | Schema varies per document type; unstructured blob storage |
| **Qdrant** | Policy embeddings, vector similarity search | 10-100x faster ANN than pgvector at scale; built-in filtering |
| **Neo4j** | Entity relationships (applicant → family → employers → assets) | Multi-hop graph traversal in Cypher vs. recursive CTEs in SQL |

**Consolidation argument:** For production with limited graph depth, PostgreSQL + pgvector could replace Qdrant and Neo4j. The current architecture treats each as a pluggable store behind a port interface, so consolidation requires changing only one file per store.

**Consequences:** Positive: each query pattern is served by the best tool. Negative: operational complexity of 4 databases (backup, monitoring, version upgrades). Tradeoff acceptable for a reference architecture demonstrating polyglot persistence.
