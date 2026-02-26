"""Pytest configuration for ASGI GraphQL framework tests.

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
    # Shared security tests
    "tests.common.test_security_injection",
    "tests.common.test_security_validation",
    "tests.common.test_security_integrity",
    # Shared error scenario tests
    "tests.common.test_error_scenarios_base",
    # Shared performance tests
    "tests.common.test_perf_simple_queries",
    "tests.common.test_perf_list_queries",
    "tests.common.test_perf_relationship_queries",
    "tests.common.test_perf_n_plus_one",
    "tests.common.test_perf_filtered_queries",
    "tests.common.test_perf_complex_nested",
]
