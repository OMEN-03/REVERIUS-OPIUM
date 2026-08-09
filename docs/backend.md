# Backend guide

REVERIUS OPIUM supports multiple backend implementations through the backend manager:

- `openjarvis`: optional OpenJarvis SDK adapter
- `local_llm`: deterministic local placeholder backend
- `direct_api`: lightweight direct API-compatible backend
- `offline`: offline-safe fallback backend

The shared manager initializes the preferred backend and automatically falls back to the next available implementation when a backend fails health checks.
