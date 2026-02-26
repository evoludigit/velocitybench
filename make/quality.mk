# Code Quality Targets
# Lint, format, type-check, and audit Python code

.PHONY: lint format type-check quality

# Lint Python code with ruff
lint:
	@echo "Linting Python code with ruff..."
	@if [ -d "$(PROJECT_ROOT)database" ]; then \
		$(VENV_PYTHON) -m ruff check $(PROJECT_ROOT)database/seed-data/generator/ $(PROJECT_ROOT)database/*.py; \
	fi
	@if [ -d "$(PROJECT_ROOT)frameworks/fastapi-rest" ]; then \
		$(VENV_PYTHON) -m ruff check $(PROJECT_ROOT)frameworks/fastapi-rest/; \
	fi
	@echo "✓ Linting complete"

# Format Python code with ruff
format:
	@echo "Formatting Python code with ruff..."
	@if [ -d "$(PROJECT_ROOT)database" ]; then \
		$(VENV_PYTHON) -m ruff format $(PROJECT_ROOT)database/seed-data/generator/ $(PROJECT_ROOT)database/*.py; \
	fi
	@if [ -d "$(PROJECT_ROOT)frameworks/fastapi-rest" ]; then \
		$(VENV_PYTHON) -m ruff format $(PROJECT_ROOT)frameworks/fastapi-rest/; \
	fi
	@echo "✓ Formatting complete"

# Type-check Python code with ty
type-check:
	@echo "Type-checking Python code with ty..."
	@ty check $(PROJECT_ROOT)database/seed-data/generator/ $(PROJECT_ROOT)frameworks/fastapi-rest/
	@echo "✓ Type-check complete"

# Run all quality checks
quality: lint type-check
	@echo "✓ All quality checks complete"
