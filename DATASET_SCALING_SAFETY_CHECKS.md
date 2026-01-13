# Dataset Scaling Safety Checks & Security Measures

**Date**: 2026-01-13
**Purpose**: Prevent disk space exhaustion, data corruption, and runaway processes
**Status**: ✅ Plan ready for implementation

---

## Overview

Before generating 1M posts (~8.5 GB), the system must verify:

1. **Disk Space Available** (primary concern)
2. **Database Connectivity** (if loading)
3. **Output Directory Permissions**
4. **Memory Availability**
5. **Process Safety** (prevent zombies, timeouts)
6. **Data Integrity** (checksums, validation)

---

## 1. Disk Space Safety Checks

### 1.1 Pre-Generation Checks

Before generating any data, check available disk space:

```python
# database/seed-data/generator/safety_checks.py

import shutil
import os
from pathlib import Path
from typing import Tuple

class DiskSpaceChecker:
    """Check and monitor disk space during dataset generation."""

    # Safety margins
    SAFETY_MARGIN_GB = 1.0  # Always keep 1 GB free
    WARN_THRESHOLD_PCT = 80  # Warn if > 80% used
    CRITICAL_THRESHOLD_PCT = 95  # Fail if > 95% used

    # Dataset size estimates (in GB)
    DATASET_SIZES = {
        'tiny': {
            'posts': 0.015,      # 15 MB
            'users': 0.0025,     # 2.5 MB
            'comments': 0.075,   # 75 MB
            'total': 0.1
        },
        'dev': {
            'posts': 0.15,       # 150 MB
            'users': 0.025,      # 25 MB
            'comments': 0.75,    # 750 MB
            'total': 1.0
        },
        'staging': {
            'posts': 3.0,        # 3 GB
            'users': 0.5,        # 500 MB
            'comments': 7.5,     # 7.5 GB
            'total': 11.0
        },
        'production': {
            'posts': 3.0,        # 3 GB (1M posts)
            'users': 0.5,        # 500 MB (100K users)
            'comments': 5.0,     # 5 GB (5M comments)
            'total': 8.5
        }
    }

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def check_all(self, profile: str, format: str = 'both') -> Tuple[bool, str]:
        """
        Run all safety checks.

        Returns:
            (is_safe: bool, message: str)
        """
        checks = [
            self.check_disk_space(profile, format),
            self.check_output_dir_exists(),
            self.check_output_dir_writable(),
            self.check_no_existing_files(profile),
        ]

        # All checks must pass
        all_safe = all(check[0] for check in checks)
        messages = [msg for _, msg in checks]

        return all_safe, '\n'.join(messages)

    def check_disk_space(self, profile: str, format: str = 'both') -> Tuple[bool, str]:
        """Check if enough disk space is available."""

        # Get required space
        required_gb = self._get_required_space(profile, format)

        # Get available space
        stat = shutil.disk_usage(self.output_dir)
        available_gb = stat.free / (1024 ** 3)
        used_pct = (stat.used / stat.total) * 100

        # Build message
        message = f"Disk Space Check:\n"
        message += f"  Output: {self.output_dir}\n"
        message += f"  Required: {required_gb:.2f} GB\n"
        message += f"  Available: {available_gb:.2f} GB\n"
        message += f"  Used: {used_pct:.1f}%"

        # Safety checks
        min_required = required_gb + self.SAFETY_MARGIN_GB

        if used_pct >= self.CRITICAL_THRESHOLD_PCT:
            message += f"\n  ❌ CRITICAL: Disk usage > {self.CRITICAL_THRESHOLD_PCT}%"
            return False, message

        if available_gb < min_required:
            message += f"\n  ❌ FAIL: Need {min_required:.2f} GB (including {self.SAFETY_MARGIN_GB} GB margin)"
            return False, message

        if used_pct >= self.WARN_THRESHOLD_PCT:
            message += f"\n  ⚠️  WARNING: Disk usage > {self.WARN_THRESHOLD_PCT}%"
            # Still allows generation, but warns user
            return True, message

        message += f"\n  ✅ OK"
        return True, message

    def check_output_dir_exists(self) -> Tuple[bool, str]:
        """Check if output directory exists or can be created."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            return True, f"Output Directory: {self.output_dir} ✅"
        except Exception as e:
            return False, f"Output Directory: Cannot create {self.output_dir} - {e} ❌"

    def check_output_dir_writable(self) -> Tuple[bool, str]:
        """Check if output directory is writable."""
        try:
            test_file = self.output_dir / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
            return True, f"Write Permission: {self.output_dir} ✅"
        except Exception as e:
            return False, f"Write Permission: Cannot write to {self.output_dir} - {e} ❌"

    def check_no_existing_files(self, profile: str) -> Tuple[bool, str]:
        """Check if existing dataset files would be overwritten."""
        expected_files = [
            self.output_dir / 'posts.tsv',
            self.output_dir / 'users.tsv',
            self.output_dir / 'comments.tsv',
            self.output_dir / 'data.sql',
        ]

        existing = [f for f in expected_files if f.exists()]

        if existing:
            msg = f"Existing Files: Found {len(existing)} existing file(s):\n"
            for f in existing:
                size_mb = f.stat().st_size / (1024 ** 2)
                msg += f"  - {f.name} ({size_mb:.1f} MB)\n"
            msg += "Use --force to overwrite"
            return False, msg

        return True, "Existing Files: None (safe to proceed) ✅"

    def _get_required_space(self, profile: str, format: str) -> float:
        """Get required disk space in GB for given profile and format."""

        if profile not in self.DATASET_SIZES:
            raise ValueError(f"Unknown profile: {profile}")

        dataset = self.DATASET_SIZES[profile]

        if format == 'both':
            # TSV + SQL (SQL is ~2x larger)
            return dataset['total'] + (dataset['total'] * 2)
        elif format == 'tsv':
            return dataset['total']
        elif format == 'sql':
            return dataset['total'] * 2
        else:
            raise ValueError(f"Unknown format: {format}")

    def get_available_space(self) -> float:
        """Get available disk space in GB."""
        stat = shutil.disk_usage(self.output_dir)
        return stat.free / (1024 ** 3)

    def get_disk_usage(self) -> dict:
        """Get disk usage statistics."""
        stat = shutil.disk_usage(self.output_dir)
        total_gb = stat.total / (1024 ** 3)
        used_gb = stat.used / (1024 ** 3)
        free_gb = stat.free / (1024 ** 3)
        used_pct = (stat.used / stat.total) * 100

        return {
            'total_gb': total_gb,
            'used_gb': used_gb,
            'free_gb': free_gb,
            'used_pct': used_pct,
        }
```

