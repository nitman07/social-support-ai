from uuid import UUID

from neo4j import AsyncGraphDatabase, AsyncDriver

from backend.core.config import settings
from backend.domain.ports import IGraphStore, GraphNode, GraphRelationship, GraphPath


class Neo4jGraphStore(IGraphStore):
    """Neo4j implementation of IGraphStore for entity relationship management.

    Stores applicants, family members, employers, assets, liabilities,
    and their interconnections for fraud detection and relationship discovery.
    """

    def __init__(self) -> None:
        self.driver: AsyncDriver | None = None

    async def connect(self) -> None:
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_dsn,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def close(self) -> None:
        if self.driver:
            await self.driver.close()

    async def create_node(self, node_id: str, labels: list[str], properties: dict) -> None:
        if not self.driver:
            raise RuntimeError("Neo4j not connected")
        labels_str = ":".join(labels)
        properties["id"] = node_id
        async with self.driver.session(database=settings.neo4j_database) as session:
            await session.run(
                f"MERGE (n:{labels_str} {{id: $id}}) SET n += $properties",
                id=node_id,
                properties=properties,
            )

    async def create_relationship(
        self, from_id: str, to_id: str, rel_type: str, properties: dict | None = None
    ) -> None:
        if not self.driver:
            raise RuntimeError("Neo4j not connected")
        async with self.driver.session(database=settings.neo4j_database) as session:
            await session.run(
                f"MATCH (a {{id: $from_id}}), (b {{id: $to_id}}) "
                f"MERGE (a)-[r:{rel_type}]->(b) "
                f"SET r += $properties",
                from_id=from_id,
                to_id=to_id,
                properties=properties or {},
            )

    async def get_node(self, node_id: str) -> GraphNode | None:
        if not self.driver:
            raise RuntimeError("Neo4j not connected")
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(
                "MATCH (n {id: $id}) RETURN labels(n) AS labels, properties(n) AS props",
                id=node_id,
            )
            record = await result.single()
            if not record:
                return None
            props = dict(record["props"])
            props.pop("id", None)
            return GraphNode(labels=list(record["labels"]), properties=props)

    async def get_relationships(
        self, node_id: str, rel_type: str | None = None, direction: str = "both"
    ) -> list[GraphRelationship]:
        if not self.driver:
            raise RuntimeError("Neo4j not connected")
        direction_pattern = {
            "outgoing": "(a)-[r]->(b)",
            "incoming": "(a)<-[r]-(b)",
            "both": "(a)-[r]-(b)",
        }.get(direction, "(a)-[r]-(b)")

        type_filter = f"TYPE(r) = '{rel_type}'" if rel_type else "true"
        query = f"MATCH {direction_pattern} WHERE a.id = $node_id AND {type_filter} RETURN r, startNode(r).id AS from_id, endNode(r).id AS to_id"

        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, node_id=node_id)
            relationships = []
            async for record in result:
                rel = record["r"]
                relationships.append(
                    GraphRelationship(
                        type=rel.type,
                        from_node_id=record["from_id"],
                        to_node_id=record["to_id"],
                        properties=dict(rel),
                    )
                )
            return relationships

    async def find_path(self, from_id: str, to_id: str, max_hops: int = 5) -> list[GraphPath]:
        if not self.driver:
            raise RuntimeError("Neo4j not connected")
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(
                "MATCH path = shortestPath((a {id: $from_id})-[*1..$max_hops]-(b {id: $to_id})) "
                "RETURN nodes(path) AS nodes, relationships(path) AS relationships",
                from_id=from_id,
                to_id=to_id,
                max_hops=max_hops,
            )
            paths = []
            async for record in result:
                nodes = []
                for node in record["nodes"]:
                    props = dict(node)
                    props.pop("id", None)
                    nodes.append(GraphNode(labels=list(node.labels), properties=props))
                rels = [
                    GraphRelationship(
                        type=rel.type,
                        from_node_id=rel.start_node["id"],
                        to_node_id=rel.end_node["id"],
                        properties=dict(rel),
                    )
                    for rel in record["relationships"]
                ]
                paths.append(GraphPath(nodes=nodes, relationships=rels))
            return paths

    async def query(self, cypher: str, params: dict | None = None) -> list[dict]:
        if not self.driver:
            raise RuntimeError("Neo4j not connected")
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(cypher, params or {})
            return [dict(record) async for record in result]

    async def delete_node(self, node_id: str) -> None:
        if not self.driver:
            raise RuntimeError("Neo4j not connected")
        async with self.driver.session(database=settings.neo4j_database) as session:
            await session.run(
                "MATCH (n {id: $id}) DETACH DELETE n",
                id=node_id,
            )

    async def build_applicant_graph(
        self,
        applicant_id: UUID,
        family_members: list[dict] | None = None,
        employers: list[dict] | None = None,
        assets: list[dict] | None = None,
        liabilities: list[dict] | None = None,
    ) -> None:
        """Build or update the full Neo4j graph for an applicant.

        Creates applicant, family, employer, asset, liability, and
        application nodes with typed relationships. Idempotent via MERGE.

        Args:
            applicant_id: UUID of the applicant to build graph for.
            family_members: List of dicts with name, relationship, is_dependent.
            employers: List of dicts with name, position, start_date, end_date.
            assets: List of dicts with type, value, description.
            liabilities: List of dicts with type, amount, monthly_payment.
        """
        uid = str(applicant_id)

        async with self.driver.session(database=settings.neo4j_database) as session:
            await session.run(
                """
                MATCH (a:Applicant {id: $id})
                OPTIONAL MATCH (a)-[r]-()
                DELETE r
                """,
                id=uid,
            )

            if family_members:
                for fm in family_members:
                    fm_id = f"{uid}_family_{fm.get('name', 'unknown')}"
                    await session.run(
                        """
                        MERGE (fm:FamilyMember {id: $id})
                        SET fm += $props
                        WITH fm
                        MATCH (a:Applicant {id: $applicant_id})
                        MERGE (a)-[:HAS_FAMILY {relationship: $rel}]->(fm)
                        """,
                        id=fm_id,
                        props=fm,
                        rel=fm.get("relationship", "unknown"),
                        applicant_id=uid,
                    )

            if employers:
                for emp in employers:
                    emp_id = f"{uid}_employer_{emp.get('name', 'unknown')}"
                    await session.run(
                        """
                        MERGE (e:Employer {id: $id})
                        SET e += $props
                        WITH e
                        MATCH (a:Applicant {id: $applicant_id})
                        MERGE (a)-[:EMPLOYED_AT {
                            position: $position,
                            from: $from_date,
                            to: $to_date
                        }]->(e)
                        """,
                        id=emp_id,
                        props=emp,
                        position=emp.get("position", ""),
                        from_date=emp.get("start_date", ""),
                        to_date=emp.get("end_date", ""),
                        applicant_id=uid,
                    )

            if assets:
                for asset in assets:
                    asset_id = f"{uid}_asset_{asset.get('type', 'unknown')}"
                    await session.run(
                        """
                        MERGE (as:Asset {id: $id})
                        SET as += $props
                        WITH as
                        MATCH (a:Applicant {id: $applicant_id})
                        MERGE (a)-[:OWNS]->(as)
                        """,
                        id=asset_id,
                        props=asset,
                        applicant_id=uid,
                    )

            if liabilities:
                for liability in liabilities:
                    liab_id = f"{uid}_liability_{liability.get('type', 'unknown')}"
                    await session.run(
                        """
                        MERGE (l:Liability {id: $id})
                        SET l += $props
                        WITH l
                        MATCH (a:Applicant {id: $applicant_id})
                        MERGE (a)-[:HAS_LIABILITY]->(l)
                        """,
                        id=liab_id,
                        props=liability,
                        applicant_id=uid,
                    )


neo4j_graph_store = Neo4jGraphStore()
