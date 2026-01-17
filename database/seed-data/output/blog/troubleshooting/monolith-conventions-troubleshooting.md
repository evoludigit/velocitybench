# **Debugging Monolith Conventions: A Troubleshooting Guide**

## **Introduction**
The **Monolith Conventions** pattern encapsulates a structured approach to organizing a monolithic application by enforcing consistent naming, directory structures, configuration, and best practices across the entire codebase. While this pattern improves maintainability, adherence issues can lead to **inconsistency bugs, deployment failures, and performance bottlenecks**.

This guide provides a **practical, action-oriented** approach to debugging common Monolith Conventions-related issues in a fast-paced development environment.

---

## **1. Symptom Checklist: Identifying Monolith Conventions Issues**
Before diving into fixes, verify if the issue stems from Monolith Conventions violations. Check for:

| **Symptom** | **Possible Cause** | **Quick Verification** |
|-------------|-------------------|----------------------|
| **Inconsistent naming** (e.g., `user` vs. `users` in API endpoints) | Missing or poorly enforced naming conventions |
| **Broken migrations** (`MigrationNotFound`, `SchemaMismatch`) | Database schema drift due to inconsistent table/column naming |
| **Dependency conflicts** (`ImportError`, `ModuleNotFound`) | Improper package/module organization (e.g., misplaced services) |
| **Configuration drift** (e.g., `app.config` vs. `server.config`) | Non-standardized config file locations/naming |
| **Slow builds/deploys** | Unoptimized build scripts due to inconsistent script placement |
| **Runtime errors** (e.g., `AttributeError`, `InvalidArgument`) | Inconsistent data types, serialization formats, or validation rules |
| **Hard-to-debug logs** | Missing or misplaced logging configurations |
| **Security vulnerabilities** (e.g., hardcoded secrets) | Non-standardized secrets management (e.g., `.env` files in wrong locations) |

**Action:** If multiple symptoms appear, focus on **naming, directory structure, and configuration** first.

---

## **2. Common Issues & Fixes**

### **Issue 1: Inconsistent Naming Across the Codebase**
**Symptoms:**
- `user_service.py` vs. `users_service.py` in different modules.
- API endpoints like `/v1/user` and `/v2/users`.
- Database columns `user_id` vs. `userID`.

**Root Cause:**
Lack of **code style enforcement** (e.g., missing `.pre-commit-hooks`, static analysis failures).

**Fixes:**

#### **A. Enforce Naming via Linters & Formatters**
Add **pre-commit hooks** (using `pre-commit` or `husky`) to enforce conventions:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace

  - repo: https://github.com/psf/black
    rev: 23.10.0
    hooks:
      - id: black
        args: [--safe]  # Prevents accidental overwrites

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ["--extend-ignore=E501"]  # Ignore line length if needed
```
**Fix:** Run `pre-commit run --all-files` to auto-correct violations.

#### **B. Use a Naming Convention Enforcement Tool**
For Python, tools like **`pylint`** or **`pydocstyle`** can enforce docstring/naming rules:
```python
# pylint rules in .pylintrc
[FORMAT]
max-line-length=120

[Naming]
class-name-fixes=lowercase
method-name-fixes=lowercase
variable-name-fixes=lowercase
```

**Fix:** Run `pylint --generate-rcfile` to auto-generate rules, then adjust.

---

### **Issue 2: Database Schema Mismatches (Broken Migrations)**
**Symptoms:**
- `ALIAS NOT FOUND` in SQL queries.
- `Column 'user_id' does not exist` errors.

**Root Cause:**
Manual SQL edits, inconsistent column naming, or missing migrations.

**Fixes:**

#### **A. Standardize Migration Files**
Ensure migrations follow a **consistent naming pattern** (e.g., `YYYYMMDD_HHMM_description.py`).
```python
# Corrected migration file
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('users', '20231015_1200_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
    ]
```

**Fix:** Rename mismatched migrations and regenerate `sqlmigrate` files:
```bash
python manage.py makemigrations --name fix_email_field --empty
```

#### **B. Use a Migration Lockdown System**
Prevent accidental schema changes:
```bash
# Example: Block schema changes in non-develop branches
git diff --cached --name-only | grep -E '\.(py|sql)$' | grep -v 'migrations' || echo "Schema changes not allowed!"
```

---

### **Issue 3: Dependency Conflicts**
**Symptoms:**
- `ImportError: Cannot import 'service' from 'wrong_module'`.
- Build failures due to missing `requirements.txt` entries.

**Root Cause:**
Improper package structure or missing `pyproject.toml`/`setup.py` dependencies.

**Fixes:**

#### **A. Standardize Package Structure**
Enforce a **monorepo-like structure** (even in a single repo):
```
monolith/
├── config/          # Global configs (e.g., `settings.py`)
├── apps/            # Feature modules (e.g., `users/`, `auth/`)
│   └── users/
│       ├── migrations/
│       ├── models.py
│       └── services.py
└── scripts/         # Deployment/DB scripts
```

**Fix:** Use `pip-tools` to manage dependencies:
```bash
pip-compile --upgrade  # Update dependencies
pip-sync              # Ensure consistency
```

#### **B. Use Absolute Imports**
Replace relative imports (`from .. import x`) with absolute ones:
```python
# Wrong:
from ..utils import validate_email