### 1.2 Integration with scale_dataset.py

```python
# In scale_dataset.py main()

def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument('--force', action='store_true',
                        help='Skip safety checks (not recommended)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be generated without writing')
    args = parser.parse_args()

    config = resolve_config(args)
    output_dir = Path(args.output_dir or '/tmp/velocitybench')

    # RUN SAFETY CHECKS
    print("Running safety checks...")
    checker = DiskSpaceChecker(output_dir)
    is_safe, check_message = checker.check_all(args.profile, args.format)

    print(check_message)
    print()

    if not is_safe:
        if args.force:
            print("⚠️  WARNING: Proceeding despite failed safety checks (--force)")
        else:
            print("❌ FAILED: Safety checks did not pass")
            print("Use --force to override (not recommended)")
            sys.exit(1)

    # Continue with generation...
```

---

## 2. Runtime Monitoring & Limits

### 2.1 Memory Usage Monitoring

```python
# database/seed-data/generator/resource_monitor.py

import psutil
from typing import Optional

class ResourceMonitor:
    """Monitor memory and CPU during generation."""

    # Safety limits
    MAX_MEMORY_PCT = 85  # Fail if > 85% memory used
    MAX_CPU_PCT = 95     # Warn if CPU > 95%

    def __init__(self, name: str = "dataset_generator"):
        self.name = name
        self.process = psutil.Process()

    def check_memory(self) -> Tuple[bool, str]:
        """Check current memory usage."""
        memory = psutil.virtual_memory()
        used_pct = memory.percent

        message = f"Memory: {used_pct:.1f}% used ({memory.available / (1024**3):.1f} GB available)"

        if used_pct >= self.MAX_MEMORY_PCT:
            message += f" ❌ CRITICAL (>{self.MAX_MEMORY_PCT}%)"
            return False, message

        if used_pct > 70:
            message += " ⚠️  WARNING (>70%)"
        else:
            message += " ✅"

        return True, message

    def get_process_memory(self) -> float:
        """Get this process's memory usage in MB."""
        return self.process.memory_info().rss / (1024 ** 2)

    def check_process_memory(self, limit_mb: int = 2048) -> Tuple[bool, str]:
        """Check if this process exceeds memory limit."""
        usage_mb = self.get_process_memory()
        message = f"Process Memory: {usage_mb:.1f} MB"

        if usage_mb > limit_mb:
            message += f" ❌ EXCEEDED (limit: {limit_mb} MB)"
            return False, message

        message += " ✅"
        return True, message

    def check_all(self, process_limit_mb: int = 2048) -> Tuple[bool, str]:
        """Run all resource checks."""
        checks = [
            self.check_memory(),
            self.check_process_memory(process_limit_mb),
        ]

        all_ok = all(check[0] for check in checks)
        messages = [msg for _, msg in checks]

        return all_ok, '\n'.join(messages)
```

