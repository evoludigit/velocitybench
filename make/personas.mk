# Persona Generation Targets
# Generate and validate diverse personas for comments

.PHONY: personas-test personas-generate personas-validate personas-validate-sample \
        personas-correct personas-correct-sample personas-correct-dry personas-analyze personas-clean

# Test persona generation (10 personas, dry-run)
personas-test: venv-check
	@echo "======================================================================"
	@echo "Testing Persona Generation (10 personas)..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) generate_personas.py --count 10 --dry-run
	@echo "======================================================================"

# Generate full persona set (~2000 personas)
personas-generate: venv-check
	@echo "======================================================================"
	@echo "Generating ~2000 Diverse Personas (this will take 30-60 minutes)..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml jsonschema
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) generate_personas.py --count 2000
	@echo "======================================================================"
	@echo "✓ Personas generated!"
	@echo "Output directory: $(PROJECT_ROOT)database/seed-data/output/personas/"
	@echo "  - personas/index.json (quick lookup)"
	@echo "  - personas/persona_*.json (individual persona files)"
	@echo "  - personas.json (legacy format, for backwards compatibility)"
	@echo "======================================================================"

# Analyze generated personas
personas-analyze: venv-check
	@echo "======================================================================"
	@echo "Analyzing Generated Personas..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) generate_personas.py --analyze $(PROJECT_ROOT)database/seed-data/output/personas/personas.json
	@echo "======================================================================"

# Validate persona coherence (2nd pass quality check - checks all 6 coherence criteria)
personas-validate: venv-check
	@echo "======================================================================"
	@echo "Validating All Generated Personas (Coherence Check)..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml jsonschema
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) validate_personas.py --input-dir $(PROJECT_ROOT)database/seed-data/output/personas/personas
	@echo "======================================================================"

# Validate persona coherence - sample only (first 100 personas, faster)
personas-validate-sample: venv-check
	@echo "======================================================================"
	@echo "Validating Sample of Generated Personas (first 100)..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml jsonschema
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) validate_personas.py --input-dir $(PROJECT_ROOT)database/seed-data/output/personas/personas --count 100
	@echo "======================================================================"

# Correct personas based on vLLM analysis (Layer 3 - automatic corrections)
personas-correct: venv-check
	@echo "======================================================================"
	@echo "Correcting Personas Based on vLLM Analysis (Layer 3)..."
	@echo "This will identify and fix coherence issues in all personas..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml jsonschema
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) correct_personas.py --input-dir $(PROJECT_ROOT)database/seed-data/output/personas/personas --output-dir $(PROJECT_ROOT)database/seed-data/output/personas/corrected
	@echo "======================================================================"
	@echo "✓ Persona corrections completed!"
	@echo "Output: $(PROJECT_ROOT)database/seed-data/output/personas/corrected/"
	@echo "======================================================================"

# Correct personas - sample only (first 50 personas, faster testing)
personas-correct-sample: venv-check
	@echo "======================================================================"
	@echo "Testing Persona Corrections (first 50)..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml jsonschema
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) correct_personas.py --input-dir $(PROJECT_ROOT)database/seed-data/output/personas/personas --output-dir $(PROJECT_ROOT)database/seed-data/output/personas/corrected --count 50
	@echo "======================================================================"

# Correct personas - dry run (analyze only, no changes)
personas-correct-dry: venv-check
	@echo "======================================================================"
	@echo "Analyzing Personas for Corrections (Dry Run - no changes)..."
	@echo "======================================================================"
	@$(VENV_PYTHON) -m pip install -q requests pyyaml jsonschema
	@cd $(GENERATOR_DIR) && $(VENV_PYTHON) correct_personas.py --input-dir $(PROJECT_ROOT)database/seed-data/output/personas/personas --dry-run
	@echo "======================================================================"

# Clean persona files
personas-clean:
	@echo "Cleaning persona files..."
	@rm -rf $(PROJECT_ROOT)database/seed-data/output/personas
	@echo "✓ Personas cleaned"
