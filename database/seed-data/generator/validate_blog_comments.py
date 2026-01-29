#!/usr/bin/env python
"""
Validate and filter generated blog comments.

Detects:
- Hallucinated errors (claiming issues that don't exist)
- Generic praise (too vague/promotional)
- Duplicates (same comment repeated)
- Too short (insufficient substance)
- Off-topic comments

Usage:
    python validate_blog_comments.py --comments-dir /tmp/blog_comments
    python validate_blog_comments.py --comments-dir /tmp/blog_comments --strict
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================================
# Configuration
# ============================================================================

GENERIC_PRAISE_PATTERNS = [
    r"^(great|excellent|wonderful|amazing|fantastic|awesome)\s+post",
    r"thanks?\s+(for\s+)?(sharing|writing)",
    r"(very\s+)?(helpful|useful|informative)",
    r"^i\s+(really\s+)?(like|love|enjoy|appreciate)",
    r"^love\s+this",
    r"^great\s+work",
    r"^thanks?$",
    r"^nice\s+(article|post|work)",
]

HALLUCINATION_KEYWORDS = [
    "missing",
    "forgot",
    "doesn't handle",
    "broken",
    "wrong",
    "incorrect",
    "error",
    "bug",
    "security issue",
    "vulnerability",
]

MIN_COMMENT_LENGTH = 80  # chars
MAX_COMMENT_LENGTH = 1000  # chars

DUPLICATE_SIMILARITY_THRESHOLD = 0.75  # 75% similarity = duplicate


# ============================================================================
# Validation Functions
# ============================================================================


def is_generic_praise(comment_text: str) -> bool:
    """Check if comment is generic praise."""
    lower_text = comment_text.lower()

    for pattern in GENERIC_PRAISE_PATTERNS:
        if re.search(pattern, lower_text):
            return True

    return False


def is_too_short(comment_text: str) -> bool:
    """Check if comment is too short to be substantive."""
    return len(comment_text) < MIN_COMMENT_LENGTH


def is_too_long(comment_text: str) -> bool:
    """Check if comment is unreasonably long."""
    return len(comment_text) > MAX_COMMENT_LENGTH


def extract_claims(comment_text: str) -> List[Dict]:
    """
    Extract technical claims from comment.

    Returns list of claims like:
    - {"type": "missing", "content": "error handling", "context": "..."}
    - {"type": "security", "content": "SQL injection", "context": "..."}
    """
    claims = []

    # Look for common claim patterns
    patterns = [
        (r"(missing|forgot|doesn't have)\s+([^.!?]+)", "missing"),
        (r"(security|vulnerability|injection|xss|csrf)\s+([^.!?]+)", "security"),
        (r"(error handling?|exception)\s+([^.!?]+)", "error_handling"),
        (r"(performance|optimization)\s+([^.!?]+)", "performance"),
        (r"(broken|doesn't work|wrong)\s+([^.!?]+)", "broken"),
    ]

    for pattern, claim_type in patterns:
        for match in re.finditer(pattern, comment_text, re.IGNORECASE):
            claims.append(
                {
                    "type": claim_type,
                    "content": match.group(2).strip(),
                    "match": match.group(0),
                }
            )

    return claims


def might_be_hallucinated(comment_text: str, post_content: str) -> float:
    """
    Estimate probability comment is hallucinated (0.0-1.0).

    Higher = more likely to be hallucinated.
    """
    score = 0.0

    # Extract claims from comment
    claims = extract_claims(comment_text)

    if not claims:
        # No claims = probably OK (if not generic praise)
        return 0.0

    # Check if claims are grounded in post
    post_lower = post_content.lower()
    ungrounded_claims = 0

    for claim in claims:
        content_lower = claim["content"].lower()

        # Check if claim content appears in post
        if content_lower not in post_lower:
            # Claim mentions something not in the post
            ungrounded_claims += 1

    if claims:
        hallucination_ratio = ungrounded_claims / len(claims)
        score = hallucination_ratio * 0.8  # 80% weight for ungrounded claims

    # Boost score if making very specific false claims
    if "line " in comment_text and "should be" in comment_text:
        # Claiming specific line numbers - high hallucination risk
        if any(
            str(i) in comment_text for i in range(1, 500)
        ):  # Check if any line numbers
            score = min(1.0, score + 0.3)

    return score


def similarity_score(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts (0.0-1.0).

    Simple token-based similarity.
    """
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())

    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    return intersection / union if union > 0 else 0.0


