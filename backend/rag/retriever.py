from backend.core.logging import get_logger
from backend.database.qdrant.vector_store import qdrant_vector_store
from backend.services.llm_service import llm_service
from backend.workflows.state import PolicyContext

logger = get_logger(__name__)

COLLECTION_POLICIES = qdrant_vector_store.COLLECTION_POLICIES
EMBEDDING_SIZE = 768


async def retrieve_policies(query: str, top_k: int = 3) -> list[PolicyContext]:
    embedding = await llm_service.embed(query)
    results = await qdrant_vector_store.search(
        collection_name=COLLECTION_POLICIES,
        query_vector=embedding.vector,
        limit=top_k,
        score_threshold=0.0,
    )
    policies = []
    for r in results:
        policies.append(PolicyContext(
            id=r.id,
            title=r.payload.get("title", ""),
            content=r.payload.get("content", r.payload.get("title", "")),
            relevance_score=r.score,
        ))
    return policies
