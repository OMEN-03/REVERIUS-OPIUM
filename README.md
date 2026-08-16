# REVERIUS OPIUM

REVERIUS OPIUM is an enterprise-grade AI assistant and asset management platform built for modular extensibility, secure AI operations, and cross-platform deployment.

## Features

- AI assistant with hybrid backend support (OpenJarvis/OpenAI)
- Asset scanning, validation, theming, and path management
- Plugin discovery and hot-loadable command dispatch
- Ethical request filtering and privacy-friendly design
- Voice and UI support through optional modules
- Structured logging, diagnostics, and developer workflows

## Architecture

- `core/`: application orchestration, AI kernel, and router
- `modules/`: extension modules for commands, memory, voice, and automation
- `plugins/`: discoverable plugin components
- `utils/`: reusable utilities including asset management and project health
- `config/`: environment and runtime configuration

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # PowerShell
# or
.\.venv\Scripts\activate     # cmd.exe
pip install -r requirements.txt
pip install -r requirements-dev.txt
# or install editable dev dependencies:
pip install -e .[dev]
```

## Configuration

Copy `.env.example` to `.env` and populate your OpenAI API keys and optional settings.
The repository already ignores `.env` files so secrets are not committed.
You can also set the key directly in `config.toml` under the `[ai]` section.

## Running

```bash
python main.py
```

## Testing

```bash
python -m pytest -q
```

## Pre-commit

Git is required to install and run `pre-commit` hooks successfully.
Install the pre-commit hook once after creating the virtual environment:

```bash
pre-commit install
pre-commit run --all-files
```

## Development workflow

For a reproducible development environment and CI-like checks, use `tox`:

```bash
tox
```

See `docs/development_setup.md` for full onboarding and packaging guidance.

## Contributing

See `CONTRIBUTING.md`.

## License

**PROPRIETARY SOFTWARE - ALL RIGHTS RESERVED**

REVERIUS OPIUM is proprietary software owned exclusively by REVERIUS OPIUM.
No public license is granted.

**Unauthorized use, copying, modification, distribution, sublicensing, or
creation of derivative works is strictly prohibited.**

Access to this repository is restricted to explicitly authorized individuals
only. This software is confidential and may be subject to trade secret
protection. Unauthorized access, use, or disclosure may result in civil and
criminal liability.

For more information, see the [LICENSE](LICENSE) file and [TERMS OF USE](TERMS_OF_USE.md).
