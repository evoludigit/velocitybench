# Shared variables for all modular Makefiles
# This file is included by Makefile and all make/*.mk files

# Project paths (resolve from main Makefile location, not this file)
PROJECT_ROOT := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))
VENV_PATH := $(PROJECT_ROOT)venv
VENV_PYTHON := $(VENV_PATH)/bin/python
VENV_ACTIVATE := $(VENV_PATH)/bin/activate
GENERATOR_DIR := $(PROJECT_ROOT)database/seed-data/generator
GENERATOR_SCRIPT := generate_blog_vllm.py
OUTPUT_DIR := $(PROJECT_ROOT)database/seed-data/output/blog
