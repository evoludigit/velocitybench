#!/usr/bin/env python
"""
VelocityBench Dataset Scaling System

Scale blog post dataset from 5K gold corpus to 1M posts with parameterized variants.
Generates lightweight variants (different metadata, same body) for realistic query patterns.

Usage:
    # Generate 1M posts with 200x multiplier (5K × 200)
    python scale_dataset.py --scale-multiplier 200 --output-dir /tmp/velocitybench

    # Explicit sizing
    python scale_dataset.py --posts 100000 --users 10000 --output-dir /tmp/velocitybench

    # Use preset profile
    python scale_dataset.py --profile dev --output-dir /tmp/velocitybench

    # Load to database after generation
    python scale_dataset.py --profile production --load --connection "postgresql://..."

    # Dry run (validate without generating)
    python scale_dataset.py --profile dev --dry-run

    # Force generation despite safety warnings
    python scale_dataset.py --profile production --force

Environment:
    VELOCITYBENCH_SEED_DIR: Path to gold corpus (default: database/seed-data/gold-corpus)
    VELOCITYBENCH_OUTPUT_DIR: Path for generated files (default: /tmp/velocitybench)
"""

import argparse
import sys
import time
import yaml
from pathlib import Path
from typing import Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules
from variant_generator import VariantGenerator
from bulk_loader import BulkLoader
from disk_space_checker import DiskSpaceChecker
from resource_monitor import ResourceMonitor
from database_safety_checker import DatabaseSafetyChecker
from data_validator import DataValidator


