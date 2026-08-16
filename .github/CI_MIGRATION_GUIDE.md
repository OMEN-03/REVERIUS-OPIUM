# CI Migration Guide: REVERIUS-OPIUM

## Strategy: Hybrid CI (Code Quality + Technical Debt Tracking)

**Date:** August 16, 2026  
**Status:** Active  
**Phase:** 1 of 4

---

## Overview

This project uses a **hybrid CI strategy** that balances strict code quality enforcement with practical development velocity. The strategy is designed to:

1. ✅ **Protect functionality** — Tests must pass
2. ✅ **Maintain integrity** — Repository hygiene is enforced  
3. ✅ **Track debt** — Technical debt is visible and measured
4. ⚠️ **Unblock development** — Type/style issues are advisory, not blocking
5. 📈 **Enable gradual improvement** — Path to production-grade strictness

---

## CI Architecture

### BLOCKING CHECKS (CI fails if violated)

These checks **must pass** before code is merged:

| Check | Tool | Purpose | Runtime Impact |
|-------|------|---------|-----------------|
| **Dependency Installation** | pip | Validates requirements can be installed | Critical |
| **YAML Syntax** | pre-commit hook | Validates GitHub Actions/config files | High |
| **Large File Check** | pre-commit hook | Prevents binary/huge file commits | Medium |
| **File Endings** | pre-commit hook | Ensures files end with newlines | Low |
| **Trailing Whitespace** | pre-commit hook | Repository hygiene | Low |
| **Unit Tests (3 platforms)** | pytest | Validates application behavior | Critical |

### ADVISORY CHECKS (CI reports but doesn't block)

These checks **report findings** but don't block merging:

| Check | Tool | Purpose | Status |
|-------|------|---------|--------|
| **Type Checking** | mypy | Validates type annotations | Advisory (staged: manual) |
| **Linting** | ruff | Reports code quality issues | Advisory (reported) |
| **Code Formatting** | black | Reports formatting violations | Advisory (via pre-commit) |
| **Import Ordering** | isort | Reports import order issues | Advisory (via pre-commit) |

---

## Pre-Commit Hooks (Local Development)

When you run `pre-commit run --all-files` or commit locally, these hooks execute:

### ✅ Automatic Fixes
- **ruff --fix** — Auto-corrects fixable issues
- **black** — Auto-formats code
- **isort** — Auto-sorts imports
- **end-of-file-fixer** — Adds final newlines
- **trailing-whitespace** — Removes trailing spaces

### ⚠️ Manual Review Required
- **mypy** — Type checking (stages: manual → requires explicit `pre-commit run --hook-stage manual`)
- **check-yaml** — YAML syntax
- **check-added-large-files** — Large file detection

---

## GitHub Actions Workflow

### Lint Job (Blocking)
```
1. Install dependencies
   └─ FAILS: Cannot proceed without dependencies

2. Run pre-commit (blocking)
   └─ Repository integrity checks must pass
   └─ Auto-fixes applied; violations reported

3. Type checking report (advisory)
   └─ Runs mypy; doesn't block CI
   └─ Results shown in GitHub Actions summary

4. Lint report (advisory)
   └─ Runs ruff; doesn't block CI
   └─ Results shown in GitHub Actions summary
```

### Test Job (Blocking, runs after lint)
```
1. Install dependencies
2. Run pytest on [ubuntu-latest, windows-latest, macos-latest]
   └─ FAILS: Tests must pass on all platforms
```

---

## Technical Debt Tracking

### Current Baseline (Commit: eb4b7f7)

| Category | Count | Status |
|----------|-------|--------|
| mypy errors | 2,331 | Advisory (tracked) |
| ruff issues | 1,189 | Advisory (tracked) |
| Files needing black | 52 | Advisory (tracked) |

### Tracking Mechanism

Technical debt is **visible** in GitHub Actions:
1. Run workflow on `main` push
2. View "Lint Report" section in GitHub Actions summary
3. Compare counts across weeks to see trends

### Monthly Review

Team reviews technical debt report:
- Are violations increasing? 🔴 (problem)
- Are violations decreasing? 🟢 (good)
- Which areas need focus? 📊 (priority)

---

## Migration Timeline

### Phase 1: Infrastructure (Week 1) ✅ ACTIVE
- ✅ Fix configuration inconsistencies
- ✅ Remove CI tool redundancy  
- ✅ Make mypy advisory
- ✅ Add debt tracking
- **Result:** CI unblocked; debt visible

### Phase 2: Cleanup (Weeks 2-3)
- 🔄 Fix black formatting (52 files)
- 🔄 Fix isort import order
- 🔄 Review and fix ruff undefined-name errors
- **Target:** 30% reduction in violations

### Phase 3: Type Safety (Week 4)
- 🔄 Developers add type hints to public APIs
- 🔄 Fix ~500 of 2,331 mypy errors
- **Target:** 50% reduction in type errors

### Phase 4: Strictness Restoration (Weeks 5+)
- 🔄 Remove `stages: [manual]` from mypy → becomes blocking
- 🔄 Increase ruff strictness as violations decrease
- 🔄 Restore `strict = true` when 80%+ errors fixed
- **Target:** Production-grade CI

