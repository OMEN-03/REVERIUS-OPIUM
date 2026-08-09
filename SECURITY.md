# Security Policy

## Reporting a Vulnerability

If you discover a security issue, please report it privately to the project maintainers.

## Supported Versions

This project supports the latest Python 3.11 release.

## Security Guidelines

- Do not commit secrets or API keys.
- Store secrets in `.env` or environment variables.
- Validate input before executing commands.
- Prefer safe subprocess calls and avoid shell expansion.
