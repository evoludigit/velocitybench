#!/usr/bin/env python
"""
Fix formatting issues in generated blog posts.

Issues fixed:
1. Remove markdown code fence wrappers (```markdown ... ```)
2. Remove trailing/leading whitespace
3. Fix multiple consecutive blank lines
4. Ensure proper frontmatter format
5. Remove duplicate frontmatter

Usage:
    python fix_blog_posts.py --dry-run  # Preview changes
    python fix_blog_posts.py            # Apply fixes
    python fix_blog_posts.py --path database/seed-data/output/blog/tutorials  # Fix specific directory
"""

import argparse
import re
from pathlib import Path
from typing import Tuple


def fix_markdown_wrapper(content: str) -> tuple[str, bool]:
    """Remove markdown code fence wrapper if present."""
    changed = False

    # Check if content starts with ```markdown
    if content.startswith("```markdown\n"):
        content = content[12:]  # Remove ```markdown\n
        changed = True
    elif content.startswith("```markdown"):
        content = content[11:]  # Remove ```markdown
        changed = True

    # Check if content ends with ```
    if content.endswith("\n```"):
        content = content[:-4]  # Remove \n```
        changed = True
    elif content.endswith("```"):
        content = content[:-3]  # Remove ```
        changed = True

    return content, changed


def fix_multiple_blank_lines(content: str) -> tuple[str, bool]:
    """Replace 3+ consecutive blank lines with 2 blank lines."""
    original = content
    content = re.sub(r"\n{4,}", "\n\n\n", content)
    return content, content != original


def fix_trailing_whitespace(content: str) -> tuple[str, bool]:
    """Remove trailing whitespace from each line."""
    lines = content.split("\n")
    fixed_lines = [line.rstrip() for line in lines]
    fixed_content = "\n".join(fixed_lines)
    return fixed_content, fixed_content != content


def fix_frontmatter(content: str) -> tuple[str, bool]:
    """Ensure proper frontmatter format (YAML between --- markers)."""
    changed = False

    # Check if frontmatter exists and is properly formatted
    if not content.startswith("---\n") and not content.startswith("---\r\n"):
        # No frontmatter, nothing to fix
        return content, False

    # Extract frontmatter
    lines = content.split("\n")
    if lines[0].strip() == "---":
        # Find the closing ---
        closing_idx = None
        for i in range(1, min(20, len(lines))):  # Check first 20 lines
            if lines[i].strip() == "---":
                closing_idx = i
                break

        if closing_idx:
            # Check for duplicate frontmatter (sometimes AI generates two)
            remaining = "\n".join(lines[closing_idx + 1 :])
            if remaining.strip().startswith("---\n"):
                # Duplicate frontmatter found, remove it
                second_closing = None
                remaining_lines = remaining.split("\n")
                for i in range(1, min(20, len(remaining_lines))):
                    if remaining_lines[i].strip() == "---":
                        second_closing = i
                        break

                if second_closing:
                    # Remove duplicate frontmatter
                    content = "\n".join(
                        lines[: closing_idx + 1] + remaining_lines[second_closing + 1 :]
                    )
                    changed = True

    return content, changed


def fix_file(file_path: Path, dry_run: bool = False) -> dict:
    """Fix all issues in a single file."""
    result = {
        "path": str(file_path),
        "changes": [],
        "success": False,
    }

    try:
        # Read file
        with open(file_path, encoding="utf-8") as f:
            original_content = f.read()

        content = original_content

        # Apply fixes
        content, wrapper_changed = fix_markdown_wrapper(content)
        if wrapper_changed:
            result["changes"].append("markdown_wrapper")

        content, frontmatter_changed = fix_frontmatter(content)
        if frontmatter_changed:
            result["changes"].append("duplicate_frontmatter")

        content, blank_changed = fix_multiple_blank_lines(content)
        if blank_changed:
            result["changes"].append("multiple_blank_lines")

        content, whitespace_changed = fix_trailing_whitespace(content)
        if whitespace_changed:
            result["changes"].append("trailing_whitespace")

        # Ensure file ends with single newline
        if not content.endswith("\n"):
            content += "\n"
            result["changes"].append("missing_final_newline")

        # Check if anything changed
        if content != original_content:
            if not dry_run:
                # Write fixed content
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            result["success"] = True
        else:
            result["changes"] = []

    except Exception as e:
        result["error"] = str(e)

    return result


