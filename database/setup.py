#!/usr/bin/env python3
"""
VelocityBench Database Setup Orchestration

Sets up isolated PostgreSQL databases for each framework with:
1. Fresh PostgreSQL database per framework
2. Shared Trinity Pattern schema (schema-template.sql)
3. Framework-specific extensions (frameworks/{framework}/database/extensions.sql)
4. Seed data from YAML corpus (database/seed-data/)

Usage:
    python database/setup.py                    # Setup all frameworks (xs dataset)
    python database/setup.py postgraphile       # Setup only postgraphile
    python database/setup.py fraiseql rails     # Setup specific frameworks
    python database/setup.py --size medium      # Use medium dataset
    python database/setup.py --size large       # Use large dataset

Dataset sizes:
    xs     - 100 users, 500 posts (default, <1 second load)
    medium - 10K users, 50K posts (30-60 second load, N+1 visible)
    large  - 100K users, 500K posts (5-15 minute load, stress testing)
    blog   - 5000 users, ~2500 blog posts (~3 second load, Faker-generated users)

Environment variables:
    DB_HOST              - PostgreSQL host (default: localhost)
    DB_PORT              - PostgreSQL port (default: 5432)
    DB_ADMIN_USER        - Admin user for creating databases (default: postgres)
    DB_ADMIN_PASSWORD    - Admin password (default: postgres)
    DB_TEST_USER         - Test user for framework databases (default: velocitybench)
    DB_TEST_PASSWORD     - Test user password (default: password)
    SEED_SIZE            - Dataset size: xs, medium, large (default: xs)
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime

# List of all frameworks in the benchmark suite
FRAMEWORKS = [
    # Phase 1-3 (Completed)
    'postgraphile',
    'fraiseql',
    # Phase 4 Week 1 - Node.js (Completed)
    'apollo-server',
    'graphql-yoga',
    'fastify-graphql',
    'express-graphql',
    'mercurius',
    # Phase 4 Week 2 - Python (Completed)
    'strawberry',
    'graphene',
    'ariadne',
    'asgi-graphql',
    # Phase 4 Week 2 - Ruby (Completed)
    'rails',
    'hanami',
    # Phase 4 Week 2 - Java (Completed)
    'spring-graphql',
    'micronaut-graphql',
    'quarkus-graphql',
    'play-graphql',
    # Phase 4 Week 3 - C#/.NET (Completed)
    'hot-chocolate',
    'entity-framework-core',
    'graphql-net',
    # Phase 4 Week 3 - Go (Completed)
    'gqlgen',
    'graphql-go',
    # Phase 4 Week 3 - PHP (Completed)
    'graphql-core-php',
    'webonyx-graphql-php',
    # Phase 4 Week 3 - Rust (Completed)
    'async-graphql',
    'juniper',
]


# Valid seed data sizes
SEED_SIZES = ['xs', 'medium', 'large', 'blog']
DEFAULT_SEED_SIZE = 'xs'


@dataclass
class DatabaseConfig:
    """PostgreSQL connection configuration"""
    host: str
    port: int
    admin_user: str
    admin_password: str
    test_user: str
    test_password: str
    schema: str = 'benchmark'
    seed_size: str = DEFAULT_SEED_SIZE


class DatabaseSetup:
    """Orchestrates per-framework database setup"""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """Initialize with database configuration"""
        self.config = config or self._load_config()
        self.setup_log: List[Dict] = []
        self.project_root = Path(__file__).parent.parent

    @staticmethod
    def _load_config(seed_size: str = DEFAULT_SEED_SIZE) -> DatabaseConfig:
        """Load database configuration from environment variables"""
        size = os.getenv('SEED_SIZE', seed_size)
        if size not in SEED_SIZES:
            print(f"Warning: Invalid SEED_SIZE '{size}', using '{DEFAULT_SEED_SIZE}'")
            size = DEFAULT_SEED_SIZE

        return DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            admin_user=os.getenv('DB_ADMIN_USER', 'postgres'),
            admin_password=os.getenv('DB_ADMIN_PASSWORD', 'postgres'),
            test_user=os.getenv('DB_TEST_USER', 'velocitybench'),
            test_password=os.getenv('DB_TEST_PASSWORD', 'password'),
            seed_size=size,
        )

    def _get_admin_connection_string(self) -> str:
        """Get PostgreSQL connection string for admin user"""
        return (
            f'postgresql://{self.config.admin_user}:{self.config.admin_password}'
            f'@{self.config.host}:{self.config.port}/postgres'
        )

    def _get_framework_connection_string(self, framework: str) -> str:
        """Get PostgreSQL connection string for framework test database"""
        db_name = f'{framework}_test'
        return (
            f'postgresql://{self.config.test_user}:{self.config.test_password}'
            f'@{self.config.host}:{self.config.port}/{db_name}'
        )

    def _run_sql(self, sql: str, connection_string: str) -> bool:
        """Execute SQL command via psql"""
        try:
            result = subprocess.run(
                ['psql', connection_string, '-c', sql],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"❌ SQL command timed out: {sql[:50]}...")
            return False
        except Exception as e:
            print(f"❌ Error executing SQL: {e}")
            return False

    def _apply_sql_file(self, db_name: str, sql_file: str) -> bool:
        """Apply SQL file to database"""
        sql_path = self.project_root / sql_file
        if not sql_path.exists():
            print(f"  ⚠️  SQL file not found: {sql_file}")
            return False

        try:
            connection_string = (
                f'postgresql://{self.config.test_user}:{self.config.test_password}'
                f'@{self.config.host}:{self.config.port}/{db_name}'
            )
            result = subprocess.run(
                ['psql', connection_string, '-f', str(sql_path)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"  ❌ Error applying {sql_file}:")
                print(f"     {result.stderr[:200]}")
                return False

            return True
        except subprocess.TimeoutExpired:
            print(f"  ❌ Timeout applying {sql_file}")
            return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

    def _generate_seed_data(self, size: str) -> bool:
        """Generate seed data SQL from YAML corpus"""
        generator_path = self.project_root / 'database' / 'seed-data' / 'generator' / 'generate_sql.py'
        output_path = self.project_root / 'database' / 'seed-data' / 'output' / 'sql' / f'03-data-{size}.sql'

        if not generator_path.exists():
            print(f"  ⚠️  Seed data generator not found: {generator_path}")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(generator_path), '--size', size, '--output', str(output_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes for large dataset
                cwd=str(self.project_root)
            )

            if result.returncode != 0:
                print(f"  ⚠️  Seed data generation failed:")
                print(f"     {result.stderr[:200]}")
                return False

            return output_path.exists()
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Seed data generation timed out")
            return False
        except Exception as e:
            print(f"  ⚠️  Seed data generation error: {e}")
            return False

    def _ensure_test_user(self) -> bool:
        """Ensure test user exists with proper permissions"""
        print("\n📋 Ensuring test user exists...")

        # Check if user exists
        check_sql = f"SELECT 1 FROM pg_roles WHERE rolname='{self.config.test_user}'"
        admin_conn = self._get_admin_connection_string()

        result = subprocess.run(
            ['psql', admin_conn, '-tc', check_sql],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            print(f"  ✓ User '{self.config.test_user}' already exists")
            return True

        # Create user if it doesn't exist
        create_sql = f"""
            CREATE ROLE {self.config.test_user} WITH LOGIN PASSWORD '{self.config.test_password}';
            ALTER ROLE {self.config.test_user} CREATEDB;
        """

        if self._run_sql(create_sql, admin_conn):
            print(f"  ✓ Created user '{self.config.test_user}'")
            return True
        else:
            print(f"  ❌ Failed to create user '{self.config.test_user}'")
            return False

    def setup_framework_database(self, framework: str) -> bool:
        """
        Create and configure isolated database for a framework

        Steps:
        1. Drop existing database (if present)
        2. Create fresh database
        3. Grant permissions to test user
        4. Apply shared Trinity Pattern schema
        5. Apply framework-specific extensions
        6. Load seed data
        """
        db_name = f'{framework}_test'
        admin_conn = self._get_admin_connection_string()

        print(f"\n{'='*70}")
        print(f"Setting up: {framework}")
        print(f"{'='*70}")
        print(f"  Database: {db_name}")

        # Step 1: Drop existing database
        print(f"  1️⃣  Dropping existing database (if present)...")
        drop_sql = f"DROP DATABASE IF EXISTS {db_name};"
        if not self._run_sql(drop_sql, admin_conn):
            print(f"  ❌ Failed to drop database")
            return self._log_failure(framework, 'drop_database')

        # Step 2: Create fresh database
        print(f"  2️⃣  Creating fresh database...")
        create_sql = f"CREATE DATABASE {db_name} OWNER {self.config.test_user};"
        if not self._run_sql(create_sql, admin_conn):
            print(f"  ❌ Failed to create database")
            return self._log_failure(framework, 'create_database')

        # Step 3: Apply PostgreSQL extensions (uuid-ossp, pg_stat_statements, etc.)
        print(f"  3️⃣  Applying PostgreSQL extensions...")
        if not self._apply_sql_file(db_name, 'database/01-extensions.sql'):
            print(f"  ❌ Failed to apply extensions")
            return self._log_failure(framework, 'apply_extensions')

        # Step 4: Apply shared Trinity Pattern schema
        print(f"  4️⃣  Applying Trinity Pattern schema...")
        if not self._apply_sql_file(db_name, 'database/schema-template.sql'):
            print(f"  ❌ Failed to apply schema template")
            return self._log_failure(framework, 'apply_schema')

        # Step 5: Apply framework-specific extensions
        extensions_file = f'frameworks/{framework}/database/extensions.sql'
        extensions_path = self.project_root / extensions_file
        if extensions_path.exists():
            print(f"  5️⃣  Applying framework-specific extensions...")
            if not self._apply_sql_file(db_name, extensions_file):
                print(f"  ⚠️  Failed to apply framework extensions (continuing anyway)")
        else:
            print(f"  5️⃣  No framework-specific extensions found (skipping)")

        # Step 6: Load seed data (size-appropriate from corpus)
        if self.config.seed_size == 'blog':
            # Use blog post loader (generates Faker users + loads blog posts)
            print(f"  6️⃣  Loading blog dataset (5000 users, ~2500 posts)...")
            loader_path = self.project_root / 'database' / 'seed-data' / 'generator' / 'load_blog_posts.py'

            if not loader_path.exists():
                print(f"  ❌ Blog loader not found: {loader_path}")
                print(f"  ⚠️  Failed to load blog data")
            else:
                try:
                    # Use uv run to execute with the database/.venv environment
                    result = subprocess.run(
                        [
                            'uv',
                            'run',
                            '--directory',
                            str(self.project_root / 'database'),
                            'python',
                            str(loader_path),
                            '--connection',
                            self._get_framework_connection_string(framework)
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120  # 2 minutes timeout for blog loading
                    )

                    if result.returncode != 0:
                        print(f"  ❌ Blog post loading failed:")
                        print(f"     {result.stderr}")
                        print(f"  ⚠️  Failed to load seed data (continuing anyway)")
                    else:
                        print(f"  ✓ Blog posts loaded successfully")
                        # Print summary from loader
                        if "SUMMARY" in result.stdout:
                            summary_lines = result.stdout.split("SUMMARY")[1].split("TSV files")[0]
                            print(f"     {summary_lines.strip()}")

                except subprocess.TimeoutExpired:
                    print(f"  ⚠️  Blog loading timed out (continuing anyway)")
                except Exception as e:
                    print(f"  ⚠️  Blog loading error: {e}")
        else:
            # Standard SQL-based seed data (xs, medium, large)
            seed_file = f'database/seed-data/output/sql/03-data-{self.config.seed_size}.sql'
            seed_path = self.project_root / seed_file

            # Generate seed data if it doesn't exist
            if not seed_path.exists():
                print(f"  6️⃣  Generating seed data ({self.config.seed_size})...")
                if not self._generate_seed_data(self.config.seed_size):
                    # Fall back to legacy seed file if generation fails
                    seed_file = 'database/03-data.sql'
                    print(f"  ⚠️  Generation failed, trying legacy seed file...")

            print(f"  6️⃣  Loading seed data ({self.config.seed_size})...")
            if not self._apply_sql_file(db_name, seed_file):
                print(f"  ⚠️  Failed to load seed data (continuing anyway)")

        # Success
        print(f"✅ {framework} database ready ({db_name})")
        return self._log_success(framework)

    def setup_all(self, frameworks: Optional[List[str]] = None) -> bool:
        """Setup all or specified frameworks sequentially"""
        to_setup = frameworks or FRAMEWORKS

        if not to_setup:
            print("❌ No frameworks to setup")
            return False

        print(f"\n🚀 VelocityBench Database Setup")
        print(f"   Frameworks to setup: {', '.join(to_setup)}")
        print(f"   PostgreSQL: {self.config.host}:{self.config.port}")

        # Ensure test user exists
        if not self._ensure_test_user():
            print("❌ Failed to ensure test user exists")
            return False

        # Setup each framework
        success_count = 0
        for framework in to_setup:
            if self.setup_framework_database(framework):
                success_count += 1

        # Print summary
        self._print_summary(to_setup, success_count)
        return success_count == len(to_setup)

    def _log_success(self, framework: str) -> bool:
        """Log successful setup"""
        self.setup_log.append({
            'framework': framework,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        })
        return True

    def _log_failure(self, framework: str, stage: str) -> bool:
        """Log failed setup"""
        self.setup_log.append({
            'framework': framework,
            'status': 'failure',
            'stage': stage,
            'timestamp': datetime.now().isoformat()
        })
        return False

    def _print_summary(self, frameworks: List[str], success_count: int) -> None:
        """Print setup summary"""
        failed_count = len(frameworks) - success_count

        print(f"\n{'='*70}")
        print(f"SUMMARY")
        print(f"{'='*70}")
        print(f"  ✅ Successful: {success_count}/{len(frameworks)}")
        print(f"  ❌ Failed: {failed_count}/{len(frameworks)}")

        if failed_count > 0:
            print(f"\n  Failed frameworks:")
            for entry in self.setup_log:
                if entry['status'] == 'failure':
                    print(f"    - {entry['framework']} ({entry.get('stage', 'unknown')})")

        # Save log
        log_file = self.project_root / 'setup-log.json'
        with open(log_file, 'w') as f:
            json.dump(self.setup_log, f, indent=2)
        print(f"\n  Setup log saved to: {log_file}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='VelocityBench Database Setup - Creates isolated databases for each framework'
    )
    parser.add_argument(
        'frameworks',
        nargs='*',
        help='Specific frameworks to setup (default: all frameworks)'
    )
    parser.add_argument(
        '--size',
        choices=SEED_SIZES,
        default=DEFAULT_SEED_SIZE,
        help=f'Dataset size: xs (100 users), medium (10K users), large (100K users), blog (5K users + ~2500 posts). Default: {DEFAULT_SEED_SIZE}'
    )
    parser.add_argument(
        '--generate-only',
        action='store_true',
        help='Only generate seed data SQL files, do not setup databases'
    )

    args = parser.parse_args()

    # Handle generate-only mode
    if args.generate_only:
        print(f"Generating seed data for size: {args.size}")
        config = DatabaseConfig(
            host='', port=0, admin_user='', admin_password='',
            test_user='', test_password='', seed_size=args.size
        )
        setup = DatabaseSetup(config)
        if setup._generate_seed_data(args.size):
            print(f"✅ Generated: database/seed-data/output/sql/03-data-{args.size}.sql")
            sys.exit(0)
        else:
            print(f"❌ Failed to generate seed data")
            sys.exit(1)

    # Create config with seed size
    config = DatabaseSetup._load_config(args.size)
    setup = DatabaseSetup(config)

    # Run setup
    frameworks = args.frameworks if args.frameworks else None
    success = setup.setup_all(frameworks)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