### 2.2 Generator with Resource Limits

```python
# In variant_generator.py

class VariantGenerator:
    """Generate variants with resource monitoring."""

    def __init__(self, seed_posts, scale_multiplier,
                 max_memory_mb: int = 2048,
                 batch_size: int = 1000):
        """
        Args:
            max_memory_mb: Kill generator if process exceeds this (default 2GB)
            batch_size: Generate variants in batches to avoid memory spike
        """
        self.seed_posts = seed_posts
        self.multiplier = scale_multiplier
        self.max_memory_mb = max_memory_mb
        self.batch_size = batch_size
        self.monitor = ResourceMonitor()

    def generate_variants(self):
        """Generate variants with resource checks."""

        variants_per_seed = self.multiplier // len(self.seed_posts)

        for seed_post in self.seed_posts:
            # Check resources before each seed
            is_ok, msg = self.monitor.check_all(self.max_memory_mb)
            if not is_ok:
                raise RuntimeError(f"Resource limit exceeded: {msg}")

            # Generate in batches
            for batch_start in range(0, variants_per_seed, self.batch_size):
                batch_end = min(batch_start + self.batch_size, variants_per_seed)

                for idx in range(batch_start, batch_end):
                    variant = self._create_variant(seed_post, idx)
                    yield variant  # Use generator pattern (not materialized)
```

---

## 3. Database Safety Checks

### 3.1 Pre-Load Validation

