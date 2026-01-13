#!/usr/bin/env python
"""
Data Validator for Dataset Scaling

Validates generated data integrity (checksums, row counts, file consistency).
"""

import hashlib
import json
from pathlib import Path
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate generated dataset integrity."""

    def __init__(self, output_dir: Path):
        """
        Initialize data validator.

        Args:
            output_dir: Directory with generated files
        """
        self.output_dir = Path(output_dir)
        self.manifest_file = self.output_dir / 'MANIFEST.json'

    def compute_checksums(self, algorithm: str = 'sha256') -> Dict[str, str]:
        """
        Compute checksums for generated files.

        Args:
            algorithm: Hash algorithm ('sha256', 'md5')

        Returns:
            dict mapping filename -> checksum
        """
        checksums = {}

        for tsv_file in self.output_dir.glob('blog_*.tsv'):
            checksum = self._compute_file_checksum(tsv_file, algorithm)
            checksums[tsv_file.name] = checksum
            logger.info(f"  {tsv_file.name}: {checksum[:16]}...")

        return checksums

    def _compute_file_checksum(self, filepath: Path, algorithm: str = 'sha256') -> str:
        """
        Compute checksum for a single file.

        Args:
            filepath: Path to file
            algorithm: Hash algorithm

        Returns:
            Hex checksum string
        """
        h = hashlib.new(algorithm)

        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)

        return h.hexdigest()

    def save_checksums(self, checksums: Dict[str, str]) -> bool:
        """
        Save checksums to MANIFEST.json.

        Args:
            checksums: dict mapping filename -> checksum

        Returns:
            True if successful
        """
        try:
            manifest = {
                'algorithm': 'sha256',
                'checksums': checksums,
            }

            with open(self.manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)

            logger.info(f"  Saved manifest: {self.manifest_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")
            return False

    def verify_checksums(self) -> Tuple[bool, str]:
        """
        Verify checksums against saved manifest.

        Returns:
            (is_valid: bool, message: str)
        """
        if not self.manifest_file.exists():
            return (False, "Checksum verification: ❌ No manifest file found")

        try:
            with open(self.manifest_file, 'r') as f:
                manifest = json.load(f)

            saved_checksums = manifest.get('checksums', {})
            current_checksums = self.compute_checksums()

            if saved_checksums == current_checksums:
                return (True, "Checksum verification: ✅ All files intact")
            else:
                return (False, "Checksum verification: ❌ File integrity check failed")

        except Exception as e:
            return (False, f"Checksum verification: ❌ {e}")

    def validate_row_counts(self, expected: Dict[str, int]) -> Tuple[bool, str]:
        """
        Validate row counts in generated TSV files.

        Args:
            expected: dict mapping 'posts'/'users'/'comments' -> expected count

        Returns:
            (is_valid: bool, message: str)
        """
        file_mapping = {
            'posts': 'blog_posts.tsv',
            'users': 'blog_users.tsv',
            'comments': 'blog_comments.tsv',
        }

        msg = "Row count validation:"
        all_ok = True

        for key, filename in file_mapping.items():
            if key not in expected:
                continue

            filepath = self.output_dir / filename

            if not filepath.exists():
                msg += f"\n  ❌ {filename}: File not found"
                all_ok = False
                continue

            try:
                row_count = sum(1 for _ in open(filepath))
                expected_count = expected[key]

                if row_count == expected_count:
                    msg += f"\n  ✅ {filename}: {row_count:,} rows"
                else:
                    msg += f"\n  ❌ {filename}: {row_count:,} rows (expected {expected_count:,})"
                    all_ok = False

            except Exception as e:
                msg += f"\n  ❌ {filename}: {e}"
                all_ok = False

        if all_ok:
            return (True, msg)
        else:
            return (False, msg)

    def validate_file_sizes(self) -> Tuple[bool, str]:
        """
        Validate that generated files have reasonable sizes.

        Returns:
            (is_valid: bool, message: str)
        """
        msg = "File size validation:"
        all_ok = True

        for tsv_file in sorted(self.output_dir.glob('blog_*.tsv')):
            size_mb = tsv_file.stat().st_size / (1024 ** 2)

            if size_mb > 0:
                msg += f"\n  ✅ {tsv_file.name}: {size_mb:.1f} MB"
            else:
                msg += f"\n  ❌ {tsv_file.name}: File is empty"
                all_ok = False

        if all_ok and size_mb > 0:
            return (True, msg)
        else:
            return (False, msg)
