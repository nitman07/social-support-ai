# LangGraph Workflow Design

## State Definition

```python
class ApplicationState(TypedDict):
    # Core identifiers
    application_id: str
    applicant_id: str

    # Workflow control
    status: str                           # draft|submitted|processing|awaiting_review|approved|declined|failed
    workflow_id: str                      # LangGraph run identifier
    checkpoint_id: Optional[str]          # Current checkpoint for resume
    retry_count: int                      # Number of retries attempted
    max_retries: int                      # Max retries before escalating
    errors: list[WorkflowError]           # Accumulated errors

    # Document processing
    documents: list[DocumentInfo]         # Uploaded document manifest
    ocr_results: dict[str, OCROutput]     # document_type -> OCR output
    extraction_complete: bool

    # Validation
    validated_data: ExtractedData         # Normalized, cross-validated data
    inconsistencies: list[Inconsistency]  # Flags requiring resolution
    validation_complete: bool
    requires_human_review: bool           # True if HITL checkpoint needed

    # Knowledge / RAG
    retrieved_policies: list[PolicyContext]
    knowledge_queries: list[str]

    # Eligibility
    ml_features: dict[str, float]         # Feature vector for model
    ml_prediction: Optional[MEPrediction] # Model output
    eligibility_rules_applied: list[RuleResult]

    # Decision
    decision: Optional[str]               # approved|soft_decline|referred
    decision_rationale: Optional[str]
    decision_confidence: float

    # Recommendations
    recommendations: list[Recommendation]

    # Audit
    agent_traces: list[AgentTrace]        # Every agent step recorded
    human_actions: list[HumanAction]      # HITL interventions

    # Chat (populated by chat subgraph)
    chat_history: list[ChatMessage]
```

## Graph Structure

```
                                ┌──────────────────┐
                                │   ENTRY (START)  │
                                └────────┬─────────┘
                                         │
                                  ┌──────▼──────┐
                                  │  Intake Node │
                                  │  (Agent #1)  │
                                  └──────┬──────┘
                                         │
                                  ┌──────▼──────┐
                                  │Route Docs    │
                                  │by Type       │
                                  └──────┬──────┘
                                         │
                                  ┌──────▼──────┐
                                  │  OCR Node    │
                                  │  (Agent #2)  │
                                  └──────┬──────┘
                                         │
                                  ┌──────▼──────┐
                                  │ Validate     │
                                  │ (Agent #3)   │
                                  └──────┬──────┘
                                         │
                              ┌──────────┴──────────┐
                              │                     │
                    ┌─────────▼──┐           ┌──────▼─────────┐
                    │ Has         │           │ No              │
                    │ Inconsisten-│           │ Inconsistencies │
                    │ cies?       │           │                 │
                    └─────────┬──┘           └──────┬──────────┘
                              │                     │
                    ┌─────────▼──┐                  │
                    │ Suspend for│                  │
                    │ HITL Review│                  │
                    │ (checkpoint)│                 │
                    └─────────┬──┘                  │
                              │ (resume)            │
                              └──────────┬──────────┘
                                         │
                                  ┌──────▼──────┐
                                  │Knowledge Node│
                                  │ (Agent #4)   │
                                  └──────┬──────┘
                                         │
                                  ┌──────▼──────┐
                                  │Eligibility   │
                                  │Node (Agent#5)│
                                  └──────┬──────┘
                                         │
                                  ┌──────▼──────┐
                                  │ Decision     │
                                  │ Node(Agent#6)│
                                  └──────┬──────┘
                                         │
                              ┌──────────┴──────────┐
                              │                     │
                    ┌─────────▼──┐           ┌──────▼─────────┐
                    │ Needs       │           │ Auto-approve   │
                    │ Human Sign- │           │ (low risk,     │
                    │ off?        │           │ high confidence│
                    └─────────┬──┘           └──────┬──────────┘
                              │                     │
                    ┌─────────▼──┐                  │
                    │ Suspend for│                  │
                    │ HITL Review│                  │
                    │ (checkpoint)│                 │
                    └─────────┬──┘                  │
                              │ (resume)            │
                              └──────────┬──────────┘
                                         │
                                  ┌──────▼──────┐
                                  │Recommendation│
                                  │ Node(Agent#7)│
                                  └──────┬──────┘
                                         │
                                  ┌──────▼──────┐
                                  │   END        │
                                  │ (finalize)   │
                                  └─────────────┘
```

