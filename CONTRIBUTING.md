# Contributing to REVERIUS OPIUM

Thank you for your interest in contributing! This guide explains how to contribute code, tests, documentation, and issue reports.

## Getting Started

1. Fork the repository.
2. Create a feature branch with a descriptive name.
3. Set up your development environment and install dependencies.
4. Run tests and formatting checks before submitting.

## Local setup

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # PowerShell
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
```

When available, use `tox` for a consistent development flow:

```bash
tox
```

## Code style

- Use `black` for formatting.
- Keep functions small and single-purpose.
- Add type hints to new code.
- Run `ruff`, `isort`, and `mypy` before committing.

## Testing

Run the full test suite locally with:

```bash
python -m pytest -q
```

If using `tox`:

```bash
tox -e py311
```

## Pull Requests

- One change per PR when possible.
- Document behavior in the PR description.
- Keep breaking changes explicit.
- Reference relevant issues or design notes.
