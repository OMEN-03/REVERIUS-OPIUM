from core.architecture import CommandRouter, EventBus, PluginRegistry


def test_event_bus_delivers_payloads():
    bus = EventBus()
    received = []

    bus.subscribe("task.started", lambda payload: received.append(payload["name"]))
    bus.publish("task.started", {"name": "build"})

    assert received == ["build"]


def test_plugin_registry_tracks_enabled_plugins():
    registry = PluginRegistry()

    class DummyPlugin:
        pass

    registry.register("demo", DummyPlugin())
    assert registry.is_enabled("demo")

    registry.set_enabled("demo", False)
    assert not registry.is_enabled("demo")
    assert "demo" in registry.get_registered_names()


def test_command_router_dispatches_registered_commands():
    router = CommandRouter()
    router.register("help", lambda command, context: True)

    assert router.dispatch("help", {}) is True
    assert router.dispatch("missing", {}) is False
