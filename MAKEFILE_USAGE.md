# Makefile Usage Guide - Blog Generation

This Makefile provides convenient commands for generating blog posts from patterns using the vLLM local model.

## Quick Start

```bash
# Show available commands
make help

# Check if virtual environment is set up
make venv-check

# Generate blog posts for a specific pattern
make blog-fraisier
make blog-webhooks
make blog-git-providers
make blog-cqrs
make blog-history
make blog-multi-provider
make blog-multi-env

# Generate all blog posts (all patterns)
make blog-all
```

## Available Commands

### Blog Generation

#### Generate All Blogs
```bash
make blog-all
```
Generates blog posts for every pattern in the corpus using vLLM. Creates:
- Tutorial blogs (beginner, intermediate, advanced)
- Troubleshooting guides
- Reference documentation

Output: `database/seed-data/output/blog/`

#### Generate Fraisier Deployment Pattern Blogs
```bash
make blog-fraisier
```
Generates 5 blog posts for the Fraisier deployment orchestration pattern:
- `fraisier-deployment-orchestration-tutorial-beginner.md`
- `fraisier-deployment-orchestration-tutorial-intermediate.md`
- `fraisier-deployment-orchestration-tutorial-advanced.md`
- `fraisier-deployment-orchestration-troubleshooting.md`
- `fraisier-deployment-orchestration-reference.md`

#### Generate Webhook Deployment Blogs
```bash
make blog-webhooks
```
Generates 5 blog posts for webhook event-driven deployment pattern.

#### Generate Git Provider Abstraction Blogs
```bash
make blog-git-providers
```
Generates 5 blog posts for multi-provider Git abstraction pattern.

#### Generate CQRS Deployment Pattern Blogs
```bash
make blog-cqrs
```
Generates 5 blog posts for CQRS deployment state management pattern.

#### Generate Deployment History Tracking Blogs
```bash
make blog-history
```
Generates 5 blog posts for deployment history and audit trail pattern.

#### Generate Multi-Git-Provider Blogs
```bash
make blog-multi-provider
```
Generates 5 blog posts for mixed Git provider configuration pattern.

#### Generate Multi-Environment Blogs
```bash
make blog-multi-env
```
Generates 5 blog posts for multi-environment deployment configuration pattern.

#### Generate for Specific Pattern
```bash
# Generate tutorial (beginner)
make blog-pattern PATTERN=fraisier-deployment-orchestration

# Generate intermediate tutorial
make blog-pattern PATTERN=fraisier-deployment-orchestration DEPTH=intermediate

# Generate advanced tutorial
make blog-pattern PATTERN=fraisier-deployment-orchestration DEPTH=advanced

# Generate troubleshooting guide
make blog-pattern PATTERN=fraisier-deployment-orchestration TYPE=troubleshooting

# Generate reference documentation
make blog-pattern PATTERN=fraisier-deployment-orchestration TYPE=reference
```

**Parameters:**
- `PATTERN` (required): Pattern ID
- `TYPE` (optional): `tutorial`, `troubleshooting`, `reference`, `comparison` (default: `tutorial`)
- `DEPTH` (optional): `beginner`, `intermediate`, `advanced` (default: `beginner`)

### Information Commands

#### List All Patterns
```bash
make blog-list
```
Displays all discovered patterns in the corpus, including newly added Fraisier patterns.

#### Check Virtual Environment
```bash
make venv-check
```
Verifies that the virtual environment is set up and working:
```
✓ Virtual environment found at /home/lionel/code/velocitybench/venv
✓ Python: Python 3.13.7
```

#### Show Virtual Environment Info
```bash
make venv-info
```
Shows details about the virtual environment setup.

### Setup Commands

#### Create Virtual Environment
```bash
make venv-setup
```
Creates the virtual environment if it doesn't exist and installs dependencies:
- Creates `venv/` directory
- Installs `requests` and `pyyaml` packages
- Sets up Python 3.13

(Runs automatically if venv exists - safe to run multiple times)

### Cleanup Commands

#### Clean Generated Blog Files
```bash
make blog-clean
```
Removes all generated markdown files from `database/seed-data/output/blog/`.

## How It Works

The Makefile does the following:

1. **Locates the virtual environment** at `velocitybench/venv`
2. **Uses the venv Python** to run the generator script
3. **Calls** `database/seed-data/generator/generate_blog_vllm.py`
4. **Passes pattern ID, type, and depth** to the generator
5. **Saves output** to `database/seed-data/output/blog/`

## Environment Variables

The virtual environment is automatically activated via the Makefile. You can also manually activate it:

```bash
source venv/bin/activate
```

## vLLM Server Requirement

