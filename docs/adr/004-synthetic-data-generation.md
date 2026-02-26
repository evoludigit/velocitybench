# ADR-004: Synthetic Data Generation with vLLM for Realistic Workloads

**Status**: Accepted
**Date**: 2024-01-18
**Author**: VelocityBench Team

## Context

Benchmarking requires realistic data that:
1. Mimics real user behavior and content
2. Is reproducible across test runs
3. Doesn't require copyright/privacy-sensitive real data
4. Scales to thousands/millions of records
5. Represents diverse content patterns

Manual data creation is infeasible. Static datasets lack realism. Random data doesn't represent user patterns.

## Decision

Use **vLLM (Local Large Language Model)** to generate synthetic data:

### 1. Components

```
┌─────────────────────────────────────┐
│  Seed Data Generation Scripts       │
├─────────────────────────────────────┤
│  ├── generate_personas.py           │ Generate user profiles
│  ├── generate_blog_vllm.py          │ Generate blog articles
│  ├── generate_blog_comments.py      │ Generate comments on blogs
│  ├── validate_blog_comments.py      │ Quality control filtering
│  └── corpus/patterns/               │ Pattern library (YAML)
├─────────────────────────────────────┤
│  ↓ Uses vLLM server (localhost:8000)│
├─────────────────────────────────────┤
│  ├── Personas (diverse profiles)    │
│  ├── Blog Posts (technical articles)│
│  ├── Comments (realistic responses) │
│  └── Comment Replies (discussions)  │
└─────────────────────────────────────┘
```

### 2. Data Generation Pipeline

**Step 1: Personas** (Synthetic Users)
```python
# Generate N diverse personas with:
# - Name, email, background
# - Technical interests/expertise
# - Writing style
# - Response patterns

personas = generate_personas(count=1000)
# Result: Consistent, diverse user profiles
```

**Step 2: Blog Articles** (Technical Content)
```python
# Generate blog posts from pattern library
# - Technical tutorials
# - Best practices guides
# - Case studies
# - Architecture discussions

articles = generate_blog_posts(
    patterns=[
        "deployment-history-tracking",
        "request-deduplication",
        "shared-state-resilience",
        ...
    ]
)
# Result: Realistic technical content
```

**Step 3: Blog Comments** (Realistic Responses)
```python
# Generate comments matching article content
# - Questions about implementation
# - Alternative approaches
# - Personal experiences
# - Constructive feedback

comments = generate_blog_comments(
    articles=articles,
    personas=personas,
    comments_per_article=50
)
# Result: Realistic discussion threads
```

**Step 4: Validation** (Quality Control)
```python
# Filter for:
# - Generic praise (reject)
# - Hallucinated errors (reject)
# - Duplicate comments (reject)
# - Too short/long (reject)
# - Off-topic (reject)

valid_comments = validate_comments(comments, articles)
# Result: High-quality comments only
```

### 3. vLLM Integration

```bash
# Start vLLM server (once)
python -m vllm.entrypoints.openai_api_server \
    --model meta-llama/Llama-2-7b-hf \
    --tensor-parallel-size 1

# Generator scripts call vLLM API
curl http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama-2",
        "prompt": "Generate a technical blog post about...",
        "max_tokens": 2000
    }'
```

### 4. Data Reproducibility

```python
# Set random seed for consistent generation
random.seed(42)
torch.manual_seed(42)

# Generate personas with seed
personas = generate_personas(count=100, seed=42)
# Run 1: generates same personas as Run 2

# Temperature control
response = vllm_call(
    prompt=prompt,
    temperature=0.7,  # Deterministic with same seed
    top_p=0.9,        # Consistent sampling
)
```

## Consequences

### Positive

✅ **Realistic Data**: LLM-generated content mimics human writing patterns
✅ **Diversity**: Different personas, topics, writing styles
✅ **Scale**: Generate 10K+ comments without manual effort
✅ **Reproducibility**: Same seed produces identical data
✅ **No Privacy Issues**: Synthetic data, no real user information
✅ **Fast Iteration**: Regenerate with different parameters quickly
✅ **Pattern Library**: Reusable YAML patterns for different domains

