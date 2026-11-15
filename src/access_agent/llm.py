"""The model client.

Claude is called through the Anthropic SDK, not a framework wrapper, for two
reasons: one switch moves between an API key and keyless sign-in to Microsoft
Foundry, and the SDK reports exact token counts for cost per task.

    ANTHROPIC_API_KEY set          -> the Anthropic API
    FOUNDRY_RESOURCE set, no key   -> Claude on Foundry, signed in with Entra ID
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol

DEFAULT_MODEL = "claude-haiku-5-5"
FOUNDRY_SCOPE = "https://ai.azure.com/.default"
MAX_TOKENS = 1024


@dataclass
class Reply:
    """One model turn, in plain data so it can be stored in graph state."""

    content: list[dict[str, Any]]
    stop_reason: str
    input_tokens: int = 0
    output_tokens: int = 0

    def tool_uses(self) -> list[dict[str, Any]]:
        return [block for block in self.content if block.get("type") == "tool_use"]

    def text(self) -> str:
        return " ".join(block.get("text", "") for block in self.content if block.get("type") == "text").strip()


class Model(Protocol):
    name: str

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: dict[str, Any] | None = None,
    ) -> Reply: ...


def make_client() -> Any:
    """Pick the client from the environment. Imports stay inside so tests need no SDK."""
    import anthropic

    if os.getenv("ANTHROPIC_API_KEY"):
        return anthropic.Anthropic()

    resource = os.getenv("FOUNDRY_RESOURCE")
    if not resource:
        raise RuntimeError("Set ANTHROPIC_API_KEY, or FOUNDRY_RESOURCE for keyless sign-in to Foundry.")

    from azure.identity import (
        AzureCliCredential,
        ChainedTokenCredential,
        EnvironmentCredential,
        ManagedIdentityCredential,
        get_bearer_token_provider,
    )

    # Named sources only, in a fixed order, so a run never signs in as an account
    # nobody chose: a managed identity when deployed, a service principal from the
    # environment for unattended jobs, then the caller's own `az login`.
    sources: list[Any] = []
    if os.getenv("AZURE_CLIENT_ID") and os.getenv("IDENTITY_ENDPOINT"):
        sources.append(ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"]))
    if os.getenv("AZURE_CLIENT_ID") and os.getenv("AZURE_TENANT_ID"):
        sources.append(EnvironmentCredential())
    tenant = os.getenv("AZURE_TENANT_ID")
    sources.append(AzureCliCredential(tenant_id=tenant) if tenant else AzureCliCredential())
    provider = get_bearer_token_provider(ChainedTokenCredential(*sources), FOUNDRY_SCOPE)
    return anthropic.AnthropicFoundry(resource=resource, azure_ad_token_provider=provider)


@dataclass
class ClaudeModel:
    name: str = field(default_factory=lambda: os.getenv("ACCESS_AGENT_MODEL", DEFAULT_MODEL))
    client: Any = None

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = make_client()

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: dict[str, Any] | None = None,
    ) -> Reply:
        kwargs: dict[str, Any] = {
            "model": self.name,
            "max_tokens": MAX_TOKENS,
            "system": system,
            "messages": messages,
            "tools": tools,
        }
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
        response = self.client.messages.create(**kwargs)
        content = [block.model_dump(mode="json", exclude_none=True) for block in response.content]
        return Reply(
            content=[b for b in content if b.get("type") in ("text", "tool_use")],
            stop_reason=response.stop_reason or "",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )


class ScriptedModel:
    """A stand-in for tests: answers from a function, and counts as a model."""

    name = "scripted"

    def __init__(self, respond: Any) -> None:
        self._respond = respond
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: dict[str, Any] | None = None,
    ) -> Reply:
        call = {"system": system, "messages": messages, "tools": tools, "tool_choice": tool_choice}
        self.calls.append(call)
        return self._respond(call)


def tool_use(name: str, args: dict[str, Any], call_id: str = "call-1") -> dict[str, Any]:
    """A tool_use block, for scripted replies."""
    return {"type": "tool_use", "id": call_id, "name": name, "input": args}
