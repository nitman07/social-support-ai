# ADR 005: Separation of ML and LLM

**Date:** 2026-07-20  
**Status:** Accepted  
**Context:** In a government social support system, eligibility determinations must be deterministic, reproducible, and defensible in court. LLM reasoning is probabilistic — it could give different answers for the same input.

**Decision:** Strict separation of concerns:

```
Rules Engine → gates eligibility (hard blocks)
    ↓
ML Model (Random Forest) → produces numeric score + SHAP values
    ↓
LLM (Qwen2.5:0.5b) → interprets score in natural language (NEVER decides)
```

**Rules are hard constraints** applied *before* ML scoring:
- Income > AED 50K → blocked
- Assets > AED 500K → blocked  
- Debt ratio > 3x → blocked
- Income < AED 1K → blocked
- Document completeness → soft flag

**ML owns the score:** Random Forest computes eligibility score (0.0–1.0). SHAP TreeExplainer provides per-feature marginal contributions.

**LLM owns the explanation:** Generates human-readable rationale based on ML score, SHAP values, and retrieved policy context. Cannot override or modify the score.

**Consequences:** Positive: decisions are deterministic and auditable via SHAP values. Negative: LLM explanations may be less fluent than if the LLM made the decision. This is the most important architectural decision — it directly impacts legal and ethical defensibility.
