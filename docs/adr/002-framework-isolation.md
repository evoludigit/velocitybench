# ADR-002: Framework Isolation via Virtual Environments and Databases

**Status**: Accepted
**Date**: 2024-01-16
**Author**: VelocityBench Team

## Context

VelocityBench benchmarks 38 frameworks across 8 programming languages. Each framework has:
- Different dependency versions
- Language-specific requirements
- Conflicting version constraints
- Unique development environments

The challenge is ensuring fair, reproducible benchmarks without dependency conflicts.

## Decision

Implement **complete isolation** across three dimensions:

### 1. Virtual Environment Isolation

Each framework gets its own isolated Python/language environment:

```
frameworks/
├── fastapi-rest/
│   └── .venv/              # Isolated venv
│       ├── bin/python      # FastAPI-specific Python
│       └── lib/python3.13/site-packages/
├── flask-rest/
│   └── .venv/              # Different venv
│       ├── bin/python      # Flask-specific Python
│       └── lib/python3.13/site-packages/
├── strawberry/
│   └── .venv/              # Separate venv
└── graphene/
    └── .venv/              # Independent venv
```

### 2. Database Isolation

Each framework (or group) gets its own PostgreSQL database:

```
velocitybench_fastapi_rest    # FastAPI database
velocitybench_flask_rest      # Flask database
velocitybench_strawberry      # Strawberry database
velocitybench_graphene        # Graphene database
... (one per framework)
```

### 3. Dependency Isolation

Each framework specifies its own requirements:

```
fastapi-rest/
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml             # Project configuration
└── Dockerfile                 # Docker build spec
```

## Consequences

### Positive

✅ **No Dependency Conflicts**: pip packages in one venv don't affect others
✅ **Fair Benchmarking**: Each framework uses its optimal dependencies
✅ **Language Support**: Easy to add non-Python frameworks (Node.js, Go, Rust, etc.)
✅ **Reproducibility**: Lock file ensures exact same environment every run
✅ **Parallel Execution**: Frameworks can run simultaneously without conflicts
✅ **Easy Debugging**: Isolate issues to specific framework environment
✅ **Independent Scaling**: Framework venvs only contain needed packages

### Negative

❌ **Disk Space**: 38 venvs × ~500MB = ~19GB overhead
❌ **Setup Time**: Creating 38 environments takes ~30-60 minutes
❌ **Maintenance**: Updates to dependencies replicated across environments
❌ **Shared Tooling**: CI/CD must activate correct venv per framework
❌ **Development Complexity**: Developers must remember which venv to activate

## Alternatives Considered

### Alternative 1: Single Global Environment
```python
# All frameworks in one venv
pip install fastapi flask strawberry graphene django tornado ...
```

- Pros: Simple setup, minimal disk space
- Cons: Dependency conflicts, unfair comparison (one framework's optimizations affect others)
- **Rejected**: Violates fairness requirement

### Alternative 2: Docker Containers (No Isolation)
```bash
docker run -it fastapi-rest python main.py
docker run -it flask-rest python main.py
# Both use same base image, some shared layers
```

- Pros: Cleaner than venvs
- Cons: Still requires managing separate images, doesn't prevent conflicts
- **Rejected**: Doesn't fully isolate environments

### Alternative 3: Docker with Full Isolation
```dockerfile
# Each framework in separate container with unique base
FROM python:3.13
RUN pip install fastapi  # No conflict, isolated layer
```

- Pros: Complete isolation, reproducible
- Cons: Much larger disk footprint, slower CI/CD
- **Status**: Currently explored for CI/CD (full Docker containerization)

## Implementation Details

### Virtual Environment Creation

```bash
# Create isolated venv for each framework
for framework in fastapi-rest flask-rest strawberry graphene; do
    cd frameworks/$framework
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    deactivate
    cd ../..
done
```

### Database Isolation

```python
# Each framework connection string is unique
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://benchmark:password@localhost/velocitybench_fastapi_rest"
)

# Schema migrations per database
psql -d velocitybench_fastapi_rest -f schema.sql
```

### Running Tests with Isolation

```bash
# Activate correct venv, run tests
source frameworks/fastapi-rest/.venv/bin/activate
pytest tests/
deactivate

# Next framework
source frameworks/flask-rest/.venv/bin/activate
pytest tests/
deactivate
```

### Makefile Support

```makefile
test-fastapi:
	. frameworks/fastapi-rest/.venv/bin/activate && \
	pytest frameworks/fastapi-rest/tests/

test-all:
	. frameworks/fastapi-rest/.venv/bin/activate && pytest frameworks/fastapi-rest/tests/
	. frameworks/flask-rest/.venv/bin/activate && pytest frameworks/flask-rest/tests/
	# ... continue for all frameworks
```

## Related Decisions

- ADR-001: Trinity Pattern (same schema for all databases)
- ADR-003: Multi-Language Support (enables multiple languages)
- ADR-005: Ruff Linting (enforced in all venvs)

## Implementation Status

✅ Complete - All 38 frameworks have isolated environments

## Maintenance Strategy

1. **Updates**: Pin specific versions in requirements.txt per framework
2. **Security**: Regular `pip audit` and dependency updates
3. **Conflicts**: Test matrix catches dependency issues early
4. **Cleanup**: `make clean` removes all venvs, `make install-all` recreates

## References

- [Python venv Documentation](https://docs.python.org/3/library/venv.html)
- [Dependency Management Best Practices](https://packaging.python.org/en/latest/)
- [Docker Image Isolation](https://docs.docker.com/get-started/overview/)
