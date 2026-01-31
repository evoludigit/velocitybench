"""Pytest configuration for Flask REST framework tests.

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

# Import shared error scenario tests
from tests.common import (
    test_error_scenarios_base,
)

# Import shared mutation tests
from tests.common import (
    test_mutations_base,
)

# Import shared performance tests
from tests.common import (
    test_perf_simple_queries,
    test_perf_list_queries,
    test_perf_relationship_queries,
    test_perf_n_plus_one,
    test_perf_filtered_queries,
    test_perf_complex_nested,
)
