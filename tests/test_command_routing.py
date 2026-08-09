import importlib


def test_reverius_process_command_uses_shared_router():
    reverius_module = importlib.import_module("core.reverius_opium")
    command_module = importlib.import_module("modules.command_processing")

    assert reverius_module.process_command is command_module.process_command


def test_plugin_loader_dispatches_registered_commands():
    plugin_loader = importlib.import_module("plugins.plugin_loader")
    assert plugin_loader.dispatch_command("help") is True


def test_plugin_initialization_discovers_modules():
    plugin_loader = importlib.import_module("plugins.plugin_loader")
    plugins = plugin_loader.initialize_plugins()
    assert "assistant" in plugins


def test_command_processing_imports_without_ui_widget():
    command_module = importlib.import_module("modules.command_processing")
    assert callable(command_module.process_command)
