#!/usr/bin/env python
"""
Generate reply comments that respond to hallucinated/debatable comments.

Converts hallucinations into features:
- High hallucination score → generate corrections
- Medium score → generate challenges/agreements
- Replies create realistic discussion threads

Usage:
    python generate_comment_replies.py --comments-dir /tmp/blog_comments \
                                       --blog-dir /path/to/blog/posts \
                                       --test --posts 20

    python generate_comment_replies.py --comments-dir /tmp/blog_comments \
                                       --blog-dir /path/to/blog/posts \
                                       --all
"""

import argparse
import json
import random
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests

from .exceptions import VLLMTimeoutError, VLLMConnectionError, VLLMError

# ============================================================================
# Configuration
# ============================================================================

VLLM_URL = "http://localhost:8000/v1/chat/completions"
MODEL_ID = "/data/models/fp16/Ministral-3-8B-Instruct-2512"
MAX_TOKENS = 300
TEMPERATURE = 0.6
TOP_P = 0.9

# Reply configuration
REPLY_PROBABILITY = 0.4  # 40% of debatable comments get replies
REPLIES_PER_COMMENT_MIN = 1
REPLIES_PER_COMMENT_MAX = 2

# Hallucination score thresholds
HALLUCINATION_SCORE_MIN = 0.3  # Too obvious = no reply needed
HALLUCINATION_SCORE_MAX = 0.9  # Too hallucinated = can't reply meaningfully

# Reply types and their prompts
REPLY_TYPES = {
    "correction": {
        "weight": 0.45,
        "trigger": lambda score: score > 0.65,  # High hallucination score
        "system_prompt": """You are a knowledgeable engineer respectfully correcting a misunderstanding.
The original commenter made a claim, but looking at the actual code/post, they missed something.
Your job is to:
1. Acknowledge what they might have misunderstood
2. Point to specific evidence (line numbers, code snippets)
3. Explain why the correction matters
4. Be respectful and helpful, not condescending

Write a natural reply (100-200 words) that would appear in a technical discussion.""",
    },
    "agreement": {
        "weight": 0.25,
        "trigger": lambda score: 0.4 < score < 0.65,
        "system_prompt": """You are validating a concern raised by another commenter.
They've identified a real issue or limitation. Your job is to:
1. Affirm that they're right
2. Explain why this matters in practice
3. Share relevant context or experience
4. Maybe suggest a workaround or solution

Be conversational and helpful. Write 100-200 words.""",
    },
    "challenge": {
        "weight": 0.20,
        "trigger": lambda score: 0.35 < score < 0.75,
        "system_prompt": """You are respectfully challenging an assumption or oversimplification.
The commenter made a claim that's partially true but misses important context.
Your job is to:
1. Acknowledge what they got right
2. Point out the missing context or nuance
3. Ask clarifying questions
4. Suggest they might be thinking of a specific scenario

Be curious and collaborative. Write 100-200 words.""",
    },
    "question": {
        "weight": 0.10,
        "trigger": lambda score: 0.3 < score < 0.8,
        "system_prompt": """You are asking thoughtful follow-up questions.
The commenter raised an interesting point. Your job is to:
1. Ask clarifying questions about what they mean
2. Probe assumptions they might be making
3. Request more details or examples
4. Show genuine curiosity

Be friendly and genuine. Write 100-200 words.""",
    },
}


# ============================================================================
# Core Classes
# ============================================================================


