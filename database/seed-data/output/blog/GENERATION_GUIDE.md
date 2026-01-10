# Blog Post Generation Guide

This guide explains how to generate blog posts from the YAML corpus using various AI models.

## Quick Start

### Option 1: Interactive opencode (Recommended for Quality)

Run opencode interactively to generate blog posts with full control:

```bash
cd /home/lionel/code/velocitybench

# Generate Trinity Pattern tutorial for beginners
opencode run "Generate a blog post about the Trinity Pattern. Read the source material from database/seed-data/corpus/patterns/identifiers/trinity-pattern.yaml and write a beginner-friendly tutorial. Save to database/seed-data/output/blog/tutorials/trinity-pattern-tutorial-beginner.md"

# Generate N+1 troubleshooting guide
opencode run "Generate a troubleshooting guide for N+1 query problems. Read database/seed-data/corpus/patterns/queries/n-plus-one.yaml and create a debugging guide. Save to database/seed-data/output/blog/troubleshooting/n-plus-one-troubleshooting.md"
```

### Option 2: Using the Generator Script

First generate the prompt, then pass to opencode:

```bash
# Generate prompt
python3 database/seed-data/generator/generate_blog_prompt.py \
  --pattern trinity-pattern \
  --type tutorial \
  --depth beginner \
  --stdout > /tmp/prompt.txt

# Use prompt with opencode
cat /tmp/prompt.txt | opencode run
```

### Option 3: Batch Generation (Manual)

Run the batch script and approve permissions as prompted:

```bash
./database/seed-data/generator/generate_blogs_with_opencode.sh
```

## Blog Posts to Generate

### Trinity Pattern (database/seed-data/corpus/patterns/identifiers/trinity-pattern.yaml)

| Type | Depth | Output File |
|------|-------|-------------|
| Tutorial | Beginner | `tutorials/trinity-pattern-tutorial-beginner.md` |
| Tutorial | Intermediate | `tutorials/trinity-pattern-tutorial-intermediate.md` |
| Tutorial | Advanced | `tutorials/trinity-pattern-tutorial-advanced.md` |
| Troubleshooting | All | `troubleshooting/trinity-pattern-troubleshooting.md` |
| Reference | All | `reference/trinity-pattern-reference.md` |

### N+1 Query Problem (database/seed-data/corpus/patterns/queries/n-plus-one.yaml)

| Type | Depth | Output File |
|------|-------|-------------|
| Tutorial | Beginner | `tutorials/n-plus-one-tutorial-beginner.md` |
| Tutorial | Intermediate | `tutorials/n-plus-one-tutorial-intermediate.md` |
| Tutorial | Advanced | `tutorials/n-plus-one-tutorial-advanced.md` |
| Troubleshooting | All | `troubleshooting/n-plus-one-troubleshooting.md` |
| Reference | All | `reference/n-plus-one-reference.md` |

## Available Models

```bash
# Free opencode models
opencode run --model "opencode/glm-4.7-free" "..."
opencode run --model "opencode/gpt-5-nano" "..."

# Local vLLM (if running)
opencode run --model "vllm/ministral-3-8b" "..."
```

## Example Prompts

### Tutorial (Beginner)
```
You are a senior backend engineer writing educational content. Write a tutorial blog post about the Trinity Pattern for database identifier design.

Target audience: Beginner backend developers (1-3 years experience).

The Trinity Pattern uses three identifier types:
1. pk_* (SERIAL INTEGER) - Internal database operations, never exposed
2. id (UUID) - Public API exposure, always stable
3. identifier/slug (VARCHAR) - Human-readable URLs

Include:
- An analogy (like SSN vs Passport vs Nickname)
- SQL schema examples
- Common mistakes to avoid
- Key takeaways

Length: 1500-2000 words
Save to: database/seed-data/output/blog/tutorials/trinity-pattern-tutorial-beginner.md
```

### Troubleshooting Guide
```
Write a troubleshooting guide for the N+1 query problem in database applications.

Include:
- How to detect N+1 problems (symptoms, query logging)
- Step-by-step debugging procedures
- Solutions: Eager loading, DataLoader, denormalization
- Prevention strategies
- Framework-specific solutions (Django, Rails, GraphQL)

Save to: database/seed-data/output/blog/troubleshooting/n-plus-one-troubleshooting.md
```

## Quality Checklist

After generation, verify each blog post has:
- [ ] Clear title with pattern name
- [ ] Introduction with problem statement
- [ ] Code examples (SQL, JavaScript, Python)
- [ ] Performance data where applicable
- [ ] Common mistakes section
- [ ] Key takeaways / summary
- [ ] Proper markdown formatting
- [ ] 1500+ words

## Commit Generated Posts

After generating and reviewing:

```bash
git add database/seed-data/output/blog/
git commit -m "docs: Add generated blog posts for backend patterns"
```
