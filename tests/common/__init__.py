"""Shared test infrastructure for VelocityBench framework test suites.

This package provides:
- Database fixtures (db, factory, bulk_factory)
- Pytest markers and configuration
- Framework-agnostic test data factories

All frameworks import fixtures via pytest plugin system in their conftest.py:

    pytest_plugins = [
        "tests.common.fixtures",
        "tests.common.factory",
        "tests.common.bulk_factory",
    ]
"""
