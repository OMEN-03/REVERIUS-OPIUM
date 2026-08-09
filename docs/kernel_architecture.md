# REVERIUS OPIUM Kernel Architecture

## Design goals

- Keep the kernel lightweight and always active.
- Detect user intent before loading capabilities.
- Resolve the minimum plugin set required for the request.
- Keep plugin interactions event-driven and isolated.
- Unload idle plugins to conserve memory.

## Core runtime

The kernel now classifies incoming requests into intents such as search, coding, vision, voice, and diagnostics. It then resolves the minimal plugin set needed for that request and loads only those capabilities.

## Extensibility

New plugins can be added by registering a `PluginSpec` and associating supported intents. The kernel will route future requests to the right plugin set without requiring changes to the central dispatcher.
