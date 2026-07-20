from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VectorSearchResult:
    id: str
    score: float
    payload: dict
    vector: list[float] | None = None


@dataclass
class VectorRecord:
    id: str
    vector: list[float]
    payload: dict


class IVectorStore(ABC):
    """Interface for vector similarity search.

    Implementations can use Qdrant, Redis Stack with RediSearch,
    or pgvector without affecting retrieval logic.
    """

    @abstractmethod
    async def create_collection(self, collection_name: str, vector_size: int) -> None:
        """Create a new collection with the specified vector dimensions."""
        ...

    @abstractmethod
    async def upsert(self, collection_name: str, records: list[VectorRecord]) -> None:
        """Insert or update vectors in a collection."""
        ...

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filter_payload: dict | None = None,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors with optional payload filtering."""
        ...

    @abstractmethod
    async def delete(self, collection_name: str, record_ids: list[str]) -> None:
        """Delete vectors by their IDs."""
        ...

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> None:
        """Remove an entire collection."""
        ...

    @abstractmethod
    async def collection_info(self, collection_name: str) -> dict:
        """Get metadata about a collection (count, dimension, etc.)."""
        ...
