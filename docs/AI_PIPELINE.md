# AI pipeline

The REVERIUS AI pipeline routes requests through the shared backend manager and orchestrator. The NVIDIA DeepSeek V4 Flash provider is registered as an OpenAI-compatible backend adapter and is selected through the same backend manager used by the other providers.

## Provider flow

1. User input enters the orchestrator.
2. The orchestrator forwards the request to the shared backend manager.
3. The backend manager selects the highest-priority healthy backend.
4. The NVIDIA adapter sends a chat completion request to the NVIDIA endpoint.
5. The response is returned to the orchestrator and then to the frontend.

## Security

- API keys are read from the environment via settings.
- Secrets are never written into logs or UI state.
- If NVIDIA_API_KEY is missing, the backend reports NOT CONFIGURED and does not crash the rest of the application.
