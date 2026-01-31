# Utility Targets
# Virtual environment, database, vLLM server, and system utilities

.PHONY: venv-check venv-setup venv-info vllm-start vllm-status vllm-stop db-up db-down

# Check if virtualenv exists
venv-check:
	@if [ -d "$(VENV_PATH)" ]; then \
		echo "✓ Virtual environment found at $(VENV_PATH)"; \
		echo "✓ Python: $$($(VENV_PYTHON) --version)"; \
	else \
		echo "✗ Virtual environment NOT found at $(VENV_PATH)"; \
		echo "  Run: make venv-setup"; \
		exit 1; \
	fi

# Setup virtualenv if it doesn't exist
venv-setup:
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV_PATH); \
		$(VENV_PYTHON) -m pip install --upgrade pip; \
		echo "Installing dependencies..."; \
		$(VENV_PYTHON) -m pip install requests pyyaml; \
		echo "✓ Virtual environment ready"; \
	else \
		echo "✓ Virtual environment already exists"; \
	fi

# Show venv info
venv-info:
	@echo "Virtual Environment Info:"
	@echo "  Path: $(VENV_PATH)"
	@echo "  Python: $(VENV_PYTHON)"
	@echo "  Activate: source $(VENV_ACTIVATE)"

# Start vLLM server (required for comment generation)
vllm-start:
	@echo "======================================================================"
	@echo "Starting vLLM Server (implementer model)..."
	@echo "======================================================================"
	@$(PROJECT_ROOT)bin/vllm-start-helper.sh
	@echo "======================================================================"

# Check vLLM service status
vllm-status:
	@vllm-switch status

# Stop vLLM server
vllm-stop:
	@echo "Stopping vLLM server..."
	@vllm-switch stop
	@echo "✓ vLLM stopped"

# Start database only
db-up:
	@echo "Starting PostgreSQL database..."
	docker compose up -d postgres
	@echo "Waiting for database to be healthy..."
	@sleep 3
	@docker compose exec postgres pg_isready -U benchmark || echo "Database starting up..."

# Stop database
db-down:
	@echo "Stopping PostgreSQL database..."
	docker compose down postgres
