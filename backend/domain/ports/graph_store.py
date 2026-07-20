from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class GraphNode:
    labels: list[str]
    properties: dict[str, Any]


@dataclass
class GraphRelationship:
    type: str
    from_node_id: str
    to_node_id: str
    properties: dict[str, Any] | None = None


@dataclass
class GraphPath:
    """Result of a multi-hop graph traversal."""
    nodes: list[GraphNode]
    relationships: list[GraphRelationship]


class IGraphStore(ABC):
    """Interface for graph database operations.

    Implementations can use Neo4j, ArangoDB, or Amazon Neptune
    without affecting entity resolution logic.
    """

    @abstractmethod
    async def create_node(self, node_id: str, labels: list[str], properties: dict[str, Any]) -> None:
        ...

    @abstractmethod
    async def create_relationship(
        self, from_id: str, to_id: str, rel_type: str, properties: dict[str, Any] | None = None
    ) -> None:
        ...

    @abstractmethod
    async def get_node(self, node_id: str) -> GraphNode | None:
        ...

    @abstractmethod
    async def get_relationships(
        self, node_id: str, rel_type: str | None = None, direction: str = "both"
    ) -> list[GraphRelationship]:
        ...

    @abstractmethod
    async def find_path(
        self, from_id: str, to_id: str, max_hops: int = 5
    ) -> list[GraphPath]:
        """Find all paths between two nodes up to max_hops depth."""
        ...

    @abstractmethod
    async def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a raw Cypher query for complex traversals."""
        ...

    @abstractmethod
    async def delete_node(self, node_id: str) -> None:
        ...

    @abstractmethod
    async def build_applicant_graph(self, applicant_id: UUID) -> None:
        """Create/update the full graph for an applicant including:
        - Applicant node
        - Family member nodes with HAS_FAMILY relationships
        - Employer nodes with EMPLOYED_AT relationships
        - Asset and liability nodes
        - Previous application nodes
        """
        ...
