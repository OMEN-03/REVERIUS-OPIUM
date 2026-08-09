import asyncio

from backends.backend_manager import BackendManager
from backends.base import BackendResponse
from backends.registry import BackendRegistry
from backends.offline import OfflineBackend
from modules import ai_backend as ai_backend_module
from core.reverius_opium import query_ai as core_query_ai


class DummyBackend:
    name = "dummy"
    priority = 5

    def __init__(self) -> None:
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True

    async def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        return BackendResponse(text=f"dummy response: {prompt}", backend=self.name)

    async def chat(self, messages, *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        return BackendResponse(text="dummy chat", backend=self.name)

    async def stream(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256):
        yield BackendResponse(text=f"dummy stream: {prompt}", backend=self.name)

    async def embeddings(self, text: str):
        return [1.0, 2.0]

    async def health_check(self) -> bool:
        return True

    async def shutdown(self) -> None:
        self._initialized = False

    def get_status(self):
        return {
            "name": self.name,
            "status": "ONLINE",
            "configured": True,
            "model": "dummy-model",
            "reasoning_effort": "low",
            "latency_ms": 1,
            "request_count": 1,
            "error": None,
        }


def test_get_backend_info_returns_dummy_backend(monkeypatch):
    monkeypatch.setattr(ai_backend_module, "_backend_manager", None)
    registry = BackendRegistry()
    registry.register(DummyBackend())
    registry.register(OfflineBackend())
    manager = BackendManager(registry=registry, preferred_backend="dummy")
    monkeypatch.setattr(ai_backend_module, "_backend_manager", manager)

    info = ai_backend_module.get_backend_info()

    assert info["name"] == "dummy"
    assert info["status"] == "ONLINE"
    assert info["configured"] is True
    assert info["request_count"] == 1
    assert info["latency_ms"] == 1


def test_core_query_ai_uses_shared_backend(monkeypatch):
    monkeypatch.setattr(ai_backend_module, "query_ai", lambda prompt, temperature=0.5, max_tokens=1024: "dummy response")
    result = core_query_ai("Hello")
    assert result == "dummy response"
