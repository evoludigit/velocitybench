"""Pytest configuration for Graphene GraphQL framework tests.

Imports shared fixtures from tests.common:
- db: Database connection with transaction isolation
- factory: Test data factory
- bulk_factory: Bulk operations factory
"""

# Import shared fixtures via pytest plugin system
pytest_plugins = [
    "tests.common.fixtures",
    "tests.common.factory",
    "tests.common.bulk_factory",
]

# Import shared security tests
from tests.common import (
    test_security_injection,
    test_security_validation,
    test_security_integrity,
)
