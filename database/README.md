# VelocityBench Database Tools

Database setup and seed data generators for VelocityBench framework benchmarking.

## Python Environment Setup

This directory uses `uv` for Python dependency management with an isolated virtual environment.

### Initial Setup

```bash
# Navigate to database directory
cd database

# Create virtual environment and install dependencies
uv sync --no-build-isolation
```

This creates a `.venv` directory with all dependencies:
- `faker` - Generate realistic user data
- `psycopg` (v3) - PostgreSQL adapter
- `pyyaml` - YAML parsing

### Running Scripts

Use `uv run` to execute scripts with the correct environment:

```bash
# Test blog post loader (dry run)
uv run python seed-data/generator/load_blog_posts.py --dry-run

# Load blog posts to database
uv run python seed-data/generator/load_blog_posts.py \
  --users 5000 \
  --connection "postgresql://user:pass@localhost/db"
```

Or activate the environment manually:

```bash
source .venv/bin/activate
python seed-data/generator/load_blog_posts.py --dry-run
```

## Database Setup

### Quick Start

```bash
# Setup all frameworks with XS dataset (default)
python setup.py

# Setup with blog dataset (5000 users, 2243 posts)
python setup.py --size blog

# Setup specific framework
python setup.py fraiseql --size blog
```

### Dataset Sizes

| Size | Users | Posts | Load Time | Use Case |
|------|-------|-------|-----------|----------|
| `xs` | 100 | 500 | <1s | Development |
| `medium` | 10K | 50K | 30-60s | N+1 testing |
| `large` | 100K | 500K | 5-15min | Stress testing |
| `blog` | 5000 | 2243 | 30-45s | Real blog posts with Faker users |

## Blog Post Loader

The blog dataset uses a specialized loader that:
1. Generates 5000 realistic users with Faker
2. Parses 2,243 markdown blog posts
3. Assigns authors via round-robin (most users have 0 posts for future comments)
4. Bulk loads via PostgreSQL COPY command

### Usage

```bash
# Full load (default: 5000 users)
uv run python seed-data/generator/load_blog_posts.py \
  --connection "postgresql://velocitybench:password@localhost/db_fraiseql"

# Test with smaller dataset
uv run python seed-data/generator/load_blog_posts.py \
  --users 100 \
  --connection "postgresql://..."

# Dry run (validate only, no database)
uv run python seed-data/generator/load_blog_posts.py --dry-run

# Generate TSV only (no database load)
uv run python seed-data/generator/load_blog_posts.py --generate-only
```

### CLI Options

- `--users N` - Number of users to generate (default: 5000)
- `--connection STRING` - PostgreSQL connection string
- `--dry-run` - Validate files without loading to database
- `--generate-only` - Generate TSV files only (no database)
- `--output PATH` - Output directory for TSV files (default: /tmp)

## Project Structure

```
database/
├── pyproject.toml          # Python dependencies (uv)
├── .venv/                  # Virtual environment (gitignored)
├── setup.py                # Main orchestration script
├── 01-extensions.sql       # PostgreSQL extensions
├── 02-schema.sql          # Trinity Pattern schema
├── seed-data/
│   ├── generator/
│   │   ├── markdown_parser.py       # Parse blog markdown
│   │   ├── load_blog_posts.py       # Blog loader with Faker
│   │   └── generate_blog_vllm.py    # Generate blog posts (vLLM)
│   ├── corpus/
│   │   ├── patterns/                 # YAML pattern definitions
│   │   └── datasets/
│   │       └── blog.yaml             # Blog dataset config
│   └── output/
│       ├── blog/                     # Generated markdown posts
│       └── sql/                      # Generated SQL seed data
```

## Dependencies

### System Requirements
- Python 3.10+
- PostgreSQL 14+
- `uv` package manager

### Python Packages (managed by uv)
- `faker>=28.0.0` - Realistic test data generation
- `psycopg>=3.2.0` - PostgreSQL adapter (v3)
- `pyyaml>=6.0.0` - YAML parsing

## Development

### Adding Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev pytest-cov
```

### Running Tests

```bash
# Install dev dependencies
uv sync

# Run tests (when available)
uv run pytest
```

### Linting

```bash
# Run ruff linter
uv run ruff check .

# Format code
uv run ruff format .
```

## Troubleshooting

### Import Errors

If you see "ModuleNotFoundError: No module named 'faker'":

```bash
# Make sure you're using uv run
uv run python script.py

# Or activate the environment first
source .venv/bin/activate
python script.py
```

### Database Connection Issues

Check PostgreSQL is running:
```bash
systemctl status postgresql
```

Verify connection string format:
```
postgresql://user:password@host:port/database
```

### Blog Post Parsing Warnings

Some YAML frontmatter warnings are expected (malformed frontmatter in a few posts).
The loader handles these gracefully and continues parsing.