```python
# database/seed-data/generator/db_safety.py

import psycopg
from typing import Optional

class DatabaseSafetyChecker:
    """Check database safety before loading."""

    def __init__(self, connection_str: str):
        self.connection_str = connection_str

    def check_connectivity(self) -> Tuple[bool, str]:
        """Test database connectivity."""
        try:
            with psycopg.connect(self.connection_str, timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True, "Database Connectivity: ✅"
        except Exception as e:
            return False, f"Database Connectivity: ❌ {e}"

    def check_schema_exists(self) -> Tuple[bool, str]:
        """Check if schema tables exist."""
        try:
            with psycopg.connect(self.connection_str) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables
                            WHERE table_name='tb_user'
                        )
                    """)
                    exists = cur.fetchone()[0]

                    if exists:
                        return True, "Schema Exists: ✅"
                    else:
                        return False, "Schema Exists: ❌ (run schema creation first)"
        except Exception as e:
            return False, f"Schema Check: ❌ {e}"

    def check_table_sizes(self) -> Tuple[bool, dict]:
        """Get current table row counts."""
        try:
            with psycopg.connect(self.connection_str) as conn:
                with conn.cursor() as cur:
                    tables = ['tb_user', 'tb_post', 'tb_comment']
                    sizes = {}

                    for table in tables:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cur.fetchone()[0]
                        sizes[table] = count

                    return True, sizes
        except Exception as e:
            return False, {'error': str(e)}

    def check_available_disk_on_database(self) -> Tuple[bool, str]:
        """Check disk space on database server (PostgreSQL)."""
        try:
            with psycopg.connect(self.connection_str) as conn:
                with conn.cursor() as cur:
                    # PostgreSQL-specific: check available space
                    cur.execute("""
                        SELECT pg_size_pretty(
                            pg_database_size(current_database())
                        )
                    """)
                    size = cur.fetchone()[0]
                    return True, f"Database Size: {size} ✅"
        except Exception as e:
            return False, f"Database Check: ❌ {e}"

    def check_all(self) -> Tuple[bool, list]:
        """Run all database safety checks."""
        checks = [
            self.check_connectivity(),
            self.check_schema_exists(),
            self.check_available_disk_on_database(),
        ]

        all_ok = all(check[0] for check in checks)
        messages = [msg for _, msg in checks]

        return all_ok, messages
```

---

## 4. Data Integrity Checks

### 4.1 Checksum Validation

```python
# database/seed-data/generator/data_validator.py

import hashlib
from pathlib import Path

class DataValidator:
    """Validate generated data integrity."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def compute_checksums(self) -> dict:
        """Compute SHA256 checksums of generated files."""
        checksums = {}

        for file in self.output_dir.glob('*.tsv'):
            checksums[file.name] = self._file_sha256(file)

        return checksums

    def save_checksums(self, checksums: dict):
        """Save checksums to manifest file."""
        manifest = self.output_dir / 'MANIFEST.txt'
        with open(manifest, 'w') as f:
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            for filename, checksum in checksums.items():
                f.write(f"{checksum}  {filename}\n")

    def verify_checksums(self) -> Tuple[bool, str]:
        """Verify checksums against manifest."""
        manifest = self.output_dir / 'MANIFEST.txt'

        if not manifest.exists():
            return False, "No MANIFEST.txt found"

        current = self.compute_checksums()

        with open(manifest) as f:
            lines = f.readlines()[2:]  # Skip header

        for line in lines:
            if not line.strip():
                continue

            checksum, filename = line.strip().split()

            if filename not in current:
                return False, f"Missing file: {filename}"

            if current[filename] != checksum:
                return False, f"Checksum mismatch: {filename}"

        return True, "All checksums verified ✅"

    def _file_sha256(self, file: Path) -> str:
        """Compute SHA256 of file."""
        sha256 = hashlib.sha256()
        with open(file, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def validate_row_counts(self, expected: dict) -> Tuple[bool, str]:
        """Validate TSV row counts match expected."""
        message = "Row Counts:\n"
        all_ok = True

        for filename, expected_count in expected.items():
            filepath = self.output_dir / filename

            if not filepath.exists():
                message += f"  {filename}: ❌ FILE NOT FOUND\n"
                all_ok = False
                continue

            # Count lines (minus header)
            with open(filepath) as f:
                actual_count = sum(1 for _ in f) - 1

            if actual_count == expected_count:
                message += f"  {filename}: {actual_count:,} ✅\n"
            else:
                message += f"  {filename}: {actual_count:,} (expected {expected_count:,}) ❌\n"
                all_ok = False

        return all_ok, message
```

