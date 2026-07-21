# ADR 003: Local LLM Strategy (Ollama)

**Date:** 2026-07-20  
**Status:** Accepted  
**Context:** Government data sovereignty requirements prohibit sending citizen data to cloud LLM providers (OpenAI, Anthropic, etc.). All model inference must run on-premises.

**Decision:** Run all LLM inference locally via Ollama.

**Model Selection:**
| Model | Purpose | Rationale |
|-------|---------|-----------|
| `qwen2.5:0.5b` | Decision rationale generation | Small enough for Docker (OOM-safe), adequate English output |
| `nomic-embed-text` | Policy embedding for RAG | 768-dim vectors, fast inference, available via Ollama |
| `qwen2.5-vl:7b` | Vision (future OCR enhancement) | Multimodal, handles Arabic script |

**Why not Mistral 7B:** Caused OOM in Docker with 4 GB container memory limit. Qwen2.5:0.5b is 1/14th the size and fits comfortably.

**Fallback strategy:** If Ollama is down or slow, the decision node generates a template-based rationale using feature names and scores instead of natural language. The workflow never crashes due to LLM failure.

**Consequences:** Positive: fully local, no data leaves the premises. Negative: small model produces less nuanced rationale than GPT-4. Acceptable because the ML model (not LLM) drives eligibility decisions.
