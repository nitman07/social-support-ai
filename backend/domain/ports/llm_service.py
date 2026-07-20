from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int
    response_tokens: int
    total_duration_ms: float


@dataclass
class EmbeddingResponse:
    vector: list[float]
    model: str
    total_duration_ms: float


class ILLMService(ABC):
    """Interface for LLM and embedding operations.

    Implementations can use Ollama, vLLM, or cloud APIs
    without affecting agent logic.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate text response from an LLM with low temperature for consistency."""
        ...

    @abstractmethod
    async def generate_with_context(
        self,
        prompt: str,
        context: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate response grounded in provided context (for RAG)."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResponse:
        """Generate embedding vector for a text string."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
        """Generate embeddings for multiple texts efficiently."""
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Multi-turn chat interaction."""
        ...
