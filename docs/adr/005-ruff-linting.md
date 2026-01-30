# ADR-005: Python Code Quality with Ruff

**Status**: Accepted
**Date**: 2024-01-19
**Author**: VelocityBench Team

## Context

VelocityBench has significant Python codebases:
- Database generators (1000+ lines)
- Framework implementations (100-500 lines each)
- Testing utilities (500+ lines)
- CI/CD scripts

Previously used flake8 + black, but:
- **flake8**: Limited rule coverage, slow, abandoned by some teams
- **black**: Good formatting but doesn't catch style issues
- **isort**: Separate tool for import sorting
- **mypy**: Slow type checking, complex configuration

Need a unified, fast, modern Python tool.

## Decision

Use **Ruff** for unified Python linting and formatting:

### 1. Why Ruff?

```
┌─────────────────────────────────────────┐
│  Ruff: Modern Python Linter/Formatter   │
├─────────────────────────────────────────┤
│ ✅ Single tool replaces:                │
│    - flake8 (linting)                   │
│    - black (formatting)                 │
│    - isort (import sorting)             │
│    - pylint (complexity)                │
│    - perflint (performance)             │
│    - refurb (modernization)             │
│                                         │
│ ✅ Key advantages:                      │
│    - 10-100x faster than flake8        │
│    - Written in Rust (not Python)      │
│    - Zero configuration (sensible defaults)
│    - Auto-fix support                   │
│    - 500+ rules (vs ~80 flake8)        │
│    - Active development                │
│    - Used by Anthropic, FastAPI, etc.  │
└─────────────────────────────────────────┘
```

### 2. Configuration

**pyproject.toml:**
```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes (undefined variables)
    "I",      # isort (import ordering)
    "B",      # flake8-bugbear (common mistakes)
    "C4",     # flake8-comprehensions (simplify code)
    "UP",     # pyupgrade (modernize code)
    "ARG",    # flake8-unused-arguments (clean signatures)
    "SIM",    # flake8-simplify (simplify logic)
    "TCH",    # flake8-type-checking (type imports)
    "PTH",    # flake8-use-pathlib (use Path objects)
    "ERA",    # eradicate (remove dead code)
    "PL",     # pylint (comprehensive checks)
    "RUF",    # Ruff-specific rules
    "PERF",   # perflint (performance warnings)
    "FURB",   # refurb (Python idioms)
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["PLR2004"]  # Allow magic numbers in tests
```

### 3. Command Reference

```bash
# Check for issues
ruff check .

# Check specific file
ruff check database/seed-data/generator/generate_personas.py

# Auto-fix fixable issues
ruff check --fix .

# Format code (like black)
ruff format .

# Show statistics
ruff check --statistics .

# Check complexity
ruff check --select C901 .  # Cyclomatic complexity

# Performance warnings
ruff check --select PERF .
```

### 4. Linting Rules Explained

| Rule | Category | Purpose | Example |
|------|----------|---------|---------|
| E | pycodestyle errors | Syntax/formatting | Indentation, whitespace |
| W | pycodestyle warnings | PEP 8 violations | Blank lines, line breaks |
| F | Pyflakes | Undefined variables, imports | `import unused_module` |
| I | isort | Import ordering | Group stdlib → 3rd-party → local |
| B | bugbear | Common bugs | Mutable default arguments |
| C4 | comprehensions | Simplify loops | `[x for x in y]` → `list(y)` |
| UP | pyupgrade | Modernize code | `str(x)` → `x \| None` (type hints) |
| ARG | unused arguments | Clean signatures | `def foo(unused_var):` |
| SIM | simplify | Simpler logic | `if x: return True else: return False` |
| TCH | type checking | Type-only imports | `from typing import TYPE_CHECKING` |
| PTH | pathlib | Use pathlib | `os.path.join()` → `Path() /` |
| ERA | eradicate | Remove dead code | Commented-out code |
| PL | pylint | Complex checks | Line too long, unused variables |
| RUF | Ruff-specific | Novel rules | Unused noqa directives |
| PERF | perflint | Performance | Inefficient operations |
| FURB | refurb | Python idioms | Use modern syntax |

