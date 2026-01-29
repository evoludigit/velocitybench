# Blog Generation Cheat Sheet

## Quick Start

### Check vLLM Status
```bash
make vllm-status
```

### Generate Single Blog
```bash
make blog-pattern PATTERN=comparison-postgraphile-vs-fraiseql TYPE=comparison DEPTH=beginner
```

### Generate All Depths for a Pattern
```bash
for depth in beginner intermediate advanced; do
  make blog-pattern PATTERN=comparison-graphql-vs-rest TYPE=comparison DEPTH=$depth
done
```

## Available Patterns

### Framework Comparisons (Tier 1)
- `comparison-frameworks-code-vs-schema-vs-autogen`
- `comparison-postgraphile-vs-fraiseql`
- `comparison-hasura-vs-fraiseql`
- `comparison-strawberry-vs-fraiseql`

### Framework Comparisons (Tier 2)
- `comparison-graphql-vs-rest`
- `comparison-federation-strategies-by-framework`
- `comparison-type-safety-by-language`
- `comparison-orm-and-graphql-integration`

### Architectural Benchmarks
- `benchmark-caching-strategies`
- `benchmark-error-handling-strategies`
- `benchmark-federation-vs-monolithic`
- `benchmark-n-plus-one-prevention-strategies`
- `benchmark-pagination-strategies`
- `benchmark-testing-strategies`

## All Generated Blogs Location
```
/home/lionel/code/velocitybench/database/seed-data/output/blog/comparisons/
```

## Regenerate Batch

### All Framework Comparisons
```bash
bash /tmp/generate_all_blogs.sh
```

### All Benchmarks
```bash
bash /tmp/generate_benchmarks.sh
```

## Environment

- **vLLM Server**: http://localhost:8000
- **Model**: Ministral-3-8B-Instruct-2512
- **Python Env**: `/home/lionel/code/velocitybench/venv`
- **Generator Script**: `database/seed-data/generator/generate_blog_vllm.py`

