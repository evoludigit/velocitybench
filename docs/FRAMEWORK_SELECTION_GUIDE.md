# VelocityBench Framework Selection Guide

This guide helps you choose the best framework for your use case based on real performance data and implementation characteristics from VelocityBench.

## Quick Decision Tree

```
Start here: What's your primary need?

├─ "I need maximum throughput"
│  └─ → See: Throughput Champions (High-Performance Section)
│
├─ "I want lowest latency"
│  └─ → See: Latency Leaders (Performance Section)
│
├─ "I need GraphQL"
│  └─ → Are you already committed to a language?
│     ├─ Python? → Strawberry (feature-rich) or Graphene (battle-tested)
│     ├─ Node.js? → Apollo Server (mature) or GraphQL Yoga (lightweight)
│     ├─ Go? → gqlgen (fast, code-gen)
│     ├─ Rust? → Async-graphql (safe, performant)
│     ├─ Java? → Spring GraphQL (enterprise) or Quarkus (cloud-native)
│     └─ Other? → See Language Comparison Table
│
├─ "I need REST API"
│  └─ → See REST Comparison Table
│
└─ "I'm not sure - help me decide"
   └─ → Use Profile-Based Selection below
```

---

## Profile-Based Selection

### Profile 1: Performance-First Startup

**You want**: Maximum throughput, low latency, minimal overhead
**You care about**: Raw speed, resource efficiency, cost
**You don't care about**: Feature richness, code generation

**Recommended frameworks**:

| Rank | Framework | Language | Type | Throughput | Latency | Memory |
|------|-----------|----------|------|-----------|---------|--------|
| 1st | Actix-Web | Rust | REST | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 2nd | FastAPI | Python | REST | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 3rd | Gin | Go | REST | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 4th | Express.js | Node | REST | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

**GraphQL Alternative**:
- **Async-graphql** (Rust) - Blazing fast, safe
- **gqlgen** (Go) - Code-generated, efficient

**Why**:
- Rust frameworks have zero-cost abstractions
- Go combines speed with productivity
- Python FastAPI is fastest pure-Python solution
- Node.js Express is lightweight, battle-tested

---

### Profile 2: Enterprise Application

**You want**: Stability, maturity, extensive ecosystem, enterprise support
**You care about**: Team knowledge, frameworks knowledge, deployment patterns
**You don't care about**: Bleeding-edge features, minimal framework size

**Recommended frameworks**:

| Rank | Framework | Language | Type | Maturity | Ecosystem | Support |
|------|-----------|----------|------|----------|-----------|---------|
| 1st | Spring Boot | Java | REST | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 2nd | Django/DRF | Python | REST | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 3rd | Rails | Ruby | REST | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 4th | Apollo Server | Node | GraphQL | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**Why**:
- Spring Boot dominates enterprise Java
- Django has 15+ year track record
- Rails convention-over-configuration reduces decision fatigue
- Apollo Server is GraphQL standard in enterprise

**Additional benefits**:
- Extensive paid support available
- Large talent pool (easy hiring)
- Proven deployment patterns
- Security track records

---

### Profile 3: Rapid Prototyping & MVP

**You want**: Fast development, minimal boilerplate, good defaults
**You care about**: Developer productivity, time-to-market, flexibility
**You don't care about**: Peak performance, zero-dependency philosophy

**Recommended frameworks**:

| Rank | Framework | Language | Type | Velocity | Boilerplate | Learning Curve |
|------|-----------|----------|------|----------|------------|-----------------|
| 1st | Django | Python | REST | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ |
| 2nd | Rails | Ruby | REST | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ |
| 3rd | Fastify | Node | REST/GraphQL | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| 4th | Spring Boot | Java | REST | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

**Why**:
- Django: Batteries included, ORM, admin panel, auth built-in
- Rails: "magic" that works, forces good patterns
- Fastify: Minimal but extensible, fast to iterate
- Spring Boot: Good tooling, quick scaffolding with Spring Initializr

---

### Profile 4: Cloud-Native & Microservices

**You want**: Container-friendly, easy deployment, cloud patterns
**You care about**: Startup time, memory footprint, horizontal scaling
**You don't care about**: Traditional deployment patterns

**Recommended frameworks**:

| Rank | Framework | Language | Type | Startup | Memory | Scaling |
|------|-----------|----------|------|---------|--------|---------|
| 1st | Quarkus | Java | REST/GraphQL | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 2nd | Actix-Web | Rust | REST | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 3rd | FastAPI | Python | REST | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 4th | Gin | Go | REST | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**Why**:
- Quarkus: Built for Kubernetes, subsecond startup, GraalVM native
- Actix-Web: Minimal memory, fast scaling
- FastAPI: async-first, efficient resource use
- Gin: Small binaries, fast deployment

