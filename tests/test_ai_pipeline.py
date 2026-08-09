import asyncio

from backends.backend_manager import BackendManager
from backends.base import BackendResponse
from backends.registry import BackendRegistry
from core.orchestrator import AIOrchestrator


class DummyBackend:
    name = "dummy"
    priority = 10

    async def initialize(self) -> None:
        self._initialized = True

    async def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        return BackendResponse(text=f"dummy:{prompt}", backend=self.name)

    async def chat(self, messages, *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        return BackendResponse(text="chat", backend=self.name)

    async def stream(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256):
        yield BackendResponse(text=prompt, backend=self.name)

    async def embeddings(self, text: str):
        return [1.0, 2.0]

    async def health_check(self) -> bool:
        return True

    async def shutdown(self) -> None:
        self._initialized = False


def test_orchestrator_builds_plan_and_reflection():
    registry = BackendRegistry()
    registry.register(DummyBackend())
    manager = BackendManager(registry=registry, preferred_backend="dummy")
    orchestrator = AIOrchestrator(backend_manager=manager)

    async def run() -> None:
        result = await orchestrator.handle_request("Summarize this request for me")
        assert result.intent == "general"
        assert len(result.plan) >= 2
        assert result.response.startswith("dummy:")
        assert "reflection" in result.reflection.lower()

    asyncio.run(run())
