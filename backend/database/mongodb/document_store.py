import io
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket

from backend.core.config import settings
from backend.domain.entities.document import Document
from backend.domain.ports import IDocumentStore


class MongoDocumentStore(IDocumentStore):
    """MongoDB implementation of IDocumentStore using GridFS for binary files."""

    def __init__(self) -> None:
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self.bucket: AsyncIOMotorGridFSBucket | None = None

    async def connect(self) -> None:
        self.client = AsyncIOMotorClient(settings.mongodb_dsn)
        self.db = self.client[settings.mongodb_db]
        self.bucket = AsyncIOMotorGridFSBucket(self.db)

    async def close(self) -> None:
        if self.client is not None:
            self.client.close()

    async def upload(self, document: Document, content: bytes) -> str:
        if self.bucket is None:
            raise RuntimeError("MongoDB not connected")
        if isinstance(content, (bytes, bytearray)):
            source = io.BytesIO(bytes(content))
        else:
            source = content
        grid_id = await self.bucket.upload_from_stream(
            filename=document.file_name,
            source=source,
            metadata={
                "document_id": str(document.id),
                "application_id": str(document.application_id),
                "document_type": document.document_type.value,
                "mime_type": document.mime_type,
            },
        )
        return str(grid_id)

    async def download(self, document: Document) -> bytes:
        if self.bucket is None:
            raise RuntimeError("MongoDB not connected")
        stream = await self.bucket.open_download_stream_by_name(document.file_name)
        chunks = []
        while True:
            chunk = await stream.read()
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)

    async def delete(self, document: Document) -> None:
        if self.bucket is None:
            raise RuntimeError("MongoDB not connected")
        cursor = self.db.fs.files.find({"metadata.document_id": str(document.id)})
        async for file_doc in cursor:
            await self.bucket.delete(file_doc["_id"])

    async def save_ocr_result(
        self,
        application_id: UUID,
        document_id: UUID,
        text: str,
        tables: list[dict] | None = None,
    ) -> None:
        if self.db is None:
            raise RuntimeError("MongoDB not connected")
        await self.db.ocr_results.update_one(
            {"document_id": str(document_id)},
            {
                "$set": {
                    "application_id": str(application_id),
                    "document_id": str(document_id),
                    "text": text,
                    "tables": tables or [],
                    "processed_at": None,
                }
            },
            upsert=True,
        )

    async def get_ocr_result(self, application_id: UUID, document_id: UUID) -> dict | None:
        if self.db is None:
            raise RuntimeError("MongoDB not connected")
        result = await self.db.ocr_results.find_one(
            {"document_id": str(document_id), "application_id": str(application_id)}
        )
        if result:
            result.pop("_id", None)
        return result


mongo_document_store = MongoDocumentStore()
