# Site — build and publish the interactive benchmark explainer (site/).

# The run JSON the site ships. Override to build a different run:
#   make site-build SITE_RUN=reports/…/other.json
SITE_RUN ?= reports/hetzner-2026-07-22/bench-hetzner-2026-07-25-median.json
SITE_DIST := $(PROJECT_ROOT)site/dist

.PHONY: site-build site-test site-publish

site-build: ## Build the static site from SITE_RUN into site/dist
	python3 $(PROJECT_ROOT)site/build.py $(SITE_RUN) --out $(SITE_DIST)

site-test: ## Run the site contract tests (QA venv)
	$(PROJECT_ROOT)tests/qa/.venv/bin/python -m pytest $(PROJECT_ROOT)site/tests/

site-publish: ## Build + push site/dist to gh-pages (GitHub Pages)
	$(PROJECT_ROOT)scripts/publish-site.sh $(SITE_RUN)
