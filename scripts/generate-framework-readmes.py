#!/usr/bin/env python3
"""
Generate README.md files for all frameworks lacking documentation.

This script reads framework-config.json and generates comprehensive README files
for each framework with standardized structure and framework-specific information.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


FRAMEWORK_ROOT = Path(__file__).parent.parent / "frameworks"
CONFIG_FILE = FRAMEWORK_ROOT.parent / "tests" / "integration" / "framework-config.json"

# Language-specific setup and command templates
LANGUAGE_TEMPLATES = {
    "python": {
        "test_command": "pytest tests/ --cov=src --cov-report=html",
        "setup": """### Setup Virtual Environment
```bash
cd frameworks/{framework}
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```""",
        "run": """### Run the Server
```bash
export DATABASE_URL="postgresql://velocitybench:password@localhost:5432/velocitybench_test"
python -m uvicorn app:app --reload --host 0.0.0.0 --port {port}
# or for Flask:
# python app.py
```""",
        "dev_commands": """### Development Commands

```bash
# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Format code
ruff format .

# Lint code
ruff check .

# Type check
ty check .
```""",
    },
    "typescript": {
        "test_command": "npm test -- --coverage",
        "setup": """### Setup Dependencies
```bash
cd frameworks/{framework}
npm install
# or
yarn install
```""",
        "run": """### Run the Server
```bash
npm run dev
# or
npm start
```""",
        "dev_commands": """### Development Commands

```bash
# Run tests with coverage
npm test -- --coverage

# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check
```""",
    },
    "go": {
        "test_command": "go test -v ./... -cover",
        "setup": """### Setup
```bash
cd frameworks/{framework}
go mod download
go mod tidy
```""",
        "run": """### Run the Server
```bash
export DATABASE_URL="postgres://velocitybench:password@localhost:5432/velocitybench_test"
go run main.go
# or
go run .
```""",
        "dev_commands": """### Development Commands

```bash
# Run tests with coverage
go test -v ./... -coverprofile=coverage.out
go tool cover -html=coverage.out

# Format code
gofmt -w .
go vet ./...

# Run linter
golangci-lint run
```""",
    },
    "rust": {
        "test_command": "cargo test --verbose",
        "setup": """### Prerequisites
- Rust 1.70+ (install from https://rustup.rs/)

### Setup
```bash
cd frameworks/{framework}
cargo check  # Verify setup
```""",
        "run": """### Run the Server
```bash
export DATABASE_URL="postgres://velocitybench:password@localhost:5432/velocitybench_test"
cargo run --release
```""",
        "dev_commands": """### Development Commands

```bash
# Check compilation
cargo check

# Run tests
cargo test --verbose

# Format code
cargo fmt

# Lint code (strict)
cargo clippy -- -D warnings

# Build release
cargo build --release
```""",
    },
    "java": {
        "test_command": "mvn test",
        "setup": """### Prerequisites
- Java 17+ (JDK)
- Maven 3.8+

### Setup
```bash
cd frameworks/{framework}
mvn clean install
```""",
        "run": """### Run the Server
```bash
export DATABASE_URL="jdbc:postgresql://localhost:5432/velocitybench_test"
mvn spring-boot:run
# or just:
java -jar target/app.jar
```""",
        "dev_commands": """### Development Commands

```bash
# Run tests
mvn test

# Check code quality
mvn clean verify

# Format code
mvn spotless:apply

# Build jar
mvn clean package
```""",
    },
    "php": {
        "test_command": "php artisan test  # or: vendor/bin/phpunit",
        "setup": """### Prerequisites
- PHP 8.1+
- Composer

### Setup
```bash
cd frameworks/{framework}
composer install
cp .env.example .env
php artisan key:generate  # For Laravel
```""",
        "run": """### Run the Server
```bash
# For Laravel
php artisan serve --host=0.0.0.0 --port={port}

# For standalone Composer projects
php -S 0.0.0.0:{port}
```""",
        "dev_commands": """### Development Commands

```bash
# Run tests
php artisan test  # Laravel
vendor/bin/phpunit  # Standard

# Format code
vendor/bin/pint

# Lint code
vendor/bin/phpstan analyze
```""",
    },
    "ruby": {
        "test_command": "bundle exec rspec",
        "setup": """### Prerequisites
- Ruby 3.2+
- Bundler

### Setup
```bash
cd frameworks/{framework}
bundle install
bundle exec rake db:create db:migrate
```""",
        "run": """### Run the Server
```bash
# For Rails
bundle exec rails server --port {port}

# For Hanami
bundle exec hanami server --port {port}
```""",
        "dev_commands": """### Development Commands

```bash
# Run tests
bundle exec rspec

# Format code
bundle exec rubocop -A

# Check code quality
bundle exec brakeman

# Database migrations
bundle exec rake db:migrate
```""",
    },
    "csharp": {
        "test_command": "dotnet test",
        "setup": """### Prerequisites
- .NET 6.0+ SDK

### Setup
```bash
cd frameworks/{framework}
dotnet restore
```""",
        "run": """### Run the Server
```bash
dotnet run --configuration Release
# or
dotnet watch run
```""",
        "dev_commands": """### Development Commands

```bash
# Run tests
dotnet test

# Format code
dotnet format

# Check code quality
dotnet analyzers

# Build
dotnet build --configuration Release
```""",
    },
    "scala": {
        "test_command": "sbt test",
        "setup": """### Prerequisites
- Java 17+
- sbt 1.8+

### Setup
```bash
cd frameworks/{framework}
sbt update
```""",
        "run": """### Run the Server
```bash
sbt run
# or for Play Framework:
sbt "run {port}"
```""",
        "dev_commands": """### Development Commands

```bash
# Run tests
sbt test

# Format code
sbt scalafmtAll

# Lint code
sbt scalacOptions

# Build assembly
sbt assembly
```""",
    },
    "haskell": {
        "test_command": "N/A - Hasura is configuration-based",
        "setup": """### Setup Hasura
Hasura is a GraphQL engine that auto-generates APIs from PostgreSQL schemas.
It does not require code setup - configuration is done via the Hasura console.

See Hasura documentation: https://hasura.io/docs""",
        "run": """### Run via Docker Compose
```bash
docker-compose --profile hasura up
```

Hasura console will be available at: http://localhost:{port}""",
        "dev_commands": """No development commands - Hasura is configuration-based.""",
    },
}