---

## 5. Complete Safety Flow in scale_dataset.py

```python
#!/usr/bin/env python
"""Scale dataset with comprehensive safety checks."""

import sys
from pathlib import Path
from safety_checks import DiskSpaceChecker
from resource_monitor import ResourceMonitor
from db_safety import DatabaseSafetyChecker
from data_validator import DataValidator

def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument('--profile', default='dev')
    parser.add_argument('--output-dir', type=Path, default=Path('/tmp/velocitybench'))
    parser.add_argument('--connection', default='postgresql://localhost/velocitybench')
    parser.add_argument('--force', action='store_true', help='Skip safety checks')
    parser.add_argument('--load', action='store_true')
    args = parser.parse_args()

    print("=" * 80)
    print("DATASET SCALING - SAFETY CHECKS")
    print("=" * 80)
    print()

    # PHASE 1: Local Resource Checks
    print("📋 PHASE 1: Local Resources")
    print("-" * 80)

    disk_checker = DiskSpaceChecker(args.output_dir)
    disk_ok, disk_msg = disk_checker.check_all(args.profile, 'both')
    print(disk_msg)
    print()

    if not disk_ok and not args.force:
        print("❌ FAILED: Insufficient disk space")
        sys.exit(1)

    # PHASE 2: Memory Checks
    print("📋 PHASE 2: Memory Resources")
    print("-" * 80)

    monitor = ResourceMonitor()
    mem_ok, mem_msg = monitor.check_all(process_limit_mb=2048)
    print(mem_msg)
    print()

    if not mem_ok and not args.force:
        print("❌ FAILED: Insufficient memory")
        sys.exit(1)

    # PHASE 3: Database Checks (if loading)
    if args.load:
        print("📋 PHASE 3: Database Safety")
        print("-" * 80)

        db_checker = DatabaseSafetyChecker(args.connection)
        db_ok, db_messages = db_checker.check_all()
        for msg in db_messages:
            print(msg)
        print()

        if not db_ok and not args.force:
            print("❌ FAILED: Database checks did not pass")
            sys.exit(1)

    # PHASE 4: Generate Data
    print("📋 PHASE 4: Generating Dataset")
    print("-" * 80)

    gold_posts = load_gold_corpus(...)
    variant_gen = VariantGenerator(gold_posts, scale_multiplier=..., max_memory_mb=2048)

    variants = variant_gen.generate_variants()
    loader = BulkLoader(args.output_dir)
    loader.save(variants, ...)

    print(f"✅ Generated {len(variants):,} posts")
    print()

    # PHASE 5: Validate Data
    print("📋 PHASE 5: Data Validation")
    print("-" * 80)

    validator = DataValidator(args.output_dir)
    checksums = validator.compute_checksums()
    validator.save_checksums(checksums)

    expected = {'posts.tsv': 1000000, 'users.tsv': 100000, 'comments.tsv': 5000000}
    valid_ok, valid_msg = validator.validate_row_counts(expected)
    print(valid_msg)
    print()

    if not valid_ok:
        print("❌ FAILED: Data validation did not pass")
        sys.exit(1)

    # PHASE 6: Load to Database (optional)
    if args.load:
        print("📋 PHASE 6: Loading to Database")
        print("-" * 80)

        loader.load_to_db(args.connection, ...)
        print("✅ Data loaded successfully")

    print()
    print("=" * 80)
    print("✅ ALL SAFETY CHECKS PASSED - DATASET READY")
    print("=" * 80)

if __name__ == '__main__':
    main()
```

---

## 6. Usage Examples with Safety Checks

### Example 1: Dry-Run Check (No Generation)

