# Development Setup

This document describes the recommended local development workflow for REVERIUS OPIUM.

## Prerequisites

- Python 3.11 installed
- Git
- Optional: a terminal with PowerShell support on Windows

## Local environment setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Add environment configuration

Copy the example file and populate your keys:

```powershell
copy .env.example .env
```

Then edit `.env` and add your API keys.

## Formatting and linting

Use `pre-commit` to keep code consistent:

```bash
pre-commit install
pre-commit run --all-files
```

You can also run each tool manually:

```bash
ruff check .
isort --check-only .
black --check .
mypy .
```

## Running the app

```bash
python main.py
```

## Running tests

```bash
python -m pytest -q
```

## Tox support

Use `tox` for a reproducible test environment.

```bash
tox
```

If you only want Python 3.11:

```bash
tox -e py311
```

## Release checklist

- Confirm `python -m pytest -q` passes.
- Confirm `pre-commit run --all-files` passes.
- Confirm `tox -e py311` passes if using tox.
- Update changelog or release notes.