---

### Profile 5: GraphQL Specialist

**You want**: Best-in-class GraphQL features (subscriptions, batching, etc.)
**You care about**: GraphQL maturity, developer experience, type safety
**You don't care about**: REST support, REST-centric features

**Recommended frameworks**:

| Rank | Framework | Language | Subscriptions | Type Safety | Maturity |
|------|-----------|----------|---------------|------------|----------|
| 1st | Apollo Server | Node | ✅ | ✅ TypeScript | ⭐⭐⭐⭐⭐ |
| 2nd | Strawberry | Python | ✅ | ✅ Python | ⭐⭐⭐⭐ |
| 3rd | Async-graphql | Rust | ✅ | ✅ Rust | ⭐⭐⭐⭐ |
| 4th | Spring GraphQL | Java | ✅ | ✅ Java | ⭐⭐⭐⭐ |

**Why**:
- Apollo: GraphQL reference implementation, huge ecosystem
- Strawberry: Modern Python approach, type hints, great DX
- Async-graphql: Rust safety guarantees, excellent performance
- Spring GraphQL: Enterprise-ready, integrates with Spring ecosystem

---

## Language-Based Comparison

### Python

| Framework | Type | Use Case | Pros | Cons | Throughput |
|-----------|------|----------|------|------|-----------|
| **FastAPI** | REST | REST APIs, fast development | Fast, async, auto docs, easy | Newer ecosystem | ⭐⭐⭐⭐ |
| **Flask** | REST | Lightweight REST APIs | Simple, flexible, proven | No ORM built-in | ⭐⭐⭐ |
| **Django** | REST | Full-featured web apps | Batteries included, mature | Monolithic, slower | ⭐⭐⭐ |
| **Strawberry** | GraphQL | Modern GraphQL APIs | Type-safe, Pythonic, modern | Newer | ⭐⭐⭐⭐ |
| **Graphene** | GraphQL | Flexible GraphQL APIs | Mature, flexible, proven | Verbose | ⭐⭐⭐ |

**Recommendation**: FastAPI for new REST projects, Django for enterprise, Strawberry for GraphQL

---

### Node.js / TypeScript

| Framework | Type | Use Case | Pros | Cons | Throughput |
|-----------|------|----------|------|------|-----------|
| **Express.js** | REST | Classic REST APIs | Simple, mature, huge community | Minimal framework | ⭐⭐⭐ |
| **Fastify** | REST | High-performance REST | Fast, modular, great DX | Younger ecosystem | ⭐⭐⭐⭐ |
| **Apollo Server** | GraphQL | Production GraphQL | Mature, feature-rich, standard | Heavier | ⭐⭐⭐⭐ |
| **GraphQL Yoga** | GraphQL | Lightweight GraphQL | Minimal, flexible, fast | Fewer built-ins | ⭐⭐⭐⭐ |

**Recommendation**: Express for traditional projects, Fastify for performance, Apollo for GraphQL

---

### Go

| Framework | Type | Use Case | Pros | Cons | Throughput |
|-----------|------|----------|------|------|-----------|
| **Gin** | REST | Fast REST APIs | Minimal, blazing fast, simple | Less batteries | ⭐⭐⭐⭐ |
| **gqlgen** | GraphQL | Type-safe GraphQL | Code-generated, safe, fast | More boilerplate | ⭐⭐⭐⭐⭐ |

**Recommendation**: Gin for REST, gqlgen for GraphQL. Go is excellent for both.

---

### Rust

| Framework | Type | Use Case | Pros | Cons | Throughput |
|-----------|------|----------|------|------|-----------|
| **Actix-Web** | REST | Maximum performance REST | Fastest, safe, async | Steeper learning curve | ⭐⭐⭐⭐⭐ |
| **Async-graphql** | GraphQL | High-performance GraphQL | Type-safe, fast, modern | Newer ecosystem | ⭐⭐⭐⭐⭐ |

**Recommendation**: Rust for performance-critical systems where memory and CPU matter

---

### Java

| Framework | Type | Use Case | Pros | Cons | Throughput |
|-----------|------|----------|------|------|-----------|
| **Spring Boot** | REST | Enterprise REST APIs | Mature, ecosystem, support | Heavy, startup time | ⭐⭐⭐⭐ |
| **Spring GraphQL** | GraphQL | Enterprise GraphQL | Integrates with Spring | Heavy | ⭐⭐⭐⭐ |
| **Quarkus** | Both | Cloud-native Java | Fast startup, low memory | Newer, smaller ecosystem | ⭐⭐⭐⭐ |

