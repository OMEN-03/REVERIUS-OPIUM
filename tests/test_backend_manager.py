import asyncio

from backends.backend_manager import BackendManager
from backends.base import BaseBackend, BackendResponse
from backends.offline import OfflineBackend
from backends.registry import BackendRegistry
from config.settings import load_settings


class DummyBackend(BaseBackend):
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


def test_load_settings_defaults_and_validation():
    settings = load_settings(path="config.toml")
    assert settings.preferred_backend in {"openjarvis", "local_llm", "direct_api", "offline"}
    assert settings.max_tokens > 0
    assert settings.temperature >= 0.0


def test_backend_registry_and_manager_use_preferred_backend():
    registry = BackendRegistry()
    backend = DummyBackend()
    registry.register(backend)

    manager = BackendManager(registry=registry, preferred_backend="dummy")

    async def run() -> None:
        await manager.initialize()
        response = await manager.generate("hello")
        assert response.text == "dummy:hello"
    assert manager.current_backend.name == "dummy"

    asyncio.run(run())


def test_backend_manager_prefers_non_offline_backends_when_offline_is_default():
    registry = BackendRegistry()
    class DummyBackend(BaseBackend):
        name = "dummy"
        priority = 5

        def __init__(self) -> None:
            self._initialized = False

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
            return self._initialized

        async def shutdown(self) -> None:
            self._initialized = False

    dummy = DummyBackend()
    registry.register(dummy)
    registry.register(OfflineBackend())

    manager = BackendManager(registry=registry)

    async def run() -> None:
        await manager.initialize()
        assert manager.current_backend is not None
        assert manager.current_backend.name == "dummy"

    asyncio.run(run())