class CommentReplyGenerator:
    """Generates reply comments to hallucinated/debatable comments."""

    def __init__(self, blog_dir: Path):
        self.blog_dir = blog_dir
        self.vllm_url = VLLM_URL
        self.generated_count = 0
        self.failed_count = 0
        self.start_time = time.time()

    def load_post_content(self, post_filename: str) -> str:
        """Load blog post content for context."""
        post_path = self.blog_dir / post_filename
        if post_path.exists():
            with open(post_path) as f:
                return f.read()
        return ""

    def select_reply_type(self, hallucination_score: float) -> str:
        """Select reply type based on hallucination score."""
        candidates = [
            (rtype, config) for rtype, config in REPLY_TYPES.items()
            if config["trigger"](hallucination_score)
        ]

        if not candidates:
            # Default to challenge if score is in ambiguous range
            return "challenge"

        # Weight by probability
        rtype, _ = random.choice(candidates)
        return rtype

    def generate_single_reply(
        self,
        original_comment: Dict,
        post_content: str,
        reply_type: str,
    ) -> Optional[Dict]:
        """Generate a single reply to a comment."""
        config = REPLY_TYPES.get(reply_type, {})
        system_prompt = config.get("system_prompt", "")

        # Extract claim/topic from original comment
        claim = original_comment["text"][:200]  # Use first 200 chars as context

        prompt = f"""The original blog post discussed:
{post_content[:300]}

...

A commenter wrote:
"{claim}"

Your task: Write a {reply_type} reply to this comment.
Keep it natural and conversational (100-200 words).
Do not use markdown formatting."""

        try:
            response = self._call_vllm(prompt, system_prompt)
            if response and len(response) > 50:
                return {
                    "text": response,
                    "type": reply_type,
                    "generated_at": datetime.now().isoformat(),
                    "parent_comment_id": original_comment.get("id"),
                }
        except Exception as e:
            print(f"    ⚠️ Failed to generate {reply_type} reply: {e}")

        return None

    def generate_replies_for_comment(
        self,
        comment: Dict,
        post_content: str,
        dry_run: bool = False,
    ) -> List[Dict]:
        """Generate 1-2 replies to a single comment."""
        replies = []

        # Determine number of replies
        num_replies = random.randint(REPLIES_PER_COMMENT_MIN, REPLIES_PER_COMMENT_MAX)

        for i in range(num_replies):
            reply_type = self.select_reply_type(
                comment.get("hallucination_score", 0.5)
            )

            if dry_run:
                replies.append(
                    {
                        "text": f"[DRY RUN] {reply_type} reply to: {comment['text'][:50]}...",
                        "type": reply_type,
                        "parent_comment_id": comment.get("id"),
                    }
                )
            else:
                reply = self.generate_single_reply(comment, post_content, reply_type)
                if reply:
                    replies.append(reply)
                    self.generated_count += 1
                else:
                    self.failed_count += 1

        return replies

    def should_generate_replies(self, comment: Dict) -> bool:
        """Decide if a comment should get replies."""
        # Only reply to comments with scores in debate range
        score = comment.get("hallucination_score", 0.5)
        if not (HALLUCINATION_SCORE_MIN < score < HALLUCINATION_SCORE_MAX):
            return False

        # Skip generic comments
        text = comment.get("text", "").lower()
        if any(
            phrase in text
            for phrase in ["great post", "thanks for", "love this", "great work"]
        ):
            return False

        # Random selection (40% chance)
        return random.random() < REPLY_PROBABILITY

    def process_comments_file(
        self,
        comments_file: Path,
        output_file: Path,
        dry_run: bool = False,
    ) -> Dict:
        """Process a single comments file and generate replies."""
        stats = {"comments_with_replies": 0, "total_replies": 0, "failed": 0}

        try:
            with open(comments_file) as f:
                data = json.load(f)

            post_title = data.get("post_title", "")
            post_file = data.get("post_file", "")
            comments = data.get("comments", [])

            # Load post content for context
            post_content = self.load_post_content(post_file)

            # Process each comment
            for comment in comments:
                if self.should_generate_replies(comment):
                    # Generate replies
                    replies = self.generate_replies_for_comment(
                        comment, post_content, dry_run=dry_run
                    )

                    if replies:
                        comment["replies"] = replies
                        stats["comments_with_replies"] += 1
                        stats["total_replies"] += len(replies)

            # Save enhanced comments (with replies)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(
                    {
                        "post_title": post_title,
                        "post_file": post_file,
                        "generated_at": datetime.now().isoformat(),
                        "comment_count": len(comments),
                        "comments_with_replies": stats["comments_with_replies"],
                        "total_replies": stats["total_replies"],
                        "comments": comments,
                    },
                    f,
                    indent=2,
                )

            return stats

        except Exception as e:
            print(f"  Error processing {comments_file.name}: {e}")
            stats["failed"] = 1
            return stats

    def process_all(
        self,
        comments_dir: Path,
        output_dir: Path,
        num_posts: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict:
        """Process all comment files and generate replies."""
        comment_files = sorted(list(comments_dir.glob("*_comments.json")))

        if num_posts:
            comment_files = comment_files[:num_posts]

        print(f"\n{'='*70}")
        print(f"COMMENT REPLY GENERATION")
        print(f"{'='*70}")
        print(f"Comment files to process: {len(comment_files)}")
        print(f"Reply generation probability: {REPLY_PROBABILITY*100:.0f}%")
        print(f"Replies per comment: {REPLIES_PER_COMMENT_MIN}-{REPLIES_PER_COMMENT_MAX}")
        print(f"Hallucination score range: {HALLUCINATION_SCORE_MIN}-{HALLUCINATION_SCORE_MAX}")
        print(f"{'='*70}\n")

        output_dir.mkdir(parents=True, exist_ok=True)

        total_stats = {
            "files_processed": 0,
            "comments_with_replies": 0,
            "total_replies": 0,
            "failed": 0,
        }

        for i, comment_file in enumerate(comment_files, 1):
            output_file = output_dir / comment_file.name

            print(
                f"[{i:5d}/{len(comment_files):5d}] {comment_file.stem:50s}",
                end="",
                flush=True,
            )

            stats = self.process_comments_file(
                comment_file, output_file, dry_run=dry_run
            )

            if stats.get("failed"):
                print(f" ✗")
                total_stats["failed"] += 1
            else:
                print(
                    f" ✓ ({stats['comments_with_replies']:2d} comments with {stats['total_replies']:2d} replies)"
                )
                total_stats["files_processed"] += 1
                total_stats["comments_with_replies"] += stats["comments_with_replies"]
                total_stats["total_replies"] += stats["total_replies"]

            # Checkpoint every 100 files
            if i % 100 == 0:
                elapsed = time.time() - self.start_time
                rate = i / elapsed
                remaining = (len(comment_files) - i) / rate if rate > 0 else 0
                print(
                    f"  ✓ Processed {i}/{len(comment_files)} files ({rate:.1f} files/sec, ~{remaining/60:.0f}min remaining)\n"
                )

        total_stats["duration"] = time.time() - self.start_time
        return total_stats

    def _call_vllm(self, prompt: str, system_prompt: str) -> Optional[str]:
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


# ============================================================================
# CLI
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate reply comments to hallucinated/debatable comments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 20 posts
  python generate_comment_replies.py --comments-dir /tmp/blog_comments \\
                                     --blog-dir ./output/blog \\
                                     --test --posts 20

  # Full generation
  python generate_comment_replies.py --comments-dir /tmp/blog_comments \\
                                     --blog-dir ./output/blog \\
                                     --all

  # Dry run (don't call vLLM)
  python generate_comment_replies.py --comments-dir /tmp/blog_comments \\
                                     --blog-dir ./output/blog \\
                                     --all \\
                                     --dry-run
        """,
    )

    parser.add_argument(
        "--comments-dir",
        type=Path,
        required=True,
        help="Directory with generated comments",
    )

    parser.add_argument(
        "--blog-dir",
        type=Path,
        required=True,
        help="Directory with blog post files",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for comments with replies (default: comments-dir/with-replies)",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all comment files",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode with limited files",
    )

    parser.add_argument(
        "--posts",
        type=int,
        default=20,
        help="Number of posts in test mode (default: 20)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't call vLLM, just show what would be done",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.all and not args.test:
        parser.error("Either --all or --test is required")

    if not args.comments_dir.exists():
        print(f"Error: Comments directory not found: {args.comments_dir}")
        sys.exit(1)

    if not args.blog_dir.exists():
        print(f"Error: Blog directory not found: {args.blog_dir}")
        sys.exit(1)

    # Check vLLM is running (unless dry run)
    if not args.dry_run:
        try:
            response = requests.get("http://localhost:8000/v1/models", timeout=5)
            response.raise_for_status()
        except (requests.RequestException, requests.Timeout) as e:
            print("Error: vLLM server not running at localhost:8000")
            print(f"Details: {e}")
            print("Start it with: vllm-switch implementer")
            sys.exit(1)

    # Determine output directory
    output_dir = args.output_dir or (args.comments_dir.parent / "with-replies")

    # Process files
    generator = CommentReplyGenerator(blog_dir=args.blog_dir)

    num_posts = None if args.all else args.posts

    stats = generator.process_all(
        comments_dir=args.comments_dir,
        output_dir=output_dir,
        num_posts=num_posts,
        dry_run=args.dry_run,
    )

    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Files processed:        {stats['files_processed']:,}")
    print(f"Comments with replies:  {stats['comments_with_replies']:,}")
    print(f"Total replies generated:{stats['total_replies']:,}")
    print(f"Failed files:           {stats['failed']:,}")
    print(f"Duration:               {stats['duration']/60:.1f} min")
    if stats["comments_with_replies"] > 0:
        avg_replies = stats["total_replies"] / stats["comments_with_replies"]
        print(f"Avg replies/comment:    {avg_replies:.2f}")
    print(f"Output directory:       {output_dir}")
    print(f"{'='*70}\n")

    sys.exit(0 if stats["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
