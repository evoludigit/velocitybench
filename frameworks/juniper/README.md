# Juniper

GRAPHQL API implementation for VelocityBench framework benchmarking.

## 📋 Overview

This GRAPHQL implementation provides a standardized API endpoint for the VelocityBench performance testing suite. It enables direct performance comparison across different frameworks and languages.

## 🏗️ Technology Stack

- **Language**: Rust
- **API Type**: GRAPHQL
- **Framework**: Juniper
- **Database**: PostgreSQL
- **Port**: 8033

## 🚀 Quick Start

### Prerequisites
- Rust 1.70+ (install from https://rustup.rs/)

### Setup
```bash
cd frameworks/juniper
cargo check  # Verify setup
```

### Run the Server
```bash
export DATABASE_URL="postgres://velocitybench:password@localhost:5432/velocitybench_test"
cargo run --release
```

### Verify the Server

```bash
# Health check
curl http://localhost:8033/health

# API endpoint
curl http://localhost:8033/graphql
```

## 🧪 Testing

### Run Tests

```bash
cargo test --verbose
```

### Test Coverage

The test suite validates:
- ✅ Health check endpoint
- ✅ API schema correctness
- ✅ GraphQL/REST endpoint functionality
- ✅ Database connectivity
- ✅ Error handling
- ✅ Performance baseline

### Development Commands

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
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```
**Response**: {"status": "ok"}

### Main API Endpoint
```http
GRAPHQL /graphql
```

For GraphQL frameworks, use GraphQL queries.
For REST frameworks, refer to the implementation's endpoint documentation.

## 🐳 Docker

### Build
```bash
cd frameworks/juniper
docker build -t velocitybench-juniper .
```

### Run with Docker Compose
```bash
docker-compose --profile juniper up -d
```

The framework will be available at: http://localhost:8033

## 🔗 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgres://velocitybench:password@localhost:5432/velocitybench_test | Database connection string |
| `PORT` | 8033 | Server port |
| `LOG_LEVEL` | info | Logging level (debug, info, warn, error) |

### Database Schema

The framework expects these tables:
- `benchmark.tb_user` - User data
- `benchmark.tb_post` - Post data
- `benchmark.tb_comment` - Comment data

## 🧩 Project Structure

```
frameworks/juniper/
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
# Find process using port 8033
lsof -i :8033
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

- **1.0.0** (2026-01-31) - Initial implementation

## 🤝 Contributing

When making changes:
1. Ensure tests pass: `cargo test --verbose`
2. Format code according to language standards
3. Update this README if adding new features
4. Submit PR with description of changes

## 📄 License

MIT License - see main project LICENSE file

---

**Framework**: Juniper
**Language**: Rust
**API Type**: GRAPHQL
**Port**: 8033
**Status**: Active in CI/CD Pipeline ✅
