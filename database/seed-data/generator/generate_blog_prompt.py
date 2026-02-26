#!/usr/bin/env python3
"""
Blog Prompt Generator - Creates AI prompts from YAML corpus

This generator reads the YAML corpus and creates prompts for AI models
(Claude Code, opencode, vLLM) to generate blog posts.

Usage:
    # Generate tutorial prompt for Trinity Pattern
    python generate_blog_prompt.py --pattern trinity-pattern --type tutorial --depth beginner

    # Generate comparison prompt
    python generate_blog_prompt.py --type comparison --framework-a postgraphile --framework-b apollo-server

    # Generate all prompts for a pattern
    python generate_blog_prompt.py --pattern trinity-pattern --all-types --all-depths

    # Batch generate prompts
    python generate_blog_prompt.py --batch --output prompts/batch.json

Multi-Model Strategy:
    - Claude Code: Use for complex prompts requiring judgment
    - opencode (free): Use for actual blog generation
    - vLLM (local): Use for simple/repetitive transformations
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# Base path for corpus
CORPUS_PATH = Path(__file__).parent.parent / "corpus"
PROMPTS_PATH = Path(__file__).parent.parent / "prompts"
OUTPUT_PATH = Path(__file__).parent.parent / "output" / "blog"


def load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file and return parsed content."""
    with open(path) as f:
        return yaml.safe_load(f)


def find_pattern(pattern_id: str) -> dict[str, Any] | None:
    """Find pattern definition in corpus."""
    for category in [
        "identifiers",
        "queries",
        "architecture",
        "relationships",
        "performance",
    ]:
        pattern_path = CORPUS_PATH / "patterns" / category / f"{pattern_id}.yaml"
        if pattern_path.exists():
            return load_yaml(pattern_path)
    return None


def find_framework(framework_id: str) -> dict[str, Any] | None:
    """Find framework definition in corpus."""
    framework_path = CORPUS_PATH / "frameworks" / f"{framework_id}.yaml"
    if framework_path.exists():
        return load_yaml(framework_path)
    return None


def generate_tutorial_prompt(pattern: dict, depth: str = "beginner") -> str:
    """Generate tutorial-style blog post prompt."""
    blog_hooks = pattern.get("blog_hooks", {}).get(depth, {})

    prompt = f"""You are a senior backend engineer writing educational content about database and API design patterns. Write a tutorial blog post about the "{pattern["name"]}" pattern.

## Target Audience
{depth.title()} backend developers (1-3 years experience for beginner, 3-5 for intermediate, 5+ for advanced).

## Source Material

### Summary
{pattern["summary"]["long"]}

### The Problem
{pattern["problem"]["description"]}

### The Solution
{pattern["solution"]["principle"]}

### Components
"""

    for component in pattern["solution"]["components"]:
        prompt += f"""
**{component["name"]}** ({component["type"]}):
- Purpose: {component["purpose"]}
- Visibility: {component.get("visibility", "N/A")}
"""

    prompt += f"""
### Schema Example
```sql
{pattern["schema"]["sql"]}
```

### Performance Data
"""

    for benchmark in pattern.get("performance", {}).get("benchmarks", []):
        prompt += f"\n**{benchmark['operation']}**:\n"
        for result in benchmark["results"]:
            prompt += f"- {result['identifier']}: {result['avg_time']}\n"

    if "analogy" in blog_hooks:
        prompt += f"""
### Analogy for {depth.title()} Audience
{blog_hooks["analogy"]}
"""

    if "common_mistakes" in blog_hooks:
        prompt += """
### Common Mistakes to Address
"""
        for mistake in blog_hooks["common_mistakes"]:
            prompt += f"- {mistake}\n"

    prompt += """
## Output Requirements

Write a blog post with:
1. **Title**: Catchy, SEO-friendly, includes the pattern name
2. **Introduction**: Hook with the problem, promise of solution (2-3 paragraphs)
3. **The Problem** section: Real-world pain points developers face
4. **The Solution** section: Step-by-step explanation with code
5. **Implementation Guide**: Practical SQL/code examples
6. **Performance Comparison**: Table showing benchmark data
7. **Common Mistakes**: What NOT to do
8. **Key Takeaways**: 3-5 bullet point summary
9. **Conclusion**: Next steps, related patterns

**Length**: 1500-2500 words
**Code blocks**: Use ```sql, ```python, ```javascript as appropriate
**Formatting**: Use headers (##), bullet points, and code blocks liberally
**Tone**: Technical but accessible, practical, honest about tradeoffs
"""

    return prompt