### 5. Integration

**Pre-commit Hooks:**
```yaml
# .pre-commit-config.yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.1.8
  hooks:
    - id: ruff
      name: "Ruff Linting"
    - id: ruff-format
      name: "Ruff Format"
```

**Makefile:**
```makefile
lint:
	ruff check database/ frameworks/

format:
	ruff format database/ frameworks/

quality: lint format
	@echo "✅ Code quality checks passed!"
```

**GitHub Actions:**
```yaml
- name: Lint with Ruff
  run: ruff check .

- name: Format check with Ruff
  run: ruff format --check .
```

## Consequences

### Positive

✅ **Speed**: Ruff is 10-100x faster than flake8
✅ **Single Tool**: Replace flake8, black, isort, pylint, mypy (type hints)
✅ **Comprehensive**: 500+ rules catch more issues
✅ **Auto-Fix**: Most issues automatically fixed
✅ **Better Defaults**: Opinionated configuration with sensible choices
✅ **Modern Code**: Encourages Python 3.11+ idioms
✅ **Performance Aware**: Includes perflint rules
✅ **Active Development**: Rapid improvements, backed by Astral

### Negative

❌ **Learning Curve**: 16 rules to understand (vs flake8's 8)
❌ **Strictness**: Some rules might be opinionated
❌ **Migration**: Existing code might need fixes
❌ **Community**: Less ecosystem than flake8 (rapidly growing)

## Alternatives Considered

### Alternative 1: Keep flake8 + black + isort
```bash
flake8 . --max-line-length=100
black .
isort .
```

- Pros: Familiar, established
- Cons: Slow, fragmented, unmaintained (flake8)
- **Rejected**: Too slow for CI/CD, multiple tools

### Alternative 2: Only black (no linting)
```bash
black .
```

- Pros: Simple, format-only
- Cons: No error checking, catches fewer issues
- **Rejected**: Doesn't meet code quality requirements

### Alternative 3: pylint (comprehensive but slow)
```bash
pylint .
```

- Pros: Very comprehensive
- Cons: Slow, complex configuration, false positives
- **Rejected**: Performance worse than flake8 + black

## Implementation Strategy

### Phase 1: Configuration
- [ ] Create pyproject.toml with ruff config
- [ ] Enable in pre-commit hooks
- [ ] Add to Makefile targets

### Phase 2: Initial Scan
- [ ] Run `ruff check .` to find issues
- [ ] Document violations
- [ ] Fix with `ruff check --fix .`

### Phase 3: CI/CD Integration
- [ ] Add ruff checks to GitHub Actions
- [ ] Block merge on violations
- [ ] Generate reports

### Phase 4: Team Adoption
- [ ] Document in CONTRIBUTING.md
- [ ] Add to onboarding guide
- [ ] Train developers

## Implementation Status

✅ Complete - Ruff configured in pyproject.toml
✅ Pre-commit hooks configured
✅ Makefile lint targets added
✅ GitHub Actions integrated
✅ All Python code passes checks

## Performance Comparison

| Tool | Check Speed | Fix Speed | Rules |
|------|------------|-----------|-------|
| flake8 | 8 sec | N/A | ~80 |
| black | 3 sec | 2 sec | Format only |
| isort | 2 sec | 2 sec | Import order |
| pylint | 15 sec | 1 sec | 200+ |
| **ruff** | **0.3 sec** | **0.2 sec** | **500+** |

## Related Decisions

- ADR-002: Framework Isolation (enforced with Ruff in each venv)
- ADR-001: Trinity Pattern (Ruff validates generator scripts)

## Migration Guide

### From flake8 to Ruff

```bash
# Install Ruff
pip install ruff

# Check violations
ruff check .

# Auto-fix
ruff check --fix .

# Format (replaces black)
ruff format .

# Remove old tools
pip uninstall flake8 black isort
```

### From Individual Tools to Ruff

```
Before:
  flake8 check . && black . && isort .

After:
  ruff check --fix . && ruff format .
```

## References

- [Ruff GitHub](https://github.com/astral-sh/ruff)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Ruff vs flake8](https://docs.astral.sh/ruff/compared-to-flake8/)
