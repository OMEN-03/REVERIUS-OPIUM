# Plugin guide

Plugins are discovered from the `plugins` package and can expose either `init_plugin` or `handle_command` hooks.

The plugin manager supports registering plugins with lightweight metadata, making it straightforward to add new capabilities without changing the core runtime.
