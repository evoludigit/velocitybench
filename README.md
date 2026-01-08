# VelocityBench

Comprehensive GraphQL & REST Framework Performance Benchmarking Suite

**28 frameworks across 8 languages.** Measure throughput, latency, and resources with publication-ready methodology.

## Overview

VelocityBench helps developers choose the right framework with real performance data.

- ✅ 28+ framework implementations
- ✅ 450+ comprehensive tests
- ✅ Throughput, latency, and resource analysis
- ✅ Multi-language support (Python, Node.js, Go, Java, Rust, PHP, Ruby, C#)
- ✅ Publication-ready benchmarking methodology

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

- **[SCOPE_AND_LIMITATIONS.md](SCOPE_AND_LIMITATIONS.md)** - What we test and what we don't (benchmark methodology)
- **[TESTING_STANDARDS.md](TESTING_STANDARDS.md)** - Universal testing standards and best practices
- **[testing-templates/](testing-templates/)** - Reusable test templates for all languages
- **[docs/](docs/)** - Complete framework documentation
- **[phase-plans/](phase-plans/)** - Implementation phases and roadmaps
- **[.github/workflows/](​.github/workflows/)** - CI/CD pipeline configuration

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

**Status**: Beta (Phase 9 in progress)
**Latest Release**: v0.1.0-beta
**Last Updated**: 2026-01-08

For more information, see [docs/](docs/) and [phase-plans/](phase-plans/)
