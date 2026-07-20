import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from backend.core.config import settings
from backend.domain.ports import IVectorStore, VectorRecord, VectorSearchResult


class QdrantVectorStore(IVectorStore):
    """Qdrant implementation of IVectorStore for vector similarity search.

    Collections are created per domain (policies, programs, FAQs) with
    configurable vector sizes matching the embedding model dimensions.
    """

    COLLECTION_POLICIES = "government_policies"
    COLLECTION_PROGRAMS = "training_programs"
    COLLECTION_FAQS = "faq_embeddings"

    def __init__(self) -> None:
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            prefer_grpc=settings.qdrant_prefer_grpc,
        )

    async def create_collection(self, collection_name: str, vector_size: int) -> None:
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def _to_point_id(self, id: str) -> int | str:
        try:
            return uuid.UUID(id)
        except ValueError:
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, id))

    async def upsert(self, collection_name: str, records: list[VectorRecord]) -> None:
        points = [
            models.PointStruct(
                id=self._to_point_id(record.id),
                vector=record.vector,
                payload=record.payload,
            )
            for record in records
        ]
        self.client.upsert(
            collection_name=collection_name,
            points=points,
        )

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filter_payload: dict | None = None,
    ) -> list[VectorSearchResult]:
        search_filter = None
        if filter_payload:
            conditions = [
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value),
                )
                for key, value in filter_payload.items()
            ]
            search_filter = models.Filter(must=conditions)

        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=search_filter,
        )

        return [
            VectorSearchResult(
                id=str(r.id),
                score=r.score,
                payload=r.payload or {},
            )
            for r in results
        ]

    async def delete(self, collection_name: str, record_ids: list[str]) -> None:
        self.client.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(
                points=[self._to_point_id(rid) for rid in record_ids],
            ),
        )

    async def delete_collection(self, collection_name: str) -> None:
        self.client.delete_collection(collection_name)

    async def collection_info(self, collection_name: str) -> dict:
        info = self.client.get_collection(collection_name)
        return {
            "name": collection_name,
            "points_count": info.points_count,
            "segments_count": info.segments_count,
            "status": info.status,
        }


qdrant_vector_store = QdrantVectorStore()
