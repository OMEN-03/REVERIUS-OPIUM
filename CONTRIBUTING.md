# Contributing to REVERIUS OPIUM

## ⚠️ PROPRIETARY SOFTWARE NOTICE

**REVERIUS OPIUM is proprietary software owned exclusively by REVERIUS OPIUM.**

**Public contributions are NOT accepted.**

If you are an **authorized team member**, the guidelines below apply to you.
If you are **not authorized**, you do not have permission to access, use, or
contribute to this software. Unauthorized access or contribution is prohibited.

---

## For Authorized Team Members Only

Thank you for your interest in contributing! This guide explains how to
contribute code, tests, documentation, and issue reports as an authorized
team member.

## Getting Started

1. Ensure you are an authorized team member with repository access
2. Clone the repository (do not fork; this is proprietary software)
3. Create a feature branch with a descriptive name
4. Set up your development environment and install dependencies
5. Run tests and formatting checks before submitting

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

When submitting a pull request:

1. Ensure all tests pass
2. Ensure code follows style guidelines
3. Include a clear description of changes
4. Reference any related issues
5. Do not include unnecessary changes
6. Ensure this repository remains private and secure

## Important Reminders

### Confidentiality

- Do not share code or documentation outside the authorized team
- Do not discuss implementation details in public channels
- Protect your access credentials
- Do not publish this code to public repositories

### Intellectual Property

- All contributions are owned by REVERIUS OPIUM
- By contributing, you acknowledge REVERIUS OPIUM's ownership
- You agree not to claim authorship or use contributions in competing products
- Ensure you have rights to any external code or dependencies you contribute

### Legal Compliance

- Comply with [LICENSE](LICENSE) and [TERMS_OF_USE.md](TERMS_OF_USE.md)
- Review [SECURITY.md](SECURITY.md) for confidentiality requirements
- Report any security issues immediately
- Report any unauthorized access or breaches

## Code of Conduct

All team members must follow the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## Need Help?

If you're an authorized team member with questions:
- Reach out to the REVERIUS OPIUM development team
- Check documentation in `docs/development_setup.md`

## Unauthorized Contributors

**If you are not an authorized team member:**
You do not have permission to access or contribute to this proprietary software.
Unauthorized access is prohibited and may result in legal action.

For authorization inquiries, contact the REVERIUS OPIUM development team.

- One change per PR when possible.
- Document behavior in the PR description.
- Keep breaking changes explicit.
- Reference relevant issues or design notes.