def is_duplicate(comment_text: str, previous_comments: List[str]) -> bool:
    """Check if comment is too similar to previous comments."""
    for prev in previous_comments:
        if similarity_score(comment_text, prev) > DUPLICATE_SIMILARITY_THRESHOLD:
            return True

    return False


# ============================================================================
# Validation and Filtering
# ============================================================================


class CommentValidator:
    """Validate and filter blog comments."""

    def __init__(self):
        self.stats = {
            "total_comments": 0,
            "accepted": 0,
            "rejected_generic_praise": 0,
            "rejected_too_short": 0,
            "rejected_too_long": 0,
            "rejected_hallucinated": 0,
            "rejected_duplicate": 0,
            "rejected_other": 0,
        }

    def validate_comments_for_post(
        self,
        post_content: str,
        comments: List[Dict],
        strict: bool = False,
    ) -> Tuple[List[Dict], List[Tuple[Dict, str]]]:
        """
        Validate comments for a post.

        Returns:
            - accepted: List of valid comments
            - rejected: List of (comment, reason) tuples
        """
        accepted = []
        rejected = []
        seen_texts = []

        for comment in comments:
            comment_text = comment.get("text", "").strip()
            reason = self._validate_comment(
                comment_text, post_content, seen_texts, strict=strict
            )

            if reason is None:
                accepted.append(comment)
                seen_texts.append(comment_text)
                self.stats["accepted"] += 1
            else:
                rejected.append((comment, reason))
                # Track reason
                if "generic" in reason:
                    self.stats["rejected_generic_praise"] += 1
                elif "too short" in reason:
                    self.stats["rejected_too_short"] += 1
                elif "too long" in reason:
                    self.stats["rejected_too_long"] += 1
                elif "hallucinated" in reason:
                    self.stats["rejected_hallucinated"] += 1
                elif "duplicate" in reason:
                    self.stats["rejected_duplicate"] += 1
                else:
                    self.stats["rejected_other"] += 1

        return accepted, rejected

    def _validate_comment(
        self,
        comment_text: str,
        post_content: str,
        previous_comments: List[str],
        strict: bool = False,
    ) -> Optional[str]:
        """
        Validate single comment.

        Returns None if valid, otherwise reason for rejection.
        """
        self.stats["total_comments"] += 1

        # Check length
        if is_too_short(comment_text):
            return "too short (< 80 chars)"

        if is_too_long(comment_text):
            return "too long (> 1000 chars)"

        # Check for generic praise
        if is_generic_praise(comment_text):
            return "generic praise"

        # Check for duplicates
        if is_duplicate(comment_text, previous_comments):
            return "duplicate"

        # Check for hallucination
        hallucination_score = might_be_hallucinated(comment_text, post_content)

        if strict:
            # Strict: reject if >50% likely hallucinated
            if hallucination_score > 0.5:
                return f"likely hallucinated (score: {hallucination_score:.2f})"
        else:
            # Lenient: reject only if >80% likely hallucinated
            if hallucination_score > 0.8:
                return f"likely hallucinated (score: {hallucination_score:.2f})"

        return None


