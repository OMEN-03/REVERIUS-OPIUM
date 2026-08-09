# Architecture

REVERIUS OPIUM now uses a layered architecture with explicit runtime boundaries:

- `core/`: orchestrates the assistant, kernel, and routing logic.
- `backends/`: provider implementations and failover-aware backend management.
- `plugins/`: discoverable command handlers with hot-load support.
- `memory/`: sqlite-backed storage for conversation and knowledge memory.
- `config/`: TOML-based configuration with environment compatibility.
- `modules/`: compatibility wrappers that preserve existing entry points.