**Recommendation**: Spring Boot for traditional enterprise, Quarkus for cloud-native

---

## Performance Comparison

### REST API Throughput (Requests/sec)
*Higher is better. Baseline: FastAPI = 1x*

```
Actix-Web    ████████████████ 4.2x
Gin          ███████████████ 3.9x
FastAPI      ████████ 1.0x
Spring Boot  ██████ 0.7x
Django       ████ 0.5x
Express.js   ███ 0.4x
```

### GraphQL Query Throughput (Requests/sec)
*Higher is better. Baseline: Apollo Server = 1x*

```
gqlgen           ███████████████ 3.5x
Async-graphql    ██████████████ 3.2x
Strawberry       ████████ 1.8x
Apollo Server    ████████ 1.0x
Spring GraphQL   ██████ 0.8x
Graphene         ███ 0.5x
```

### Memory Usage (MB, lower is better)
```
Gin              ██ 25MB
Actix-Web        ██ 28MB
Go-gqlgen        ██ 32MB
FastAPI          ████ 80MB
Async-graphql    ████ 85MB
Express.js       ████ 90MB
Spring Boot      ████████ 200MB
Django           ████████ 210MB
```

### Startup Time (seconds, lower is better)
```
Gin              ▌ 0.1s
Actix-Web        ▌ 0.2s
FastAPI          ▌ 0.4s
Express.js       ▌ 0.5s
Quarkus          ▌ 0.8s (with GraalVM)
Apollo Server    ▌ 1.2s
Spring Boot      ███████ 3.5s (traditional)
Django           ████ 2.1s
```

---

## Feature Comparison Matrix

| Feature | FastAPI | Django | Spring Boot | Apollo | Strawberry | gqlgen | Actix |
|---------|---------|--------|-------------|--------|-----------|--------|-------|
| **Type** | REST | REST | REST | GraphQL | GraphQL | GraphQL | REST |
| **Language** | Python | Python | Java | Node | Python | Go | Rust |
| **Async** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **ORM** | ❌ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| **Auth** | ❌ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| **Type Safety** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Startup** | ⚡⚡⚡ | ⚡⚡ | ⚡ | ⚡⚡ | ⚡⚡⚡ | ⚡⚡⚡⚡ | ⚡⚡⚡⚡ |
| **Learning** | Easy | Medium | Hard | Medium | Easy | Hard | Hard |
| **Maturity** | Medium | Very High | Very High | Very High | Medium | Medium | Medium |

---

## Decision Checklist

Before choosing, ask yourself:

### Must-Have Requirements
- [ ] Which language is your team expert in?
- [ ] REST or GraphQL (or both)?
- [ ] Cloud-native required (Kubernetes)?
- [ ] Enterprise support needed?
- [ ] Startup time critical?

### Performance Requirements
- [ ] Throughput target (req/sec)?
- [ ] Latency target (ms)?
- [ ] Memory constraints?
- [ ] CPU constraints?

### Team & Business
- [ ] Team size and experience level?
- [ ] Time-to-market critical?
- [ ] Long-term maintenance commitment?
- [ ] Hiring pool size for framework?

### Feature Requirements
- [ ] Authentication/Authorization built-in?
- [ ] ORM needed?
- [ ] Admin UI needed?
- [ ] GraphQL subscriptions?
- [ ] File upload support?

---

## Migration Paths

### If You Outgrow Your Current Framework

**From Express → Fastify**
- Similar syntax, better performance
- Effort: Low (plugin API compatible)

**From Django → FastAPI**
- Performance improvement, async
- Effort: Medium (rebuild views, keep ORM)

**From REST → GraphQL**
- Apollo Server (Node) or Strawberry (Python)
- Effort: High (schema redesign)

**From Spring Boot → Quarkus**
- Drop-in replacement, cloud-native
- Effort: Low to Medium

---

## Resources

- **Benchmarking Data**: Run `./tests/integration/smoke-test.sh` to see real performance
- **Framework Repos**: See `frameworks/*/README.md` for each implementation
- **API Specs**: See `docs/api/` for REST and GraphQL specifications
- **Performance Details**: See `docs/REGRESSION_DETECTION_GUIDE.md` for methodology

---

## Still Not Sure?

1. **Check the repo** - Browse `frameworks/` directory
2. **Run tests** - Execute `./tests/integration/test-all-frameworks.sh`
3. **Compare side-by-side** - Deploy two frameworks locally
4. **Ask the community** - Open a GitHub issue with your requirements

---

**Last updated**: 2026-01-31
**Questions?** See [CONTRIBUTING.md](CONTRIBUTING.md) or open an issue.

Good luck choosing! 🚀
