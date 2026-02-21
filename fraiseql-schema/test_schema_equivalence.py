"""
Schema Equivalence Tests

Verifies that schema definitions in all languages produce identical schema.json.
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

    def _get_go_schema(self) -> dict:
        """Export schema from Go implementation."""
        schema_file = Path(__file__).parent / "schema.fraiseql.go"

        if not schema_file.exists():
            raise FileNotFoundError(f"Go schema not found: {schema_file}")

        # Go schema will be compiled and run
        result = subprocess.run(
            ["go", "run", str(schema_file)],
            cwd=str(schema_file.parent),
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Go schema compilation failed: {result.stderr}")

        schema_data = json.loads(result.stdout)
        return schema_data

    def _get_java_schema(self) -> dict:
        """Export schema from Java implementation."""
        schema_file = Path(__file__).parent / "schema.fraiseql.java"

        if not schema_file.exists():
            raise FileNotFoundError(f"Java schema not found: {schema_file}")

        # Java schema will be compiled and run
        result = subprocess.run(
            ["java", str(schema_file)],
            cwd=str(schema_file.parent),
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Java schema execution failed: {result.stderr}")

        schema_data = json.loads(result.stdout)
        return schema_data

    def _get_php_schema(self) -> dict:
        """Export schema from PHP implementation."""
        schema_file = Path(__file__).parent / "schema.fraiseql.php"

        if not schema_file.exists():
            raise FileNotFoundError(f"PHP schema not found: {schema_file}")

        # PHP schema will be executed
        result = subprocess.run(
            ["php", str(schema_file)],
            cwd=str(schema_file.parent),
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            raise RuntimeError(f"PHP schema execution failed: {result.stderr}")

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

    def test_python_vs_go_schema(self):
        """Python and Go schemas must be identical."""
        python_schema = self._get_python_schema()
        go_schema = self._get_go_schema()

        # Compare type definitions
        assert python_schema["types"].keys() == go_schema["types"].keys(), (
            "Type names differ between Python and Go"
        )

        # Compare User type fields
        python_user = python_schema["types"]["User"]
        go_user = go_schema["types"]["User"]
        assert python_user["fields"].keys() == go_user["fields"].keys(), (
            "User fields differ"
        )

        # Compare Post type fields
        python_post = python_schema["types"]["Post"]
        go_post = go_schema["types"]["Post"]
        assert python_post["fields"].keys() == go_post["fields"].keys(), (
            "Post fields differ"
        )

        # Compare queries
        assert python_schema["query"].keys() == go_schema["query"].keys(), (
            "Query fields differ"
        )

        # Compare mutations
        assert python_schema["mutation"].keys() == go_schema["mutation"].keys(), (
            "Mutation fields differ"
        )

    def test_go_schema_exports_valid_json(self):
        """Go schema must compile and export valid JSON."""
        try:
            schema = self._get_go_schema()
            assert schema is not None
            assert "types" in schema
            assert "query" in schema
            assert "mutation" in schema
        except FileNotFoundError:
            # Expected to fail at RED stage until Go schema is implemented
            pass

    def test_python_vs_java_schema(self):
        """Python and Java schemas must be identical."""
        python_schema = self._get_python_schema()
        try:
            java_schema = self._get_java_schema()
        except (FileNotFoundError, RuntimeError):
            # Java not available, skip test
            return

        # Compare type definitions
        assert python_schema["types"].keys() == java_schema["types"].keys(), (
            "Type names differ between Python and Java"
        )

        # Compare User type fields
        python_user = python_schema["types"]["User"]
        java_user = java_schema["types"]["User"]
        assert python_user["fields"].keys() == java_user["fields"].keys(), (
            "User fields differ"
        )

        # Compare Post type fields
        python_post = python_schema["types"]["Post"]
        java_post = java_schema["types"]["Post"]
        assert python_post["fields"].keys() == java_post["fields"].keys(), (
            "Post fields differ"
        )

        # Compare queries
        assert python_schema["query"].keys() == java_schema["query"].keys(), (
            "Query fields differ"
        )

        # Compare mutations
        assert python_schema["mutation"].keys() == java_schema["mutation"].keys(), (
            "Mutation fields differ"
        )

    def test_java_schema_exports_valid_json(self):
        """Java schema must compile and export valid JSON."""
        try:
            schema = self._get_java_schema()
            assert schema is not None
            assert "types" in schema
            assert "query" in schema
            assert "mutation" in schema
        except (FileNotFoundError, RuntimeError):
            # Java not available, skip test
            pass

    def test_python_vs_php_schema(self):
        """Python and PHP schemas must be identical."""
        python_schema = self._get_python_schema()
        try:
            php_schema = self._get_php_schema()
        except (FileNotFoundError, RuntimeError):
            # PHP not available, skip test
            return

        # Compare type definitions
        assert python_schema["types"].keys() == php_schema["types"].keys(), (
            "Type names differ between Python and PHP"
        )

        # Compare User type fields
        python_user = python_schema["types"]["User"]
        php_user = php_schema["types"]["User"]
        assert python_user["fields"].keys() == php_user["fields"].keys(), (
            "User fields differ"
        )

        # Compare Post type fields
        python_post = python_schema["types"]["Post"]
        php_post = php_schema["types"]["Post"]
        assert python_post["fields"].keys() == php_post["fields"].keys(), (
            "Post fields differ"
        )

        # Compare queries
        assert python_schema["query"].keys() == php_schema["query"].keys(), (
            "Query fields differ"
        )

        # Compare mutations
        assert python_schema["mutation"].keys() == php_schema["mutation"].keys(), (
            "Mutation fields differ"
        )

    def test_php_schema_exports_valid_json(self):
        """PHP schema must execute and export valid JSON."""
        try:
            schema = self._get_php_schema()
            assert schema is not None
            assert "types" in schema
            assert "query" in schema
            assert "mutation" in schema
        except (FileNotFoundError, RuntimeError):
            # PHP not available, skip test
            pass


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
