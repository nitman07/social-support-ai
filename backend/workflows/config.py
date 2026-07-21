from backend.core.config import settings

RETRY_CONFIG: dict[str, dict] = {
    "ocr_node": {
        "max_retries": 3,
        "backoff": "exponential",
        "on_failure": "skip_document",
    },
    "validation_node": {
        "max_retries": 2,
        "backoff": "linear",
        "on_failure": "flag_for_review",
    },
    "knowledge_node": {
        "max_retries": 2,
        "backoff": "exponential",
        "on_failure": "empty_result",
    },
    "eligibility_node": {
        "max_retries": 1,
        "backoff": "none",
        "on_failure": "fallback_to_rules",
    },
    "decision_node": {
        "max_retries": 2,
        "backoff": "exponential",
        "on_failure": "escalate_to_human",
    },
}

CHECKPOINT_CONFIG = {
    "thread_id_key": "workflow_id",
    "postgres_table": "langgraph_checkpoints",
}

AUTO_APPROVE_THRESHOLD = settings.ml_auto_approve_threshold
AUTO_DECLINE_THRESHOLD = settings.ml_auto_decline_threshold
HITL_INCONSISTENCY_THRESHOLD = settings.workflow_hitl_inconsistency_threshold
MAX_RETRIES = settings.workflow_max_retries