def load_framework_config():
    """Load framework configuration from JSON."""
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {CONFIG_FILE} not found", file=sys.stderr)
        sys.exit(1)


def get_language(framework_name, config):
    """Detect framework language from config."""
    frameworks = config.get("frameworks", {})
    fw_data = frameworks.get(framework_name, {})
    language = fw_data.get("language", "").lower()

    # Map language names to template keys
    language_map = {
        "python": "python",
        "typescript": "typescript",
        "nodejs": "typescript",
        "go": "go",
        "rust": "rust",
        "java": "java",
        "scala": "scala",
        "php": "php",
        "ruby": "ruby",
        "csharp": "csharp",
        "c#": "csharp",
        ".net": "csharp",
        "haskell": "haskell",
    }

    return language_map.get(language, "python")  # Default to Python


def get_framework_type(framework_name, config):
    """Get framework type (REST, GraphQL, etc)."""
    frameworks = config.get("frameworks", {})
    fw_data = frameworks.get(framework_name, {})
    return fw_data.get("type", "unknown").upper()


def get_framework_port(framework_name, config):
    """Get framework port from config."""
    frameworks = config.get("frameworks", {})
    fw_data = frameworks.get(framework_name, {})
    return fw_data.get("port", "XXXX")


def get_framework_health(framework_name, config):
    """Get framework health check endpoint."""
    frameworks = config.get("frameworks", {})
    fw_data = frameworks.get(framework_name, {})
    return fw_data.get("health", "/health")


def get_framework_endpoint(framework_name, config):
    """Get main API endpoint."""
    frameworks = config.get("frameworks", {})
    fw_data = frameworks.get(framework_name, {})
    return fw_data.get("endpoint", "/graphql")


