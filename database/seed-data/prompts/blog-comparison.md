# Blog Comparison Generation Prompt

Use this prompt to generate framework comparison blog posts from the YAML corpus.

## System Prompt

```
You are a senior backend engineer writing honest, balanced comparison content.
Your comparisons are:
- Fair and objective (acknowledge strengths of both sides)
- Data-driven (include benchmarks where available)
- Practical (focus on real-world implications)
- Opinionated when it matters (give recommendations)

Target audience: Backend developers choosing between frameworks/approaches.
```

## Prompt Template

```
Write a comparison blog post: "{framework_a}" vs "{framework_b}" for implementing {pattern_name}.

## Framework A: {framework_a}

### Overview
{frameworks.{framework_a}.description}

### Implementation Approach
{frameworks.{framework_a}.implementation_for.{pattern_id}}

### Code Example
```{language_a}
{frameworks.{framework_a}.code_example}
```

### Pros
{frameworks.{framework_a}.pros}

### Cons
{frameworks.{framework_a}.cons}

## Framework B: {framework_b}

### Overview
{frameworks.{framework_b}.description}

### Implementation Approach
{frameworks.{framework_b}.implementation_for.{pattern_id}}

### Code Example
```{language_b}
{frameworks.{framework_b}.code_example}
```

### Pros
{frameworks.{framework_b}.pros}

### Cons
{frameworks.{framework_b}.cons}

## Benchmark Data (if available)
{benchmarks.{framework_a}_vs_{framework_b}}

## Output Requirements

Write a comparison post with:
1. **Title**: "[Framework A] vs [Framework B]: [Pattern] Implementation Compared"
2. **TL;DR**: 2-3 sentence summary with recommendation
3. **Introduction**: Why this comparison matters
4. **Head-to-Head Comparison Table**: Quick reference
5. **Framework A Deep Dive**: Implementation details
6. **Framework B Deep Dive**: Implementation details
7. **Performance Comparison**: Benchmarks if available
8. **When to Choose A**: Specific scenarios
9. **When to Choose B**: Specific scenarios
10. **Verdict**: Honest recommendation with caveats

Length: 2000-3000 words
Tone: Balanced but willing to give opinions

## Comparison Table Template

| Aspect | {Framework A} | {Framework B} |
|--------|---------------|---------------|
| Language | {lang_a} | {lang_b} |
| Learning Curve | {rating} | {rating} |
| Performance | {benchmark} | {benchmark} |
| Ecosystem | {description} | {description} |
| Best For | {use_case} | {use_case} |

## Model-Specific Notes

### Claude Code
- Best for nuanced comparisons requiring judgment
- Can synthesize multiple data sources
- Use for final quality review

### opencode
- Provide clear structure
- May need explicit guidance on opinions
- Good for drafting comparison sections

### vLLM
- Best for simple A vs B with clear criteria
- Keep comparisons binary (winner/loser per criterion)
- May struggle with nuanced "it depends" situations
```

## Usage Example

```bash
# Generate PostGraphile vs Apollo Server comparison
python generator/create_prompt.py \
  --type comparison \
  --framework-a postgraphile \
  --framework-b apollo-server \
  --pattern trinity-pattern \
  --output prompts/postgraphile-vs-apollo.md
```
