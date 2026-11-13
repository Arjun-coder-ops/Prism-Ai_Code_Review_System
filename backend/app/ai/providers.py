import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class ProviderUnavailableError(RuntimeError):
    """A provider failed without exposing its response or credentials."""


class StructuredResponseError(ValueError):
    """A provider response cannot be treated as a structured candidate."""


class JsonCompletionProvider(Protocol):
    name: str

    async def complete_json(self, prompt: str) -> dict[str, Any]: ...


@dataclass
class GroqProvider:
    api_key: str
    model: str
    client: httpx.AsyncClient
    name: str = "groq"

    async def complete_json(self, prompt: str) -> dict[str, Any]:
        try:
            response = await self.client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return _parse_json_object(content)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise ProviderUnavailableError("groq response unavailable") from exc


@dataclass
class GeminiProvider:
    api_key: str
    model: str
    client: httpx.AsyncClient
    name: str = "gemini"

    async def complete_json(self, prompt: str) -> dict[str, Any]:
        try:
            response = await self.client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                headers={"x-goog-api-key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"},
                },
            )
            response.raise_for_status()
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return _parse_json_object(content)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise ProviderUnavailableError("gemini response unavailable") from exc


@dataclass
class FailoverJsonProvider:
    primary: JsonCompletionProvider
    fallback: JsonCompletionProvider
    on_fallback: Callable[[str, str], Awaitable[None]] | None = None

    async def complete_json(self, prompt: str) -> tuple[str, dict[str, Any]]:
        try:
            return self.primary.name, await self.primary.complete_json(prompt)
        except ProviderUnavailableError:
            if self.on_fallback is not None:
                await self.on_fallback(self.primary.name, self.fallback.name)
            return self.fallback.name, await self.fallback.complete_json(prompt)


def _parse_json_object(content: object) -> dict[str, Any]:
    if not isinstance(content, str):
        raise StructuredResponseError("expected JSON text")
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise StructuredResponseError("expected a JSON object")
    return parsed
