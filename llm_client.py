#!/usr/bin/env python3
"""
Unified LLM Client for Critique-Oriented RAG
==============================================
Supports multiple LLM providers through a common interface:
  - Anthropic (Claude)
  - OpenAI (ChatGPT)
  - Google Gemini
  - DeepSeek
  - Kimi (Moonshot AI)
  - MiniMax
  - GLM (Zhipu AI / ChatGLM)

Most providers use OpenAI-compatible APIs, making integration straightforward.
"""

import os
from typing import Optional


# ---------------------------------------------------------------------------
# Provider Registry
# ---------------------------------------------------------------------------
PROVIDERS = {
    "anthropic": {
        "name": "Anthropic (Claude)",
        "env_key": "ANTHROPIC_API_KEY",
        "env_base_url": "ANTHROPIC_BASE_URL",
        "default_base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-20250514",
        "sdk": "anthropic",
    },
    "openai": {
        "name": "OpenAI (ChatGPT)",
        "env_key": "OPENAI_API_KEY",
        "env_base_url": "OPENAI_BASE_URL",
        "default_base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "sdk": "openai",
    },
    "gemini": {
        "name": "Google Gemini",
        "env_key": "GEMINI_API_KEY",
        "env_base_url": "GEMINI_BASE_URL",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-2.0-flash",
        "sdk": "openai",  # Gemini supports OpenAI-compatible endpoint
    },
    "deepseek": {
        "name": "DeepSeek",
        "env_key": "DEEPSEEK_API_KEY",
        "env_base_url": "DEEPSEEK_BASE_URL",
        "default_base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "sdk": "openai",
    },
    "kimi": {
        "name": "Kimi (Moonshot AI)",
        "env_key": "KIMI_API_KEY",
        "env_base_url": "KIMI_BASE_URL",
        "default_base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-128k",
        "sdk": "openai",
    },
    "minimax": {
        "name": "MiniMax",
        "env_key": "MINIMAX_API_KEY",
        "env_base_url": "MINIMAX_BASE_URL",
        "default_base_url": "https://api.minimax.chat/v1",
        "default_model": "MiniMax-Text-01",
        "sdk": "openai",
    },
    "glm": {
        "name": "GLM (Zhipu AI / ChatGLM)",
        "env_key": "GLM_API_KEY",
        "env_base_url": "GLM_BASE_URL",
        "default_base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-plus",
        "sdk": "openai",
    },
}


def list_providers() -> dict:
    """Return all supported providers with their info."""
    return PROVIDERS


def get_available_providers() -> list:
    """Return providers that have API keys configured."""
    available = []
    for provider_id, info in PROVIDERS.items():
        if os.environ.get(info["env_key"]):
            available.append(provider_id)
    return available


# ---------------------------------------------------------------------------
# Unified LLM Client
# ---------------------------------------------------------------------------
class LLMClient:
    """
    Unified LLM client that wraps multiple providers behind a single interface.

    Usage:
        client = LLMClient(provider="openai")
        response = client.chat(system="You are helpful.", messages=[...], max_tokens=4000)
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        if provider not in PROVIDERS:
            raise ValueError(
                f"Unknown provider '{provider}'. Supported: {list(PROVIDERS.keys())}"
            )

        self.provider_id = provider
        self.provider_info = PROVIDERS[provider]
        self.model = model or self.provider_info["default_model"]

        # Resolve API key
        self.api_key = api_key or os.environ.get(self.provider_info["env_key"])
        if not self.api_key:
            raise EnvironmentError(
                f"{self.provider_info['env_key']} not set for provider '{provider}'.\n"
                f"Set it in .env or export it as an environment variable."
            )

        # Resolve base URL
        self.base_url = (
            base_url
            or os.environ.get(self.provider_info["env_base_url"])
            or self.provider_info["default_base_url"]
        )

        # Initialize the appropriate SDK client
        self._sdk = self.provider_info["sdk"]
        self._client = self._init_client()

    def _init_client(self):
        """Initialize the SDK-specific client."""
        if self._sdk == "anthropic":
            import anthropic
            return anthropic.Anthropic(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        elif self._sdk == "openai":
            from openai import OpenAI
            return OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        else:
            raise ValueError(f"Unknown SDK type: {self._sdk}")

    def chat(
        self,
        system: str,
        messages: list,
        max_tokens: int = 4000,
        temperature: float = 0.1,
    ) -> str:
        """
        Send a chat completion request and return the response text.

        Args:
            system: System prompt string
            messages: List of {"role": "user"|"assistant", "content": "..."}
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            The assistant's response text.
        """
        if self._sdk == "anthropic":
            return self._chat_anthropic(system, messages, max_tokens, temperature)
        elif self._sdk == "openai":
            return self._chat_openai(system, messages, max_tokens, temperature)

    def _chat_anthropic(self, system, messages, max_tokens, temperature) -> str:
        """Call Anthropic's Messages API."""
        response = self._client.messages.create(
            model=self.model,
            system=system,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.content[0].text

    def _chat_openai(self, system, messages, max_tokens, temperature) -> str:
        """Call OpenAI-compatible Chat Completions API."""
        # Prepend system message
        full_messages = [{"role": "system", "content": system}] + messages

        response = self._client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content

    @property
    def provider_name(self) -> str:
        return self.provider_info["name"]

    def __repr__(self):
        return f"LLMClient(provider={self.provider_id!r}, model={self.model!r})"
