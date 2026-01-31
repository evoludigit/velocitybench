# VelocityBench Versioning Scheme

## Overview

VelocityBench uses **semantic versioning (SemVer)** for releases. The project version tracks the overall benchmarking suite, while individual framework implementations maintain their own versioning.

## Version Format

```
MAJOR.MINOR.PATCH

Example: 0.2.0
```

## Semantic Versioning Rules

- **MAJOR**: Incompatible API or benchmark methodology changes
  - Changes to database schema that require migration
  - Changes to framework test interfaces
  - Changes to performance baseline expectations

- **MINOR**: New features, frameworks, or capabilities added (backward compatible)
  - New framework implementations
  - New benchmarking dimensions or metrics
  - New documentation or testing infrastructure
  - Enhanced observability features

- **PATCH**: Bug fixes and documentation updates (backward compatible)
  - Code quality improvements
  - Test coverage enhancements
  - Documentation corrections
  - Security patches

## Current Versions

### Project Version
- **Current**: 0.2.0 (released 2026-01-30)
- See [CHANGELOG.md](../CHANGELOG.md) for detailed release notes

### Framework Versions
- All individual framework implementations: 0.1.0
- Located in `frameworks/*/pyproject.toml` (Python frameworks)
- Framework versions are independent of project version
- They track the implementation maturity of each framework

## Release Process

1. **Update CHANGELOG.md** with all changes since last release
2. **Update version numbers** in:
   - Project documentation (if applicable)
   - Individual framework `pyproject.toml` files (if changed)
3. **Create git tag**: `git tag -a v0.X.Y -m "Release v0.X.Y"`
4. **Push tag**: `git push origin v0.X.Y`
5. **Create GitHub Release** with CHANGELOG entries

## Branch Versioning

- **main**: Stable release branch (tagged with versions)
- **feat/\***: Feature branches (no version tags)
- **develop** (if created): Pre-release development (can use pre-release tags like v0.3.0-rc1)

## Pre-Release Versions

For development and release candidates, use pre-release suffixes:
- `0.3.0-alpha.1` - Early development version
- `0.3.0-beta.1` - Feature complete, testing phase
- `0.3.0-rc.1` - Release candidate, ready for testing

Example tag:
```bash
git tag -a v0.3.0-rc.1 -m "Release Candidate 1 for v0.3.0"
```

## Dependency Versioning

### Python Packages
- Use version constraints in `requirements.txt` and `pyproject.toml`
- Pin major.minor for stability: `requests>=2.32,<3.0`
- Review `CHANGELOG.md` when updating major versions

### Docker Images
- PostgreSQL: Fixed major version (16-alpine)
- MySQL: Fixed major version (8.0)
- SQL Server: Fixed major version (2022-latest)

## Documentation

- Maintain CHANGELOG.md with all user-visible changes
- Update README.md version references when needed
- Document breaking changes prominently in release notes
- Include migration guides for MAJOR version updates

---

**Last Updated**: 2026-01-30
**Maintainers**: VelocityBench Core Team
