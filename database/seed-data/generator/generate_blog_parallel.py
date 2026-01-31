#!/home/lionel/.venv/bin/python
"""
Parallel Blog Generator using multiple AI backends

Uses three backends simultaneously:
1. Local vLLM (Ministral-3-8B) - Free, on-GPU
2. opencode free tier (GLM-4.7-free) - Free, rate-limited
3. opencode paid (Grok) - Paid, fast

Usage:
    python generate_blog_parallel.py --all
    python generate_blog_parallel.py --backends vllm,grok  # Specific backends
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import aiohttp
import yaml

# Configuration
VLLM_URL = "http://localhost:8000/v1/chat/completions"
VLLM_MODEL = "/data/models/fp16/Ministral-3-8B-Instruct-2512"

# opencode uses environment or config for API keys
OPENCODE_FREE_MODEL = "openrouter/glm-4-9b-chat"  # Free tier
OPENCODE_GROK_MODEL = "x-ai/grok-beta"  # Paid Grok

MAX_TOKENS = 4096
TEMPERATURE = 0.7

# Paths
SCRIPT_DIR = Path(__file__).parent
CORPUS_DIR = SCRIPT_DIR.parent / "corpus"
OUTPUT_DIR = SCRIPT_DIR.parent / "output" / "blog"

BackendType = Literal["vllm", "opencode_free", "grok"]


@dataclass
class GenerationTask:
    """A single blog post generation task."""

    pattern_id: str
    post_type: str  # tutorial, troubleshooting, reference, comparison
    depth: str  # beginner, intermediate, advanced
    output_path: Path
    prompt: str
    system_prompt: str


@dataclass
class GenerationResult:
    """Result of a generation task."""

    task: GenerationTask
    backend: BackendType
    content: str
    duration: float
    success: bool
    error: str | None = None


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def find_pattern(pattern_id: str) -> dict | None:
    """Find pattern in corpus."""
    for category in [
        "identifiers",
        "queries",
        "architecture",
        "relationships",
        "performance",
        "frameworks",
    ]:
        path = CORPUS_DIR / "patterns" / category / f"{pattern_id}.yaml"
        if path.exists():
            return load_yaml(path)
    return None


def build_tutorial_prompt(pattern: dict, depth: str) -> tuple[str, str]:
    """Build prompt for tutorial generation."""
    blog_hooks = pattern.get("blog_hooks", {}).get(depth, {})

    system_prompt = """You are a senior backend engineer writing educational content about database and API design patterns. Your writing style is:
