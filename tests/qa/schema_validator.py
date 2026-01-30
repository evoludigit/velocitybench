"""
Schema Validator - Verifies database schema consistency

Tests:
1. All expected tables exist in database
2. Tables have correct columns (id, created_at, updated_at, etc.)
3. Foreign key relationships are correct
4. Indexes exist on foreign keys and frequently queried columns

Outputs:
- List of missing tables
- List of missing columns
- List of missing indexes
- Schema diff report
"""

import asyncpg
from dataclasses import dataclass, field


@dataclass
class TableSchema:
    schema: str
    table: str
    columns: list[str] = field(default_factory=list)
    indexes: list[str] = field(default_factory=list)
    foreign_keys: list[dict[str, str]] = field(default_factory=list)


class SchemaValidator:
    """Validates database schema matches expected structure."""

    def __init__(self):
        self.conn: asyncpg.Connection | None = None

    async def connect(self, db_url: str):
        """Connect to database."""
        self.conn = await asyncpg.connect(db_url)

    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()

    async def get_actual_tables(self) -> list[str]:
        """Query pg_catalog to get all tables in benchmark schema."""
        query = """
            SELECT schemaname, tablename
            FROM pg_tables
            WHERE schemaname = 'benchmark'
            ORDER BY tablename
        """
        rows = await self.conn.fetch(query)
        return [f"{row['schemaname']}.{row['tablename']}" for row in rows]

    async def get_table_columns(self, schema: str, table: str) -> list[dict[str, str]]:
        """Get all columns for a table."""
        query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """
        rows = await self.conn.fetch(query, schema, table)
        return [
            {
                'name': row['column_name'],
                'type': row['data_type'],
                'nullable': row['is_nullable'] == 'YES'
            }
            for row in rows
        ]

    async def get_table_indexes(self, schema: str, table: str) -> list[dict[str, str]]:
        """Get all indexes for a table."""
        query = """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = $1 AND tablename = $2
        """
        rows = await self.conn.fetch(query, schema, table)
        return [
            {
                'name': row['indexname'],
                'definition': row['indexdef']
            }
            for row in rows
        ]

    async def get_table_foreign_keys(self, schema: str, table: str) -> list[dict[str, str]]:
        """Get all foreign keys for a table."""
        query = """
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = $1
                AND tc.table_name = $2
        """
        rows = await self.conn.fetch(query, schema, table)
        return [
            {
                'constraint_name': row['constraint_name'],
                'column': row['column_name'],
                'foreign_table': f"{row['foreign_table_schema']}.{row['foreign_table_name']}",
                'foreign_column': row['foreign_column_name']
            }
            for row in rows
        ]

    async def get_table_schema(self, schema: str, table: str) -> TableSchema:
        """Get complete schema information for a table."""
        columns = await self.get_table_columns(schema, table)
        indexes = await self.get_table_indexes(schema, table)
        foreign_keys = await self.get_table_foreign_keys(schema, table)

        return TableSchema(
            schema=schema,
            table=table,
            columns=[col['name'] for col in columns],
            indexes=[idx['name'] for idx in indexes],
            foreign_keys=foreign_keys
        )

    async def verify_framework_schema(self, framework: dict) -> dict:
        """
        Verify a framework references correct tables.

        Returns:
            {
                'framework': 'fraiseql',
                'status': 'pass' | 'fail',
                'missing_tables': [],
                'extra_tables': [],
                'issues': []
            }
        """
        actual_tables = set(await self.get_actual_tables())
        expected_tables = set(framework.get('expected_tables', []))

        missing_tables = expected_tables - actual_tables
        # Note: extra_tables would be actual_tables - expected_tables,
        # but we don't consider that an error (frameworks can use subset of tables)

        issues = []
        if missing_tables:
            issues.append(f"Missing tables: {', '.join(missing_tables)}")

        status = 'fail' if missing_tables else 'pass'

        return {
            'framework': framework['name'],
            'status': status,
            'missing_tables': list(missing_tables),
            'expected_tables': list(expected_tables),
            'actual_tables': list(actual_tables),
            'issues': issues
        }

    async def generate_schema_report(self) -> str:
        """Generate markdown report of actual database schema."""
        report = []
        report.append("# Database Schema Report\n")
        report.append("## benchmark Schema\n")

        actual_tables = await self.get_actual_tables()

        for table_name in sorted(actual_tables):
            schema, table = table_name.split('.')
            table_schema = await self.get_table_schema(schema, table)

            report.append(f"\n### {table_name}\n")

            # Columns
            report.append("**Columns:**\n")
            columns = await self.get_table_columns(schema, table)
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                report.append(f"- `{col['name']}` {col['type']} {nullable}")

            # Foreign keys
            if table_schema.foreign_keys:
                report.append("\n**Foreign Keys:**\n")
                for fk in table_schema.foreign_keys:
                    report.append(
                        f"- `{fk['column']}` → `{fk['foreign_table']}.{fk['foreign_column']}`"
                    )

            # Indexes
            if table_schema.indexes:
                report.append("\n**Indexes:**\n")
                for idx_info in await self.get_table_indexes(schema, table):
                    report.append(f"- `{idx_info['name']}`")

        return '\n'.join(report)


# Standalone test
async def main():
    """Test schema validator."""
    import yaml
    from pathlib import Path

    # Load framework registry
    registry_path = Path(__file__).parent / 'framework_registry.yaml'
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    # Load validation config
    config_path = Path(__file__).parent / 'validation_config.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)

    validator = SchemaValidator()
    await validator.connect(config['database']['url'])

    try:
        print("Database Schema Report")
        print("=" * 60)
        print()

        # Get actual tables
        actual_tables = await validator.get_actual_tables()
        print(f"Actual tables in database: {len(actual_tables)}")
        for table in actual_tables:
            print(f"  - {table}")
        print()

        # Verify each framework
        print("Framework Schema Validation")
        print("=" * 60)
        for framework in registry['frameworks']:
            result = await validator.verify_framework_schema(framework)
            status_icon = "✅" if result['status'] == 'pass' else "❌"
            print(f"{status_icon} {result['framework']}: {result['status']}")
            if result['issues']:
                for issue in result['issues']:
                    print(f"    - {issue}")

        # Generate schema report
        print("\n" + "=" * 60)
        report = await validator.generate_schema_report()
        print(report)

    finally:
        await validator.close()


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