def generate_comparison_prompt(
    framework_a: str, framework_b: str, pattern: dict
) -> str:
    """Generate framework comparison blog post prompt."""
    prompt = f"""You are a senior backend engineer writing honest, balanced comparison content. Write a comparison blog post: "{framework_a}" vs "{framework_b}" for implementing the {pattern["name"]}.

## Pattern Being Compared
{pattern["summary"]["short"]}

## Framework A: {framework_a}
(Provide implementation details for {framework_a})

## Framework B: {framework_b}
(Provide implementation details for {framework_b})

## Output Requirements

Write a comparison post with:
1. **Title**: "[{framework_a}] vs [{framework_b}]: {pattern["name"]} Implementation Compared"
2. **TL;DR**: 2-3 sentence summary with recommendation
3. **Introduction**: Why this comparison matters
4. **Head-to-Head Comparison Table**: Quick reference
5. **{framework_a} Deep Dive**: Implementation details with code
6. **{framework_b} Deep Dive**: Implementation details with code
7. **Performance Comparison**: Benchmarks if available
8. **When to Choose {framework_a}**: Specific scenarios
9. **When to Choose {framework_b}**: Specific scenarios
10. **Verdict**: Honest recommendation with caveats

**Length**: 2000-3000 words
**Tone**: Balanced but willing to give opinions
**Format**: Include comparison table and code examples for both frameworks
"""

    return prompt


def generate_troubleshooting_prompt(pattern: dict, depth: str = "intermediate") -> str:
    """Generate troubleshooting guide prompt."""
    problem = pattern.get("problem", {})

    prompt = f"""You are a senior backend engineer writing a troubleshooting guide. Create a debugging guide for the "{pattern["name"]}" pattern.

## Pattern Overview
{pattern["summary"]["short"]}

## Common Symptoms to Address
"""

    for symptom in problem.get("symptoms", []):
        prompt += f"""
**{symptom["name"]}**:
- Description: {symptom["description"]}
- Example: {symptom.get("example", "N/A")}
- Detection: {symptom.get("detection", "N/A")}
"""

    prompt += """
## Output Requirements

Write a troubleshooting guide with:
1. **Title**: "Debugging [Pattern]: A Complete Troubleshooting Guide"
2. **Introduction**: When to use this guide
3. **Symptom Checklist**: Quick diagnostic questions
4. **Common Issues and Fixes**: Each issue with:
   - Symptoms
   - Root cause
   - Solution with code
   - Prevention tips
5. **Debugging Tools**: Commands and techniques
6. **Prevention Strategies**: How to avoid these issues
7. **When to Ask for Help**: Escalation guidance

**Length**: 1500-2000 words
**Format**: Step-by-step debugging procedures
**Tone**: Practical, focused on quick resolution
"""

    return prompt


def generate_reference_prompt(pattern: dict) -> str:
    """Generate API/reference documentation prompt."""
    prompt = f"""You are a technical writer creating reference documentation. Write a reference guide for the "{pattern["name"]}" pattern.

## Pattern Definition
{pattern["summary"]["long"]}

## Schema
```sql
{pattern["schema"]["sql"]}
```

## Components
"""

    for component in pattern["solution"]["components"]:
        prompt += f"""
### {component["name"]}
- **Type**: {component["type"]}
- **Purpose**: {component["purpose"]}
- **Visibility**: {component.get("visibility", "N/A")}
"""

    prompt += """
## Output Requirements

Write reference documentation with:
1. **Title**: "[Pattern Name] Reference Guide"
2. **Overview**: 1 paragraph summary
3. **Schema Reference**: Table format with all columns
4. **API Endpoints**: How to interact with this pattern
5. **Query Examples**: Common query patterns
6. **Configuration Options**: Settings and defaults
7. **Related Patterns**: Links to related documentation
8. **Changelog**: Version history (if applicable)

**Length**: 1000-1500 words
**Format**: Reference-style with tables and code blocks
**Tone**: Precise, technical, scannable
"""

    return prompt


