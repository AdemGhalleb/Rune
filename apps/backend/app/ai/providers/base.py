"""Provider boundaries used by the RAG and embedding services."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProviderError(RuntimeError):
    pass


class LLMProviderUnavailable(LLMProviderError):
    pass


class EmbeddingProviderError(RuntimeError):
    pass


class EmbeddingProviderUnavailable(EmbeddingProviderError):
    pass


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str: ...

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncIterator[str]: ...

    @abstractmethod
    async def is_available(self) -> bool: ...


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    async def is_available(self) -> bool: ...
