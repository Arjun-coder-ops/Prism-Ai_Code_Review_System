from dataclasses import dataclass
from typing import Any

import pytest

from app.ai.providers import FailoverJsonProvider, ProviderUnavailableError


@dataclass
class FakeProvider:
    name: str
    result: dict[str, Any] | None = None
    unavailable: bool = False

    async def complete_json(self, prompt: str) -> dict[str, Any]:
        assert prompt == "evidence-only prompt"
        if self.unavailable:
            raise ProviderUnavailableError("unavailable")
        assert self.result is not None
        return self.result


@pytest.mark.anyio
async def test_uses_groq_result_when_primary_is_available() -> None:
    provider = FailoverJsonProvider(
        primary=FakeProvider("groq", {"findings": []}),
        fallback=FakeProvider("gemini", {"findings": ["unexpected"]}),
    )

    provider_name, result = await provider.complete_json("evidence-only prompt")

    assert provider_name == "groq"
    assert result == {"findings": []}


@pytest.mark.anyio
async def test_uses_gemini_only_when_groq_is_unavailable() -> None:
    provider = FailoverJsonProvider(
        primary=FakeProvider("groq", unavailable=True),
        fallback=FakeProvider("gemini", {"findings": []}),
    )

    provider_name, result = await provider.complete_json("evidence-only prompt")

    assert provider_name == "gemini"
    assert result == {"findings": []}
