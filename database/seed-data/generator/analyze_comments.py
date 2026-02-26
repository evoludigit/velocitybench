#!/usr/bin/env python
"""Analyze generated comments."""

import json
from pathlib import Path


def analyze_comments(comments_dir: Path):
    """Analyze comments in a directory."""
    if not comments_dir.exists():
        print("No comments found.")
        print("Run: make comments-test")
        return

    files = list(comments_dir.glob("*_comments.json"))
    print(f"Found {len(files)} comment files")

    total_comments = 0
    total_posts = 0
    comment_types = {}
    author_count = {}

    for cf in files[:10]:  # Sample first 10 files
        with open(cf) as f:
            data = json.load(f)
            comments = data.get("comments", [])
            total_comments += len(comments)
            total_posts += 1

            for comment in comments:
                ctype = comment.get("type", "unknown")
                comment_types[ctype] = comment_types.get(ctype, 0) + 1

                author = comment.get("author_name", "Unknown")
                author_count[author] = author_count.get(author, 0) + 1

    if total_posts > 0:
        print("\nSample Analysis (first 10 files):")
        print(f"  Total comments: {total_comments}")
        print(f"  Total posts: {total_posts}")
        print(f"  Avg comments/post: {total_comments / total_posts:.1f}")

        print("\nComment Types:")
        for ctype, count in sorted(comment_types.items(), key=lambda x: -x[1]):
            pct = 100 * count / total_comments
            print(f"  {ctype:20s}: {count:4d} ({pct:5.1f}%)")

        print("\nTop Authors:")
        for author, count in sorted(author_count.items(), key=lambda x: -x[1])[:10]:
            print(f"  {author:20s}: {count:3d} comments")

    if len(files) > 0:
        with open(files[0]) as f:
            data = json.load(f)
            if data.get("comments"):
                comment = data["comments"][0]
                print("\nSample Comment Fields:")
                print(f"  {list(comment.keys())}")


if __name__ == "__main__":
    comments_dir = Path(__file__).parent.parent / "output" / "comments"
    analyze_comments(comments_dir)
