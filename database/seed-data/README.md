# Seed Data Knowledge Corpus

**Vision**: The seed data is a **corpus of backend best practices** that serves dual purposes:
1. **Educational Content** - Source material for AI-generated blog posts
2. **Executable Data** - Loadable into databases for benchmarking

## Architecture Overview

```
database/seed-data/
├── README.md                   ← This file
├── corpus/                     ← KNOWLEDGE BASE (source of truth)
│   ├── patterns/               ← Backend pattern definitions (YAML)
│   │   ├── identifiers/        ← Trinity Pattern, UUID strategies
│   │   ├── queries/            ← N+1, pagination, aggregation
│   │   ├── architecture/       ← CQRS, event sourcing
│   │   ├── relationships/      ← FK design, cascades, soft deletes
│   │   └── performance/        ← Indexing, caching, denormalization
│   ├── frameworks/             ← 26 framework-specific implementations
│   ├── languages/              ← 8 language-specific patterns
│   ├── use-cases/              ← Domain-specific applications
│   └── depths/                 ← Skill level configurations
│
├── prompts/                    ← AI GENERATION PROMPTS
│   ├── blog-tutorial.md        ← Prompt for tutorial-style posts
│   ├── blog-reference.md       ← Prompt for reference documentation
│   ├── blog-comparison.md      ← Prompt for framework comparisons
│   └── blog-troubleshooting.md ← Prompt for debugging guides
│
├── templates/                  ← OUTPUT TEMPLATES
│   ├── blog/                   ← Jinja2 blog post templates
│   └── sql/                    ← SQL generation templates
│
├── generator/                  ← GENERATION TOOLING
│   ├── generate_blog.py        ← Orchestrates AI blog generation
│   ├── generate_sql.py         ← Converts corpus → SQL
│   └── matrix.yaml             ← Generation combinations matrix
│
└── output/                     ← GENERATED OUTPUT
    ├── blog/                   ← AI-generated blog posts
    └── sql/                    ← Generated SQL files
```

## Multi-Model Generation Strategy

This corpus is designed for **multi-model AI generation**:

| Model | Role | Best For |
|-------|------|----------|
| **Claude Code** | Architect | Complex prompts, quality control, verification |
| **opencode** | Writer | Actual blog post generation (free tier) |
| **vLLM (local)** | Bulk | Simple transformations, boilerplate, repetitive tasks |

### Workflow

```
1. Claude Code: Design prompt + select corpus entries
         ↓
2. opencode/vLLM: Generate blog post from prompt + corpus
         ↓
3. Claude Code: Review, quality check, iterate if needed
         ↓
4. Output: Verified blog post ready for publishing
```

## YAML Corpus Format

Each pattern is defined in YAML for easy AI consumption:

```yaml
# corpus/patterns/identifiers/trinity-pattern.yaml
id: trinity-pattern
name: Trinity Pattern
category: identifiers
difficulty: intermediate

summary:
  short: "Three identifier types for optimal database + API design"
  long: |
    The Trinity Pattern uses three types of identifiers to optimize
    database performance while maintaining clean API design.

problem:
  description: |
    Backend developers face a fundamental dilemma with identifiers...
  symptoms:
    - Sequential IDs leak business information
    - UUIDs slow down database operations
    - URLs are ugly with UUIDs

solution:
  components:
    - name: pk_*
      type: SERIAL INTEGER
      purpose: Internal database operations
      visibility: never exposed
    - name: id
      type: UUID
      purpose: Public API exposure
    - name: identifier
      type: VARCHAR UNIQUE
      purpose: Human-readable URLs

schema:
  sql: |
    CREATE TABLE tb_user (
      pk_user SERIAL PRIMARY KEY,
      id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
      username VARCHAR(100) UNIQUE NOT NULL,
      ...
    );

seed_data:
  fixtures:
    - id: "11111111-1111-1111-1111-111111111111"
      username: alice
      role: admin
    - id: "22222222-2222-2222-2222-222222222222"
      username: bob
      role: user

blog_hooks:
  beginner:
    analogy: |
      Think of it like a person having a Social Security Number (internal),
      a passport number (official ID), and a nickname (human-friendly).
  advanced:
    performance_deep_dive: true
    benchmark_comparison: true
```

## Generation Scale

The combinatorial design enables massive scale:

| Source Files | × Frameworks | × Depths | × Formats | = Blog Posts |
|--------------|--------------|----------|-----------|--------------|
| 50 patterns  | 26           | 3        | 4         | 15,600       |
| 10 use-cases | 26           | 3        | 2         | 1,560        |
| Comparisons  | C(26,2)=325  | 3        | 1         | 975          |
| **Total**    |              |          |           | **18,000+**  |

## Usage

### Generate SQL for Benchmarking
```bash
# XS dataset (100 users, fast)
python generator/generate_sql.py --size xs

# Medium dataset (10K users, N+1 visible)
python generator/generate_sql.py --size medium

# Large dataset (100K users, scale testing)
python generator/generate_sql.py --size large
```

### Generate Blog Posts
```bash
# Single pattern, all frameworks
python generator/generate_blog.py --pattern trinity-pattern --all-frameworks

# Single framework, all patterns
python generator/generate_blog.py --framework postgraphile --all-patterns

# Specific combination
python generator/generate_blog.py --pattern n-plus-one --framework rails --depth beginner
```

### Use with AI Models
```bash
# Generate prompt for Claude Code review
python generator/create_prompt.py --pattern trinity-pattern --format tutorial

# Generate with opencode (free)
opencode generate output/blog/trinity-pattern-postgraphile-beginner.md

# Bulk generate with vLLM
python generator/bulk_generate.py --model vllm --batch prompts/batch-1.json
```

## Directory Contents

### /corpus/patterns/
Backend pattern definitions organized by category:
- `identifiers/` - Trinity Pattern, UUID strategies, slug handling
- `queries/` - N+1 prevention, pagination, aggregations
- `architecture/` - CQRS, event sourcing, microservices
- `relationships/` - FK design, cascades, soft deletes
- `performance/` - Indexing, caching, denormalization

### /corpus/frameworks/
Framework-specific implementations for all 26 frameworks:
- Node.js: postgraphile, apollo-server, graphql-yoga, etc.
- Python: strawberry, graphene, ariadne, etc.
- Ruby: rails, hanami
- Java: spring-graphql, micronaut-graphql, etc.
- And more...

### /corpus/languages/
Language-specific patterns and idioms:
- TypeScript, Python, Ruby, Java, Go, C#, PHP, Rust

### /prompts/
AI generation prompts optimized for different models:
- Structured prompts for opencode/vLLM
- Quality control prompts for Claude Code review

## Philosophy

1. **YAML is the Source of Truth** - All knowledge lives in structured YAML
2. **AI Does the Writing** - Humans design, AI generates
3. **Quality via Review** - Claude Code verifies AI-generated content
4. **Combinatorial Scale** - Small corpus → thousands of posts
5. **Executable Examples** - All code examples are tested and runnable
