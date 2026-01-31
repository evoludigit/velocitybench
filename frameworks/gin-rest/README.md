# Gin Rest

REST API implementation for VelocityBench framework benchmarking.

## 📋 Overview

This REST implementation provides a standardized API endpoint for the VelocityBench performance testing suite. It enables direct performance comparison across different frameworks and languages.

## 🏗️ Technology Stack

- **Language**: Go
- **API Type**: REST
- **Framework**: Gin Rest
- **Database**: PostgreSQL
- **Port**: 8006

## 🚀 Quick Start

### Setup
```bash
cd frameworks/gin-rest
go mod download
go mod tidy
```

### Run the Server
```bash
export DATABASE_URL="postgres://velocitybench:password@localhost:5432/velocitybench_test"
go run main.go
# or
go run .
```

### Verify the Server

```bash
# Health check
curl http://localhost:8006/health

# API endpoint
curl http://localhost:8006/users
```

## 🧪 Testing

### Run Tests

```bash
go test -v ./... -cover
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
# Run tests with coverage
go test -v ./... -coverprofile=coverage.out
go tool cover -html=coverage.out

# Format code
gofmt -w .
go vet ./...

# Run linter
golangci-lint run
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```
**Response**: {"status": "ok"}

### Main API Endpoint
```http
REST /users
```

For GraphQL frameworks, use GraphQL queries.
For REST frameworks, refer to the implementation's endpoint documentation.

## 🐳 Docker

### Build
```bash
cd frameworks/gin-rest
docker build -t velocitybench-gin-rest .
```

### Run with Docker Compose
```bash
docker-compose --profile gin-rest up -d
```

The framework will be available at: http://localhost:8006

## 🔗 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgres://velocitybench:password@localhost:5432/velocitybench_test | Database connection string |
| `PORT` | 8006 | Server port |
| `LOG_LEVEL` | info | Logging level (debug, info, warn, error) |

### Database Schema

The framework expects these tables:
- `benchmark.tb_user` - User data
- `benchmark.tb_post` - Post data
- `benchmark.tb_comment` - Comment data

## 🧩 Project Structure

```
frameworks/gin-rest/
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
# Find process using port 8006
lsof -i :8006
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
1. Ensure tests pass: `go test -v ./... -cover`
2. Format code according to language standards
3. Update this README if adding new features
4. Submit PR with description of changes

## 📄 License

MIT License - see main project LICENSE file

---

**Framework**: Gin Rest
**Language**: Go
**API Type**: REST
**Port**: 8006
**Status**: Active in CI/CD Pipeline ✅
