from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from backend.core.logging import get_logger
from backend.workflows.edges import route_after_decision, route_after_validation
from backend.workflows.nodes import (
    decision_node,
    eligibility_node,
    human_review_node,
    intake_node,
    knowledge_node,
    ocr_node,
    recommendation_node,
    validation_node,
)
from backend.workflows.state import ApplicationState

logger = get_logger(__name__)


def build_application_graph() -> StateGraph:
    workflow = StateGraph(ApplicationState)

    workflow.add_node("intake", intake_node)
    workflow.add_node("ocr", ocr_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("knowledge", knowledge_node)
    workflow.add_node("eligibility", eligibility_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("human_signoff", human_review_node)
    workflow.add_node("recommendation", recommendation_node)

    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "ocr")
    workflow.add_edge("ocr", "validation")

    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "human_review": "human_review",
            "knowledge_node": "knowledge",
        },
    )
    workflow.add_edge("human_review", "knowledge")
    workflow.add_edge("knowledge", "eligibility")
    workflow.add_edge("eligibility", "decision")

    workflow.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "human_signoff": "human_signoff",
            "recommendation_node": "recommendation",
        },
    )
    workflow.add_edge("human_signoff", "recommendation")
    workflow.add_edge("recommendation", END)

    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    logger.info("Application workflow graph compiled with MemorySaver checkpointing")
    return app


application_graph = build_application_graph()
