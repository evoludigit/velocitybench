# VelocityBench

Comprehensive GraphQL & REST Framework Performance Benchmarking Suite

**28 frameworks across 8 languages.** Measure throughput, latency, and resources with publication-ready methodology.

## Overview

VelocityBench helps developers choose the right framework with real performance data.

- ✅ 40+ framework implementations across 8 languages
- ✅ 450+ comprehensive tests (schema, query, N+1, performance)
- ✅ Production-ready health checks (Kubernetes-compatible probes)
- ✅ Automated regression detection (statistical analysis)
- ✅ Throughput, latency, and resource analysis
- ✅ Multi-language support (Python, Node.js, Go, Java, Rust, PHP, Ruby, C#)
- ✅ Publication-ready benchmarking methodology

## ⚠️ Intended Use & Security Model

VelocityBench is a **development and benchmarking tool**, optimized for:
- Local framework performance evaluation
- Architectural decision-making with real data
- Educational learning about design patterns
- Publication-ready benchmarking research

**This is NOT a production service.** It intentionally includes:
- Hardcoded test credentials (reduces setup friction)
- No authentication (ensures "testable by anyone")
- No rate limiting (measures true throughput)
- Generated test data only (no sensitive information)

**Security Assumptions:**
- Runs on trusted local machines or private networks
- Not exposed to the internet without additional security layers
- All users have repository access (can modify code/queries)

**Why This Design?** Adding production security features (authentication, rate limiting, TLS) would confound benchmark results with security overhead and defeat the core goal: enabling anyone to clone and benchmark frameworks fairly.

**⚠️ Important:** If you expose `docker-compose` to the internet, you'll have an unauthenticated API. Don't do this. Instead, use VelocityBench locally for benchmarking, then implement production security separately.

## Quick Start

```bash
# Clone repository
git clone https://github.com/velocitybench/velocitybench.git
cd velocitybench

# Start all frameworks
docker-compose up -d

# Run integration tests
./tests/integration/test-all-frameworks.sh

# Execute performance suite
make perf
```

## Documentation

### Core Documentation
- **[SCOPE_AND_LIMITATIONS.md](SCOPE_AND_LIMITATIONS.md)** - What we test and what we don't (benchmark methodology)
- **[TESTING_STANDARDS.md](TESTING_STANDARDS.md)** - Universal testing standards and best practices
- **[SECURITY.md](SECURITY.md)** - Security model and intended use
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute to VelocityBench

### Production Readiness
- **[docs/HEALTH_CHECKS.md](docs/HEALTH_CHECKS.md)** - Health check implementation guide (Kubernetes probes)
- **[docs/REGRESSION_DETECTION_GUIDE.md](docs/REGRESSION_DETECTION_GUIDE.md)** - Performance regression detection system
- **[docs/DEPENDENCY_AUDIT_GUIDE.md](docs/DEPENDENCY_AUDIT_GUIDE.md)** - Security vulnerability scanning
- **[docs/VERSIONING.md](docs/VERSIONING.md)** - Semantic versioning scheme and release process

### Architecture & Design
- **[docs/adr/](docs/adr/)** - Architecture Decision Records (12 ADRs)
- **[docs/api/](docs/api/)** - API documentation and schema reference
- **[docs/DOCKER_COMPOSE.md](docs/DOCKER_COMPOSE.md)** - Docker orchestration guide

### Testing & Quality
- **[testing-templates/](testing-templates/)** - Reusable test templates for all languages
- **[docs/PYTEST_CONFIGURATION.md](docs/PYTEST_CONFIGURATION.md)** - Pytest configuration guide
- **[docs/TEST_COVERAGE_VERIFICATION.md](docs/TEST_COVERAGE_VERIFICATION.md)** - Test infrastructure and coverage report
- **[phase-plans/](phase-plans/)** - Implementation phases and roadmaps

### Future Considerations
- **[docs/SUBSCRIPTION_SUPPORT.md](docs/SUBSCRIPTION_SUPPORT.md)** - GraphQL subscriptions assessment

## Frameworks Included

### GraphQL Frameworks
- Python: Strawberry, Graphene
- TypeScript: Apollo Server, PostGraphile
- Go: gqlgen
- Rust: Async-graphql
- PHP: Laravel (Lighthouse)
- Ruby: Rails (GraphQL)

### REST Frameworks
- Python: FastAPI, Flask
- TypeScript: Express.js
- Go: gin, graphql-go
- Java: Spring Boot
- Rust: Actix
- C#: .NET

### Managed Services
- Hasura (GraphQL)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Adding new frameworks
- Improving tests
- Reporting issues
- Code of conduct

## License

MIT License - See [LICENSE](LICENSE) for details

## Community

- **GitHub Issues**: Report bugs or suggest features
- **Discussions**: Ask questions and share insights
- **Twitter**: [@VelocityBench](https://twitter.com/velocitybench)

---

**Status**: Beta (Health checks, regression detection, and comprehensive documentation complete)
**Latest Release**: v0.2.0
**Last Updated**: 2026-01-30

## Features

### ✅ Benchmarking
- 40+ frameworks across 8 languages (Python, TypeScript, Go, Rust, Java, PHP, Ruby, C#)
- REST and GraphQL API benchmarking
- Trinity Pattern database architecture (optimized for read-heavy workloads)
- JMeter-based load testing with multiple workload profiles

### ✅ Quality Assurance
- 6-dimensional QA testing (Schema, Query, N+1, Consistency, Config, Performance)
- 450+ comprehensive tests across all frameworks
- Automated CI/CD validation

### ✅ Production Observability
- Kubernetes-compatible health checks (liveness, readiness, startup probes)
- Standardized health check libraries for all languages
- Database connectivity and memory monitoring

### ✅ Performance Analysis
- Automated regression detection with statistical analysis
- Baseline management and versioning
- Multiple output formats (CLI, JSON, Markdown for PR comments)
- Configurable thresholds and severity levels

### ✅ Documentation
- 12 Architecture Decision Records (ADRs)
- Comprehensive implementation guides
- API documentation and schema reference
- Security model documentation

For more information, see [docs/](docs/)