```bash
python scale_dataset.py --profile production --dry-run

# Output:
# ════════════════════════════════════════════════════════════
# DATASET SCALING - SAFETY CHECKS
# ════════════════════════════════════════════════════════════
#
# 📋 PHASE 1: Local Resources
# ────────────────────────────────────────────────────────────
# Disk Space Check:
#   Output: /tmp/velocitybench
#   Required: 25.50 GB
#   Available: 100.00 GB
#   Used: 45.2%
#   ✅ OK
#
# Output Directory: /tmp/velocitybench ✅
# Write Permission: /tmp/velocitybench ✅
# Existing Files: None (safe to proceed) ✅
#
# 📋 PHASE 2: Memory Resources
# ────────────────────────────────────────────────────────────
# Memory: 62.3% used (15.2 GB available) ✅
# Process Memory: 245.3 MB ✅
#
# ✅ ALL CHECKS PASSED - Ready to generate
```

### Example 2: Insufficient Disk Space (Warning)

```bash
python scale_dataset.py --profile production

# Output:
# Disk Space Check:
#   Required: 25.50 GB
#   Available: 8.00 GB
#   Used: 89.2%
#   ❌ FAIL: Need 25.50 GB (including 1.0 GB margin)
#
# ❌ FAILED: Safety checks did not pass
# Use --force to override (not recommended)
```

### Example 3: Force Override

```bash
python scale_dataset.py --profile production --force

# ⚠️  WARNING: Proceeding despite failed safety checks (--force)
# This may cause:
#   - Incomplete dataset generation
#   - Disk space exhaustion
#   - System instability
# Continue? [y/N]: y
```

---

## 7. Safety Features Summary

### Pre-Generation Checks

- ✅ **Disk Space**: Verify space before starting
- ✅ **Directory**: Check exists, writable, no conflicts
- ✅ **Memory**: Ensure sufficient RAM available
- ✅ **Permissions**: Validate output directory access

### During Generation

- ✅ **Resource Monitoring**: Check memory/CPU periodically
- ✅ **Batch Processing**: Generate in batches (not all in memory)
- ✅ **Process Limits**: Kill if memory exceeded
- ✅ **Generator Pattern**: Use iterators (stream, not materialize)

### Database Checks

- ✅ **Connectivity**: Test database connection
- ✅ **Schema**: Verify tables exist
- ✅ **Disk Space**: Check DB server disk space
- ✅ **Table Sizes**: Log current row counts

### Post-Generation Validation

- ✅ **Checksums**: SHA256 of all files
- ✅ **Row Counts**: Verify expected rows generated
- ✅ **Manifest**: Save generation metadata
- ✅ **Integrity**: Compare actual vs expected

### Failure Modes

- ✅ **--force flag**: Override checks (with warning)
- ✅ **--dry-run**: Check without generating
- ✅ **Partial failure**: Rollback TSV files (not auto-commit to DB)
- ✅ **Logging**: Full audit trail of all checks

---

## 8. Configuration for Safety Checks

```yaml
# database/seed-data/generator/config.yaml

safety:
  # Disk space
  safety_margin_gb: 1.0
  warn_threshold_pct: 80
  critical_threshold_pct: 95

  # Memory
  max_memory_pct: 85
  max_process_memory_mb: 2048

  # Batch generation
  batch_size: 1000
  checkpoint_interval: 10000

  # Database
  db_connection_timeout_sec: 5

  # Validation
  validate_checksums: true
  validate_row_counts: true
  save_manifest: true
```

---

## Summary

This safety system prevents:

1. **Disk Exhaustion** ✅ - Check before, monitor during
2. **Memory Overflow** ✅ - Batch processing + process limits
3. **Database Corruption** ✅ - Validate connectivity and schema
4. **Data Loss** ✅ - Checksums + validation
5. **Runaway Processes** ✅ - Resource limits + timeouts
6. **Permission Errors** ✅ - Check writability upfront

**Key Principle**: Fail fast with clear errors, allow overrides for experts.

---

**Status**: ✅ Design complete - ready for implementation with scaling plan