def save_prompt(prompt: str, filename: str, metadata: dict) -> Path:
    """Save prompt to file with metadata."""
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_PATH / f"{filename}.prompt.md"

    content = f"""---
# Prompt Metadata
generated: {datetime.now().isoformat()}
pattern: {metadata.get("pattern", "N/A")}
type: {metadata.get("type", "N/A")}
depth: {metadata.get("depth", "N/A")}
recommended_model: {metadata.get("model", "opencode")}
---

{prompt}
"""

    with open(output_file, "w") as f:
        f.write(content)

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI prompts for blog posts from YAML corpus"
    )
    parser.add_argument(
        "--pattern", help="Pattern ID to generate prompt for (e.g., trinity-pattern)"
    )
    parser.add_argument(
        "--type",
        choices=["tutorial", "comparison", "troubleshooting", "reference"],
        default="tutorial",
        help="Type of blog post to generate",
    )
    parser.add_argument(
        "--depth",
        choices=["beginner", "intermediate", "advanced"],
        default="beginner",
        help="Target audience depth",
    )
    parser.add_argument(
        "--framework-a",
        help="First framework for comparison (required for --type comparison)",
    )
    parser.add_argument(
        "--framework-b",
        help="Second framework for comparison (required for --type comparison)",
    )
    parser.add_argument(
        "--all-types", action="store_true", help="Generate all types for the pattern"
    )
    parser.add_argument(
        "--all-depths", action="store_true", help="Generate all depths for the pattern"
    )
    parser.add_argument(
        "--stdout", action="store_true", help="Output prompt to stdout instead of file"
    )
    parser.add_argument("--output", type=Path, help="Custom output path")

    args = parser.parse_args()

    if args.type == "comparison":
        if not args.framework_a or not args.framework_b:
            parser.error("--framework-a and --framework-b required for comparison")
        if not args.pattern:
            parser.error("--pattern required for comparison")

        pattern = find_pattern(args.pattern)
        if not pattern:
            print(f"Pattern not found: {args.pattern}")
            return

        prompt = generate_comparison_prompt(args.framework_a, args.framework_b, pattern)
        filename = f"{args.framework_a}-vs-{args.framework_b}-{args.pattern}"
        metadata = {
            "pattern": args.pattern,
            "type": "comparison",
            "frameworks": [args.framework_a, args.framework_b],
            "model": "claude-code",  # Comparisons need judgment
        }

    else:
        if not args.pattern:
            parser.error("--pattern required")

        pattern = find_pattern(args.pattern)
        if not pattern:
            print(f"Pattern not found: {args.pattern}")
            return

        types = (
            ["tutorial", "troubleshooting", "reference"]
            if args.all_types
            else [args.type]
        )
        depths = (
            ["beginner", "intermediate", "advanced"]
            if args.all_depths
            else [args.depth]
        )

        for t in types:
            for d in depths:
                if t == "tutorial":
                    prompt = generate_tutorial_prompt(pattern, d)
                elif t == "troubleshooting":
                    prompt = generate_troubleshooting_prompt(pattern, d)
                elif t == "reference":
                    prompt = generate_reference_prompt(pattern)
                    d = "all"  # Reference doesn't have depth

                filename = f"{args.pattern}-{t}-{d}"
                metadata = {
                    "pattern": args.pattern,
                    "type": t,
                    "depth": d,
                    "model": "opencode",  # Most prompts can use free tier
                }

                if args.stdout:
                    print(f"=== {filename} ===")
                    print(prompt)
                    print()
                else:
                    output_file = save_prompt(prompt, filename, metadata)
                    print(f"Generated: {output_file}")

                if t == "reference":
                    break  # Reference doesn't have depth variants

        return

    if args.stdout:
        print(prompt)
    else:
        output_file = save_prompt(prompt, filename, metadata)
        print(f"Generated: {output_file}")


if __name__ == "__main__":
    main()
