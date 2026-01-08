#!/usr/bin/env python3
"""
Concatenate XXS and XS databases into XXLarge.
This script merges two SQLite databases while adjusting primary keys and unique fields.

Usage:
    python database/concatenate-databases.py [source1_db] [source2_db] [output_db]

Example:
    python database/concatenate-databases.py datasets/fraiseql_xxs.db datasets/fraiseql_xs.db datasets/fraiseql_xxlarge.db
"""

import sqlite3
import sys
import uuid
from pathlib import Path


def concatenate_databases(db1_path: str, db2_path: str, output_path: str):
    """Concatenate two SQLite databases into one, adjusting primary keys and unique fields."""

    print("=" * 70)
    print("DATABASE CONCATENATION")
    print("=" * 70)

    # Open databases
    db1 = sqlite3.connect(db1_path)
    db2 = sqlite3.connect(db2_path)
    output = sqlite3.connect(output_path)

    # Disable foreign keys for bulk operations
    output.execute("PRAGMA foreign_keys = OFF")

    try:
        # Get table info from first database (skip internal SQLite tables)
        cursor1 = db1.cursor()
        cursor1.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor1.fetchall()]

        print(f"\nTables to concatenate: {', '.join(tables)}")

        # First, create schema from first database
        print("\nCreating schema from first database...")
        cursor1.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        for row in cursor1.fetchall():
            if row[0]:
                output.execute(row[0])
        output.commit()
        print("✓ Schema created")

        # Get max primary keys from first database
        pk_map = {}
        cursor1 = db1.cursor()

        for table in tables:
            cursor1.execute(f"SELECT MAX(rowid) FROM {table}")
            max_pk = cursor1.fetchone()[0] or 0
            pk_map[table] = max_pk

        print(f"\nMax primary keys from first database:")
        for table, max_pk in pk_map.items():
            print(f"  {table}: {max_pk}")

        # Copy data from first database
        print("\nCopying data from first database...")
        for table in tables:
            cursor1.execute(f"SELECT * FROM {table}")
            rows = cursor1.fetchall()

            if rows:
                # Get column count
                num_cols = len(rows[0])
                placeholders = ', '.join(['?' for _ in range(num_cols)])

                cursor_out = output.cursor()
                cursor_out.executemany(
                    f"INSERT INTO {table} VALUES ({placeholders})",
                    rows
                )
                output.commit()
                print(f"  ✓ {table}: {len(rows)} rows")
            else:
                print(f"  ✓ {table}: 0 rows")

        # Copy data from second database, adjusting primary keys and unique fields
        print("\nCopying data from second database (adjusting keys and unique fields)...")
        cursor2 = db2.cursor()

        for table in tables:
            cursor2.execute(f"SELECT * FROM {table}")
            rows = cursor2.fetchall()

            if rows:
                # Get column info
                cursor2.execute(f"PRAGMA table_info({table})")
                columns = cursor2.fetchall()

                # Find column indices for special handling
                pk_idx = None
                unique_indices = {}

                for i, col in enumerate(columns):
                    col_name = col[1]
                    if col[5] > 0:  # pk > 0 means primary key
                        pk_idx = i
                    # Check for UNIQUE constraints
                    if table == 'users' and col_name in ['id', 'identifier', 'email', 'username']:
                        unique_indices[col_name] = i
                    elif table == 'posts' and col_name in ['id', 'identifier']:
                        unique_indices[col_name] = i
                    elif table == 'comments' and col_name == 'id':
                        unique_indices[col_name] = i

                # Adjust rows
                adjusted_rows = []
                for row in rows:
                    row_list = list(row)

                    # Adjust primary key
                    if pk_idx is not None:
                        row_list[pk_idx] = row_list[pk_idx] + pk_map[table]

                    # Adjust unique fields
                    if table == 'users':
                        user_offset = pk_map['users']
                        if 'id' in unique_indices:
                            row_list[unique_indices['id']] = str(uuid.uuid4())
                        if 'identifier' in unique_indices:
                            row_list[unique_indices['identifier']] = f"{row_list[unique_indices['identifier']]}_{user_offset}"
                        if 'email' in unique_indices:
                            parts = row_list[unique_indices['email']].split('@')
                            row_list[unique_indices['email']] = f"{parts[0]}_xs{user_offset}@{parts[1]}"
                        if 'username' in unique_indices:
                            row_list[unique_indices['username']] = f"{row_list[unique_indices['username']]}_xs{user_offset}"

                    elif table == 'posts':
                        if 'id' in unique_indices:
                            row_list[unique_indices['id']] = str(uuid.uuid4())
                        if 'identifier' in unique_indices:
                            row_list[unique_indices['identifier']] = f"{row_list[unique_indices['identifier']]}_{pk_map['posts']}"

                    elif table == 'comments':
                        if 'id' in unique_indices:
                            row_list[unique_indices['id']] = str(uuid.uuid4())

                    adjusted_rows.append(tuple(row_list))

                num_cols = len(adjusted_rows[0])
                placeholders = ', '.join(['?' for _ in range(num_cols)])

                cursor_out = output.cursor()
                cursor_out.executemany(
                    f"INSERT INTO {table} VALUES ({placeholders})",
                    adjusted_rows
                )
                output.commit()
                print(f"  ✓ {table}: {len(adjusted_rows)} rows")
            else:
                print(f"  ✓ {table}: 0 rows")

        # Re-enable foreign keys
        output.execute("PRAGMA foreign_keys = ON")

        # Optimize output database
        print("\nOptimizing output database...")
        output.execute("VACUUM")
        output.execute("ANALYZE")
        output.commit()
        print("✓ Database optimized")

        # Validate concatenation
        print("\nValidating concatenation...")
        cursor_out = output.cursor()

        for table in tables:
            cursor_out.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor_out.fetchone()[0]

            cursor1.execute(f"SELECT COUNT(*) FROM {table}")
            count1 = cursor1.fetchone()[0]

            cursor2.execute(f"SELECT COUNT(*) FROM {table}")
            count2 = cursor2.fetchone()[0]

            expected = count1 + count2
            status = "✓" if count == expected else "❌"
            print(f"  {status} {table}: {count} rows (expected: {expected} = {count1} + {count2})")

        # Report final size
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        size_str = f"{size_mb:.1f}MB" if size_mb < 1024 else f"{size_mb/1024:.1f}GB"
        print(f"\n✓ Output database: {size_str}")

        print("\n" + "=" * 70)
        print("✅ CONCATENATION COMPLETE")
        print("=" * 70)

    finally:
        db1.close()
        db2.close()
        output.close()


if __name__ == "__main__":
    db1_path = sys.argv[1] if len(sys.argv) > 1 else "datasets/fraiseql_xxs.db"
    db2_path = sys.argv[2] if len(sys.argv) > 2 else "datasets/fraiseql_xs.db"
    output_path = sys.argv[3] if len(sys.argv) > 3 else "datasets/fraiseql_xxlarge.db"

    if not Path(db1_path).exists():
        print(f"Error: {db1_path} not found")
        sys.exit(1)

    if not Path(db2_path).exists():
        print(f"Error: {db2_path} not found")
        sys.exit(1)

    # Remove output if it exists
    if Path(output_path).exists():
        Path(output_path).unlink()
        print(f"Removed existing {output_path}\n")

    print(f"Source 1: {db1_path}")
    print(f"Source 2: {db2_path}")
    print(f"Output:   {output_path}\n")

    concatenate_databases(db1_path, db2_path, output_path)
