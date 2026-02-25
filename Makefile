# VelocityBench Makefile
# Modular Makefile structure for better maintainability
# See make/*.mk for individual target implementations

# Include shared variables from all modules
include make/variables.mk

# Include all modular Makefiles
include make/blog.mk
include make/personas.mk
include make/comments.mk
include make/framework.mk
include make/quality.mk
include make/utils.mk

# Default target
.PHONY: help
help:
	@echo "======================================================================"
	@echo "VelocityBench - Framework Benchmarking Suite"
	@echo "======================================================================"
	@echo ""
	@echo "Status:"
	@echo "  make status                                - Framework health dashboard (container, health, Q1 smoke)"
	@echo "  make status ARGS=--json                    - JSON output for CI consumption"
	@echo ""
	@echo "Benchmarking:"
	@echo "  make up                                    - Start 8 benchmark frameworks (DATA_VOLUME=xs)"
	@echo "  make up-medium                             - Start with medium dataset (10K users)"
	@echo "  make down                                  - Stop all benchmark frameworks"
	@echo "  make bench-sequential                      - Sequential isolation benchmark (canonical)"
	@echo "  make bench-sequential DURATION=30          -   with custom duration (seconds)"
	@echo "  make bench-sequential CONCURRENCY=40       -   with custom concurrency"
	@echo "  make bench-sequential FRAMEWORKS='a b'     -   subset of frameworks only"
	@echo "  make bench-one FRAMEWORK=<name>            - k6 benchmark a single framework"
	@echo "  make bench-all                             - Full k6 suite (all frameworks, ~90 min)"
	@echo "  make bench                                 - FraiseQL v_* vs tv_* comparison"
	@echo ""
	@echo "Database:"
	@echo "  make db-up                                 - Start PostgreSQL database"
	@echo "  make db-down                               - Stop PostgreSQL database"
	@echo "  make test-seed                             - Verify seed data row counts"
	@echo ""
	@echo "Quality:"
	@echo "  make validate                              - Full pre-benchmark check (smoke+parity+n1)"
	@echo "  make smoke-test                            - Health check all frameworks"
	@echo "  make parity-test                           - Cross-framework data consistency"
	@echo "  make n1-guard                              - N+1 query regression test (serial)"
	@echo "  make lint                                  - Lint Python code with ruff"
	@echo "  make format                                - Format Python code with ruff"
	@echo "  make type-check                            - Type-check Python code with ty"
	@echo "  make quality                               - Run all quality checks"
	@echo ""
	@echo "Framework Management:"
	@echo "  make framework-list                        - List all available frameworks"
	@echo "  make framework-start FRAMEWORK=<name>      - Start a framework"
	@echo "  make framework-stop FRAMEWORK=<name>       - Stop a framework"
	@echo "  make framework-smoke                       - Run smoke tests on running frameworks"
	@echo ""
	@echo "Content Generation (vLLM required):"
	@echo "  make personas-generate                     - Generate ~2000 diverse personas"
	@echo "  make personas-test                         - Test persona generation (10 personas)"
	@echo "  make comments-generate                     - Generate comments on ALL blog posts"
	@echo "  make comments-test                         - Test comment generation (5 posts)"
	@echo "  make blog-all                              - Generate ALL blog posts"
	@echo "  make blog-pattern PATTERN=<id>             - Generate single pattern blog"
	@echo "  make vllm-start / vllm-stop / vllm-status - Manage vLLM server"
	@echo ""
	@echo "Examples:"
	@echo "  make up && make smoke-test                 # Start stack and verify health"
	@echo "  make validate                              # Full pre-benchmark health gate"
	@echo "  make bench-sequential DURATION=30 CONCURRENCY=40"
	@echo "  make framework-start FRAMEWORK=strawberry"
	@echo ""
	@echo "======================================================================"
	@echo "For more details, see make/*.mk files or run: make <target>"
	@echo "======================================================================"