## Chat Agent (Subgraph)

```
                 ┌─────────────────────┐
                 │ Chat Entry (START)  │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │ Classify Intent     │
                 │ (Application status?│
                 │  Decision question? │
                 │  Policy question?   │
                 │  General question?) │
                 └──────────┬──────────┘
                            │
              ┌─────────────┼──────────────┐
              │             │              │
     ┌────────▼──┐  ┌──────▼─────┐  ┌─────▼──────┐
     │ Query App │  │ Query      │  │ Search     │
     │ Status    │  │ Decision   │  │ Policies   │
     │ (DB read) │  │ Rationale  │  │ (RAG)      │
     └────────┬──┘  └──────┬─────┘  └─────┬──────┘
              │             │              │
              └─────────────┼──────────────┘
                            │
                 ┌──────────▼──────────┐
                 │ Generate Response   │
                 │ (LLM with context)  │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │ Chat END            │
                 └─────────────────────┘
```

## Node Implementation Pattern

Every agent follows this same pattern:

```python
@node
async def ocr_agent_node(state: ApplicationState) -> dict:
    """Process all uploaded documents through OCR pipeline."""

    # 1. Log entry with LangFuse
    with langfuse.trace(name="ocr_agent", application_id=state["application_id"]) as trace:

        results = {}
        errors = []

        for doc in state["documents"]:
            if doc.ocr_status == "completed":
                continue  # Skip already processed

            try:
                # 2. Select strategy based on document type
                strategy = OCRStrategyFactory.get_strategy(doc.document_type)

                # 3. Execute with retry
                result = await retry_with_backoff(
                    strategy.process,
                    doc=doc,
                    max_retries=state["max_retries"]
                )

                # 4. Validate output quality
                if result.confidence < MIN_OCR_CONFIDENCE:
                    raise LowConfidenceError(result.confidence)

                results[doc.document_type] = result

                # 5. Store in MongoDB
                await document_store.save_ocr_result(state["application_id"], doc.id, result)

            except Exception as e:
                errors.append(WorkflowError(
                    agent="ocr",
                    document_id=doc.id,
                    error=str(e),
                    retry_count=doc.retry_count
                ))

        # 6. Determine next state
        return {
            "ocr_results": results,
            "errors": state["errors"] + errors,
            "extraction_complete": len(errors) == 0,
        }
```

## Checkpointing & Human-in-the-Loop

LangGraph's built-in `interrupt` is used:

```python
from langgraph.checkpoint import MemorySaver

# Configure checkpointer to persist after every node
checkpointer = MemorySaver()

graph = workflow.compile(checkpointer=checkpointer)

# At validation checkpoint:
if len(state["inconsistencies"]) > 0:
    # The graph will pause here and wait for external resume
    interrupt_after = "validation_node"

# Resume via API:
# POST /api/v1/applications/{id}/resume
# With payload: {"action": "approved", "notes": "Inconsistencies resolved manually"}
```

## Retry Strategy

```python
RETRY_CONFIG = {
    "ocr_node":           {"max_retries": 3, "backoff": "exponential", "on_failure": "skip_document"},
    "validation_node":    {"max_retries": 2, "backoff": "linear",      "on_failure": "flag_for_review"},
    "knowledge_node":     {"max_retries": 2, "backoff": "exponential", "on_failure": "empty_result"},
    "ml_prediction_node": {"max_retries": 1, "backoff": "none",        "on_failure": "fallback_to_llm"},
    "decision_node":      {"max_retries": 2, "backoff": "exponential", "on_failure": "escalate_to_human"},
}
```

## Conditional Edges

```python
def route_after_validation(state: ApplicationState) -> str:
    """Determine next step based on validation results."""
    if state["requires_human_review"]:
        return "human_review"
    return "knowledge_node"

def route_after_decision(state: ApplicationState) -> str:
    """Determine if human sign-off is needed before finalizing."""
    if state["decision_confidence"] < AUTO_APPROVE_THRESHOLD:
        return "human_signoff"
    return "recommendation_node"
```
