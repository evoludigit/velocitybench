# VelocityBench Blog Posts

Generated educational content about backend best practices, database patterns, and API design.

## Content Overview

| Pattern | Tutorials | Troubleshooting | Reference |
|---------|-----------|-----------------|-----------|
| **Trinity Pattern** | 3 (beginner, intermediate, advanced) | 1 | 1 |
| **N+1 Query Problem** | 3 (beginner, intermediate, advanced) | 1 | 1 |

**Total: 10 blog posts**

---

## Tutorials

Step-by-step educational content for different skill levels.

### Trinity Pattern
The Trinity Pattern uses three identifier types (pk_*, id UUID, slug) for optimal database design.

| Level | File | Description |
|-------|------|-------------|
| Beginner | [trinity-pattern-tutorial-beginner.md](tutorials/trinity-pattern-tutorial-beginner.md) | Introduction to the pattern with analogies |
| Intermediate | [trinity-pattern-tutorial-intermediate.md](tutorials/trinity-pattern-tutorial-intermediate.md) | Implementation details and ORM integration |
| Advanced | [trinity-pattern-tutorial-advanced.md](tutorials/trinity-pattern-tutorial-advanced.md) | Performance optimization and edge cases |

### N+1 Query Problem
The N+1 problem occurs when an app executes N+1 queries instead of 1-2 optimized queries.

| Level | File | Description |
|-------|------|-------------|
| Beginner | [n-plus-one-tutorial-beginner.md](tutorials/n-plus-one-tutorial-beginner.md) | Understanding the problem with examples |
| Intermediate | [n-plus-one-tutorial-intermediate.md](tutorials/n-plus-one-tutorial-intermediate.md) | Solutions: eager loading, batching |
| Advanced | [n-plus-one-tutorial-advanced.md](tutorials/n-plus-one-tutorial-advanced.md) | DataLoader, denormalization, caching |

---

## Troubleshooting Guides

Practical debugging guides for common issues.

| Pattern | File | Description |
|---------|------|-------------|
| Trinity Pattern | [trinity-pattern-troubleshooting.md](troubleshooting/trinity-pattern-troubleshooting.md) | Debugging identifier-related issues |
| N+1 Query Problem | [n-plus-one-troubleshooting.md](troubleshooting/n-plus-one-troubleshooting.md) | Detecting and fixing N+1 queries |

---

## Reference Documentation

Quick-reference guides for each pattern.

| Pattern | File | Description |
|---------|------|-------------|
| Trinity Pattern | [trinity-pattern-reference.md](reference/trinity-pattern-reference.md) | Schema, queries, and API reference |
| N+1 Query Problem | [n-plus-one-reference.md](reference/n-plus-one-reference.md) | Query examples and solutions |

---

## Generation

These blog posts were generated using local AI models from the VelocityBench seed data corpus.

### Source Material
- Pattern definitions: `database/seed-data/corpus/patterns/`
- Generator script: `database/seed-data/generator/generate_blog_vllm.py`

### Regenerate Posts
```bash
# Ensure vLLM is running
vllm-switch status

# Generate all posts
python database/seed-data/generator/generate_blog_vllm.py --all

# Generate specific post
python database/seed-data/generator/generate_blog_vllm.py \
  --pattern trinity-pattern \
  --type tutorial \
  --depth beginner
```

### Available Options
- `--pattern`: `trinity-pattern`, `n-plus-one`
- `--type`: `tutorial`, `troubleshooting`, `reference`
- `--depth`: `beginner`, `intermediate`, `advanced` (tutorials only)
- `--all`: Generate all posts
- `--stdout`: Output to console instead of file
