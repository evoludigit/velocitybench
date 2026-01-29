# Development Guide for VelocityBench

Welcome to VelocityBench development! This guide covers setup, development workflows, and how to contribute.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Virtual Environments](#virtual-environments)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Adding New Frameworks](#adding-new-frameworks)
- [Adding New Benchmarks](#adding-new-benchmarks)
- [Testing](#testing)
- [Git Workflow](#git-workflow)

---

## Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- PostgreSQL client tools (psql, pg_dump)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/velocitybench/velocitybench.git
cd velocitybench

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install

# Set up root virtual environment (for blog generation)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Docker containers
docker-compose up -d postgres

# That's it! Check status with:
make venv-check
make db-up
```

---

## Project Structure

```
velocitybench/
├── database/                    # Database schema, migrations, seed data
│   ├── pyproject.toml          # Database project config (uv)
│   ├── .venv/                  # Database venv (Python 3.11)
│   ├── schema/                 # SQL schema files
│   └── seed-data/              # Data generation scripts
│       ├── generator/          # Python generators for personas, comments, blogs
│       ├── corpus/             # YAML pattern library
│       └── output/             # Generated output (blogs, comments, personas)
│
├── frameworks/                  # Framework implementations (28 frameworks)
│   ├── fastapi-rest/           # FastAPI REST implementation
│   ├── flask-rest/             # Flask REST implementation
│   ├── strawberry/             # Strawberry GraphQL
│   ├── graphene/               # Graphene GraphQL
│   ├── fraiseql/               # FraiseQL custom framework
│   └── ...                     # Other frameworks
│
├── tests/                      # Testing infrastructure
│   ├── integration/            # Framework integration tests
│   ├── perf/                   # Performance benchmarking
│   │   ├── jmeter/            # JMeter test plans
│   │   └── scripts/           # Analysis scripts (including index-results.py)
│   └── qa/                     # QA validators
│
├── docs/                       # Documentation
├── monitoring/                 # Prometheus/Grafana config
├── Makefile                    # Build automation
├── docker-compose.yml          # Multi-container orchestration
├── README.md                   # Project overview
├── DEVELOPMENT.md              # This file
├── VLLM_SETUP.md              # vLLM configuration
└── .github/workflows/         # CI/CD pipeline
```

---

## Virtual Environments

VelocityBench uses **multiple isolated Python venvs**. Each component has its own:

### Root venv (Python 3.13.7)
```bash
source venv/bin/activate
# For: Blog generation, Makefile execution
```

### Database venv (Python 3.11.14)
```bash
source database/.venv/bin/activate
# For: Database setup, seed data generation
```

### Framework venvs (Python 3.13.7)
```bash
source frameworks/fastapi-rest/.venv/bin/activate
source frameworks/strawberry/.venv/bin/activate
# etc.
```

### Why multiple venvs?
- Framework compatibility: Each framework has specific version requirements
- Isolation: No cross-framework dependency conflicts
- Fair benchmarking: Each framework gets its own environment

---

## Development Workflow

### 1. Pick What You Want to Work On

**Option A: Framework Development**
```bash
cd frameworks/fastapi-rest
source .venv/bin/activate
# Edit code, run tests, benchmark

# Run tests
python -m pytest tests/

# Start framework
python main.py
```

**Option B: Database/Generator Development**
```bash
cd database
source .venv/bin/activate
# Edit data generation code

# Generate test personas
python seed-data/generator/generate_personas.py --count 10 --dry-run

# Generate blog posts
python seed-data/generator/generate_blog_vllm.py --pattern trinity-pattern
```

**Option C: Testing & Validation**
```bash
source tests/qa/.venv/bin/activate
# Run integration tests, validators

make framework-smoke
make framework-list
```

### 2. Code Quality Checks

Run before committing:

```bash
# Lint and format Python code
make lint
make format

# Type-check
make type-check

# All at once
make quality

# Or use pre-commit (automatic on commit)
pre-commit run --all-files
```

### 3. Testing

```bash
# Run framework-specific tests
cd frameworks/fastapi-rest
python -m pytest tests/

# Run integration tests
cd tests/integration
bash test-all-frameworks.sh

# Run performance tests
cd tests/perf
bash scripts/run-test.sh
```

### 4. Performance Analysis

```bash
# Index all performance results
python tests/perf/scripts/index-results.py

# Query results
python tests/perf/scripts/index-results.py --query framework=strawberry
python tests/perf/scripts/index-results.py --recent 10
python tests/perf/scripts/index-results.py --summary
```

---

## Code Quality

### Style Standards

We follow [ruff](https://github.com/astral-sh/ruff) standards:

```bash
# Check style
make lint

# Auto-fix style issues
make format
```

### Type Hints

All new functions should have complete type hints:

```python
def generate_personas(count: int, output_dir: Path) -> list[dict]:
    """Generate N personas and return them."""
    ...
```

### Pre-commit Hooks

Auto-format code before commits:

```bash
# Install hooks (one-time)
pre-commit install

# Hooks run automatically on commit
git commit ...  # ruff, prettier, security checks run automatically

# Or run manually
pre-commit run --all-files
```

### Test Coverage

Coverage thresholds are set in `.coveragerc`:

```bash
# Generate coverage report
python -m pytest --cov=frameworks/fastapi-rest tests/

# Check coverage
coverage report --fail-under=70
```

---

## Adding New Frameworks

### Step 1: Create Framework Directory

```bash
mkdir -p frameworks/my-framework
cd frameworks/my-framework

# Create structure
mkdir -p src tests database
touch main.py requirements.txt requirements-dev.txt
```

### Step 2: Implement Required Endpoints

Your framework must implement these endpoints (REST or GraphQL):

**REST Endpoints:**
- `GET /ping` - Health check
- `GET /users` - List users
- `GET /users/:id` - Get user
- `POST /users` - Create user
- `GET /posts` - List posts
- `GET /posts/:id` - Get post with author
- Similar for comments

**GraphQL Queries:**
- `users` - List users
- `user(id: ID!)` - Get user
- `posts` - List posts
- `post(id: ID!)` - Get post
- Similar structure for mutations

### Step 3: Set Up Tests

Copy test template from `testing-templates/`:

```bash
cp ../../testing-templates/FRAMEWORK_TEST_TEMPLATE_*.py tests/
# Edit for your framework specifics
```

### Step 4: Add to docker-compose.yml

```yaml
my-framework:
  build: frameworks/my-framework
  ports:
    - "8123:8000"  # Use unique port
  environment:
    DB_HOST: postgres
    DB_NAME: my_framework_test
  depends_on:
    postgres:
      condition: service_healthy
```

### Step 5: Update Framework Registry

Edit `tests/qa/framework_registry.yaml`:

```yaml
my-framework:
  language: python
  type: rest  # or graphql
  endpoint: http://localhost:8123
  features:
    - authentication: false
    - rate_limiting: false
  expected_response_time: 50  # ms
```

### Step 6: Run Tests

```bash
# Integration tests
make framework-smoke

# Performance tests
make framework-perf FRAMEWORK=my-framework
```

---

## Adding New Benchmarks

### Step 1: Create YAML Pattern

Add to `database/seed-data/corpus/patterns/`:

```yaml
# patterns/my-benchmark-category/my-benchmark.yaml
name: "My Benchmark Pattern"
summary:
  short: "Brief description"
  long: "Detailed description with context"

problem:
  description: "What problem does this solve?"

solution:
  principle: "The core solution approach"
  components:
    - name: "Component 1"
      purpose: "What it does"

use_case_recommendations:
  - scenario: "When to use this"
    recommendation: "Use this approach because..."
    reason: "Technical justification"
```

### Step 2: Generate Blog Content

```bash
# Single pattern
make blog-pattern PATTERN=my-benchmark TYPE=tutorial DEPTH=beginner

# All patterns
make blog-all
```

### Step 3: Generate Comments

```bash
# Generate personas
make personas-generate

# Generate comments on blogs
make comments-generate

# Validate and filter
make comments-validate

# Load to database
make comments-load
```

---

## Testing

### Running Tests

```bash
# All Python tests
python -m pytest frameworks/*/tests/ database/tests/

# Specific framework
python -m pytest frameworks/fastapi-rest/tests/ -v

# With coverage
python -m pytest --cov=frameworks/fastapi-rest frameworks/fastapi-rest/tests/

# Only specific test type
python -m pytest -m performance
python -m pytest -m security
python -m pytest -m integration
```

### Test Markers

Tests use pytest markers for organization:

```python
@pytest.mark.asyncio
@pytest.mark.integration
def test_user_creation():
    ...

@pytest.mark.performance
def test_query_latency():
    ...

@pytest.mark.security
def test_sql_injection_prevention():
    ...
```

Run specific markers:
```bash
pytest -m performance
pytest -m "security and not slow"
```

---

## Git Workflow

### Commit Message Format

```
<type>(<scope>): <description>

## Changes
- Change 1
- Change 2

## Verification
✅ Tests pass
✅ Lints clean

Co-Authored-By: Your Name <email@example.com>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code reorganization
- `test`: Test additions
- `docs`: Documentation
- `chore`: Maintenance

### Branching Strategy

```bash
# Create feature branch
git checkout -b feat/my-feature

# Work and commit
git add .
git commit -m "feat(framework): add support for X"

# Push
git push origin feat/my-feature

# Create pull request
# (GitHub: compare & pull request)
```

### Pre-commit Hooks

Pre-commit hooks run automatically:

```bash
# On commit, these run:
# - ruff check (linting)
# - ruff format (formatting)
# - prettier (YAML/Markdown)
# - trailing-whitespace, end-of-file-fixer
# - security checks (bandit)

# If any fail, commit is blocked
# Fix issues and re-commit
```

### Code Review Checklist

- [ ] Code follows style guidelines (lint passes)
- [ ] Type hints are complete
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No hardcoded credentials or secrets
- [ ] Performance impact considered
- [ ] Backward compatibility maintained

---

## Common Tasks

### Update Dependencies

```bash
# Root venv
pip install --upgrade -r requirements.txt

# Database
cd database && uv sync --upgrade

# Framework
cd frameworks/fastapi-rest && pip install --upgrade -r requirements.txt
```

### Generate Data at Different Scales

```bash
# Small dataset (testing)
DATA_VOLUME=xs make db-setup

# Medium dataset (development)
DATA_VOLUME=medium make db-setup

# Large dataset (benchmarking)
DATA_VOLUME=large make db-setup
```

### Debug a Framework

```bash
cd frameworks/fastapi-rest

# Start in debug mode
python main.py --debug

# Or with logging
LOGLEVEL=DEBUG python main.py

# Check health
curl http://localhost:8003/health
```

### Profile Performance

```bash
# Run with profiler
python -m cProfile -o profile.stats main.py

# Analyze results
python -m pstats profile.stats

# Or use py-spy
pip install py-spy
py-spy record -o profile.svg -- python main.py
```

---

## Troubleshooting

### vLLM Not Running

```bash
# Start vLLM
make vllm-start

# Check status
make vllm-status

# View logs
sudo journalctl -u vllm -n 50 --follow
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Reset database
make db-down
make db-up

# Check connection
psql -h localhost -U benchmark -d velocitybench_benchmark
```

### Framework Won't Start

```bash
# Check logs
docker-compose logs my-framework

# Rebuild image
docker-compose build --no-cache my-framework

# Start in debug mode
docker-compose run --rm -it my-framework bash
```

### Tests Failing

```bash
# Run with verbose output
pytest -vv tests/

# Run single test
pytest tests/test_users.py::test_get_user -vv

# With debugging
pytest --pdb tests/  # Drops to pdb on failure
```

---

## Resources

- **[README.md](README.md)** - Project overview
- **[SCOPE_AND_LIMITATIONS.md](SCOPE_AND_LIMITATIONS.md)** - Benchmark methodology
- **[docs/README_ARCHITECTURE.md](docs/README_ARCHITECTURE.md)** - Architecture guide
- **[tests/qa/](tests/qa/)** - Integration validators
- **[Makefile](Makefile)** - All available commands

---

## Questions?

- Check [GitHub Issues](https://github.com/velocitybench/velocitybench/issues)
- Review [test examples](tests/)
- Look at existing [framework implementations](frameworks/)

---

**Happy developing! 🚀**
