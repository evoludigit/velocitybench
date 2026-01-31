#!/usr/bin/env python
"""
Markdown parsing utilities for blog post loader.

Extracts frontmatter (YAML), converts markdown to plain text, and generates excerpts.
"""

import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Tuple


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Extract YAML frontmatter and body from markdown content.

    Handles both plain markdown and ```markdown wrappers.

    Args:
        content: Full markdown file content

    Returns:
        Tuple of (frontmatter_dict, body_content)
    """
    # Remove ```markdown wrapper if present
    if content.startswith("```markdown\n"):
        content = content[12:]  # Remove ```markdown\n
    elif content.startswith("```markdown"):
        content = content[11:]  # Remove ```markdown

    if content.endswith("\n```"):
        content = content[:-4]  # Remove \n```
    elif content.endswith("```"):
        content = content[:-3]  # Remove ```

    # Check for frontmatter
    if not content.startswith("---\n") and not content.startswith("---\r\n"):
        # No frontmatter
        return {}, content

    # Find closing ---
    lines = content.split("\n")
    closing_idx = None
    for i in range(1, min(50, len(lines))):  # Check first 50 lines
        if lines[i].strip() == "---":
            closing_idx = i
            break

    if not closing_idx:
        # No closing frontmatter marker
        return {}, content

    # Extract frontmatter YAML
    frontmatter_text = "\n".join(lines[1:closing_idx])
    body = "\n".join(lines[closing_idx + 1 :])

    # Parse YAML
    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
        # Ensure we got a dict (YAML can return strings, lists, etc.)
        if not isinstance(frontmatter, dict):
            print(
                f"Warning: YAML frontmatter is not a dict, got {type(frontmatter).__name__}"
            )
            frontmatter = {}
    except yaml.YAMLError as e:
        print(f"Warning: Failed to parse YAML frontmatter: {e}")
        frontmatter = {}

    return frontmatter, body


def markdown_to_plain_text(markdown: str) -> str:
    """
    Convert markdown to plain text by removing markdown syntax.

    Preserves code blocks as indented text, collapses multiple newlines.

    Args:
        markdown: Markdown content

    Returns:
        Plain text version
    """
    text = markdown

    # Remove code fence blocks (preserve content as indented)
    text = re.sub(r"```[\w]*\n(.*?)\n```", r"\n\1\n", text, flags=re.DOTALL)

    # Remove inline code backticks
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Remove headers (keep text)
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

    # Remove bold/italic
    text = re.sub(r"\*\*([^\*]+)\*\*", r"\1", text)  # **bold**
    text = re.sub(r"__([^_]+)__", r"\1", text)  # __bold__
    text = re.sub(r"\*([^\*]+)\*", r"\1", text)  # *italic*
    text = re.sub(r"_([^_]+)_", r"\1", text)  # _italic_

    # Remove links (keep link text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # [text](url)

    # Remove images
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", "", text)  # ![alt](url)

    # Remove horizontal rules
    text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*\*\*+$", "", text, flags=re.MULTILINE)

    # Remove blockquotes
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

    # Remove list markers
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Collapse multiple blank lines to 2 max
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def generate_excerpt(content: str, max_length: int = 200) -> str:
    """
    Generate excerpt from content.

    Extracts first paragraph OR first 200 chars at sentence boundary.

    Args:
        content: Plain text content
        max_length: Maximum excerpt length

    Returns:
        Excerpt text
    """
    # Split into paragraphs
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    if not paragraphs:
        return ""

    first_para = paragraphs[0]

    # If first paragraph is short enough, use it
    if len(first_para) <= max_length:
        return first_para

    # Otherwise, truncate at sentence boundary
    # Find last sentence ending before max_length
    sentences = re.split(r"([.!?]\s+)", first_para[: max_length + 50])

    excerpt = ""
    for i in range(0, len(sentences), 2):  # sentences are at even indices
        sentence = sentences[i]
        separator = sentences[i + 1] if i + 1 < len(sentences) else ""

        if len(excerpt + sentence + separator) > max_length:
            break

        excerpt += sentence + separator

    # Fallback: just truncate at max_length
    if not excerpt:
        excerpt = first_para[:max_length].rsplit(" ", 1)[0] + "..."

    return excerpt.strip()


def extract_blog_metadata(file_path: Path) -> dict:
    """
    Extract metadata from blog post markdown file.

    Args:
        file_path: Path to markdown file

    Returns:
        Dict with: title, content, excerpt, published_at, tags, pattern_name, post_type, difficulty
        Returns None if file cannot be parsed
    """
    try:
        # Read file
        with open(file_path, encoding="utf-8") as f:
            raw_content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    # Parse frontmatter
    frontmatter, body = parse_frontmatter(raw_content)

    # Convert markdown to plain text
    plain_text = markdown_to_plain_text(body)

    # Generate excerpt
    excerpt = generate_excerpt(plain_text)

    # Extract metadata
    metadata = {
        "file_path": str(file_path),
        "file_name": file_path.name,
    }

    # Title (from frontmatter or filename)
    if "title" in frontmatter:
        metadata["title"] = frontmatter["title"][:500]  # Trim to 500 chars
    else:
        # Use filename as fallback (remove extension, replace dashes)
        metadata["title"] = file_path.stem.replace("-", " ").title()[:500]

    # Content and excerpt
    metadata["content"] = plain_text
    metadata["excerpt"] = excerpt

    # Published date (from frontmatter or file mtime)
    if "date" in frontmatter:
        try:
            # Parse ISO date
            if isinstance(frontmatter["date"], datetime):
                metadata["published_at"] = frontmatter["date"]
            else:
                metadata["published_at"] = datetime.fromisoformat(
                    str(frontmatter["date"])
                )
        except Exception:
            metadata["published_at"] = datetime.fromtimestamp(file_path.stat().st_mtime)
    else:
        metadata["published_at"] = datetime.fromtimestamp(file_path.stat().st_mtime)

    # Tags (optional)
    metadata["tags"] = frontmatter.get("tags", [])

    # Pattern name (extract from filename or frontmatter)
    # Filename pattern: {pattern}-{type}-{difficulty}.md
    parts = file_path.stem.split("-")
    if len(parts) >= 3:
        metadata["pattern_name"] = "-".join(
            parts[:-2]
        )  # Everything except last 2 parts
        metadata["post_type"] = parts[-2]  # e.g., tutorial, reference, troubleshooting
        metadata["difficulty"] = parts[-1]  # e.g., beginner, intermediate, advanced
    else:
        metadata["pattern_name"] = frontmatter.get("pattern", file_path.stem)
        metadata["post_type"] = frontmatter.get("type", "unknown")
        metadata["difficulty"] = frontmatter.get("difficulty", "unknown")

    return metadata
