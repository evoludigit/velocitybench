# Development Guide - Cost Simulation Engine

This guide covers setup, testing, and development practices for the Cost Simulation Engine.

## Setup

### Prerequisites

- Python 3.10+ (tested with Python 3.13)
- pytest for testing
- No external dependencies for Phase 1 (core engine)

### Installation

```bash
# Clone/navigate to VelocityBench repository
cd /home/lionel/code/velocitybench

# Verify Phase 1 modules exist
ls -la costs/

# Run tests to verify setup
python -m pytest costs/tests/ -v
```

## Running Tests

### All Tests
```bash
python -m pytest costs/tests/ -v
```

### Specific Module
```bash
python -m pytest costs/tests/test_cost_config.py -v
python -m pytest costs/tests/test_load_profiler.py -v
python -m pytest costs/tests/test_resource_calculator.py -v
```

### Specific Test
```bash
python -m pytest costs/tests/test_cost_config.py::TestCostConfiguration::test_init_with_defaults -v
```

### With Coverage
```bash
python -m pytest costs/tests/ --cov=costs --cov-report=html
open htmlcov/index.html
```

### Watch Mode (if using pytest-watch)
```bash
ptw costs/tests/ -- -v
```

## Code Style

### Type Hints
Use Python 3.10+ style type hints:

```python
# ✅ Good
def calculate(value: float) -> dict[str, float]:
    return {"result": value * 2}

# ❌ Avoid
from typing import Dict
def calculate(value: float) -> Dict[str, float]:
    return {"result": value * 2}
```

### Naming Conventions
- Classes: PascalCase (e.g., `LoadProfiler`, `ResourceRequirements`)
- Functions/methods: snake_case (e.g., `calculate_cpu_cores`, `get_instance`)
- Constants: UPPER_SNAKE_CASE (e.g., `DEFAULT_PEAK_MULTIPLIER`)
- Private methods: prefix with `_` (e.g., `_load_default_pricing`)

### Docstrings
Use Google-style docstrings:

```python
def calculate_requirements(
    self,
    load_projection: LoadProjection,
    cpu_headroom_percent: float = 30.0,
) -> ResourceRequirements:
    """Calculate all resource requirements.

    Args:
        load_projection: LoadProjection object with load data.
        cpu_headroom_percent: CPU headroom percentage (default 30%).

    Returns:
        ResourceRequirements object with calculated values.
    """
```

## Project Structure

```
costs/
├── cost_config.py              # Cloud provider pricing
├── load_profiler.py            # Load projection
├── resource_calculator.py      # Resource requirements
├── integration.py              # Pipeline orchestration (Phase 2)
├── cost_calculator.py          # Cost calculation (Phase 2)
├── efficiency_analyzer.py      # Efficiency scoring (Phase 2)
├── result_builder.py           # Report generation (Phase 3)
├── cli.py                      # CLI tool (Phase 3)
├── exceptions.py               # Custom exceptions
├── utils.py                    # Helper functions
├── __init__.py                 # Package initialization
│
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_cost_config.py
│   ├── test_load_profiler.py
│   ├── test_resource_calculator.py
│   ├── test_cost_calculator.py         (Phase 2)
│   ├── test_efficiency_analyzer.py     (Phase 2)
│   ├── test_result_builder.py          (Phase 3)
│   └── test_integration.py             (Phase 4)
│
├── fixtures/
│   ├── cost-config.json                # Cloud pricing data
│   ├── sample-jmeter-results.jtl       # Sample benchmark data
│   ├── framework-config-sample.json    # Framework config
│   └── expected-outputs/               # Expected test outputs
│
├── README.md                   # User guide
├── DEVELOPMENT.md              # This file
└── PHASE_1_SUMMARY.md          # Implementation status
```

## Development Workflow

### Adding a New Feature

1. **Create test first (TDD)**
   ```bash
   # Edit costs/tests/test_module.py
   # Add test_new_feature() to appropriate test class
   ```

2. **Run failing test**
   ```bash
   python -m pytest costs/tests/test_module.py::TestClass::test_new_feature -v
   # Should fail (RED)
   ```

3. **Implement feature**
   ```bash
   # Edit costs/module.py
   # Add implementation to make test pass
   ```

4. **Run test again**
   ```bash
   python -m pytest costs/tests/test_module.py::TestClass::test_new_feature -v
   # Should pass (GREEN)
   ```

5. **Run full test suite**
   ```bash
   python -m pytest costs/tests/ -v
   # All tests should pass
   ```

6. **Refactor if needed**
   - Clean up code
   - Remove duplication
   - Improve clarity
   - Re-run tests

7. **Commit**
   ```bash
   git add costs/module.py costs/tests/test_module.py
   git commit -m "feat(costs): Add new feature description"
   ```

### Debugging Tests

```bash
# Run test with print statements
python -m pytest costs/tests/test_module.py::TestClass::test_name -v -s

# Run test with pdb on failure
python -m pytest costs/tests/test_module.py::TestClass::test_name --pdb

# Run test with detailed output
python -m pytest costs/tests/test_module.py::TestClass::test_name -vv --tb=long
```

## Testing Guidelines

### Test Structure
```python
class TestModuleClass:
    """Test ModuleClass functionality."""

    def test_basic_operation(self):
        """Test basic expected behavior."""
        # Arrange
        instance = ModuleClass()

        # Act
        result = instance.method()

        # Assert
        assert result == expected_value

    def test_edge_case(self):
        """Test edge case handling."""
        instance = ModuleClass()
        result = instance.method(edge_value)
        assert result == expected_result

    def test_error_handling(self):
        """Test error handling."""
        instance = ModuleClass()
        with pytest.raises(CustomError):
            instance.method(invalid_input)
```

