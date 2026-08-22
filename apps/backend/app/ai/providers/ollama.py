"""Ollama-backed local chat and embedding providers."""

import json
import time
from collections.abc import AsyncIterator

import httpx

from app.ai.providers.base import (
    EmbeddingProvider,
    EmbeddingProviderError,
    EmbeddingProviderUnavailable,
    LLMProvider,
    LLMProviderError,
    LLMProviderUnavailable,
)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str, timeout_seconds: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._available_until = 0.0
        self._available = False

    async def is_available(self) -> bool:
        if time.monotonic() < self._available_until:
            return self._available
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                self._available = response.is_success
        except httpx.HTTPError:
            self._available = False
        self._available_until = time.monotonic() + 3.0
        return self._available

    async def generate(self, prompt: str) -> str:
        return "".join([part async for part in self.stream(prompt)])

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        if not await self.is_available():
            raise LLMProviderUnavailable("Ollama isn't running")
        payload = {"model": self.model, "prompt": prompt, "stream": True}
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout_seconds, connect=3.0)) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError as err:
                            raise LLMProviderError("Ollama returned malformed streaming data") from err
                        token = event.get("response")
                        if isinstance(token, str) and token:
                            yield token
                        if event.get("done"):
                            return
        except httpx.TimeoutException as err:
            raise LLMProviderError("Ollama request timed out") from err
        except httpx.HTTPError as err:
            raise LLMProviderUnavailable("Ollama isn't running") from err


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, base_url: str, model: str, timeout_seconds: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._available_until = 0.0
        self._available = False

    async def is_available(self) -> bool:
        if time.monotonic() < self._available_until:
            return self._available
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                self._available = response.is_success
        except httpx.HTTPError:
            self._available = False
        self._available_until = time.monotonic() + 3.0
        return self._available

    async def embed(self, text: str) -> list[float]:
        if not await self.is_available():
            raise EmbeddingProviderUnavailable("Ollama isn't running")
        payload = {"model": self.model, "input": text}
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout_seconds, connect=3.0)) as client:
                response = await client.post(f"{self.base_url}/api/embed", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as err:
            raise EmbeddingProviderError("Ollama embedding request timed out") from err
        except httpx.HTTPError as err:
            raise EmbeddingProviderUnavailable("Ollama isn't running") from err

        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise EmbeddingProviderError("Ollama returned no embeddings")
        vector = embeddings[0]
        if not isinstance(vector, list):
            raise EmbeddingProviderError("Ollama returned malformed embeddings")
        return [float(item) for item in vector]
