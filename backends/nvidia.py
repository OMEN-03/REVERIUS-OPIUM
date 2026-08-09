from __future__ import annotations

import logging
import time
from typing import Any

import requests

from config.settings import load_settings
from .base import BackendResponse
from .errors import AuthenticationError, GenerationError, NetworkError

logger = logging.getLogger(__name__)


class NvidiaDeepSeekBackend:
    """OpenAI-compatible NVIDIA backend for DeepSeek V4 Flash."""

    name = "nvidia"
    priority = 15

    def __init__(self) -> None:
        self._initialized = False
        self._status = "NOT CONFIGURED"
        self._last_error: str | None = None
        self._request_count = 0
        self._latency_ms = 0

    def _get_config(self) -> dict[str, Any]:
        settings = load_settings()
        return {
            "api_key": settings.nvidia_api_key,
            "model": settings.nvidia_model or "deepseek-ai/deepseek-v4-flash",
            "base_url": settings.nvidia_base_url or "https://integrate.api.nvidia.com/v1",
            "reasoning_effort": settings.nvidia_reasoning_effort or "high",
        }

    async def initialize(self) -> None:
        if self._initialized:
            return
        config = self._get_config()
        if not config["api_key"]:
            self._status = "NOT CONFIGURED"
            self._last_error = "missing NVIDIA_API_KEY"
            self._initialized = True
            return
        self._status = "ONLINE"
        self._initialized = True
        logger.info("NVIDIA backend initialized")

    async def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        if not self._initialized:
            await self.initialize()
        config = self._get_config()
        if not config["api_key"]:
            raise GenerationError("NVIDIA API key not configured")

        start = time.perf_counter()
        self._request_count += 1
        payload = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "reasoning_effort": config["reasoning_effort"],
        }
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                f"{config['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            self._latency_ms = int((time.perf_counter() - start) * 1000)
            if response.status_code == 401:
                self._status = "ERROR"
                self._last_error = "invalid_api_key"
                raise AuthenticationError("invalid NVIDIA API key")
            if response.status_code >= 500:
                self._status = "ERROR"
                self._last_error = "server_error"
                raise NetworkError("NVIDIA server error")
            if response.status_code >= 400:
                self._status = "ERROR"
                self._last_error = "request_error"
                raise GenerationError("NVIDIA request failed")
            data = response.json()
            choices = data.get("choices", [])
            if not isinstance(choices, list) or not choices:
                self._status = "ERROR"
                self._last_error = "empty_response"
                return BackendResponse(text="[nvidia] empty response received", backend=self.name, metadata={"request_count": self._request_count, "latency_ms": self._latency_ms})
            message = choices[0].get("message", {}).get("content", "")
            if not message:
                self._status = "ERROR"
                self._last_error = "empty_response"
                return BackendResponse(text="[nvidia] empty response received", backend=self.name, metadata={"request_count": self._request_count, "latency_ms": self._latency_ms})
            self._status = "ONLINE"
            return BackendResponse(text=message, backend=self.name, metadata={"request_count": self._request_count, "latency_ms": self._latency_ms})
        except requests.RequestException as exc:
            self._status = "ERROR"
            self._last_error = "network_failure"
            raise NetworkError(str(exc)) from exc

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        if not self._initialized:
            await self.initialize()
        content = " ".join(message.get("content", "") for message in messages)
        return await self.generate(content, temperature=temperature, max_tokens=max_tokens)

    async def stream(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256):
        if not self._initialized:
            await self.initialize()
        response = await self.generate(prompt, temperature=temperature, max_tokens=max_tokens)
        yield response

    async def embeddings(self, text: str) -> list[float]:
        return [float(len(text)), 0.0]

    async def health_check(self) -> bool:
        if not self._initialized:
            await self.initialize()
        config = self._get_config()
        if not config["api_key"]:
            self._status = "NOT CONFIGURED"
            return False
        try:
            response = requests.post(
                f"{config['base_url']}/chat/completions",
                headers={"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"},
                json={"model": config["model"], "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1, "reasoning_effort": config["reasoning_effort"]},
                timeout=10,
            )
        except requests.RequestException:
            self._status = "ERROR"
            return False
        if response.status_code in {200, 201}:
            self._status = "ONLINE"
            return True
        self._status = "ERROR"
        return False

    async def shutdown(self) -> None:
        self._initialized = False
        self._status = "OFFLINE"

    def get_status(self) -> dict[str, Any]:
        config = self._get_config()
        return {
            "name": self.name,
            "status": self._status,
            "configured": bool(config["api_key"]),
            "model": config["model"],
            "reasoning_effort": config["reasoning_effort"],
            "latency_ms": self._latency_ms,
            "request_count": self._request_count,
            "error": self._last_error,
        }