def process_directory(directory: Path, dry_run: bool = False) -> dict:
    """Process all markdown files in directory."""
    stats = {
        "total": 0,
        "fixed": 0,
        "unchanged": 0,
        "errors": 0,
        "changes_by_type": {
            "markdown_wrapper": 0,
            "duplicate_frontmatter": 0,
            "multiple_blank_lines": 0,
            "trailing_whitespace": 0,
            "missing_final_newline": 0,
        },
    }

    # Find all markdown files
    md_files = list(directory.rglob("*.md"))
    stats["total"] = len(md_files)

    print(f"\nProcessing {stats['total']} files in {directory}...")
    if dry_run:
        print("DRY RUN MODE - No files will be modified\n")
    else:
        print("LIVE MODE - Files will be modified\n")

    for file_path in md_files:
        result = fix_file(file_path, dry_run)

        if "error" in result:
            stats["errors"] += 1
            print(f"❌ ERROR: {result['path']}: {result['error']}")
        elif result["changes"]:
            stats["fixed"] += 1
            for change_type in result["changes"]:
                stats["changes_by_type"][change_type] += 1

            changes_str = ", ".join(result["changes"])
            print(f"✓ Fixed: {file_path.name} ({changes_str})")
        else:
            stats["unchanged"] += 1

    return stats


def print_summary(stats: dict, dry_run: bool):
    """Print summary of changes."""
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total files: {stats['total']}")
    print(f"Fixed: {stats['fixed']}")
    print(f"Unchanged: {stats['unchanged']}")
    print(f"Errors: {stats['errors']}")
    print()
    print("Changes by type:")
    for change_type, count in stats["changes_by_type"].items():
        if count > 0:
            print(f"  - {change_type}: {count}")

    if dry_run:
        print(f"\n⚠️  DRY RUN - No files were modified")
        print("Run without --dry-run to apply changes")
    else:
        print(f"\n✅ All changes applied successfully!")


def main():
    parser = argparse.ArgumentParser(
        description="Fix formatting issues in generated blog posts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes without modifying files
  python fix_blog_posts.py --dry-run

  # Apply fixes to all blog posts
  python fix_blog_posts.py

  # Fix only tutorial posts
  python fix_blog_posts.py --path database/seed-data/output/blog/tutorials

  # Fix single file
  python fix_blog_posts.py --file database/seed-data/output/blog/tutorials/api-troubleshooting-tutorial-beginner.md
        """,
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )

    parser.add_argument(
        "--path",
        type=str,
        default="database/seed-data/output/blog",
        help="Path to blog directory (default: database/seed-data/output/blog)",
    )

    parser.add_argument(
        "--file", type=str, help="Fix a single file instead of entire directory"
    )

    args = parser.parse_args()

    if args.file:
        # Fix single file
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return 1

        print(f"Processing single file: {file_path}")
        if args.dry_run:
            print("DRY RUN MODE - No files will be modified\n")

        result = fix_file(file_path, args.dry_run)

        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
            return 1
        elif result["changes"]:
            changes_str = ", ".join(result["changes"])
            print(f"✓ Fixed: {changes_str}")
            if not args.dry_run:
                print("Changes applied successfully!")
            else:
                print("DRY RUN - No changes applied")
        else:
            print("No changes needed")

        return 0

    else:
        # Process directory
        blog_dir = Path(args.path)
        if not blog_dir.exists():
            print(f"Error: Directory not found: {blog_dir}")
            return 1

        stats = process_directory(blog_dir, args.dry_run)
        print_summary(stats, args.dry_run)

        return 0


if __name__ == "__main__":
    exit(main())
