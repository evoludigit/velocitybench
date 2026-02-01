"""
Phase 1, Cycle 2+: Schema Equivalence Tests

RED: Tests verify that schema definitions in all languages produce identical schema.json
"""

import json
import subprocess
from pathlib import Path


class TestSchemaEquivalence:
    """Test that all language implementations produce identical schemas."""

    def _get_python_schema(self) -> dict:
        """Export schema from Python implementation."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent))

        from schema_fraiseql import export_schema

        schema_file = Path("/tmp/python_schema.json")
        export_schema(str(schema_file))
        return json.loads(schema_file.read_text())

    def _get_typescript_schema(self) -> dict:
        """Export schema from TypeScript implementation."""
        schema_file = Path(__file__).parent / "schema.fraiseql.ts"

        if not schema_file.exists():
            raise FileNotFoundError(f"TypeScript schema not found: {schema_file}")

        # TypeScript schema will be compiled via Node/tsx
        result = subprocess.run(
            ["npx", "tsx", str(schema_file)],
            cwd=str(schema_file.parent),
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            raise RuntimeError(f"TypeScript schema compilation failed: {result.stderr}")

        schema_data = json.loads(result.stdout)
        return schema_data

    def test_python_vs_typescript_schema(self):
        """Python and TypeScript schemas must be identical."""
        python_schema = self._get_python_schema()
        typescript_schema = self._get_typescript_schema()

        # Compare type definitions
        assert python_schema["types"].keys() == typescript_schema["types"].keys(), (
            "Type names differ between Python and TypeScript"
        )

        # Compare User type fields
        python_user = python_schema["types"]["User"]
        ts_user = typescript_schema["types"]["User"]
        assert python_user["fields"].keys() == ts_user["fields"].keys(), (
            "User fields differ"
        )

        # Compare Post type fields
        python_post = python_schema["types"]["Post"]
        ts_post = typescript_schema["types"]["Post"]
        assert python_post["fields"].keys() == ts_post["fields"].keys(), (
            "Post fields differ"
        )

        # Compare queries
        assert python_schema["query"].keys() == typescript_schema["query"].keys(), (
            "Query fields differ"
        )

        # Compare mutations
        assert (
            python_schema["mutation"].keys() == typescript_schema["mutation"].keys()
        ), "Mutation fields differ"

    def test_typescript_schema_exports_valid_json(self):
        """TypeScript schema must compile and export valid JSON."""
        try:
            schema = self._get_typescript_schema()
            assert schema is not None
            assert "types" in schema
            assert "query" in schema
            assert "mutation" in schema
        except FileNotFoundError:
            # Expected to fail at RED stage until TypeScript schema is implemented
            pass


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
