#!/usr/bin/env python
"""
Generate comments for blog posts using vLLM with Gaussian distribution.

Generates 0-25 comments per post with Gaussian distribution centered at 12.
- Most posts get 8-16 comments
- Some get very few (0-4)
- Some get many (20-25)

Usage:
    python generate_blog_comments.py --test --posts 20
    python generate_blog_comments.py --all
    python generate_blog_comments.py --resume
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import re

import requests
import yaml

from logger_config import setup_logging
from .exceptions import VLLMTimeoutError, VLLMConnectionError, VLLMError

# ============================================================================
# Configuration
# ============================================================================

VLLM_URL = "http://localhost:8000/v1/chat/completions"
MODEL_ID = "/data/models/fp16/Ministral-3-8B-Instruct-2512"
MAX_TOKENS = 300
TEMPERATURE = 0.5
TOP_P = 0.9

# Paths
SCRIPT_DIR = Path(__file__).parent
CORPUS_DIR = SCRIPT_DIR.parent / "corpus"
BLOG_DIR = SCRIPT_DIR.parent / "output" / "blog"
OUTPUT_DIR = SCRIPT_DIR.parent / "output" / "comments"
PERSONAS_FILE = SCRIPT_DIR.parent / "output" / "personas" / "personas.json"
STATE_FILE = OUTPUT_DIR / "generation_state.json"

# Comment generation
COMMENTS_MEAN = 12
COMMENTS_STDDEV = 5.5
COMMENTS_MIN = 0
COMMENTS_MAX = 25

# Comment types with weights
COMMENT_TYPES = {
    "technical_issue": {
        "weight": 0.35,
        "prompt_suffix": "Point out a specific technical error, oversimplification, or assumption that may not hold.",
    },
    "missing_edge_case": {
        "weight": 0.30,
        "prompt_suffix": "What scenario or edge case does this solution NOT handle well?",
    },
    "question": {
        "weight": 0.20,
        "prompt_suffix": "Ask a thoughtful clarifying question about this approach or recommendation.",
    },
    "tradeoff": {
        "weight": 0.10,
        "prompt_suffix": "What important tradeoff or hidden cost is the author not mentioning?",
    },
    "validation": {
        "weight": 0.05,
        "prompt_suffix": "If this section is well-written, explain what makes it good in one sentence.",
    },
}


# ============================================================================
# Core Classes
# ============================================================================


class BlogPost:
    """Represents a blog post with metadata and sections."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.title = self._extract_title()
        self.content = self._read_content()
        self.sections = self._extract_sections()

    def _read_content(self) -> str:
        """Read markdown file."""
        with open(self.file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _extract_title(self) -> str:
        """Extract title from filename or first heading."""
        # Try filename first
        stem = self.file_path.stem
        title = stem.replace("-", " ").title()

        # Override with first heading if exists
        content = ""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read(500)
        except (IOError, OSError):
            pass

        match = re.search(r"^#+\s+(.+)$", content, re.MULTILINE)
        if match:
            title = match.group(1)

        return title

    def _extract_sections(self) -> List[Dict]:
        """
        Extract major sections from post that are suitable for commenting.

        Splits by level-2 headings (##), extracts 200-500 char excerpt.
        """
        sections = []
        parts = re.split(r"\n(##\s+[^\n]+)\n", self.content)

        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                heading = parts[i].replace("## ", "").strip()
                body = parts[i + 1]

                # Clean up body
                body = body.strip()
                if not body or len(body) < 100:
                    continue

                # Extract excerpt (first 300-500 chars)
                excerpt = body[:400]
                if len(body) > 400:
                    excerpt = excerpt[: excerpt.rfind(" ")] + "..."

                # Extract any code blocks in this section
                code_blocks = re.findall(r"```[\w]*\n(.*?)\n```", body, re.DOTALL)
                code_excerpt = ""
                if code_blocks:
                    code_excerpt = code_blocks[0][:200]

                sections.append(
                    {
                        "heading": heading,
                        "body": body,
                        "excerpt": excerpt,
                        "code_excerpt": code_excerpt,
                        "has_code": bool(code_blocks),
                    }
                )

        return sections

    def get_comment_scope(self) -> str:
        """Get string describing what to comment on."""
        if self.sections:
            return f"{self.title} - {self.sections[0]['heading']}"
        return self.title


class CommentGenerator:
    """Generates comments for blog posts using vLLM."""

    def __init__(self, output_dir: Path = OUTPUT_DIR, personas_file: Path = PERSONAS_FILE):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.personas = self._load_personas(personas_file)
        self.state = self._load_state()
        self.generated_count = 0
        self.failed_count = 0
        self.start_time = time.time()

    def _load_personas(self, personas_file: Path) -> List[Dict]:
        """Load personas from JSON file or index."""
        # Try new format first: individual files with index
        personas_dir = personas_file.parent / "personas"
        if personas_dir.exists():
            try:
                index_file = personas_dir / "index.json"
                if index_file.exists():
                    with open(index_file) as f:
                        index = json.load(f)
                        # Load full persona objects from individual files
                        personas = []
                        for item in index.get("personas", []):
                            pk_user = item.get("pk_user")
                            persona_file = personas_dir / f"persona_{pk_user:06d}.json"
                            if persona_file.exists():
                                with open(persona_file) as pf:
                                    persona = json.load(pf)
                                    personas.append(persona)
                        if personas:
                            print(f"Loaded {len(personas)} personas from directory")
                            return personas
            except Exception as e:
                print(f"Warning: Failed to load personas from directory: {e}")

        # Fallback to legacy format: single personas.json file
        if not personas_file.exists():
            print(f"Warning: Personas file not found: {personas_file}")
            print("         Comments will be generated without personas")
            return []

        try:
            with open(personas_file) as f:
                data = json.load(f)
                personas = data.get("personas", [])
                print(f"Loaded {len(personas)} personas from single file")
                return personas
        except Exception as e:
            print(f"Warning: Failed to load personas: {e}")
            return []

    def _load_state(self) -> Dict:
        """Load generation state from file (for resuming)."""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
        return {"processed_posts": [], "total_comments": 0}

    def _save_state(self) -> None:
        """Save generation state for resuming."""
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract meaningful keywords from text (lowercase)."""
        # Remove common words and split on non-alphanumeric
        text = text.lower()
        words = re.split(r'[^a-z0-9]+', text)
        # Filter short words and common stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'to', 'of', 'and', 'in', 'for', 'on', 'with', 'as', 'at',
                     'by', 'from', 'or', 'that', 'this', 'it', 'its', 'md', 'reference',
                     'tutorial', 'guide', 'advanced', 'beginner', 'intermediate'}
        return {w for w in words if len(w) > 2 and w not in stopwords}

    def _score_persona_for_post(self, persona: Dict, post_keywords: set, blog_type: str) -> float:
        """
        Score a persona's relevance to a blog post.
        Higher score = better match for commenting on this post.
        """
        score = 0.0

        # Extract persona keywords
        expertise_keywords = self._extract_keywords(' '.join(persona.get('expertise_areas', [])))
        title_keywords = self._extract_keywords(persona.get('title', ''))
        interest_keywords = self._extract_keywords(' '.join(persona.get('interests', [])))
        background_keywords = self._extract_keywords(persona.get('background', ''))

        # Score expertise match (highest weight)
        expertise_overlap = len(expertise_keywords & post_keywords)
        score += expertise_overlap * 3.0

        # Score title match (medium weight)
        title_overlap = len(title_keywords & post_keywords)
        score += title_overlap * 2.0

        # Score interest/background match (lower weight)
        interest_overlap = len(interest_keywords & post_keywords)
        background_overlap = len(background_keywords & post_keywords)
        score += interest_overlap * 1.0
        score += background_overlap * 0.5

        # Experience level matching
        exp_level = persona.get('experience_level', '').lower()
        if blog_type == 'tutorial':
            # Tutorials benefit from diverse perspectives
            if 'beginner' in blog_type.lower() and exp_level in ['junior', 'mid']:
                score += 1.5
            elif 'advanced' in blog_type.lower() and exp_level in ['senior', 'principal']:
                score += 1.5
        elif blog_type == 'reference':
            # Reference docs benefit from senior reviewers
            if exp_level in ['senior', 'principal']:
                score += 1.0
        elif blog_type == 'troubleshooting':
            # Troubleshooting benefits from experienced devs
            if exp_level in ['senior', 'principal']:
                score += 1.5

        # Ensure some minimum score for diversity
        return max(score, 0.1)

    def _select_personas_for_post(self, post: 'BlogPost', num_personas: int) -> List[Dict]:
        """
        Select personas relevant to the blog post topic.
        Uses weighted random selection based on relevance scores.
        """
        if not self.personas:
            return []

        # Extract keywords from post
        post_keywords = self._extract_keywords(post.title)
        post_keywords.update(self._extract_keywords(post.file_path.stem))

        # Determine blog type from path
        blog_type = 'general'
        path_str = str(post.file_path).lower()
        if 'tutorial' in path_str:
            blog_type = 'tutorial'
        elif 'reference' in path_str:
            blog_type = 'reference'
        elif 'troubleshooting' in path_str:
            blog_type = 'troubleshooting'
        elif 'comparison' in path_str:
            blog_type = 'comparison'

        # Score all personas
        scored_personas = []
        for persona in self.personas:
            score = self._score_persona_for_post(persona, post_keywords, blog_type)
            scored_personas.append((persona, score))

        # Sort by score (highest first) for weighted selection
        scored_personas.sort(key=lambda x: x[1], reverse=True)

        # Use weighted random selection (top personas more likely)
        # Take top 20% as high-probability pool, rest as low-probability
        top_count = max(len(scored_personas) // 5, num_personas * 2)
        top_pool = scored_personas[:top_count]

        # Extract weights for random.choices
        weights = [score for _, score in top_pool]
        personas_only = [p for p, _ in top_pool]

        # Select unique personas
        selected = []
        available_indices = list(range(len(personas_only)))

        for _ in range(min(num_personas, len(personas_only))):
            if not available_indices:
                break
            # Normalize weights for available personas
            available_weights = [weights[i] for i in available_indices]
            total_weight = sum(available_weights)
            if total_weight == 0:
                idx = random.choice(available_indices)
            else:
                # Weighted random choice
                r = random.uniform(0, total_weight)
                cumsum = 0
                for i, w in enumerate(available_weights):
                    cumsum += w
                    if r <= cumsum:
                        idx = available_indices[i]
                        break
                else:
                    idx = available_indices[-1]

            selected.append(personas_only[idx])
            available_indices.remove(idx)

        return selected

    def generate_comments_for_post(
        self, post: BlogPost, num_comments: int, dry_run: bool = False
    ) -> List[Dict]:
        """
        Generate specified number of comments for a post.

        Returns list of comment dicts with: text, type, section, author, confidence
        """
        if not post.sections:
            return []

        comments = []
        weighted_types = self._prepare_comment_types(num_comments)

        # Pre-select topic-relevant personas for this post
        selected_personas = self._select_personas_for_post(post, num_comments) if self.personas else []

        for i, comment_type in enumerate(weighted_types):
            # Select a section to comment on
            section = random.choice(post.sections)

            # Use pre-selected persona (topic-aware) or fall back to random
            if i < len(selected_personas):
                persona = selected_personas[i]
            elif self.personas:
                persona = random.choice(self.personas)
            else:
                persona = None

            # Generate comment
            comment_text = self._generate_single_comment(
                post, section, comment_type, persona=persona, dry_run=dry_run
            )

            if comment_text:
                comment_data = {
                    "text": comment_text,
                    "type": comment_type,
                    "section": section["heading"],
                    "has_code": section["has_code"],
                    "generated_at": datetime.now().isoformat(),
                }
                # Include persona info if available
                if persona:
                    comment_data["author_name"] = persona.get("name", "Anonymous")
                    comment_data["author_title"] = persona.get("title", "")
                    comment_data["author_id"] = persona.get("pk_user")

                comments.append(comment_data)
                self.generated_count += 1
            else:
                self.failed_count += 1

        return comments

    def _prepare_comment_types(self, num_comments: int) -> List[str]:
        """Prepare comment types distribution."""
        types = []
        remaining = num_comments

        # Allocate based on weights
        for ctype, config in COMMENT_TYPES.items():
            count = max(1, int(num_comments * config["weight"]))
            count = min(count, remaining)
            types.extend([ctype] * count)
            remaining -= count

        # Add remaining to random type
        while remaining > 0:
            types.append(random.choice(list(COMMENT_TYPES.keys())))
            remaining -= 1

        random.shuffle(types)
        return types[:num_comments]

    def _generate_single_comment(
        self, post: BlogPost, section: Dict, comment_type: str, persona: Dict | None = None, dry_run: bool = False
    ) -> str | None:
        """Generate a single comment, optionally from a persona."""
        config = COMMENT_TYPES.get(comment_type, {})
        prompt_suffix = config.get("prompt_suffix", "")

        # Build system prompt with persona if available
        if persona:
            expertise_str = ", ".join(persona.get("expertise_areas", [])[:3])
            communication_style = persona.get("communication_style", "critical but constructive")

            system_prompt = f"""You are {persona.get('name', 'Anonymous')}, a {persona.get('title', 'Software Engineer')} with {persona.get('years_experience', 5)} years of experience.

Your expertise: {expertise_str}
Your communication style: {communication_style}
Your interests: {', '.join(persona.get('interests', [])[:3])}

Your job is to write critical but constructive comments on blog posts about software architecture and database design.

Guidelines:
- Comments must be substantive - at least 2-3 sentences
- Be respectful and constructive, not dismissive
- Reference specific parts of the content you're addressing
- Don't praise obvious content - only comment if you have real feedback
- If genuinely nothing to critique, explain what's done well (briefly)
- Avoid generic comments like "Great post!" or "Thanks for sharing!"
- Comments should be 100-250 words
- Write in your characteristic style: {persona.get('personality_traits', ['thoughtful'])[0] if persona.get('personality_traits') else 'thoughtful'}"""
        else:
            system_prompt = """You are an experienced backend engineer reviewing blog posts about software architecture and database design.
Your job is to write critical but constructive comments pointing out issues, missing edge cases, or asking clarifying questions.

Guidelines:
- Comments must be substantive - at least 2-3 sentences
- Be respectful and constructive, not dismissive
- Reference specific parts of the content you're addressing
- Don't praise obvious content - only comment if you have real feedback
- If genuinely nothing to critique, explain what's done well (briefly)
- Avoid generic comments like "Great post!" or "Thanks for sharing!"
- Comments should be 100-250 words"""

        prompt = f"""Comment on this section from "{post.title}":

**Section**: {section['heading']}

**Content**:
{section['excerpt']}
"""
        if section["code_excerpt"]:
            prompt += f"\n**Code Example**:\n```\n{section['code_excerpt']}\n```\n"

        prompt += f"\n**Task**: {prompt_suffix}\n"
        prompt += "\nWrite the comment as a single paragraph (no markdown formatting)."

        if dry_run:
            persona_name = persona.get("name", "Anonymous") if persona else "Generic"
            return f"[DRY RUN] Comment from {persona_name} on {section['heading']} ({comment_type})"

        try:
            comment_text = self._call_vllm(prompt, system_prompt)
            if comment_text and len(comment_text) > 50:
                return comment_text
        except Exception as e:
            print(f"    ⚠️ Failed to generate comment: {e}")

        return None

    def _call_vllm(self, prompt: str, system_prompt: str) -> str | None:
        """Call vLLM API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": MODEL_ID,
            "messages": messages,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
        }

        try:
            response = requests.post(VLLM_URL, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()

            if result.get("choices"):
                return result["choices"][0]["message"]["content"].strip()

        except requests.exceptions.Timeout:
            raise VLLMTimeoutError("Request timed out after 60s") from None
        except requests.exceptions.ConnectionError:
            raise VLLMConnectionError("Cannot connect to vLLM server at localhost:8000") from None
        except Exception as e:
            raise VLLMError(f"vLLM error: {e}") from e

        return None

    def process_posts(
        self,
        post_paths: List[Path],
        dry_run: bool = False,
        resume: bool = False,
    ) -> Dict:
        """Process multiple posts and generate comments."""
        results = {
            "posts_processed": 0,
            "total_comments": 0,
            "failed_posts": 0,
            "duration": 0,
        }

        print(f"\n{'='*70}")
        print(f"BLOG COMMENT GENERATION (PERSONA-BASED)")
        print(f"{'='*70}")
        print(f"Posts to process: {len(post_paths)}")
        print(f"Comments per post: {COMMENTS_MIN}-{COMMENTS_MAX} (μ={COMMENTS_MEAN}, σ={COMMENTS_STDDEV})")
        print(f"Personas loaded: {len(self.personas)}")
        print(f"{'='*70}\n")

        already_processed = set(self.state.get("processed_posts", []))
        if resume:
            post_paths = [p for p in post_paths if p.name not in already_processed]
            print(f"Resuming: {len(post_paths)} posts remaining\n")

        for i, post_path in enumerate(post_paths, 1):
            post_name = post_path.name

            # Skip if already processed
            if post_name in already_processed:
                continue

            try:
                post = BlogPost(post_path)

                # Determine number of comments with Gaussian distribution
                num_comments = self._sample_comment_count()

                print(
                    f"[{i:5d}/{len(post_paths):5d}] {post_name:50s} → {num_comments:2d} comments",
                    end="",
                    flush=True,
                )

                # Generate comments
                comments = self.generate_comments_for_post(
                    post, num_comments, dry_run=dry_run
                )

                # Save comments
                self._save_comments(post_path, comments)

                print(f" ✓")

                results["posts_processed"] += 1
                results["total_comments"] += len(comments)

                # Update state
                self.state["processed_posts"].append(post_name)
                self.state["total_comments"] += len(comments)

                # Checkpoint every 100 posts
                if i % 100 == 0:
                    self._save_state()
                    elapsed = time.time() - self.start_time
                    rate = i / elapsed
                    remaining = (len(post_paths) - i) / rate if rate > 0 else 0
                    print(
                        f"  ✓ Processed {i}/{len(post_paths)} posts ({rate:.1f} posts/sec, ~{remaining/60:.1f}min remaining)\n"
                    )

            except Exception as e:
                print(f" ✗ ({e})")
                results["failed_posts"] += 1

        results["duration"] = time.time() - self.start_time
        self._save_state()

        return results

    def _sample_comment_count(self) -> int:
        """Sample number of comments with Gaussian distribution."""
        count = int(random.gauss(COMMENTS_MEAN, COMMENTS_STDDEV))
        return max(COMMENTS_MIN, min(COMMENTS_MAX, count))

    def _save_comments(self, post_path: Path, comments: list[dict]) -> None:
        """Save comments to JSON file."""
        output_file = self.output_dir / f"{post_path.stem}_comments.json"

        with open(output_file, "w") as f:
            json.dump(
                {
                    "post_file": post_path.name,
                    "post_title": post_path.stem,
                    "generated_at": datetime.now().isoformat(),
                    "count": len(comments),
                    "comments": comments,
                },
                f,
                indent=2,
            )


# ============================================================================
# Distribution Utilities
# ============================================================================


def analyze_distribution(num_samples: int = 1000) -> None:
    """Analyze the comment count distribution."""
    samples = [
        max(COMMENTS_MIN, min(COMMENTS_MAX, int(random.gauss(COMMENTS_MEAN, COMMENTS_STDDEV))))
        for _ in range(num_samples)
    ]

    print("\n" + "=" * 70)
    print("COMMENT DISTRIBUTION ANALYSIS")
    print("=" * 70)
    print(f"Samples: {num_samples}")
    print(f"Target: Gaussian (μ={COMMENTS_MEAN}, σ={COMMENTS_STDDEV}), clipped [{COMMENTS_MIN}, {COMMENTS_MAX}]")
    print(f"\nStatistics:")
    print(f"  Mean:     {sum(samples) / len(samples):.2f}")
    print(f"  Median:   {sorted(samples)[len(samples) // 2]:.2f}")
    print(f"  Min:      {min(samples)}")
    print(f"  Max:      {max(samples)}")
    print(f"  Std Dev:  {(sum((x - sum(samples)/len(samples))**2 for x in samples) / len(samples))**0.5:.2f}")

    # Histogram
    print(f"\nDistribution:")
    buckets = {}
    for count in samples:
        bucket = (count // 5) * 5
        buckets[bucket] = buckets.get(bucket, 0) + 1

    for bucket in sorted(buckets.keys()):
        pct = 100 * buckets[bucket] / len(samples)
        bar = "█" * int(pct / 2)
        print(f"  {bucket:2d}-{bucket + 4:2d}: {bar} {pct:5.1f}% ({buckets[bucket]:4d})")

    print("=" * 70 + "\n")


# ============================================================================
# CLI
# ============================================================================


def discover_blog_posts() -> List[Path]:
    """Find all markdown blog post files."""
    if not BLOG_DIR.exists():
        print(f"Error: Blog directory not found: {BLOG_DIR}")
        sys.exit(1)

    posts = list(BLOG_DIR.rglob("*.md"))
    posts.sort()

    return posts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate comments for blog posts using vLLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 20 posts (dry run)
  python generate_blog_comments.py --test --posts 20

  # Full generation
  python generate_blog_comments.py --all

  # Resume from checkpoint
  python generate_blog_comments.py --all --resume

  # Analyze distribution
  python generate_blog_comments.py --analyze-distribution
        """,
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate comments for all blog posts",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode (dry run, limited posts)",
    )

    parser.add_argument(
        "--posts",
        type=int,
        default=20,
        help="Number of posts to process in test mode (default: 20)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually call vLLM, just show what would be done",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint",
    )

    parser.add_argument(
        "--analyze-distribution",
        action="store_true",
        help="Analyze comment count distribution and exit",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory for comments (default: {OUTPUT_DIR})",
    )

    args = parser.parse_args()

    # Set up structured logging
    logger = setup_logging(__name__)
    logger.info("Starting comment generation")

    # Handle distribution analysis
    if args.analyze_distribution:
        analyze_distribution()
        return

    # Check vLLM is running (unless dry run)
    if not args.dry_run:
        try:
            response = requests.get("http://localhost:8000/v1/models", timeout=5)
            response.raise_for_status()
            logger.info("vLLM server is running")
        except (requests.RequestException, requests.Timeout) as e:
            logger.error("vLLM server not running at localhost:8000")
            logger.error(f"Details: {e}")
            logger.info("To start vLLM automatically, use: make vllm-start")
            sys.exit(1)

    # Discover posts
    all_posts = discover_blog_posts()
    logger.info(f"Discovered {len(all_posts)} blog posts")

    # Determine which posts to process
    if args.test:
        posts_to_process = all_posts[: args.posts]
        logger.info(f"Test mode: processing first {len(posts_to_process)} posts")
    elif args.all:
        posts_to_process = all_posts
        logger.info(f"Full mode: processing all {len(posts_to_process)} posts")
    else:
        logger.error("Either --all or --test required")
        parser.error("Either --all or --test required")

    # Process posts
    generator = CommentGenerator(output_dir=args.output)

    results = generator.process_posts(
        posts_to_process,
        dry_run=args.dry_run,
        resume=args.resume,
    )

    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Posts processed:    {results['posts_processed']:,}")
    print(f"Total comments:     {results['total_comments']:,}")
    print(f"Failed posts:       {results['failed_posts']:,}")
    print(f"Duration:           {results['duration']/60:.1f} min")
    if results["posts_processed"] > 0:
        print(
            f"Avg comments/post:  {results['total_comments'] / results['posts_processed']:.1f}"
        )
        print(
            f"Throughput:         {results['posts_processed'] / results['duration']:.1f} posts/sec"
        )
    print(f"Output directory:   {args.output}")
    print(f"{'='*70}\n")

    sys.exit(0 if results["failed_posts"] == 0 else 1)


if __name__ == "__main__":
    main()
