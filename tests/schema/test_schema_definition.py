"""
Phase 1, Cycle 1: RED - Write failing tests for schema definition

Tests verify:
1. Schema exports valid JSON
2. Schema has required types
3. Queries are properly defined
4. Mutations are properly defined
"""

import json
import pytest
from pathlib import Path


class TestSchemaExport:
    """Test schema export functionality."""

    def test_schema_exports_valid_json(self):
        """Schema must export to valid JSON."""
        # Import and run schema export
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fraiseql-schema"))

        from schema_fraiseql import export_schema

        schema_file = Path("/tmp/test_schema.json")
        export_schema(str(schema_file))

        # Verify file exists
        assert schema_file.exists(), "Schema file not created"

        # Verify it's valid JSON
        schema_data = json.loads(schema_file.read_text())
        assert schema_data is not None

    def test_schema_has_required_types(self):
        """Schema must define User, Post, Comment types."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fraiseql-schema"))

        from schema_fraiseql import export_schema

        schema_file = Path("/tmp/test_schema.json")
        export_schema(str(schema_file))

        schema_data = json.loads(schema_file.read_text())

        # Verify types section exists
        assert "types" in schema_data, "Schema missing 'types' section"

        # Verify required types
        required_types = {"User", "Post", "Comment"}
        defined_types = set(schema_data["types"].keys())

        for type_name in required_types:
            assert type_name in defined_types, f"Missing type: {type_name}"

    def test_schema_has_query_root(self):
        """Schema must define root Query type."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fraiseql-schema"))

        from schema_fraiseql import export_schema

        schema_file = Path("/tmp/test_schema.json")
        export_schema(str(schema_file))

        schema_data = json.loads(schema_file.read_text())

        assert "query" in schema_data, "Schema missing 'query' root type"
        assert isinstance(schema_data["query"], dict), "Query root must be a dict"

    def test_schema_has_mutation_root(self):
        """Schema must define root Mutation type."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fraiseql-schema"))

        from schema_fraiseql import export_schema

        schema_file = Path("/tmp/test_schema.json")
        export_schema(str(schema_file))

        schema_data = json.loads(schema_file.read_text())

        assert "mutation" in schema_data, "Schema missing 'mutation' root type"
        assert isinstance(schema_data["mutation"], dict), "Mutation root must be a dict"

    def test_user_type_has_required_fields(self):
        """User type must have id, name, email, created_at, is_active fields."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fraiseql-schema"))

        from schema_fraiseql import export_schema

        schema_file = Path("/tmp/test_schema.json")
        export_schema(str(schema_file))

        schema_data = json.loads(schema_file.read_text())

        user_type = schema_data["types"]["User"]
        assert "fields" in user_type, "User type missing 'fields'"

        required_fields = {"id", "name", "email", "created_at", "is_active"}
        defined_fields = set(user_type["fields"].keys())

        for field_name in required_fields:
            assert field_name in defined_fields, f"User type missing field: {field_name}"

    def test_post_type_has_required_fields(self):
        """Post type must have id, title, content, author_id, published, created_at fields."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fraiseql-schema"))

        from schema_fraiseql import export_schema

        schema_file = Path("/tmp/test_schema.json")
        export_schema(str(schema_file))

        schema_data = json.loads(schema_file.read_text())

        post_type = schema_data["types"]["Post"]
        assert "fields" in post_type, "Post type missing 'fields'"

        required_fields = {"id", "title", "content", "author_id", "published", "created_at"}
        defined_fields = set(post_type["fields"].keys())

        for field_name in required_fields:
            assert field_name in defined_fields, f"Post type missing field: {field_name}"

    def test_query_has_users_query(self):
        """Query root must have 'users' query."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fraiseql-schema"))

        from schema_fraiseql import export_schema

        schema_file = Path("/tmp/test_schema.json")
        export_schema(str(schema_file))

        schema_data = json.loads(schema_file.read_text())

        query_root = schema_data["query"]
        assert "users" in query_root, "Query root missing 'users' query"

    def test_query_has_posts_query(self):
        """Query root must have 'posts' query."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fraiseql-schema"))

        from schema_fraiseql import export_schema

        schema_file = Path("/tmp/test_schema.json")
        export_schema(str(schema_file))

        schema_data = json.loads(schema_file.read_text())

        query_root = schema_data["query"]
        assert "posts" in query_root, "Query root missing 'posts' query"

    def test_mutation_has_create_user_mutation(self):
        """Mutation root must have 'create_user' mutation."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "fraiseql-schema"))

        from schema_fraiseql import export_schema

        schema_file = Path("/tmp/test_schema.json")
        export_schema(str(schema_file))

        schema_data = json.loads(schema_file.read_text())

        mutation_root = schema_data["mutation"]
        assert "create_user" in mutation_root, "Mutation root missing 'create_user' mutation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
