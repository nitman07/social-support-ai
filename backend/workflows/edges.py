from backend.core.logging import get_logger
from backend.workflows.config import AUTO_APPROVE_THRESHOLD, HITL_INCONSISTENCY_THRESHOLD
from backend.workflows.state import ApplicationState

logger = get_logger(__name__)


def route_after_validation(state: ApplicationState) -> str:
    inconsistencies = state.get("inconsistencies", [])
    high_severity = [i for i in inconsistencies if i.get("severity") == "high"]
    if len(high_severity) >= HITL_INCONSISTENCY_THRESHOLD:
        logger.info(f"Routing to human_review: {len(high_severity)} high-severity inconsistencies")
        return "human_review"
    return "knowledge_node"


def route_after_decision(state: ApplicationState) -> str:
    decision = state.get("decision")
    confidence = state.get("decision_confidence", 0.0)
    if decision == "declined" or confidence < 0.5:
        logger.info(f"Routing to human_signoff: decision={decision}, confidence={confidence}")
        return "human_signoff"
    return "recommendation_node"


def route_after_human_signoff(state: ApplicationState) -> str:
    return "recommendation_node"
