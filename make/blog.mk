# Blog Generation Targets
# Generate blog posts from patterns using vLLM

.PHONY: blog-all blog-fraisier blog-webhooks blog-git-providers blog-cqrs \
        blog-history blog-multi-provider blog-multi-env blog-pattern blog-list blog-clean

# Generate all blog posts
blog-all: venv-check
	@echo "======================================================================"
	@echo "Generating ALL blog posts from patterns (this will take a while...)"
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) $(GENERATOR_SCRIPT) --all
	@echo "======================================================================"
	@echo "✓ Blog generation complete!"
	@echo "Output directory: $(OUTPUT_DIR)"
	@echo "======================================================================"

# Generate for fraisier-deployment-orchestration pattern
blog-fraisier: venv-check
	@echo "======================================================================"
	@echo "Generating Fraisier Deployment Orchestration blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-deployment-orchestration --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-deployment-orchestration --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-deployment-orchestration --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-deployment-orchestration --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-deployment-orchestration --type reference
	@echo "======================================================================"
	@echo "✓ Fraisier deployment pattern blogs generated!"
	@echo "======================================================================"

# Generate for webhook-event-driven-deployment pattern
blog-webhooks: venv-check
	@echo "======================================================================"
	@echo "Generating Webhook Event-Driven Deployment blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern webhook-event-driven-deployment --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern webhook-event-driven-deployment --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern webhook-event-driven-deployment --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern webhook-event-driven-deployment --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern webhook-event-driven-deployment --type reference
	@echo "======================================================================"
	@echo "✓ Webhook deployment pattern blogs generated!"
	@echo "======================================================================"

# Generate for git-provider-abstraction pattern
blog-git-providers: venv-check
	@echo "======================================================================"
	@echo "Generating Git Provider Abstraction blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern git-provider-abstraction --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern git-provider-abstraction --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern git-provider-abstraction --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern git-provider-abstraction --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern git-provider-abstraction --type reference
	@echo "======================================================================"
	@echo "✓ Git provider abstraction pattern blogs generated!"
	@echo "======================================================================"

# Generate for fraisier-cqrs-deployment pattern
blog-cqrs: venv-check
	@echo "======================================================================"
	@echo "Generating CQRS Deployment Pattern blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-cqrs-deployment --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-cqrs-deployment --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-cqrs-deployment --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-cqrs-deployment --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-cqrs-deployment --type reference
	@echo "======================================================================"
	@echo "✓ CQRS deployment pattern blogs generated!"
	@echo "======================================================================"

# Generate for deployment-history-tracking pattern
blog-history: venv-check
	@echo "======================================================================"
	@echo "Generating Deployment History Tracking blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern deployment-history-tracking --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern deployment-history-tracking --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern deployment-history-tracking --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern deployment-history-tracking --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern deployment-history-tracking --type reference
	@echo "======================================================================"
	@echo "✓ Deployment history pattern blogs generated!"
	@echo "======================================================================"

# Generate for fraisier-multi-git-provider pattern
blog-multi-provider: venv-check
	@echo "======================================================================"
	@echo "Generating Multi-Git-Provider blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-git-provider --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-git-provider --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-git-provider --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-git-provider --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-git-provider --type reference
	@echo "======================================================================"
	@echo "✓ Multi-Git-provider pattern blogs generated!"
	@echo "======================================================================"

# Generate for fraisier-multi-environment pattern
blog-multi-env: venv-check
	@echo "======================================================================"
	@echo "Generating Multi-Environment blogs..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-environment --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-environment --type tutorial --depth intermediate && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-environment --type tutorial --depth advanced && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-environment --type troubleshooting && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern fraisier-multi-environment --type reference
	@echo "======================================================================"
	@echo "✓ Multi-environment pattern blogs generated!"
	@echo "======================================================================"

# Generate for specific pattern with arguments
blog-pattern: venv-check
	@if [ -z "$(PATTERN)" ]; then \
		echo "Error: PATTERN is required"; \
		echo "Usage: make blog-pattern PATTERN=<id> [TYPE=<type>] [DEPTH=<depth>]"; \
		exit 1; \
	fi
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@TYPE=$${TYPE:-tutorial}; \
	DEPTH=$${DEPTH:-beginner}; \
	echo "Generating blog for pattern: $(PATTERN)"; \
	echo "Type: $$TYPE, Depth: $$DEPTH"; \
	cd $(GENERATOR_DIR) && $(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern $(PATTERN) --type $$TYPE --depth $$DEPTH

# List all patterns
blog-list: venv-check
	@echo "======================================================================"
	@echo "Discovering patterns in corpus..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) -c "\
	from pathlib import Path; \
	import yaml; \
	corpus = Path('$(PROJECT_ROOT)database/seed-data/corpus/patterns'); \
	patterns = {}; \
	for cat_dir in corpus.iterdir(): \
		if cat_dir.is_dir(): \
			for yaml_file in cat_dir.glob('*.yaml'): \
				pattern_id = yaml_file.stem; \
				patterns[pattern_id] = cat_dir.name; \
	print(f'Total patterns: {len(patterns)}'); \
	print('\\nFraisier patterns:'); \
	for pid in sorted(patterns.keys()): \
		if 'fraisier' in pid or 'webhook' in pid or 'git-provider' in pid or 'deployment-history' in pid: \
			print(f'  - {pid} ({patterns[pid]})');"
	@echo "======================================================================"

# Clean generated blog files
blog-clean:
	@echo "Cleaning generated blog files..."
	@if [ -d "$(OUTPUT_DIR)" ]; then \
		find $(OUTPUT_DIR) -type f -name "*.md" -delete; \
		echo "✓ Cleaned: $(OUTPUT_DIR)"; \
	fi
	@echo "Done."