- Clear and practical, with real-world examples
- Code-first (show, don't just tell)
- Honest about tradeoffs (no silver bullets)
- Friendly but professional

Write complete, publishable blog posts in markdown format. Do NOT wrap the output in markdown code fences."""

    solution = pattern.get("solution", {})
    solutions = pattern.get("solutions", [])

    if solution:
        solution_text = solution.get("principle", "")
        components = solution.get("components", [])
    elif solutions:
        solution_text = "Multiple solutions exist for this problem:\n"
        for sol in solutions:
            solution_text += f"- **{sol['name']}**: {sol['description']}\n"
        components = []
    else:
        solution_text = "See the detailed solutions below."
        components = []

    prompt = f"""Write a tutorial blog post about the "{pattern["name"]}" pattern.

## Target Audience
{depth.title()} backend developers.

## Summary
{pattern["summary"]["long"]}

## The Problem
{pattern["problem"]["description"]}

## The Solution
{solution_text}

## Components/Solutions
"""
    for comp in components:
        prompt += f"- **{comp['name']}** ({comp.get('type', 'approach')}): {comp['purpose']}\n"
    for sol in solutions:
        prompt += f"- **{sol['name']}**: {sol['description']}\n"

    schema = pattern.get("schema", {})
    if schema and "sql" in schema:
        prompt += f"\n## Schema Example\n```sql\n{schema['sql']}\n```\n"
    else:
        prompt += "\n## Code Examples\nInclude practical code examples demonstrating the pattern.\n"

    if "analogy" in blog_hooks:
        prompt += f"\n## Analogy for {depth} audience\n{blog_hooks['analogy']}\n"

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
    return prompt, system_prompt


def build_comparison_prompt(pattern: dict, depth: str) -> tuple[str, str]:
    """Build prompt for comparison generation."""
    blog_hooks = pattern.get("blog_hooks", {}).get(depth, {})

    system_prompt = """You are a senior backend engineer writing educational content about API architectures and frameworks. Your writing style is:
- Clear and practical, with real-world examples
- Code-first (show, don't just tell)
- Honest about tradeoffs (no silver bullets)
- Balanced comparison without bias
- Friendly but professional

Write complete, publishable blog posts in markdown format. Do NOT wrap the output in markdown code fences."""

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
    return prompt, system_prompt


def build_troubleshooting_prompt(pattern: dict) -> tuple[str, str]:
    """Build prompt for troubleshooting guide."""
    system_prompt = """You are a senior backend engineer writing debugging guides. Be practical and focused on quick problem resolution. Do NOT wrap output in markdown code fences."""

    prompt = f"""Write a troubleshooting guide for the "{pattern["name"]}" pattern.

## Pattern Summary
{pattern["summary"]["short"]}

## Common Symptoms
"""
    for symptom in pattern.get("problem", {}).get("symptoms", []):
        prompt += f"- **{symptom['name']}**: {symptom['description']}\n"

    prompt += """
## Requirements
Write a troubleshooting guide with:
1. Title: "Debugging [Pattern]: A Troubleshooting Guide"
2. Symptom Checklist
3. Common Issues and Fixes (with code)
4. Debugging Tools and Techniques
5. Prevention Strategies

Length: 1000-1500 words
"""
    return prompt, system_prompt


def build_reference_prompt(pattern: dict) -> tuple[str, str]:
    """Build prompt for reference documentation."""
    system_prompt = """You are a technical writer creating reference documentation. Be precise and scannable. Do NOT wrap output in markdown code fences."""

    schema = pattern.get("schema", {})
    schema_section = ""
    if schema and "sql" in schema:
        schema_section = f"## Schema\n```sql\n{schema['sql']}\n```\n"
    else:
        schema_section = (
            "## Code Examples\nProvide relevant code examples for this pattern.\n"
        )

    solution = pattern.get("solution", {})
    solutions = pattern.get("solutions", [])
    components = solution.get("components", []) if solution else []

    prompt = f"""Write reference documentation for the "{pattern["name"]}" pattern.

## Summary
{pattern["summary"]["long"]}

{schema_section}

## Components/Solutions
"""
    for comp in components:
        prompt += f"- **{comp['name']}** ({comp.get('type', 'approach')}): {comp['purpose']}\n"
    for sol in solutions:
        prompt += f"- **{sol['name']}**: {sol['description']}\n"

    prompt += """
## Requirements
Write reference documentation with:
1. Title: "[Pattern] Reference Guide"
2. Overview (1 paragraph)
3. Schema Reference (table format)
4. Query Examples
5. Related Patterns

Length: 800-1200 words
"""
    return prompt, system_prompt


def build_all_tasks() -> list[GenerationTask]:
    """Build all generation tasks."""
    tasks = []

    # Standard patterns
    standard_patterns = ["trinity-pattern", "n-plus-one", "graphql-cascade"]
    comparison_patterns = ["rest-vs-graphql-vs-grpc", "graphql-frameworks"]
    depths = ["beginner", "intermediate", "advanced"]

    for pattern_id in standard_patterns:
        pattern = find_pattern(pattern_id)
        if not pattern:
            continue

        # Tutorials
        for depth in depths:
            prompt, sys_prompt = build_tutorial_prompt(pattern, depth)
            tasks.append(
                GenerationTask(
                    pattern_id=pattern_id,
                    post_type="tutorial",
                    depth=depth,
                    output_path=OUTPUT_DIR
                    / "tutorials"
                    / f"{pattern_id}-tutorial-{depth}.md",
                    prompt=prompt,
                    system_prompt=sys_prompt,
                )
            )

        # Troubleshooting
        prompt, sys_prompt = build_troubleshooting_prompt(pattern)
        tasks.append(
            GenerationTask(
                pattern_id=pattern_id,
                post_type="troubleshooting",
                depth="all",
                output_path=OUTPUT_DIR
                / "troubleshooting"
                / f"{pattern_id}-troubleshooting.md",
                prompt=prompt,
                system_prompt=sys_prompt,
            )
        )

        # Reference
        prompt, sys_prompt = build_reference_prompt(pattern)
        tasks.append(
            GenerationTask(
                pattern_id=pattern_id,
                post_type="reference",
                depth="all",
                output_path=OUTPUT_DIR / "reference" / f"{pattern_id}-reference.md",
                prompt=prompt,
                system_prompt=sys_prompt,
            )
        )

    # Comparison patterns
    for pattern_id in comparison_patterns:
        pattern = find_pattern(pattern_id)
        if not pattern:
            continue

        for depth in depths:
            prompt, sys_prompt = build_comparison_prompt(pattern, depth)
            tasks.append(
                GenerationTask(
                    pattern_id=pattern_id,
                    post_type="comparison",
                    depth=depth,
                    output_path=OUTPUT_DIR / "comparisons" / f"{pattern_id}-{depth}.md",
                    prompt=prompt,
                    system_prompt=sys_prompt,
                )
            )

    return tasks


async def generate_vllm(
    session: aiohttp.ClientSession, task: GenerationTask
) -> GenerationResult:
    """Generate using local vLLM."""
    start = time.time()

    messages = []
    if task.system_prompt:
        messages.append({"role": "system", "content": task.system_prompt})
    messages.append({"role": "user", "content": task.prompt})

    payload = {
        "model": VLLM_MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }

    try:
        async with session.post(
            VLLM_URL, json=payload, timeout=aiohttp.ClientTimeout(total=300)
        ) as resp:
            if resp.status != 200:
                return GenerationResult(
                    task=task,
                    backend="vllm",
                    content="",
                    duration=time.time() - start,
                    success=False,
                    error=f"HTTP {resp.status}",
                )
            result = await resp.json()
            content = result["choices"][0]["message"]["content"]
            return GenerationResult(
                task=task,
                backend="vllm",
                content=content,
                duration=time.time() - start,
                success=True,
            )
    except Exception as e:
        return GenerationResult(
            task=task,
            backend="vllm",
            content="",
            duration=time.time() - start,
            success=False,
            error=str(e),
        )


async def generate_opencode(
    task: GenerationTask, model: str, backend_name: BackendType
) -> GenerationResult:
    """Generate using opencode CLI (runs in subprocess)."""
    start = time.time()

    # Create a temporary prompt file
    prompt_file = Path(
        f"/tmp/blog_prompt_{task.pattern_id}_{task.depth}_{backend_name}.txt"
    )
    full_prompt = (
        f"{task.system_prompt}\n\n{task.prompt}" if task.system_prompt else task.prompt
    )
    prompt_file.write_text(full_prompt)

    try:
        # Run opencode with the specified model
        cmd = [
            "opencode",
            "run",
            "--model",
            model,
            "--prompt",
            str(prompt_file),
            "--no-interactive",
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

        if proc.returncode != 0:
            return GenerationResult(
                task=task,
                backend=backend_name,
                content="",
                duration=time.time() - start,
                success=False,
                error=stderr.decode(),
            )

        content = stdout.decode()
        return GenerationResult(
            task=task,
            backend=backend_name,
            content=content,
            duration=time.time() - start,
            success=True,
        )
    except asyncio.TimeoutError:
        return GenerationResult(
            task=task,
            backend=backend_name,
            content="",
            duration=time.time() - start,
            success=False,
            error="Timeout",
        )
    except Exception as e:
        return GenerationResult(
            task=task,
            backend=backend_name,
            content="",
            duration=time.time() - start,
            success=False,
            error=str(e),
        )
    finally:
        prompt_file.unlink(missing_ok=True)


async def generate_with_openrouter(
    session: aiohttp.ClientSession,
    task: GenerationTask,
    model: str,
    backend_name: BackendType,
) -> GenerationResult:
    """Generate using OpenRouter API directly (works for both free and paid models)."""
    start = time.time()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return GenerationResult(
            task=task,
            backend=backend_name,
            content="",
            duration=time.time() - start,
            success=False,
            error="OPENROUTER_API_KEY not set",
        )

    messages = []
    if task.system_prompt:
        messages.append({"role": "system", "content": task.system_prompt})
    messages.append({"role": "user", "content": task.prompt})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://velocitybench.dev",
        "X-Title": "VelocityBench Blog Generator",
    }

    try:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=300),
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                return GenerationResult(
                    task=task,
                    backend=backend_name,
                    content="",
                    duration=time.time() - start,
                    success=False,
                    error=f"HTTP {resp.status}: {error_text[:200]}",
                )
            result = await resp.json()
            content = result["choices"][0]["message"]["content"]
            return GenerationResult(
                task=task,
                backend=backend_name,
                content=content,
                duration=time.time() - start,
                success=True,
            )
    except Exception as e:
        return GenerationResult(
            task=task,
            backend=backend_name,
            content="",
            duration=time.time() - start,
            success=False,
            error=str(e),
        )


def save_result(result: GenerationResult) -> bool:
    """Save generation result to file."""
    if not result.success:
        return False

    result.task.output_path.parent.mkdir(parents=True, exist_ok=True)

    # Clean up markdown code fence wrapper if present
    content = result.content
    if content.startswith("```markdown\n"):
        content = content[len("```markdown\n") :]
    if content.endswith("\n```"):
        content = content[:-4]

    with open(result.task.output_path, "w") as f:
        f.write(content)
    return True


async def run_parallel_generation(
    tasks: list[GenerationTask], backends: list[BackendType]
):
    """Run generation across multiple backends in parallel."""

    # Distribute tasks across backends (round-robin)
    backend_tasks: dict[BackendType, list[GenerationTask]] = {b: [] for b in backends}
    for i, task in enumerate(tasks):
        backend = backends[i % len(backends)]
        backend_tasks[backend].append(task)

    print(f"\n{'=' * 60}")
    print(f"Parallel Blog Generation")
    print(f"{'=' * 60}")
    print(f"Total tasks: {len(tasks)}")
    for backend, btasks in backend_tasks.items():
        print(f"  {backend}: {len(btasks)} tasks")
    print(f"{'=' * 60}\n")

    results: list[GenerationResult] = []

    async with aiohttp.ClientSession() as session:
        # Create coroutines for each backend
        coros = []

        for backend, btasks in backend_tasks.items():
            for task in btasks:
                if backend == "vllm":
                    coros.append(generate_vllm(session, task))
                elif backend == "opencode_free":
                    coros.append(
                        generate_with_openrouter(
                            session, task, OPENCODE_FREE_MODEL, backend
                        )
                    )
                elif backend == "grok":
                    coros.append(
                        generate_with_openrouter(
                            session, task, OPENCODE_GROK_MODEL, backend
                        )
                    )

        # Run with progress tracking
        for coro in asyncio.as_completed(coros):
            result = await coro
            results.append(result)

            status = "✓" if result.success else "✗"
            print(
                f"  [{status}] {result.backend}: {result.task.pattern_id}/{result.task.post_type}-{result.task.depth} ({result.duration:.1f}s)"
            )

            if result.success:
                save_result(result)

    # Summary
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")

    success = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    print(f"Successful: {len(success)}/{len(results)}")
    print(f"Failed: {len(failed)}/{len(results)}")

    if failed:
        print("\nFailed tasks:")
        for r in failed:
            print(
                f"  - {r.task.pattern_id}/{r.task.post_type}-{r.task.depth} ({r.backend}): {r.error}"
            )

    total_time = sum(r.duration for r in results)
    wall_time = max(r.duration for r in results) if results else 0
    print(f"\nTotal generation time: {total_time:.1f}s")
    print(f"Wall clock time: {wall_time:.1f}s")
    print(
        f"Speedup from parallelism: {total_time / wall_time:.1f}x"
        if wall_time > 0
        else ""
    )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Parallel blog generator using multiple AI backends"
    )
    parser.add_argument("--all", action="store_true", help="Generate all blog posts")
    parser.add_argument(
        "--backends",
        default="vllm,opencode_free,grok",
        help="Comma-separated backends: vllm,opencode_free,grok",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show tasks without generating"
    )

    args = parser.parse_args()

    if not args.all:
        parser.error("--all required")

    backends = [b.strip() for b in args.backends.split(",")]
    valid_backends = ["vllm", "opencode_free", "grok"]
    for b in backends:
        if b not in valid_backends:
            parser.error(f"Invalid backend: {b}. Valid: {valid_backends}")

    # Check backend availability
    print("Checking backend availability...")

    if "vllm" in backends:
        import requests

        try:
            resp = requests.get("http://localhost:8000/v1/models", timeout=5)
            resp.raise_for_status()
            print("  ✓ vLLM available")
        except (requests.RequestException, requests.Timeout):
            print("  ✗ vLLM not available, removing from backends")
            backends.remove("vllm")

    if "opencode_free" in backends or "grok" in backends:
        if not os.environ.get("OPENROUTER_API_KEY"):
            print("  ✗ OPENROUTER_API_KEY not set")
            if "opencode_free" in backends:
                backends.remove("opencode_free")
            if "grok" in backends:
                backends.remove("grok")
        else:
            print("  ✓ OpenRouter API key found")

    if not backends:
        print("\nNo backends available!")
        sys.exit(1)

    print(f"\nUsing backends: {backends}")

    tasks = build_all_tasks()

    if args.dry_run:
        print(f"\nWould generate {len(tasks)} posts:")
        for task in tasks:
            print(f"  - {task.pattern_id}/{task.post_type}-{task.depth}")
        return

    asyncio.run(run_parallel_generation(tasks, backends))


if __name__ == "__main__":
    main()
