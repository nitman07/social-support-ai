import time

from langchain_ollama import ChatOllama, OllamaEmbeddings

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.domain.ports import EmbeddingResponse, ILLMService, LLMResponse

logger = get_logger(__name__)


class OllamaLLMService(ILLMService):
    def __init__(self) -> None:
        self._llm = ChatOllama(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_host,
            temperature=0.1,
            num_predict=1024,
        )
        self._embeddings = OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_host,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        start = time.monotonic()
        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("human", prompt))
        response = await self._llm.ainvoke(messages)
        duration = (time.monotonic() - start) * 1000
        return LLMResponse(
            content=response.content,
            model=settings.ollama_llm_model,
            prompt_tokens=response.usage_metadata.get("input_tokens", 0) if response.usage_metadata else 0,
            response_tokens=response.usage_metadata.get("output_tokens", 0) if response.usage_metadata else 0,
            total_duration_ms=round(duration, 2),
        )

    async def generate_with_context(
        self,
        prompt: str,
        context: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        grounded_prompt = f"Context:\n{context}\n\nQuestion:\n{prompt}"
        return await self.generate(grounded_prompt, system_prompt, temperature, max_tokens)

    async def embed(self, text: str) -> EmbeddingResponse:
        start = time.monotonic()
        vector = await self._embeddings.aembed_query(text)
        duration = (time.monotonic() - start) * 1000
        return EmbeddingResponse(
            vector=vector,
            model=settings.ollama_embedding_model,
            total_duration_ms=round(duration, 2),
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
        start = time.monotonic()
        vectors = await self._embeddings.aembed_documents(texts)
        duration = (time.monotonic() - start) * 1000
        return [
            EmbeddingResponse(
                vector=v,
                model=settings.ollama_embedding_model,
                total_duration_ms=round(duration, 2),
            )
            for v in vectors
        ]

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        start = time.monotonic()
        langchain_messages = [(m["role"], m["content"]) for m in messages]
        llm = ChatOllama(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_host,
            temperature=temperature,
            num_predict=max_tokens,
        )
        response = await llm.ainvoke(langchain_messages)
        duration = (time.monotonic() - start) * 1000
        return LLMResponse(
            content=response.content,
            model=settings.ollama_llm_model,
            prompt_tokens=response.usage_metadata.get("input_tokens", 0) if response.usage_metadata else 0,
            response_tokens=response.usage_metadata.get("output_tokens", 0) if response.usage_metadata else 0,
            total_duration_ms=round(duration, 2),
        )


llm_service = OllamaLLMService()
