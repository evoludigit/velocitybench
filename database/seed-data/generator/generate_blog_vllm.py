#!/usr/bin/env python
"""
Blog Generator using local vLLM

Generates blog posts directly using the local vLLM server,
bypassing opencode's interactive permission system.

Usage:
    python generate_blog_vllm.py --pattern trinity-pattern --type tutorial --depth beginner
    python generate_blog_vllm.py --all  # Generate all blog posts
"""

import argparse
import sys
from pathlib import Path

import requests
import yaml

# Configuration
VLLM_URL = "http://localhost:8000/v1/chat/completions"
MODEL_ID = "/data/models/fp16/Ministral-3-8B-Instruct-2512"
MAX_TOKENS = 4096
TEMPERATURE = 0.7

# Paths
SCRIPT_DIR = Path(__file__).parent
CORPUS_DIR = SCRIPT_DIR.parent / "corpus"
OUTPUT_DIR = SCRIPT_DIR.parent / "output" / "blog"


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def find_pattern(pattern_id: str) -> dict | None:
    """Find pattern in corpus."""
    # Search all category directories
    patterns_dir = CORPUS_DIR / "patterns"
    for category_dir in patterns_dir.iterdir():
        if category_dir.is_dir():
            path = category_dir / f"{pattern_id}.yaml"
            if path.exists():
                return load_yaml(path)
    return None


def discover_all_patterns() -> dict[str, str]:
    """Discover all patterns in corpus, returning {pattern_id: category}."""
    patterns = {}
    patterns_dir = CORPUS_DIR / "patterns"
    for category_dir in patterns_dir.iterdir():
        if category_dir.is_dir():
            category = category_dir.name
            for yaml_file in category_dir.glob("*.yaml"):
                pattern_id = yaml_file.stem
                patterns[pattern_id] = category
    return patterns


def generate_comparison(pattern: dict, depth: str) -> str:
    """Generate comparison blog post for architecture/framework comparisons."""
    blog_hooks = pattern.get("blog_hooks", {}).get(depth, {})

    system_prompt = """You are a senior backend engineer writing educational content about API architectures and frameworks. Your writing style is:
- Clear and practical, with real-world examples
- Code-first (show, don't just tell)
- Honest about tradeoffs (no silver bullets)
- Balanced comparison without bias
- Friendly but professional

Write complete, publishable blog posts in markdown format. Do NOT wrap the entire post in markdown code fences."""

    # For comparison patterns (REST vs GraphQL vs gRPC)
    paradigms = pattern.get("paradigms", [])
    frameworks = pattern.get("frameworks", [])

    if paradigms:
        items = paradigms
        item_type = "paradigm"
    elif frameworks:
        items = frameworks
        item_type = "framework"
    else:
        items = []
        item_type = "option"

    prompt = f"""Write a comparison blog post about "{pattern["name"]}".

## Target Audience
{depth.title()} backend developers.

## Summary
{pattern["summary"]["long"]}

## Items to Compare
"""
    for item in items:
        prompt += f"\n### {item['name']}\n"
        prompt += f"{item.get('description', '')}\n"
        if "strengths" in item:
            prompt += f"Strengths: {', '.join(item['strengths'][:3])}\n"
        if "weaknesses" in item:
            prompt += f"Weaknesses: {', '.join(item['weaknesses'][:3])}\n"
        if "best_for" in item:
            prompt += f"Best for: {', '.join(item['best_for'][:3])}\n"

    # Add comparison matrix if available
    comparison = pattern.get("comparison_matrix", {})
    if comparison:
        prompt += "\n## Comparison Matrix\n"
        for metric, values in list(comparison.items())[:5]:
            prompt += f"- **{metric}**: "
            if isinstance(values, dict):
                prompt += ", ".join(f"{k}: {v}" for k, v in values.items())
            else:
                prompt += str(values)
            prompt += "\n"

    # Add recommendations if available
    recommendations = pattern.get(
        "use_case_recommendations", pattern.get("recommendation_matrix", [])
    )
    if recommendations:
        prompt += "\n## Use Case Recommendations\n"
        for rec in recommendations[:4]:
            prompt += (
                f"- **{rec['scenario']}**: {rec['recommendation']} - {rec['reason']}\n"
            )

    if "analogy" in blog_hooks:
        prompt += f"\n## Analogy for {depth} audience\n{blog_hooks['analogy']}\n"

    prompt += f"""
## Requirements
Write a complete blog post with:
1. Catchy title that mentions the key {item_type}s being compared
2. Introduction explaining why this comparison matters (2-3 paragraphs)
3. Overview of each {item_type} with code examples
4. Side-by-side comparison table
5. When to use each (decision framework)
6. Common mistakes when choosing
7. Key takeaways (bullet points)
8. Conclusion with recommendation

Length: 2000-2500 words
Include code examples for each {item_type}.
"""

    return call_vllm(prompt, system_prompt)


