# REVERIUS-OPIUM Technical Debt Baseline

**Created:** August 16, 2026 (Commit: eb4b7f7)  
**Phase:** 1 - Infrastructure & Tracking  
**Status:** Active Monitoring

---

## Baseline Metrics

### Mypy Type Checking Errors

**Total:** 2,331 errors across 48 files  
**Status:** Advisory (not blocking CI)  
**Stage:** `stages: [manual]` in pre-commit config

**Action:** Will be reduced gradually in Phases 2-4

---

### Ruff Linting Issues

**Total:** 1,189 errors (after auto-fixes)  
**Status:** Advisory (reported in CI)

**Breakdown (estimated):**
- F405 (undefined-name): ~150 — Real bugs, should fix
- F401 (unused-import): ~400 — Dead code, can auto-fix
- F403 (wildcard-import): ~100 — Architectural pattern, review intent
- Other: ~439 — Various style/lint issues

**Action:** Review and categorize; fix real bugs first

---

### Code Formatting Issues

**Black:** 52 files need reformatting  
**Status:** Advisory (auto-fixable)

**Action:** Run `black .` once to fix all files

---

### Import Ordering Issues

**isort:** Multiple files need reordering  
**Status:** Advisory (auto-fixable)

**Action:** Run `isort --profile black .` once to fix all files

---

## Tracking Plan

### Weekly Check
- Run CI on main branch
- Capture mypy error count from GitHub Actions logs
- Capture ruff error count from GitHub Actions logs
- Record in TECHNICAL_DEBT_TRACKING.md

### Monthly Review
- Team reviews technical debt dashboard
- Identify high-impact fixes (biggest wins)
- Prioritize Phase 2-3 work
- Update this baseline if major cleanup happens

### Success Criteria

| Phase | Target | Timeline |
|-------|--------|----------|
| Phase 1 | Baseline established | Week 1 ✅ |
| Phase 2 | 30% reduction | Weeks 2-3 |
| Phase 3 | 70% reduction | Weeks 4-5 |
| Phase 4 | 95%+ fixed (ready for strict CI) | Week 6+ |

---

## Related Files

- `.github/workflows/python-package.yml` — CI workflow (advisory reports)
- `.pre-commit-config.yaml` — Pre-commit config (mypy stages: manual)
- `.github/CI_MIGRATION_GUIDE.md` — Developer guide
- `pyproject.toml` — Tool configurations

---

## Notes

- This baseline allows development to continue while quality improves
- All violations are visible in GitHub Actions (not hidden)
- No source code suppression (# noqa, # type: ignore) has been added
- Path to strict CI is clearly defined in CI_MIGRATION_GUIDE.md