### Fixture Usage
Use conftest.py fixtures for common test data:

```python
def test_with_fixture(self, cost_config, sample_load_projection):
    """Test using fixtures."""
    instances = cost_config.get_compute_instances_for_cores(4)
    assert len(instances) > 0
```

### Assertions
```python
# Basic assertions
assert value == expected
assert condition is True
assert instance is not None

# Approximate equality for floats
assert result == pytest.approx(expected, rel=1e-2)

# Membership and exceptions
assert item in collection
with pytest.raises(CustomError):
    function_that_fails()
```

## Performance Guidelines

### Target Times
- Unit test execution: < 0.1s per test
- Full test suite: < 1s total
- Cost calculation (Phase 2): < 10s per framework

### Profiling
```bash
# Profile slow tests
python -m pytest costs/tests/ --durations=10 -v

# Profile specific test
python -m pytest costs/tests/test_module.py -v --profile
```

## Code Review Checklist

Before committing, verify:

- [ ] Code follows style guide (type hints, naming, docstrings)
- [ ] All tests pass: `pytest costs/tests/ -v`
- [ ] New tests added for new functionality
- [ ] No hardcoded values (use constants instead)
- [ ] Error handling for edge cases
- [ ] Docstrings complete with Args/Returns
- [ ] Type hints throughout
- [ ] No commented-out code
- [ ] Imports organized (stdlib, then local)

## Commit Message Format

```
# Feature
feat(costs): Brief description of feature

# Bug fix
fix(costs): Brief description of fix

# Refactoring
refactor(costs): Brief description of changes

# Testing
test(costs): Add tests for [feature]

# Documentation
docs(costs): Update [file] with information about [topic]

# Chore
chore(costs): Update dependencies or tooling
```

## Adding New Cloud Providers

### Step 1: Update cost_config.py
```python
@dataclass
class InstancePricing:
    # ... existing fields ...
    new_cloud_hourly: float
    new_cloud_1yr_reserved: float
    new_cloud_3yr_reserved: float
```

### Step 2: Add pricing data in _load_default_pricing()
```python
def _load_default_pricing(self) -> None:
    # ... existing code ...
    self.instances["new_cloud_t3_micro"] = InstancePricing(
        instance_id="t3.micro",
        cpu_cores=1,
        memory_gb=1.0,
        aws_hourly=0.0104,
        # ... other clouds ...
        new_cloud_hourly=0.0115,
        new_cloud_1yr_reserved=0.0069,
        new_cloud_3yr_reserved=0.0052,
    )
```

### Step 3: Add tests
```python
def test_new_cloud_pricing(self):
    """Test new cloud provider pricing."""
    config = CostConfiguration()
    instance = config.get_instance("new_cloud_t3_micro")
    assert instance.new_cloud_hourly > 0
    assert instance.new_cloud_1yr_reserved < instance.new_cloud_hourly
```

### Step 4: Update Phase 2 (cost_calculator.py)
Add new_cloud_cost calculation in CostCalculator class.

## Common Issues

### Import Errors
```
ModuleNotFoundError: No module named 'costs'
```
**Solution**: Run tests from repository root:
```bash
cd /home/lionel/code/velocitybench
python -m pytest costs/tests/ -v
```

### Type Hint Errors (Python 3.13)
```
AttributeError: 'typing.Dict' not in 'builtins'
```
**Solution**: Use modern type hints without importing from typing:
```python
# ✅ Correct
result: dict[str, float] = {}

# ❌ Wrong
from typing import Dict
result: Dict[str, float] = {}
```

### Floating Point Precision
```
AssertionError: 0.29999999999 != 0.3
```
**Solution**: Use pytest.approx():
```python
assert result == pytest.approx(expected, rel=1e-2)
```

## Phase Development Roadmap

### Phase 1: Core Engine ✅ Complete
- cost_config.py: Pricing configuration
- load_profiler.py: Load projection
- resource_calculator.py: Resource requirements
- 45 comprehensive tests

### Phase 2: Calculation Engine (Next)
- cost_calculator.py: Cloud cost calculations
- efficiency_analyzer.py: Efficiency metrics
- Integration tests
- Duration: 1 week

### Phase 3: Reporting (Following)
- result_builder.py: JSON/HTML/CSV output
- cli.py: Command-line interface
- Documentation
- Duration: 1 week

### Phase 4: Integration (Final)
- integration.py: Pipeline orchestration
- Grafana dashboard configuration
- End-to-end tests
- Production deployment
- Duration: 1 week

## References

- Python 3.10+ Type Hints: https://docs.python.org/3.10/library/typing.html
- Pytest Documentation: https://docs.pytest.org/
- Google Style Guide: https://google.github.io/styleguide/pyguide.html
- VelocityBench: https://github.com/evoludigit/velocitybench

## Getting Help

### Questions about Phase 1
See `PHASE_1_SUMMARY.md` for implementation details.

### Questions about design
See `COST_SIMULATION_DESIGN.md` (root directory) for comprehensive technical design.

### Questions about integration
See `README.md` for integration points and usage examples.

---

**Happy developing!** 🚀

For detailed implementation questions, see the design documents or contact the project team.