def call_vllm(prompt: str, system_prompt: str = "") -> str:
    """Call local vLLM server."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": MODEL_ID,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }

    try:
        response = requests.post(VLLM_URL, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"Error calling vLLM: {e}")
        return ""


def generate_tutorial(pattern: dict, depth: str) -> str:
    """Generate tutorial blog post."""
    blog_hooks = pattern.get("blog_hooks", {}).get(depth, {})

    system_prompt = """You are a senior backend engineer writing educational content about database and API design patterns. Your writing style is:
- Clear and practical, with real-world examples
- Code-first (show, don't just tell)
- Honest about tradeoffs (no silver bullets)
- Friendly but professional

Write complete, publishable blog posts in markdown format."""

    # Handle both 'solution' (singular) and 'solutions' (plural) structures
    solution = pattern.get("solution", {})
    solutions = pattern.get("solutions", [])

    if solution:
        solution_text = solution.get("principle", "")
        components = solution.get("components", [])
    elif solutions:
        # For patterns with multiple solutions, summarize all
        solution_text = "Multiple solutions exist for this problem:\n"
        for sol in solutions:
            solution_text += f"- **{sol['name']}**: {sol['description']}\n"
        components = []
    else:
        solution_text = "See the detailed solutions below."
        components = []

    # Build prompt based on available fields
    problem_section = ""
    if "problem" in pattern:
        problem_section = f"\n## The Problem\n{pattern['problem']['description']}"
    elif "timeline" in pattern:
        # For history patterns
        problem_section = "\n## Context\nSee timeline below for the evolution and challenges that arose."

    prompt = f"""Write a tutorial blog post about the "{pattern["name"]}" pattern.

## Target Audience
{depth.title()} backend developers.

## Summary
{pattern["summary"]["long"]}{problem_section}

## The Solution
{solution_text}

## Components/Solutions
"""
    for comp in components:
        prompt += f"- **{comp['name']}** ({comp.get('type', 'approach')}): {comp['purpose']}\n"

    for sol in solutions:
        prompt += f"- **{sol['name']}**: {sol['description']}\n"

    # Handle schema - may not exist for all patterns
    schema = pattern.get("schema", {})
    if schema and "sql" in schema:
        prompt += f"""
## Schema Example
```sql
{schema["sql"]}
```
"""
    else:
        prompt += "\n## Code Examples\nInclude practical code examples demonstrating the pattern.\n"

    if "analogy" in blog_hooks:
        prompt += f"""
## Analogy for {depth} audience
{blog_hooks["analogy"]}
"""

    prompt += """
## Requirements
Write a complete blog post with:
1. Catchy title with the pattern name
2. Introduction (2-3 paragraphs)
3. The Problem section
4. The Solution section with code examples
5. Implementation Guide
6. Common Mistakes to Avoid
7. Key Takeaways (bullet points)
8. Conclusion

Length: 1500-2000 words
Use ```sql for SQL code blocks.
"""

    return call_vllm(prompt, system_prompt)


def generate_troubleshooting(pattern: dict) -> str:
    """Generate troubleshooting guide."""
    system_prompt = """You are a senior backend engineer writing debugging guides. Be practical and focused on quick problem resolution."""

    # Check for symptoms in problem section
    symptoms = pattern.get("problem", {}).get("symptoms", [])
    symptoms_section = ""
    if symptoms:
        symptoms_section = "## Common Symptoms\n"
        for symptom in symptoms:
            if isinstance(symptom, dict):
                symptoms_section += f"- **{symptom.get('name', 'Unknown')}**: {symptom.get('description', '')}\n"
            else:
                # Handle string symptoms
                symptoms_section += f"- {symptom}\n"
    else:
        symptoms_section = (
            "## Common Challenges\nThis pattern addresses several common challenges:\n"
        )
        # Extract challenges from pattern description if available
        if "problem" in pattern and isinstance(pattern["problem"], dict):
            desc = pattern["problem"].get("description", "")
            if desc:
                symptoms_section += f"{desc}\n"

    prompt = f"""Write a troubleshooting guide for the "{pattern["name"]}" pattern.

## Pattern Summary
{pattern["summary"]["short"]}

{symptoms_section}

## Requirements
Write a troubleshooting guide with:
1. Title: Debugging [Pattern]: A Troubleshooting Guide
2. Symptom Checklist
3. Common Issues and Fixes (with code)
4. Debugging Tools and Techniques
5. Prevention Strategies

Length: 1000-1500 words
"""

    return call_vllm(prompt, system_prompt)


def generate_reference(pattern: dict) -> str:
    """Generate reference documentation."""
    system_prompt = """You are a technical writer creating reference documentation. Be precise and scannable."""

    # Handle schema - may not exist
    schema = pattern.get("schema", {})
    schema_section = ""
    if schema and "sql" in schema:
        schema_section = f"""## Schema
```sql
{schema["sql"]}
```
"""
    else:
        schema_section = "## Implementation Details\nKey concepts and implementation details for this pattern.\n"

    # Handle solution/solutions
    solution = pattern.get("solution", {})
    solutions = pattern.get("solutions", [])
    components = solution.get("components", []) if solution else []

    # Build components/solutions section
    components_section = ""
    if components or solutions:
        components_section = "## Components/Solutions\n"
        for comp in components:
            components_section += f"- **{comp['name']}** ({comp.get('type', 'approach')}): {comp['purpose']}\n"
        for sol in solutions:
            components_section += f"- **{sol['name']}**: {sol['description']}\n"
    elif "timeline" in pattern:
        # For history patterns, use timeline as reference
        components_section = (
            "## Timeline\nKey events and milestones in the evolution of this topic.\n"
        )

    prompt = f"""Write reference documentation for the "{pattern["name"]}" pattern.

## Summary
{pattern["summary"]["long"]}

{schema_section}

{components_section}

## Requirements
Write reference documentation with:
1. Title: "[Pattern] Reference Guide"
2. Overview (1 paragraph)
3. Schema Reference (table format)
4. Query Examples
5. Related Patterns

Length: 800-1200 words
"""

    return call_vllm(prompt, system_prompt)


def save_blog(content: str, output_path: Path) -> bool:
    """Save blog post to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)
    return True


def get_existing_posts() -> set[str]:
    """Get set of patterns that already have blog posts."""
    existing = set()
    import re

    for post_type in ["tutorials", "reference", "troubleshooting", "comparisons"]:
        dir_path = OUTPUT_DIR / post_type
        if dir_path.exists():
            for md_file in dir_path.glob("*.md"):
                # Extract pattern name from filename
                match = re.match(
                    r"^(.+?)(?:-tutorial|-reference|-troubleshooting|-(?:beginner|intermediate|advanced))",
                    md_file.name,
                )
                if match:
                    existing.add(match.group(1))
    return existing


def is_comparison_pattern(pattern: dict) -> bool:
    """Check if pattern is a comparison pattern."""
    return bool(
        pattern.get("paradigms")
        or pattern.get("frameworks")
        or "paradigms" in pattern
        or "comparison_matrix" in pattern
    )


def generate_all():
    """Generate all blog posts for all patterns."""
    all_patterns = discover_all_patterns()
    existing_posts = get_existing_posts()
    depths = ["beginner", "intermediate", "advanced"]

    print(f"\n{'=' * 70}")
    print("BLOG POST GENERATION STATUS")
    print(f"{'=' * 70}")
    print(f"Total patterns discovered: {len(all_patterns)}")
    print(f"Patterns with existing posts: {len(existing_posts)}")
    print(f"Patterns to generate: {len(all_patterns) - len(existing_posts)}")
    print(f"{'=' * 70}\n")

    # Generate for all patterns
    for pattern_id, category in sorted(all_patterns.items()):
        # Skip if posts already exist
        if pattern_id in existing_posts:
            print(f"✓ Skipping {pattern_id} (already has posts)")
            continue

        print(f"\n=== Processing: {pattern_id} ({category}) ===")
        pattern = find_pattern(pattern_id)
        if not pattern:
            print("  ERROR: Pattern not found")
            continue

        is_comparison = is_comparison_pattern(pattern)

        if is_comparison:
            # Generate comparison articles at each depth
            print("  Type: Comparison pattern")
            for depth in depths:
                output_path = OUTPUT_DIR / "comparisons" / f"{pattern_id}-{depth}.md"
                print(f"  Generating comparison ({depth})...")
                content = generate_comparison(pattern, depth)
                if content:
                    save_blog(content, output_path)
                    print("    ✓ Saved")
                else:
                    print("    ✗ FAILED")
        else:
            # Generate standard content (tutorial, reference, troubleshooting)
            print("  Type: Standard pattern")

            # Tutorials
            for depth in depths:
                output_path = (
                    OUTPUT_DIR / "tutorials" / f"{pattern_id}-tutorial-{depth}.md"
                )
                print(f"  Generating tutorial ({depth})...")
                content = generate_tutorial(pattern, depth)
                if content:
                    save_blog(content, output_path)
                    print("    ✓ Saved")
                else:
                    print("    ✗ FAILED")

            # Troubleshooting
            output_path = (
                OUTPUT_DIR / "troubleshooting" / f"{pattern_id}-troubleshooting.md"
            )
            print("  Generating troubleshooting guide...")
            content = generate_troubleshooting(pattern)
            if content:
                save_blog(content, output_path)
                print("    ✓ Saved")
            else:
                print("    ✗ FAILED")

            # Reference
            output_path = OUTPUT_DIR / "reference" / f"{pattern_id}-reference.md"
            print("  Generating reference...")
            content = generate_reference(pattern)
            if content:
                save_blog(content, output_path)
                print("    ✓ Saved")
            else:
                print("    ✗ FAILED")

    print(f"\n{'=' * 70}")
    print("Blog generation complete!")
    print(f"{'=' * 70}")


def main():
    parser = argparse.ArgumentParser(description="Generate blog posts using local vLLM")
    parser.add_argument("--pattern", help="Pattern ID to generate for")
    parser.add_argument(
        "--type",
        choices=["tutorial", "troubleshooting", "reference", "comparison"],
        default="tutorial",
    )
    parser.add_argument(
        "--depth", choices=["beginner", "intermediate", "advanced"], default="beginner"
    )
    parser.add_argument("--all", action="store_true", help="Generate all blog posts")
    parser.add_argument(
        "--stdout", action="store_true", help="Output to stdout instead of file"
    )

    args = parser.parse_args()

    # Check vLLM is running
    try:
        response = requests.get("http://localhost:8000/v1/models", timeout=5)
        response.raise_for_status()
    except (requests.RequestException, requests.Timeout) as e:
        print("Error: vLLM server not running at localhost:8000")
        print(f"Details: {e}")
        print("Start it with: vllm-switch implementer")
        sys.exit(1)

    if args.all:
        generate_all()
        return

    if not args.pattern:
        parser.error("--pattern required (or use --all)")

    pattern = find_pattern(args.pattern)
    if not pattern:
        print(f"Pattern not found: {args.pattern}")
        sys.exit(1)

    # Generate based on type
    if args.type == "tutorial":
        content = generate_tutorial(pattern, args.depth)
        output_path = (
            OUTPUT_DIR / "tutorials" / f"{args.pattern}-tutorial-{args.depth}.md"
        )
    elif args.type == "troubleshooting":
        content = generate_troubleshooting(pattern)
        output_path = (
            OUTPUT_DIR / "troubleshooting" / f"{args.pattern}-troubleshooting.md"
        )
    elif args.type == "comparison":
        content = generate_comparison(pattern, args.depth)
        output_path = OUTPUT_DIR / "comparisons" / f"{args.pattern}-{args.depth}.md"
    else:
        content = generate_reference(pattern)
        output_path = OUTPUT_DIR / "reference" / f"{args.pattern}-reference.md"

    if args.stdout:
        print(content)
    else:
        save_blog(content, output_path)
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
