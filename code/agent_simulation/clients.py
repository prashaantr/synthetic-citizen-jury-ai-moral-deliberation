from __future__ import annotations

import os
from typing import Any, Protocol


class ModelClient(Protocol):
    provider: str

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.2,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Return one model completion."""


class DryRunClient:
    provider = "dry-run"

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.2,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        metadata = metadata or {}
        agent = metadata.get("agent_name", "synthesizer")
        round_title = metadata.get("round_title", "round")
        prompt_preview = " ".join(user_prompt.split())[:260]
        system_preview = " ".join(system_prompt.split())[:180]
        return (
            f"Dry-run response for {agent} in {round_title}.\n"
            f"No model call was made. Model setting: {model}.\n\n"
            f"System focus: {system_preview}\n\n"
            f"Prompt focus: {prompt_preview}"
        )


class OpenAIChatClient:
    provider = "openai"

    def __init__(self, api_key: str | None = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The OpenAI provider requires the optional dependency: "
                "pip install -e '.[openai]'"
            ) from exc

        resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required when using --provider openai."
            )

        self._client = OpenAI(api_key=resolved_api_key)

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.2,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        response = self._client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned an empty response.")
        return content


def create_client(provider: str) -> ModelClient:
    if provider == "dry-run":
        return DryRunClient()
    if provider == "openai":
        return OpenAIChatClient()
    raise ValueError(f"Unsupported provider: {provider}")