---

## Developer Workflow

### Before Committing

1. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

2. **Run hooks locally (auto-fixes cosmetic issues):**
   ```bash
   pre-commit run --all-files
   ```

3. **Run type checker (manual stage):**
   ```bash
   pre-commit run --hook-stage manual --all-files
   # or
   mypy .
   ```

4. **Review output:**
   - Auto-fixed issues (black, isort, ruff --fix)
   - Type checking warnings (mypy)
   - Repository hygiene issues

5. **Make decisions:**
   - Cosmetic issues (black/isort) → auto-fixed, no action needed
   - Real bugs (undefined-name in ruff) → fix immediately
   - Type hints (mypy) → defer or add if time permits

### After Pushing to GitHub

1. GitHub Actions runs automatically
2. **Lint job:**
   - Repository integrity checks (blocking) — must pass
   - Type/lint reports (advisory) — visible in Actions, doesn't block
3. **Test job:**
   - Runs only if lint job passes
   - Must pass on all platforms

### If CI Fails

**Scenario 1: Lint blocking check failed**
```
❌ Pre-commit hook failed (e.g., trailing-whitespace)
→ Fix locally: pre-commit run --all-files
→ Commit and push again
```

**Scenario 2: Tests failed**
```
❌ pytest failed
→ Run tests locally: python -m pytest -q
→ Debug and fix
→ Commit and push again
```

**Scenario 3: Type/Lint advisory reports (doesn't block)**
```
⚠️  mypy/ruff found issues
→ Visible in GitHub Actions summary
→ Optional to fix immediately
→ Tracked for monthly review
```

---

## Configuration Files Reference

### `.pre-commit-config.yaml`

**Key settings:**
- `ruff` (v0.0.280) with `--fix` — auto-fixes locally
- `black` (24.10.0) — auto-formats
- `isort` (v5.10.1) with `--profile black` — auto-sorts imports
- `mypy` (v1.9.0) with `stages: [manual]` — doesn't run automatically
- Basic hooks for hygiene

**To run mypy locally:**
```bash
pre-commit run --hook-stage manual --all-files
```

### `pyproject.toml`

**Key settings:**
- `requires-python` = >=3.11
- `ruff` config: line-length=88, ignore E501
- `isort` config: profile="black"
- `mypy` config: strict=true, multiple warn_* flags
- `pytest` config: cov enabled, strict markers

**Optional dependency groups:**
- `[test]` — testing tools
- `[dev]` — development tools (includes test + tox)

### `.github/workflows/python-package.yml`

**Key workflow:**
1. Install dependencies
2. Run pre-commit (repository integrity — blocking)
3. Report type checking (advisory)
4. Report linting (advisory)
5. Run tests on 3 platforms (blocking)

---

## Frequently Asked Questions

### Q: Why is mypy `stages: [manual]`?

**A:** The repository has 2,331 type errors. Making mypy blocking would fail every CI run. By setting it to `stages: [manual]`, developers can:
- Run it locally when they want: `pre-commit run --hook-stage manual`
- See results in GitHub Actions (advisory)
- Fix issues gradually without blocking development

**Future:** When 80%+ of errors are fixed, we'll remove `stages: [manual]` to make mypy blocking again.

---

### Q: Why are some issues "advisory" instead of "blocking"?

**A:** Trade-off between quality and velocity:

**Blocking issues** protect against:
- Runtime failures (dependency issues, test failures)
- Repository corruption (broken YAML, huge files, hygiene)

**Advisory issues** (tracked separately) include:
- Code formatting (cosmetic)
- Import ordering (organizational)
- Type annotations (valuable, but large refactor needed)
- Linting cleanup (dead code, style)

This allows feature development to continue while quality improves incrementally.

---

### Q: How do I know what to fix first?

**Priority order:**
1. 🔴 **Blocking CI failures** — Fix immediately
2. 🟡 **Undefined-name errors** (ruff F405) — Real bugs; fix soon
3. 🟢 **Formatting/imports** (black/isort) — Auto-fixed locally; lower priority
4. 🔵 **Type hints** (mypy) — Gradual improvement; schedule for later

---

### Q: Can I push if mypy has errors?

**A:** Yes. Mypy is advisory (not blocking). You can:
1. See mypy violations in GitHub Actions
2. Ignore them for now (tracked for team review)
3. Fix them later as part of Phase 3-4

However, if the **blocking pre-commit checks fail**, you cannot push.

---

### Q: How do I run the full CI locally?

**A:** 
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run type checking
pre-commit run --hook-stage manual --all-files

# Run tests
python -m pytest -q

# OR use tox (runs entire pipeline)
tox
```

---

## Support & Questions

For questions about this CI strategy, refer to:
- This guide (CI_MIGRATION_GUIDE.md)
- Workflow definition (.github/workflows/python-package.yml)
- Pre-commit configuration (.pre-commit-config.yaml)
- Project configuration (pyproject.toml)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Aug 16, 2026 | Initial hybrid CI strategy; Phase 1 activated |