The blog generation scripts require vLLM to be running:

```bash
# Start vLLM server (if not already running)
vllm-switch implementer

# Verify vLLM is running
curl http://localhost:8000/v1/models

# If not available, ensure it's set up
vllm-switch status
```

## File Locations

- **Makefile**: `/home/lionel/code/velocitybench/Makefile`
- **Generator Script**: `database/seed-data/generator/generate_blog_vllm.py`
- **Pattern Files**: `database/seed-data/corpus/patterns/fraiseql/*.yaml`
- **Generated Blogs**: `database/seed-data/output/blog/`
  - Tutorials: `blog/tutorials/`
  - Troubleshooting: `blog/troubleshooting/`
  - Reference: `blog/reference/`
  - Comparisons: `blog/comparisons/`

## Example Workflows

### Generate All Fraisier Blogs
```bash
cd /home/lionel/code/velocitybench
make blog-fraisier
```

### Generate Beginner Tutorials for All New Patterns
```bash
make blog-fraisier DEPTH=beginner
make blog-webhooks DEPTH=beginner
make blog-git-providers DEPTH=beginner
make blog-cqrs DEPTH=beginner
make blog-history DEPTH=beginner
make blog-multi-provider DEPTH=beginner
make blog-multi-env DEPTH=beginner
```

### Generate Specific Blog Type
```bash
# Troubleshooting guides for all Fraisier patterns
make blog-pattern PATTERN=fraisier-deployment-orchestration TYPE=troubleshooting
make blog-pattern PATTERN=fraisier-multi-environment TYPE=troubleshooting
make blog-pattern PATTERN=webhook-event-driven-deployment TYPE=troubleshooting
make blog-pattern PATTERN=git-provider-abstraction TYPE=troubleshooting
make blog-pattern PATTERN=fraisier-cqrs-deployment TYPE=troubleshooting
make blog-pattern PATTERN=deployment-history-tracking TYPE=troubleshooting
make blog-pattern PATTERN=fraisier-multi-git-provider TYPE=troubleshooting
```

### Generate and Verify
```bash
# Generate blogs for one pattern
make blog-fraisier

# Check what was created
find database/seed-data/output/blog -name "*fraisier-deployment*" -type f

# List all generated files
ls -lh database/seed-data/output/blog/tutorials/
ls -lh database/seed-data/output/blog/troubleshooting/
ls -lh database/seed-data/output/blog/reference/
```

## Troubleshooting

### "Virtual environment NOT found"
```bash
make venv-setup
```

### "vLLM server not running"
```bash
# Check vLLM status
vllm-switch status

# Start vLLM
vllm-switch implementer
```

### Blog generation is slow
- Generation with vLLM typically takes 1-2 minutes per blog post
- For 7 new patterns with 5 blogs each, expect 30-60 minutes total
- You can generate individual patterns while waiting

### Permission denied errors
```bash
# Make Makefile executable (if needed)
chmod +x Makefile

# Make generator script executable (if needed)
chmod +x database/seed-data/generator/generate_blog_vllm.py
```

## Tips

1. **Run one pattern at a time** for faster feedback:
   ```bash
   make blog-fraisier
   # Watch the output, verify blogs are created
   ```

2. **Generate in background** (if on Linux/Mac):
   ```bash
   make blog-all &
   # Continue working while generation happens
   ```

3. **Check progress**:
   ```bash
   # In another terminal
   watch -n 5 'find database/seed-data/output/blog -type f -name "*.md" | wc -l'
   ```

4. **See what would be generated**:
   ```bash
   make blog-list
   # Shows all patterns that would be processed
   ```

## Adding New Patterns

To generate blogs for a new pattern:

1. Add YAML file to `database/seed-data/corpus/patterns/fraiseql/`
2. Run: `make blog-pattern PATTERN=<new-pattern-id>`
3. Or update Makefile with shortcut target

Example:
```makefile
blog-newpattern: venv-check
	@echo "Generating New Pattern blogs..."
	@cd $(GENERATOR_DIR) && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern my-new-pattern --type tutorial --depth beginner && \
		$(VENV_PYTHON) $(GENERATOR_SCRIPT) --pattern my-new-pattern --type tutorial --depth intermediate && \
		... (and so on)
```

## Performance Notes

- **vLLM Generation Speed**: ~20-30 tokens/second
- **Typical Blog Post**: 1000-2000 words = 2000-4000 tokens = 2-3 minutes per post
- **7 new patterns × 5 blogs each = 35 posts = 70-210 minutes (~2-3.5 hours)**

To speed up:
1. Generate beginner blogs only initially
2. Generate intermediate/advanced afterwards
3. Use multiple terminals to generate different patterns in parallel
