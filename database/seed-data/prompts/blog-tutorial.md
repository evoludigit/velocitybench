# Blog Tutorial Generation Prompt

Use this prompt to generate tutorial-style blog posts from the YAML corpus.

## System Prompt (for all models)

```
You are a senior backend engineer writing educational content about database
and API design patterns. Your writing style is:
- Clear and practical, with real-world examples
- Code-first (show, don't just tell)
- Honest about tradeoffs (no silver bullets)
- Friendly but professional

Target audience: Backend developers with 1-3 years experience.
```

## Prompt Template

```
Write a tutorial blog post about the "{pattern_name}" pattern.

## Source Material (from YAML corpus)

### Summary
{summary.long}

### The Problem
{problem.description}

### The Solution
{solution.principle}

Components:
{for component in solution.components}
- **{component.name}** ({component.type}): {component.purpose}
{endfor}

### Schema Example
```sql
{schema.sql}
```

### Performance Data
{performance.benchmarks}

### Target Audience Hook
{blog_hooks.{depth}.analogy}

### Common Mistakes to Address
{blog_hooks.{depth}.common_mistakes}

## Output Requirements

Write a blog post with:
1. **Title**: Catchy, SEO-friendly, includes the pattern name
2. **Introduction**: Hook with the problem, promise of solution
3. **The Problem** section: Real-world pain points developers face
4. **The Solution** section: Step-by-step explanation with code
5. **Implementation Guide**: Practical SQL/code examples
6. **Performance Comparison**: Show the benchmarks
7. **Common Mistakes**: What NOT to do
8. **Key Takeaways**: 3-5 bullet point summary
9. **Conclusion**: Next steps, related patterns

Length: 1500-2500 words
Code blocks: Use ```sql, ```python, ```javascript as appropriate
Formatting: Use headers (##), bullet points, and code blocks liberally

## Example Structure

# {Title}

> {One-line hook/summary}

## Introduction
{2-3 paragraphs setting up the problem}

## The Problem: {Specific Pain Point}
{Explain why current approaches fail}

## The Solution: {Pattern Name}
{Core concept explanation}

### Component 1: {name}
{Explanation with code}

### Component 2: {name}
{Explanation with code}

## Implementation Guide
{Step-by-step with full code examples}

## Performance Comparison
{Table or benchmark data}

## Common Mistakes to Avoid
{List of anti-patterns}

## Key Takeaways
- Point 1
- Point 2
- Point 3

## Conclusion
{Wrap up and next steps}
```

## Model-Specific Notes

### Claude Code
- Can handle full prompt with all context
- Best for complex patterns requiring reasoning
- Use for quality review of generated content

### opencode (free tier)
- May need chunked prompts for longer content
- Provide explicit structure in prompt
- Good for initial draft generation

### vLLM (local)
- Keep prompts under 4K tokens
- Provide exact structure to follow
- Best for repetitive/similar posts
- May need multiple passes (intro → body → conclusion)

## Variables to Fill

| Variable | Source | Example |
|----------|--------|---------|
| `pattern_name` | corpus YAML `name` | "Trinity Pattern" |
| `summary.long` | corpus YAML | Full description |
| `problem.description` | corpus YAML | Problem statement |
| `solution.principle` | corpus YAML | Core solution |
| `schema.sql` | corpus YAML | SQL code |
| `depth` | generation config | "beginner", "intermediate", "advanced" |

## Usage Example

```bash
# Generate prompt from corpus
python generator/create_prompt.py \
  --pattern trinity-pattern \
  --depth beginner \
  --template blog-tutorial \
  --output prompts/trinity-beginner.md

# Use with opencode
opencode generate --prompt prompts/trinity-beginner.md --output output/blog/trinity-pattern-beginner.md

# Or use with vLLM
curl http://localhost:8000/v1/chat/completions \
  -d '{"model": "...", "messages": [{"role": "user", "content": "$(cat prompts/trinity-beginner.md)"}]}'
```
