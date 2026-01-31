# Java Spring Boot

HYBRID API implementation for VelocityBench framework benchmarking.

## 📋 Overview

This HYBRID implementation provides a standardized API endpoint for the VelocityBench performance testing suite. It enables direct performance comparison across different frameworks and languages.

## 🏗️ Technology Stack

- **Language**: Java
- **API Type**: HYBRID
- **Framework**: Java Spring Boot
- **Database**: PostgreSQL
- **Port**: 8018

## 🚀 Quick Start

### Prerequisites
- Java 17+ (JDK)
- Maven 3.8+

### Setup
```bash
cd frameworks/java-spring-boot
mvn clean install
```

### Run the Server
```bash
export DATABASE_URL="jdbc:postgresql://localhost:5432/velocitybench_test"
mvn spring-boot:run
# or just:
java -jar target/app.jar
```

### Verify the Server

```bash
# Health check
curl http://localhost:8018/health

# API endpoint
curl http://localhost:8018/graphql
```

## 🧪 Testing

### Run Tests

```bash
mvn test
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
# Run tests
mvn test

# Check code quality
mvn clean verify

# Format code
mvn spotless:apply

# Build jar
mvn clean package
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```
**Response**: {"status": "ok"}

### Main API Endpoint
```http
HYBRID /graphql
```

For GraphQL frameworks, use GraphQL queries.
For REST frameworks, refer to the implementation's endpoint documentation.

## 🐳 Docker

### Build
```bash
cd frameworks/java-spring-boot
docker build -t velocitybench-java-spring-boot .
```

### Run with Docker Compose
```bash
docker-compose --profile java-spring-boot up -d
```

The framework will be available at: http://localhost:8018

## 🔗 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgres://velocitybench:password@localhost:5432/velocitybench_test | Database connection string |
| `PORT` | 8018 | Server port |
| `LOG_LEVEL` | info | Logging level (debug, info, warn, error) |

### Database Schema

The framework expects these tables:
- `benchmark.tb_user` - User data
- `benchmark.tb_post` - Post data
- `benchmark.tb_comment` - Comment data

## 🧩 Project Structure

```
frameworks/java-spring-boot/
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
# Find process using port 8018
lsof -i :8018
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
1. Ensure tests pass: `mvn test`
2. Format code according to language standards
3. Update this README if adding new features
4. Submit PR with description of changes

## 📄 License

MIT License - see main project LICENSE file

---

**Framework**: Java Spring Boot
**Language**: Java
**API Type**: HYBRID
**Port**: 8018
**Status**: Active in CI/CD Pipeline ✅
