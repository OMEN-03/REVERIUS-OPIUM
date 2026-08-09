from __future__ import annotations


class BackendError(Exception):
    """Base error for backend failures."""


class NetworkError(BackendError):
    """Raised when a backend network request fails."""


class InitializationError(BackendError):
    """Raised when a backend cannot initialize."""


class GenerationError(BackendError):
    """Raised when generation fails."""


class AuthenticationError(BackendError):
    """Raised when API authentication fails."""


class ConfigurationError(BackendError):
    """Raised when configuration is invalid."""


class PluginError(BackendError):
    """Raised when plugin execution fails."""