### Negative

❌ **vLLM Dependency**: Requires running local LLM server (15-30 min setup)
❌ **GPU Memory**: Large models need 8GB+ VRAM (can use CPU, slower)
❌ **Setup Complexity**: Additional infrastructure beyond database + frameworks
❌ **Hallucination Risk**: LLM might generate false technical details (mitigated by validation)
❌ **License Considerations**: Must respect open source model licenses
❌ **Non-determinism**: LLM output can vary slightly even with seed

### Mitigations

- **Validation Script**: Filters hallucinated/generic comments
- **Seed Control**: Ensure reproducibility for benchmarks
- **Pattern Library**: Guide LLM with domain-specific examples
- **QA Checks**: Verify generated data makes sense

## Alternatives Considered

### Alternative 1: Manual Data Entry
```python
comments = [
    "Great tutorial!",
    "This really helped me understand X",
    "I tried this approach and...",
    # ... manually type hundreds of comments
]
```

- Pros: 100% control over content
- Cons: Time-prohibitive, not scalable, limited diversity
- **Rejected**: Infeasible for 10K+ records

### Alternative 2: Pure Random Generation
```python
def generate_comment():
    return f"User {random.randint(1, 1000)} said: {random.choice(templates)}"
```

- Pros: Fast, simple
- Cons: Unrealistic, repetitive, doesn't exercise real query patterns
- **Rejected**: Doesn't meet realism requirement

### Alternative 3: Real Data (Web Scraping)
```python
comments = scrape_hacker_news_comments()
```

- Pros: Authentic data
- Cons: Copyright issues, privacy concerns, requires attribution
- **Rejected**: Legal/ethical concerns

### Alternative 4: Static Fixtures
```python
COMMENTS = [
    "This is a well-written tutorial...",
    "The performance benchmarks are helpful...",
    # Hard-coded list, never changes
]
```

- Pros: No generation overhead
- Cons: Limited diversity, doesn't scale, unrealistic for 10K records
- **Rejected**: Not representative

## Implementation Status

✅ Complete - vLLM integration with three generator scripts
✅ Quality validation in place
✅ Pattern library with 50+ patterns
✅ Reproducible seed-based generation

## Performance Characteristics

| Component | Time | CPU | GPU |
|-----------|------|-----|-----|
| Generate 1 persona | ~100ms | Low | Med |
| Generate 1 blog post | ~2-5 sec | Low | High |
| Generate 50 comments | ~50 sec | Low | High |
| Validate 1K comments | ~30 sec | High | None |
| Total (1K personas, 50 blogs, 2.5K comments) | ~30 min | Variable | 4GB+ |

## Usage Examples

```bash
# Generate personas
python database/seed-data/generator/generate_personas.py \
    --count 1000 \
    --output-dir database/seed-data/output/

# Generate blog posts
python database/seed-data/generator/generate_blog_vllm.py \
    --pattern deployment-history-tracking \
    --num-posts 50

# Generate comments
python database/seed-data/generator/generate_blog_comments.py \
    --personas-file personas.json \
    --articles-dir blogs/

# Validate and filter
python database/seed-data/generator/validate_blog_comments.py \
    --comments-dir generated/comments \
    --strict
```

## Related Decisions

- ADR-003: Multi-Language Support (same data for all frameworks)
- ADR-001: Trinity Pattern (schema for storing generated data)
- ADR-002: Framework Isolation (each framework tests with same data)

## References

- [vLLM GitHub](https://github.com/lm-sys/vllm)
- [Synthetic Data Generation](https://en.wikipedia.org/wiki/Synthetic_data)
- [LLM Applications](https://arxiv.org/abs/2306.07730)
- [Model Reproducibility](https://pytorch.org/docs/stable/notes/randomness.html)
