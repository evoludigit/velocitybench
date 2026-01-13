#!/usr/bin/env python
"""
Disk Space Checker for Dataset Scaling

Validates available disk space before generation.
Provides pre-generation checks, monitoring, and graceful failure.
"""

import shutil
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class DiskSpaceChecker:
    """Check disk space requirements before dataset generation."""

    # Estimated sizes per item (in GB)
    # Based on empirical data: 1M posts ~ 8.5 GB
    SIZE_PER_POST_GB = 0.0085  # ~8.5 MB per post
    SIZE_PER_USER_GB = 0.0005  # ~500 KB per user
    SIZE_PER_COMMENT_GB = 0.0001  # ~100 KB per comment (lightweight)

    # Safety thresholds
    SAFETY_MARGIN_GB = 1.0
    WARN_THRESHOLD_PCT = 80
    CRITICAL_THRESHOLD_PCT = 95

    def __init__(self, output_dir: Path):
        """
        Initialize disk space checker.

        Args:
            output_dir: Path where files will be generated
        """
        self.output_dir = Path(output_dir)

    def get_disk_space(self) -> Tuple[float, float, float]:
        """
        Get disk space info for output directory.

        Returns:
            (total_gb, used_gb, available_gb)
        """
        stat = shutil.disk_usage(self.output_dir.parent)
        total_gb = stat.total / (1024 ** 3)
        used_gb = stat.used / (1024 ** 3)
        available_gb = stat.free / (1024 ** 3)
        return (total_gb, used_gb, available_gb)

    def estimate_size(self, posts: int, users: int = None, comments: int = None) -> float:
        """
        Estimate total size needed (in GB).

        Args:
            posts: Number of posts
            users: Number of users (optional, auto-calculated if not provided)
            comments: Number of comments (optional, auto-calculated if not provided)

        Returns:
            Estimated size in GB
        """
        if users is None:
            users = max(100, posts // 10)  # ~10% of posts
        if comments is None:
            comments = posts * 5  # ~5 comments per post

        size_gb = (
            (posts * self.SIZE_PER_POST_GB) +
            (users * self.SIZE_PER_USER_GB) +
            (comments * self.SIZE_PER_COMMENT_GB)
        )
        return size_gb

    def check_disk_space(self, posts: int, format: str = 'both') -> Tuple[bool, str]:
        """
        Check if sufficient disk space is available.

        Estimates TSV or SQL size and validates against available space.

        Args:
            posts: Number of posts to generate
            format: Output format ('tsv', 'sql', 'both')

        Returns:
            (is_ok: bool, message: str)
        """
        total_gb, used_gb, available_gb = self.get_disk_space()
        used_pct = (used_gb / total_gb) * 100

        # Estimate size (users and comments auto-calculated)
        estimated_gb = self.estimate_size(posts)

        # Account for format multiplier (TSV + SQL = ~1.2x for both)
        if format == 'sql':
            estimated_gb *= 1.0  # SQL only
        elif format == 'both':
            estimated_gb *= 1.1  # TSV + SQL (small overhead)

        required_gb = estimated_gb + self.SAFETY_MARGIN_GB

        # Check available space
        msg = f"Disk Space Check:\n"
        msg += f"  Required: {required_gb:.2f} GB\n"
        msg += f"  Available: {available_gb:.2f} GB\n"
        msg += f"  Used: {used_pct:.1f}%"

        if used_pct >= self.CRITICAL_THRESHOLD_PCT:
            msg += f"\n  ❌ CRITICAL: Disk usage at {used_pct:.1f}% (threshold: {self.CRITICAL_THRESHOLD_PCT}%)"
            return (False, msg)

        if available_gb < required_gb:
            msg += f"\n  ❌ INSUFFICIENT: Need {required_gb:.2f} GB but only {available_gb:.2f} GB available"
            return (False, msg)

        if used_pct >= self.WARN_THRESHOLD_PCT:
            msg += f"\n  ⚠️  WARNING: Disk usage at {used_pct:.1f}% (threshold: {self.WARN_THRESHOLD_PCT}%)"
            return (True, msg)

        msg += "\n  ✅ OK"
        return (True, msg)

    def check_output_dir_exists(self) -> Tuple[bool, str]:
        """
        Check if output directory can be created/accessed.

        Returns:
            (is_ok: bool, message: str)
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            return (True, f"Output directory check: ✅ {self.output_dir}")
        except Exception as e:
            return (False, f"Output directory check: ❌ {e}")

    def check_output_dir_writable(self) -> Tuple[bool, str]:
        """
        Check if output directory is writable.

        Returns:
            (is_ok: bool, message: str)
        """
        try:
            test_file = self.output_dir / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
            return (True, f"Write permission check: ✅ OK")
        except Exception as e:
            return (False, f"Write permission check: ❌ {e}")

    def check_no_existing_files(self) -> Tuple[bool, str]:
        """
        Check if output directory is empty (no previous generation).

        Returns:
            (is_ok: bool, message: str)
        """
        try:
            if not self.output_dir.exists():
                return (True, "Previous files check: ✅ Directory empty")

            existing_files = list(self.output_dir.glob('blog_*.{tsv,sql}'))
            if existing_files:
                files_str = ', '.join([f.name for f in existing_files])
                return (False, f"Previous files check: ❌ Found existing files ({files_str})")

            return (True, "Previous files check: ✅ Directory clean")
        except Exception as e:
            return (False, f"Previous files check: ❌ {e}")

    def check_all(self, posts: int, format: str = 'both') -> Tuple[bool, str]:
        """
        Run all disk space checks.

        Args:
            posts: Number of posts to generate
            format: Output format ('tsv', 'sql', 'both')

        Returns:
            (all_ok: bool, combined_message: str)
        """
        checks = [
            self.check_output_dir_exists(),
            self.check_output_dir_writable(),
            self.check_disk_space(posts, format),
        ]

        all_ok = all(check[0] for check in checks)
        message = '\n'.join(check[1] for check in checks)

        return (all_ok, message)