def filter_comments_directory(comments_dir: Path, strict: bool = False) -> Dict:
    """
    Filter all comments in a directory.

    Returns statistics.
    """
    validator = CommentValidator()

    if not comments_dir.exists():
        print(f"Error: Comments directory not found: {comments_dir}")
        return {}

    # Find all comment files
    comment_files = list(comments_dir.glob("*_comments.json"))
    print(f"\nFound {len(comment_files)} comment files\n")

    accepted_dir = comments_dir / "accepted"
    rejected_dir = comments_dir / "rejected"
    accepted_dir.mkdir(exist_ok=True)
    rejected_dir.mkdir(exist_ok=True)

    total_accepted = 0
    total_rejected = 0

    for i, comment_file in enumerate(sorted(comment_files), 1):
        try:
            with open(comment_file) as f:
                data = json.load(f)

            post_title = data.get("post_title", "unknown")
            comments = data.get("comments", [])

            # Get post content for hallucination checking
            post_file = comment_file.parent.parent / "blog" / data.get(
                "post_file", ""
            )
            post_content = ""
            if post_file.exists():
                with open(post_file) as f:
                    post_content = f.read()

            # Validate
            accepted, rejected = validator.validate_comments_for_post(
                post_content, comments, strict=strict
            )

            total_accepted += len(accepted)
            total_rejected += len(rejected)

            # Save results
            if accepted:
                accepted_data = {
                    "post_title": post_title,
                    "post_file": data.get("post_file"),
                    "count": len(accepted),
                    "generated_at": data.get("generated_at"),
                    "comments": accepted,
                }
                with open(accepted_dir / comment_file.name, "w") as f:
                    json.dump(accepted_data, f, indent=2)

            if rejected:
                rejected_data = {
                    "post_title": post_title,
                    "count": len(rejected),
                    "rejected_comments": [
                        {"text": c.get("text"), "reason": r, "type": c.get("type")}
                        for c, r in rejected
                    ],
                }
                with open(rejected_dir / comment_file.name, "w") as f:
                    json.dump(rejected_data, f, indent=2)

            # Progress
            if i % 100 == 0:
                print(f"Processed {i}/{len(comment_files)} files...")

        except Exception as e:
            print(f"Error processing {comment_file}: {e}")

    # Print statistics
    print(f"\n{'='*70}")
    print("VALIDATION RESULTS")
    print(f"{'='*70}")
    print(f"Total comments processed:   {validator.stats['total_comments']:,}")
    print(f"Accepted (valid):           {validator.stats['accepted']:,}")
    print(f"Rejected (generic praise):  {validator.stats['rejected_generic_praise']:,}")
    print(f"Rejected (too short):       {validator.stats['rejected_too_short']:,}")
    print(f"Rejected (too long):        {validator.stats['rejected_too_long']:,}")
    print(f"Rejected (hallucinated):    {validator.stats['rejected_hallucinated']:,}")
    print(f"Rejected (duplicate):       {validator.stats['rejected_duplicate']:,}")
    print(f"Rejected (other):           {validator.stats['rejected_other']:,}")

    acceptance_rate = (
        100 * validator.stats["accepted"] / validator.stats["total_comments"]
        if validator.stats["total_comments"]
        else 0
    )
    print(f"\nAcceptance rate:            {acceptance_rate:.1f}%")
    print(f"\nOutput directories:")
    print(f"  Accepted comments:  {accepted_dir}")
    print(f"  Rejected comments:  {rejected_dir}")
    print(f"{'='*70}\n")

    return validator.stats


# ============================================================================
# CLI
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Validate and filter blog comments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Filter comments (lenient mode)
  python validate_blog_comments.py --comments-dir /tmp/blog_comments

  # Filter with strict rules
  python validate_blog_comments.py --comments-dir /tmp/blog_comments --strict
        """,
    )

    parser.add_argument(
        "--comments-dir",
        type=Path,
        required=True,
        help="Directory with generated comments",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use strict validation (reject more hallucinations)",
    )

    args = parser.parse_args()

    # Run filtering
    stats = filter_comments_directory(args.comments_dir, strict=args.strict)

    return 0 if stats else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