class ScaleDatasetConfig:
    """Configuration for dataset scaling with profile support."""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Load configuration from YAML.

        Args:
            config_file: Path to config.yaml (default: same directory as scale_dataset.py)
        """
        if config_file is None:
            config_file = Path(__file__).parent / 'config.yaml'

        self.config_file = config_file
        self.config = self._load_config()
        self.profiles = self.config.get('profiles', {})
        self.safety = self.config.get('safety', {})

    def _load_config(self) -> dict[str, any]:
        """Load YAML configuration file."""
        if not self.config_file.exists():
            logger.warning(f"Config file not found: {self.config_file}")
            return {}

        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def get_profile(self, profile_name: str) -> dict[str, any]:
        """Get configuration for a profile."""
        if profile_name not in self.profiles:
            raise ValueError(f"Unknown profile: {profile_name}. Available: {list(self.profiles.keys())}")
        return self.profiles[profile_name]

    def get_safety_settings(self) -> dict[str, any]:
        """Get safety check settings."""
        return {
            'safety_margin_gb': self.safety.get('safety_margin_gb', 1.0),
            'warn_threshold_pct': self.safety.get('warn_threshold_pct', 80),
            'critical_threshold_pct': self.safety.get('critical_threshold_pct', 95),
            'max_memory_pct': self.safety.get('max_memory_pct', 85),
            'max_process_memory_mb': self.safety.get('max_process_memory_mb', 2048),
            'batch_size': self.safety.get('batch_size', 1000),
        }


class ScaleDatasetSystem:
    """Main system for scaling dataset from gold corpus to parameterized size."""

    def __init__(self, seed_dir: Path, output_dir: Path, config: ScaleDatasetConfig):
        """
        Initialize scaling system.

        Args:
            seed_dir: Path to gold corpus (5K seed posts)
            output_dir: Path for generated files (git-ignored)
            config: ScaleDatasetConfig instance
        """
        self.seed_dir = Path(seed_dir)
        self.output_dir = Path(output_dir)
        self.config = config
        self.stats = {}

    def resolve_scale_parameters(
        self,
        scale_multiplier: Optional[int] = None,
        posts: Optional[int] = None,
        users: Optional[int] = None,
        comments: Optional[int] = None,
        profile: Optional[str] = None,
    ) -> dict[str, any]:
        """
        Resolve scale parameters from multiplier, explicit values, or profile.

        Priority: Explicit args > Profile > Defaults

        Args:
            scale_multiplier: Multiplier (5K posts × multiplier = total posts)
            posts: Explicit post count
            users: Explicit user count
            comments: Explicit comment count
            profile: Preset profile name (tiny/dev/staging/production)

        Returns:
            dict with: posts, users, comments, seed_posts
        """
        # Default: use dev profile
        if not any([scale_multiplier, posts, profile]):
            profile = 'dev'

        # Load profile if specified
        if profile:
            profile_config = self.config.get_profile(profile)
            posts = profile_config.get('posts')
            users = profile_config.get('users')
            comments = profile_config.get('comments')
        elif scale_multiplier:
            # Calculate from multiplier (5K seed × multiplier)
            posts = 5000 * scale_multiplier
            users = users or (int(100000 * (scale_multiplier / 200)))  # Scale users proportionally
            comments = comments or (int(5000000 * (scale_multiplier / 200)))
        elif posts:
            # Auto-scale users and comments proportionally
            multiplier = posts / 5000
            users = users or int(100000 * multiplier)
            comments = comments or int(5000000 * multiplier)

        return {
            'posts': posts or 5000,  # Default to dev
            'users': users or 500,
            'comments': comments or 25000,
            'seed_posts': 5000,
            'profile': profile,
        }

    def check_safety(
        self,
        scale_params: dict[str, any],
        format: str = 'both',
        dry_run: bool = False,
        force: bool = False,
    ) -> tuple[bool, list[str]]:
        """
        Run all safety checks before generation.

        Args:
            scale_params: Scale parameters from resolve_scale_parameters
            format: Output format ('tsv', 'sql', or 'both')
            dry_run: Skip database connectivity check if True
            force: Ignore warnings if True

        Returns:
            (is_safe: bool, messages: list[str])
        """
        messages = []

        # Phase 1: Local disk space
        disk_checker = DiskSpaceChecker(self.output_dir)
        disk_ok, disk_msg = disk_checker.check_all(scale_params['posts'], format)
        messages.append(disk_msg)
        if not disk_ok:
            return (False, messages) if not force else (True, messages)

        # Phase 2: Memory resources
        monitor = ResourceMonitor()
        mem_ok, mem_msg = monitor.check_all(process_limit_mb=2048)
        messages.append(mem_msg)
        if not mem_ok:
            return (False, messages) if not force else (True, messages)

        return (True, messages)

    def run(
        self,
        scale_multiplier: Optional[int] = None,
        posts: Optional[int] = None,
        users: Optional[int] = None,
        comments: Optional[int] = None,
        profile: Optional[str] = None,
        format: str = 'both',
        load: bool = False,
        connection_string: Optional[str] = None,
        dry_run: bool = False,
        force: bool = False,
    ) -> dict[str, any]:
        """
        Main execution: resolve parameters, check safety, generate, optionally load.

        Args:
            scale_multiplier: Multiplier for 5K corpus
            posts: Explicit post count
            users: Explicit user count
            comments: Explicit comment count
            profile: Preset profile name
            format: Output format ('tsv', 'sql', 'both')
            load: Load to database after generation
            connection_string: PostgreSQL connection string
            dry_run: Validate only, no generation
            force: Ignore safety warnings

        Returns:
            Statistics dict
        """
        start_time = time.time()

        logger.info("=" * 70)
        logger.info("VelocityBench Dataset Scaling System")
        logger.info("=" * 70)

        # Step 1: Resolve scale parameters
        logger.info("\n[1/6] Resolving scale parameters...")
        scale_params = self.resolve_scale_parameters(
            scale_multiplier=scale_multiplier,
            posts=posts,
            users=users,
            comments=comments,
            profile=profile,
        )
        logger.info(f"  Profile: {scale_params['profile'] or 'custom'}")
        logger.info(f"  Posts: {scale_params['posts']:,}")
        logger.info(f"  Users: {scale_params['users']:,}")
        logger.info(f"  Comments: {scale_params['comments']:,}")
        logger.info(f"  Output: {self.output_dir}")
        logger.info(f"  Format: {format}")

        # Step 2: Check safety
        logger.info("\n[2/6] Checking safety...")
        is_safe, safety_messages = self.check_safety(scale_params, format, dry_run, force)
        for msg in safety_messages:
            logger.info(f"  {msg}")

        if not is_safe:
            logger.error("\n❌ Safety checks failed. Use --force to override.")
            return {'success': False, 'error': 'Safety checks failed', 'duration': time.time() - start_time}

        if dry_run:
            logger.info("\n⚠️  DRY RUN - No generation")
            return {'success': True, 'dry_run': True, 'duration': time.time() - start_time}

        # Step 3: Create output directory
        logger.info("\n[3/6] Preparing output directory...")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✓ {self.output_dir}")

        # Step 4: Generate variants
        logger.info("\n[4/6] Generating variant posts...")
        gen = VariantGenerator(self.seed_dir, scale_params)
        gen_success, gen_stats = gen.generate(self.output_dir, format=format)

        if not gen_success:
            logger.error("❌ Variant generation failed")
            return {'success': False, 'error': 'Generation failed', 'duration': time.time() - start_time}

        logger.info(f"  ✓ Generated {gen_stats['posts_generated']:,} posts")
        if gen_stats['users_generated'] > 0:
            logger.info(f"  ✓ Generated {gen_stats['users_generated']:,} users")
        if gen_stats['comments_generated'] > 0:
            logger.info(f"  ✓ Generated {gen_stats['comments_generated']:,} comments")

        # Step 5: Validate generated data
        logger.info("\n[5/6] Validating generated data...")
        validator = DataValidator(self.output_dir)
        valid_ok, valid_msg = validator.validate_row_counts({
            'posts': gen_stats['posts_generated'],
            'users': gen_stats['users_generated'],
        })
        logger.info(f"  {valid_msg}")

        if not valid_ok:
            logger.warning("❌ Validation failed")
            return {'success': False, 'error': 'Validation failed', 'duration': time.time() - start_time}

        # Step 6: Load to database (optional)
        if load and connection_string:
            logger.info("\n[6/6] Loading to database...")
            loader = BulkLoader(self.output_dir)
            load_ok, load_stats = loader.load_to_postgres(connection_string)

            if load_ok:
                logger.info(f"  ✓ Loaded {load_stats['posts_loaded']:,} posts")
                logger.info(f"  ✓ Loaded {load_stats['users_loaded']:,} users")
            else:
                logger.error("❌ Database loading failed")
                return {'success': False, 'error': 'Loading failed', 'duration': time.time() - start_time}
        else:
            logger.info("\n[6/6] Database loading skipped (no --load)")

        # Success summary
        elapsed = time.time() - start_time
        logger.info(f"\n{'=' * 70}")
        logger.info("COMPLETE ✅")
        logger.info(f"{'=' * 70}")
        logger.info(f"Posts: {gen_stats['posts_generated']:,}")
        logger.info(f"Users: {gen_stats['users_generated']:,}")
        logger.info(f"Comments: {gen_stats['comments_generated']:,}")
        logger.info(f"Duration: {elapsed:.2f}s")
        logger.info(f"Output: {self.output_dir}")

        return {
            'success': True,
            'posts_generated': gen_stats['posts_generated'],
            'users_generated': gen_stats['users_generated'],
            'comments_generated': gen_stats['comments_generated'],
            'duration': elapsed,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Scale VelocityBench dataset from 5K gold corpus to 1M posts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Scale Modes:
  1. Multiplier (simplest):
     --scale-multiplier 200          # 5K × 200 = 1M posts

  2. Explicit (most flexible):
     --posts 1000000 --users 100000 --comments 5000000

  3. Profile (presets):
     --profile dev           # 5K posts, 500 users, 25K comments
     --profile staging       # 50K posts, 5K users, 250K comments
     --profile production    # 1M posts, 100K users, 5M comments

Examples:
  # Generate 1M posts (default)
  python scale_dataset.py --scale-multiplier 200

  # Generate for dev environment
  python scale_dataset.py --profile dev --output-dir /tmp/velocitybench

  # Generate and load to database
  python scale_dataset.py --profile production \\
    --load --connection "postgresql://user:pass@localhost/velocitybench"

  # Dry run (validate only)
  python scale_dataset.py --profile dev --dry-run

  # Force generation despite safety warnings
  python scale_dataset.py --scale-multiplier 200 --force
        """
    )

    # Scale parameters (mutually exclusive but not enforced)
    scale_group = parser.add_argument_group('scale_parameters', 'Choose one method to specify scale')
    scale_group.add_argument(
        '--scale-multiplier',
        type=int,
        help='Multiplier for 5K seed posts (e.g., 200 = 1M posts)'
    )
    scale_group.add_argument(
        '--posts',
        type=int,
        help='Explicit number of posts to generate'
    )
    scale_group.add_argument(
        '--users',
        type=int,
        help='Explicit number of users (auto-scales with --posts if not specified)'
    )
    scale_group.add_argument(
        '--comments',
        type=int,
        help='Explicit number of comments (auto-scales with --posts if not specified)'
    )
    scale_group.add_argument(
        '--profile',
        choices=['tiny', 'dev', 'staging', 'production'],
        help='Use preset profile configuration'
    )

    # Options
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('/tmp/velocitybench'),
        help='Output directory for generated files (default: /tmp/velocitybench)'
    )
    parser.add_argument(
        '--format',
        choices=['tsv', 'sql', 'both'],
        default='both',
        help='Output format (default: both TSV and SQL)'
    )

    # Database loading
    parser.add_argument(
        '--load',
        action='store_true',
        help='Load generated data to database'
    )
    parser.add_argument(
        '--connection',
        type=str,
        help='PostgreSQL connection string (required if --load)'
    )

    # Safety/control
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate without generating'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Ignore safety warnings'
    )

    # Advanced
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to config.yaml (default: same directory as script)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.load and not args.connection:
        parser.error("--connection required when using --load")

    # Load configuration
    try:
        config = ScaleDatasetConfig(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Determine seed directory
    seed_dir = Path(__file__).parent.parent / 'gold-corpus'
    if not seed_dir.exists():
        logger.warning(f"Gold corpus not found at {seed_dir}")
        logger.info("Will generate synthetic seed posts instead")

    # Run scaling system
    try:
        system = ScaleDatasetSystem(seed_dir, args.output_dir, config)

        stats = system.run(
            scale_multiplier=args.scale_multiplier,
            posts=args.posts,
            users=args.users,
            comments=args.comments,
            profile=args.profile,
            format=args.format,
            load=args.load,
            connection_string=args.connection,
            dry_run=args.dry_run,
            force=args.force,
        )

        if stats.get('success'):
            logger.info("\n✅ Dataset scaling complete!")
            sys.exit(0)
        else:
            logger.error(f"\n❌ {stats.get('error', 'Unknown error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.error("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
