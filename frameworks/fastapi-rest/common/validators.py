"""Shared input validation utilities for REST and GraphQL APIs.

Provides validators for common input parameters:
- UUID validation
- Limit/pagination bounds checking
- UUID list validation with count limits
- Include field whitelisting
"""

from typing import Any
from uuid import UUID

from .errors import InputValidationError


class Validator:
    """Input validation utilities."""

    @staticmethod
    def validate_uuid(value: str, field_name: str = "id") -> str:
        """Validate UUID format.

        Args:
            value: String to validate as UUID
            field_name: Field name for error messages

        Returns:
            Original value if valid

        Raises:
            InputValidationError: If not a valid UUID
        """
        try:
            UUID(value)
            return value
        except (ValueError, TypeError, AttributeError):
            raise InputValidationError(
                f"Invalid UUID format for {field_name}: {value}",
                details={"field": field_name, "value": value},
            )

    @staticmethod
    def validate_limit(
        value: Any,
        min_val: int = 1,
        max_val: int = 100,
        field_name: str = "limit",
    ) -> int:
        """Validate limit parameter with bounds checking.

        Args:
            value: Value to validate (int or string)
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            field_name: Field name for error messages

        Returns:
            Validated integer value

        Raises:
            InputValidationError: If invalid or out of bounds
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise InputValidationError(
                f"Parameter {field_name} must be an integer, got: {value}",
                details={"field": field_name, "value": value},
            )

        if int_value < min_val or int_value > max_val:
            raise InputValidationError(
                f"Parameter {field_name} must be between {min_val} and {max_val}, "
                f"got: {int_value}",
                details={
                    "field": field_name,
                    "value": int_value,
                    "min": min_val,
                    "max": max_val,
                },
            )

        return int_value

    @staticmethod
    def validate_uuid_list(
        value: str, max_count: int = 100, field_name: str = "ids"
    ) -> list[str]:
        """Validate comma-separated UUID list.

        Args:
            value: Comma-separated UUIDs
            max_count: Maximum number of IDs allowed
            field_name: Field name for error messages

        Returns:
            List of validated UUID strings

        Raises:
            InputValidationError: If any UUID is invalid or count exceeds max
        """
        if not value or not value.strip():
            raise InputValidationError(
                f"Parameter {field_name} cannot be empty",
                details={"field": field_name},
            )

        id_list = [id_str.strip() for id_str in value.split(",") if id_str.strip()]

        if len(id_list) > max_count:
            raise InputValidationError(
                f"Parameter {field_name} exceeded maximum count. "
                f"Maximum {max_count} IDs allowed, got {len(id_list)}",
                details={
                    "field": field_name,
                    "count": len(id_list),
                    "max_count": max_count,
                },
            )

        # Validate each UUID
        validated = []
        for i, id_value in enumerate(id_list):
            try:
                UUID(id_value)
                validated.append(id_value)
            except (ValueError, TypeError, AttributeError):
                raise InputValidationError(
                    f"Invalid UUID at position {i} in {field_name}: {id_value}",
                    details={
                        "field": field_name,
                        "position": i,
                        "value": id_value,
                    },
                )

        return validated

    @staticmethod
    def validate_include_fields(
        value: str, allowed: set[str], field_name: str = "include"
    ) -> list[str]:
        """Validate include parameter against whitelist.

        Args:
            value: Comma-separated field names
            allowed: Set of allowed field names
            field_name: Field name for error messages

        Returns:
            List of validated field names

        Raises:
            InputValidationError: If any field is not in whitelist
        """
        if not value or not value.strip():
            return []

        fields = [f.strip() for f in value.split(",") if f.strip()]

        invalid_fields = [f for f in fields if f not in allowed]
        if invalid_fields:
            raise InputValidationError(
                f"Invalid fields in {field_name}: {', '.join(invalid_fields)}. "
                f"Allowed: {', '.join(sorted(allowed))}",
                details={
                    "field": field_name,
                    "invalid_fields": invalid_fields,
                    "allowed": sorted(allowed),
                },
            )

        return fields
