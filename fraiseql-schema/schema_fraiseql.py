"""FraiseQL Schema Definition - Python Implementation.

Defines the core GraphQL schema (User, Post, Comment types) with queries
and mutations. This schema is compiled into optimized SQL by fraiseql-server.
"""

import json
from pathlib import Path
from typing import Any


class Field:
    """Represents a GraphQL field with type information."""

    def __init__(self, name: str, field_type: str, required: bool = False) -> None:
        """Initialize a field.

        Args:
            name: Field name
            field_type: GraphQL type (e.g., "String", "ID", "DateTime")
            required: Whether the field is non-null
        """
        self.name = name
        self.field_type = field_type
        self.required = required

    def to_dict(self) -> dict[str, Any]:
        """Serialize field to dictionary."""
        return {
            "type": self.field_type,
            "required": self.required,
        }


class ObjectType:
    """Represents a GraphQL object type (e.g., User, Post)."""

    def __init__(self, name: str) -> None:
        """Initialize an object type.

        Args:
            name: Type name (e.g., "User", "Post")
        """
        self.name = name
        self.fields: dict[str, Field] = {}

    def add_field(self, name: str, field_type: str, required: bool = False) -> None:
        """Add a field to this type.

        Args:
            name: Field name
            field_type: GraphQL type
            required: Whether the field is non-null
        """
        self.fields[name] = Field(name, field_type, required)

    def to_dict(self) -> dict[str, Any]:
        """Serialize type to dictionary."""
        return {
            "name": self.name,
            "fields": {name: field.to_dict() for name, field in self.fields.items()},
        }


class QueryRoot:
    """Represents the root Query type containing all queries."""

    def __init__(self) -> None:
        """Initialize query root."""
        self.fields: dict[str, dict[str, Any]] = {}

    def add_query(self, name: str, return_type: str) -> None:
        """Add a query field.

        Args:
            name: Query name (e.g., "users", "posts")
            return_type: Return type (e.g., "[User]" for list of users)
        """
        self.fields[name] = {
            "type": return_type,
            "arguments": {},
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize query root to dictionary."""
        return self.fields


class MutationRoot:
    """Represents the root Mutation type containing all mutations."""

    def __init__(self) -> None:
        """Initialize mutation root."""
        self.fields: dict[str, dict[str, Any]] = {}

    def add_mutation(
        self, name: str, return_type: str, args: dict[str, Any] | None = None
    ) -> None:
        """Add a mutation field.

        Args:
            name: Mutation name (e.g., "create_user")
            return_type: Return type (e.g., "User")
            args: Input arguments for the mutation
        """
        self.fields[name] = {
            "type": return_type,
            "arguments": args or {},
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize mutation root to dictionary."""
        return self.fields


class Schema:
    """Root schema container holding all types, queries, and mutations."""

    def __init__(self) -> None:
        """Initialize the schema."""
        self.types: dict[str, ObjectType] = {}
        self.query = QueryRoot()
        self.mutation = MutationRoot()

    def add_type(self, type_obj: ObjectType) -> None:
        """Add an object type to the schema.

        Args:
            type_obj: The object type to add
        """
        self.types[type_obj.name] = type_obj

    def to_dict(self) -> dict[str, Any]:
        """Serialize entire schema to dictionary."""
        return {
            "types": {
                name: type_obj.to_dict() for name, type_obj in self.types.items()
            },
            "query": self.query.to_dict(),
            "mutation": self.mutation.to_dict(),
        }


def _build_schema() -> Schema:
    """Build and return the FraiseQL schema definition.

    Returns:
        Configured Schema instance
    """
    schema = Schema()

    # User type: represents a user in the system
    user_type = ObjectType("User")
    user_type.add_field("id", "ID", required=True)
    user_type.add_field("name", "String", required=True)
    user_type.add_field("email", "String", required=True)
    user_type.add_field("created_at", "DateTime", required=False)
    user_type.add_field("is_active", "Boolean", required=False)
    schema.add_type(user_type)

    # Post type: represents a blog post
    post_type = ObjectType("Post")
    post_type.add_field("id", "ID", required=True)
    post_type.add_field("title", "String", required=True)
    post_type.add_field("content", "String", required=True)
    post_type.add_field("author_id", "ID", required=True)
    post_type.add_field("published", "Boolean", required=False)
    post_type.add_field("created_at", "DateTime", required=False)
    schema.add_type(post_type)

    # Comment type: represents a comment on a post
    comment_type = ObjectType("Comment")
    comment_type.add_field("id", "ID", required=True)
    comment_type.add_field("content", "String", required=True)
    comment_type.add_field("post_id", "ID", required=True)
    comment_type.add_field("author_id", "ID", required=True)
    comment_type.add_field("created_at", "DateTime", required=False)
    schema.add_type(comment_type)

    # Query root: defines all available queries
    schema.query.add_query("users", "[User]")
    schema.query.add_query("posts", "[Post]")

    # Mutation root: defines all available mutations
    schema.mutation.add_mutation(
        "create_user", "User", {"name": "String!", "email": "String!"}
    )

    return schema


# Module-level schema instance
_schema = _build_schema()


def export_schema(output_path: str) -> None:
    """
    Export the schema to a JSON file.

    Args:
        output_path: Path where schema.json should be written
    """
    schema_data = _schema.to_dict()
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(schema_data, indent=2))
