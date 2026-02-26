# Comment & Reply Generation Targets
# Generate comments, replies, and validate against hallucinations

.PHONY: comments-test comments-generate comments-replies comments-validate \
        comments-load comments-analyze comments-clean

# Test comment generation (5 posts, dry-run)
comments-test: venv-check vllm-start
	@echo "======================================================================"
	@echo "Testing Comment Generation (5 posts, dry-run)..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) generate_blog_comments.py --test --posts 5 --dry-run
	@echo "======================================================================"

# Generate comments on all blog posts
comments-generate: venv-check vllm-start
	@echo "======================================================================"
	@echo "Generating Comments on ALL Blog Posts..."
	@echo "This will generate ~120,000 comments across 9,281 posts (6-8 hours)"
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) generate_blog_comments.py --all
	@echo "======================================================================"
	@echo "✓ Comments generated!"
	@echo "Output: $(PROJECT_ROOT)database/seed-data/output/comments/"
	@echo "======================================================================"

# Generate replies to comments
comments-replies: venv-check
	@echo "======================================================================"
	@echo "Generating Replies to Comments (hallucination-driven)..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) generate_comment_replies.py --all \
		--comments-dir $(PROJECT_ROOT)database/seed-data/output/comments \
		--blog-dir $(PROJECT_ROOT)database/seed-data/output/blog
	@echo "======================================================================"
	@echo "✓ Comment replies generated!"
	@echo "Output: $(PROJECT_ROOT)database/seed-data/output/comments-with-replies/"
	@echo "======================================================================"

# Validate/filter comments for quality
comments-validate: venv-check
	@echo "======================================================================"
	@echo "Validating & Filtering Comments (hallucination detection)..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) validate_blog_comments.py \
		--comments-dir $(PROJECT_ROOT)database/seed-data/output/comments-with-replies
	@echo "======================================================================"
	@echo "✓ Comments validated!"
	@echo "Output: $(PROJECT_ROOT)database/seed-data/output/comments-validated/"
	@echo "======================================================================"

# Load comments to PostgreSQL
comments-load: venv-check
	@echo "======================================================================"
	@echo "Loading Comments to PostgreSQL..."
	@echo "======================================================================"
	@if [ -z "$(DB_CONNECTION)" ]; then \
		echo "Error: DB_CONNECTION is required"; \
		echo "Usage: make comments-load DB_CONNECTION='postgresql://user:pass@localhost/db'"; \
		echo ""; \
		echo "Example:"; \
		echo "  make comments-load DB_CONNECTION='postgresql://user:pass@localhost:5432/velocitybench'"; \
		echo ""; \
		echo "Notes:"; \
		echo "  - Personas are mapped to consistent user PKs (1-5000)"; \
		echo "  - Same persona always maps to same user"; \
		echo "  - See PERSONA_USER_MAPPING.md for details"; \
		exit 1; \
	fi
	@$(VENV_PYTHON) -m pip install -q requests pyyaml psycopg
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) load_comments_to_db.py \
		--comments-dir $(PROJECT_ROOT)database/seed-data/output/comments-validated \
		--num-users 5000 \
		--connection "$(DB_CONNECTION)"
	@echo "======================================================================"
	@echo "✓ Comments loaded to database!"
	@echo "✓ Personas mapped to users (see PERSONA_USER_MAPPING.md)"
	@echo "======================================================================"

# Analyze generated comments
comments-analyze: venv-check
	@echo "======================================================================"
	@echo "Analyzing Generated Comments..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) analyze_comments.py
	@echo "======================================================================"

# Clean comment files
comments-clean:
	@echo "Cleaning comment files..."
	@rm -rf $(PROJECT_ROOT)database/seed-data/output/comments
	@rm -rf $(PROJECT_ROOT)database/seed-data/output/comments-with-replies
	@rm -rf $(PROJECT_ROOT)database/seed-data/output/comments-validated
	@mkdir -p $(PROJECT_ROOT)database/seed-data/output/comments
	@echo "✓ Comments cleaned"