def generate_readme(framework_name, config):
    """Generate README content for a framework."""
    language = get_language(framework_name, config)
    fw_type = get_framework_type(framework_name, config)
    port = get_framework_port(framework_name, config)
    health_endpoint = get_framework_health(framework_name, config)
    api_endpoint = get_framework_endpoint(framework_name, config)

    # Get language-specific templates
    lang_template = LANGUAGE_TEMPLATES.get(language, LANGUAGE_TEMPLATES["python"])

    # Format framework name for display
    display_name = " ".join(word.capitalize() for word in framework_name.split("-"))

    # Build README content
    readme = f"""# {display_name}

{fw_type} API implementation for VelocityBench framework benchmarking.

## 📋 Overview

This {fw_type} implementation provides a standardized API endpoint for the VelocityBench performance testing suite. It enables direct performance comparison across different frameworks and languages.

## 🏗️ Technology Stack

- **Language**: {language.capitalize()}
- **API Type**: {fw_type}
- **Framework**: {display_name}
- **Database**: PostgreSQL
- **Port**: {port}

## 🚀 Quick Start

{lang_template['setup'].format(framework=framework_name, port=port)}

{lang_template['run'].format(framework=framework_name, port=port)}

### Verify the Server

```bash
# Health check
curl http://localhost:{port}{health_endpoint}

# API endpoint
curl http://localhost:{port}{api_endpoint}
```

## 🧪 Testing

### Run Tests

```bash
{lang_template['test_command']}
```

### Test Coverage

The test suite validates:
- ✅ Health check endpoint
- ✅ API schema correctness
- ✅ GraphQL/REST endpoint functionality
- ✅ Database connectivity
- ✅ Error handling
- ✅ Performance baseline

{lang_template['dev_commands']}

## 📡 API Endpoints

### Health Check
```http
GET {health_endpoint}
```
**Response**: {{"status": "ok"}}

### Main API Endpoint
```http
{fw_type.upper()} {api_endpoint}
```

For GraphQL frameworks, use GraphQL queries.
For REST frameworks, refer to the implementation's endpoint documentation.

## 🐳 Docker

### Build
```bash
cd frameworks/{framework_name}
docker build -t velocitybench-{framework_name} .
```

### Run with Docker Compose
```bash
docker-compose --profile {framework_name} up -d
```

The framework will be available at: http://localhost:{port}

## 🔗 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgres://velocitybench:password@localhost:5432/velocitybench_test | Database connection string |
| `PORT` | {port} | Server port |
| `LOG_LEVEL` | info | Logging level (debug, info, warn, error) |

### Database Schema

The framework expects these tables:
- `benchmark.tb_user` - User data
- `benchmark.tb_post` - Post data
- `benchmark.tb_comment` - Comment data

## 🧩 Project Structure

```
frameworks/{framework_name}/
├── src/ or app/          # Source code
├── tests/                # Test files
├── Dockerfile            # Container definition
├── .dockerignore         # Docker exclusions
├── requirements.txt or equivalents
└── README.md             # This file
```

## 🐛 Troubleshooting

### Database Connection Failed
- Ensure PostgreSQL is running
- Check DATABASE_URL environment variable
- Verify database credentials
- Run: `psql $DATABASE_URL -c "SELECT 1"`

### Port Already in Use
```bash
# Find process using port {port}
lsof -i :{port}
# or kill it
kill -9 <PID>
```

### Build or Dependency Issues
```bash
# Clean and rebuild
# Python: rm -rf .venv && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
# Node.js: rm -rf node_modules package-lock.json && npm install
# Go: go clean -cache && go mod tidy
# Rust: cargo clean && cargo build
# Java: mvn clean install
# PHP: rm -rf vendor composer.lock && composer install
# Ruby: bundle clean --force && bundle install
```

## 📚 Further Reading

- **VelocityBench**: See main [README.md](../../README.md)
- **Framework Official Docs**: Check framework's official documentation
- **Testing Guide**: See [TESTING_STANDARDS.md](../../docs/testing/TESTING_STANDARDS.md)
- **CI/CD Setup**: See [.github/workflows](../../.github/workflows)

## 📝 Version History

- **1.0.0** ({datetime.now().strftime('%Y-%m-%d')}) - Initial implementation

## 🤝 Contributing

When making changes:
1. Ensure tests pass: `{lang_template['test_command']}`
2. Format code according to language standards
3. Update this README if adding new features
4. Submit PR with description of changes

## 📄 License

MIT License - see main project LICENSE file

---

**Framework**: {display_name}
**Language**: {language.capitalize()}
**API Type**: {fw_type}
**Port**: {port}
**Status**: Active in CI/CD Pipeline ✅
"""

    return readme


def main():
    """Generate README files for all frameworks."""
    config = load_framework_config()
    frameworks_dir = FRAMEWORK_ROOT

    if not frameworks_dir.exists():
        print(f"Error: {frameworks_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    # Get list of frameworks to process
    all_frameworks = config.get("frameworks", {}).keys()

    # Filter to frameworks that don't have README
    missing_readme = []
    for framework in sorted(all_frameworks):
        readme_path = frameworks_dir / framework / "README.md"
        if not readme_path.exists():
            missing_readme.append(framework)

    if not missing_readme:
        print("✅ All frameworks already have README files!")
        return 0

    print(f"📝 Generating README files for {len(missing_readme)} frameworks...\n")

    generated = 0
    skipped = 0
    failed = 0

    for framework in missing_readme:
        framework_dir = frameworks_dir / framework

        # Skip if directory doesn't exist
        if not framework_dir.exists():
            print(f"⊘ Skipped: {framework} (directory not found)")
            skipped += 1
            continue

        try:
            readme_path = framework_dir / "README.md"

            # Don't overwrite existing files
            if readme_path.exists():
                print(f"⊘ Skipped: {framework} (README already exists)")
                skipped += 1
                continue

            # Generate content
            content = generate_readme(framework, config)

            # Write file
            with open(readme_path, "w") as f:
                f.write(content)

            print(f"✓ Generated: {framework}")
            generated += 1

        except Exception as e:
            print(f"✗ Failed: {framework} - {e}", file=sys.stderr)
            failed += 1

    # Summary
    print(f"\n{'='*50}")
    print(f"✅ Generated: {generated}")
    print(f"⊘ Skipped: {skipped}")
    if failed > 0:
        print(f"✗ Failed: {failed}")
    print(f"{'='*50}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