# Right:
from apps.users.utils import validate_email
```

**Fix:** Run `isort` to auto-format imports:
```bash
pip install isort
isort . --atomic
```

---

### **Issue 4: Configuration Drift**
**Symptoms:**
- `SettingNotFound` (e.g., missing `DB_HOST`).
- Different config files in dev/stage/prod.

**Root Cause:**
Hardcoded configs or inconsistent `.env` usage.

**Fixes:**

#### **A. Standardize Config File Locations**
Use a **single `settings.py`** with environment-specific overrides:
```python
# config/settings.py
import os

DEBUG = os.getenv("DEBUG", "False") == "True"
DATABASE_URL = os.getenv("DATABASE_URL", "default_db")
```

**Fix:** Create a **config loader script**:
```bash
# scripts/load-config.sh
export $(grep -v '^#' .env | xargs)
```

#### **B. Enforce `.env` Validation**
Use `python-dotenv` with schema validation:
```python
from dotenv import dotenv_values
from pydantic import BaseSettings, ValidationError

class Settings(BaseSettings):
    DB_HOST: str
    SECRET_KEY: str

try:
    config = Settings(**dotenv_values(".env"))
except ValidationError as e:
    print(f"Invalid config: {e}")
```

---

### **Issue 5: Build & Deployment Failures**
**Symptoms:**
- `Error: No such file or directory` during `make deploy`.
- Slow `pip install` due to duplicated packages.

**Root Cause:**
Non-standardized build scripts or missing `pyproject.toml`.

**Fixes:**

#### **A. Standardize `pyproject.toml`**
Use **POETRY** or **PDM** for dependency management:
```toml
# pyproject.toml
[tool.poetry.dependencies]
Django = "^4.2"
psycopg2 = "^2.9"
python-dotenv = "^1.0"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

**Fix:** Run `poetry lock` to update dependencies.

#### **B. Use a Build Lockfile**
Prevent inconsistent builds by pinning versions:
```bash
poetry lock --no-update  # Freeze current versions
```

---

## **3. Debugging Tools & Techniques**
| **Tool** | **Use Case** | **Example Command** |
|----------|-------------|---------------------|
| **`pre-commit`** | Catch naming/style violations early | `pre-commit run --all-files` |
| **`pylint`/`mypy`** | Static type checking | `mypy . --strict` |
| **`sqlparse`** | Debug SQL queries | `sqlparse.format("SELECT * FROM user WHERE email='x'")` |
| **`docker-compose`** | Reproduce config issues | `docker-compose up --build` |
| **`pytest --cov`** | Find untested code | `pytest --cov=apps/users` |
| **`griffe`** | Inspect Django models | `griffe list models` |
| **`black`/`isort`** | Format code to convention | `black .` |
| **`git blame`** | Trace naming changes | `git blame apps/users/models.py` |

**Advanced Debugging:**
- **Use `git log --oneline --grep="user"`** to find naming inconsistencies.
- **`docker exec -it <container> bash`** to inspect runtime configs.
- **`pytest --capture=no`** to see raw logs for config errors.

---

## **4. Prevention Strategies**
To avoid Monolith Conventions issues in the future:

### **A. Automate Enforcement**
1. **Linters + Formatters (Pre-commit)**
   - Enforce **Black, Flake8, isort** via hooks.
2. **Test Naming Conventions**
   - Write **unit tests** that verify naming (e.g., `pytest-naming`).
3. **Database Schema Testing**
   - Use **`django-db-test-utils`** to validate migrations.

### **B. Document & Enforce Standards**
- **Write a `CONVENTIONS.md`** file with:
  - Naming rules (e.g., `snake_case` for DB columns).
  - Directory structure rules.
  - Config file locations.
- **Run a "Convention Compliance Sprint"** every 3 months.

### **C. Use Infrastructure as Code (IaC)**
- **Terraform/Ansible**: Ensure deployments follow config standards.
- **Docker Compose**: Standardize environments.

### **D. Monitor for Drift**
- **Git Hooks**: Block PRs with violations.
- **CI Checks**: Fail builds if conventions are violated.
  ```yaml
  # .github/workflows/check-conventions.yml
  name: Check Conventions
  on: [push]
  jobs:
    lint:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - run: pip install pre-commit
        - run: pre-commit run --all-files || exit 1
  ```

### **E. Educate the Team**
- **Pair Programming**: Review new code for convention compliance.
- **Run "Convention Deep Dives"** in team meetings.
- **Gamify Compliance**: Leaderboard for PRs with no violations.

---

## **5. Summary of Key Actions**
| **Issue** | **Quick Fix** | **Long-Term Prevention** |
|-----------|--------------|--------------------------|
| Inconsistent naming | Run `pre-commit`, `isort`, `black` | Enforce linters via hooks |
| Broken migrations | Regenerate migrations, check `sqlmigrate` | Use `pytest-django` for schema tests |
| Dependency conflicts | Run `pip-compile`, `pip-sync` | Use `poetry` or `pdm` |
| Config drift | Centralize configs in `settings.py` | Use `python-dotenv` + schema validation |
| Build failures | Standardize `pyproject.toml` | IaC for deployments |

---

## **Final Checklist Before Deployment**
✅ **All pre-commit hooks pass.**
✅ **Database migrations are frozen (`git add apps/users/migrations/`).**
✅ **Dependencies are pinned (`poetry lock`).**
✅ **Configs are validated (`.env` schema checks).**
✅ **Build artifacts are reproducible (`docker build`).**

By following this guide, you can **quickly diagnose and fix Monolith Conventions issues** while preventing future drift. 🚀