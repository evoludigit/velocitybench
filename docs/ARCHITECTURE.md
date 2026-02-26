# VelocityBench Architecture Overview

This document provides comprehensive architecture diagrams and explanation of VelocityBench's system design.

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        IntegrationTests["Integration Tests<br/>(Smoke, Health)"]
        PerfBench["Performance<br/>Benchmarks<br/>(JMeter)"]
        QAValidator["QA Validators<br/>(Schema, Query,<br/>N+1, Consistency)"]
    end

    subgraph "Framework Layer (38 Implementations)"
        direction LR
        Python["Python<br/>(FastAPI, Flask<br/>Strawberry, Graphene)"]
        NodeJS["Node.js<br/>(Express, Apollo<br/>GraphQL Yoga)"]
        Go["Go<br/>(Gin, gqlgen)"]
        Rust["Rust<br/>(Actix, Async-graphql)"]
        Java["Java<br/>(Spring Boot<br/>Quarkus)"]
        PHP["PHP<br/>(Laravel)"]
        Ruby["Ruby<br/>(Rails)"]
        CSharp["C#<br/>(.NET)"]
    end

    subgraph "Database Layer"
        direction TB
        DB["PostgreSQL<br/>(Primary)<br/>Trinity Pattern<br/>Schema"]
        Cache["Connection Pool<br/>(PgBouncer)"]
        Indexes["Optimized Indexes<br/>(Foreign Keys,<br/>Queries)"]
    end

    subgraph "Infrastructure"
        Docker["Docker Compose<br/>(Orchestration)"]
        HealthChecks["Health Checks<br/>(K8s Probes)"]
        Monitoring["Monitoring<br/>(Prometheus<br/>Metrics)"]
    end

    subgraph "CI/CD Pipeline"
        Lint["Code Quality<br/>(Ruff, Bandit)"]
        Tests["Automated Tests<br/>(Unit, Integration)"]
        SBOM["SBOM Generation<br/>(CycloneDX)"]
        Perf["Performance<br/>Regression"]
    end

    IntegrationTests --> Python
    IntegrationTests --> NodeJS
    IntegrationTests --> Go
    IntegrationTests --> Rust
    IntegrationTests --> Java
    IntegrationTests --> PHP
    IntegrationTests --> Ruby
    IntegrationTests --> CSharp

    PerfBench --> Python
    PerfBench --> NodeJS
    PerfBench --> Go
    PerfBench --> Rust

    Python --> Cache
    NodeJS --> Cache
    Go --> Cache
    Rust --> Cache
    Java --> Cache
    PHP --> Cache
    Ruby --> Cache
    CSharp --> Cache

    Cache --> DB
    Cache --> Indexes

    Docker --> Python
    Docker --> NodeJS
    Docker --> Go
    Docker --> Rust
    Docker --> Java
    Docker --> PHP
    Docker --> Ruby
    Docker --> CSharp

    Docker --> DB

    HealthChecks --> Python
    HealthChecks --> NodeJS
    HealthChecks --> Go
    HealthChecks --> Rust
    HealthChecks --> Java
    HealthChecks --> PHP
    HealthChecks --> Ruby
    HealthChecks --> CSharp

    Monitoring --> Indexes
    Monitoring --> Cache

    Lint --> Python
    Lint --> NodeJS
    Lint --> Go
    Lint --> Rust

    Tests --> Python
    Tests --> NodeJS
    Tests --> Go
    Tests --> Rust

    SBOM --> Python
    SBOM --> NodeJS

    Perf --> Python
    Perf --> NodeJS
    Perf --> Go
    Perf --> Rust
```

## Database Schema - Trinity Pattern

```mermaid
erDiagram
    USERS ||--o{ POSTS : creates
    USERS ||--o{ COMMENTS : writes
    POSTS ||--o{ COMMENTS : receives
    POSTS }o--|| TAGS : tagged_with
    USERS }o--|| ROLES : has

    USERS {
        bigint id PK
        string name
        string email UK
        string avatar_url
        text bio
        timestamp created_at
        timestamp updated_at
    }

    POSTS {
        bigint id PK
        bigint user_id FK
        string title
        text content
        integer view_count
        timestamp created_at
        timestamp updated_at
    }

    COMMENTS {
        bigint id PK
        bigint post_id FK
        bigint user_id FK
        text content
        timestamp created_at
        timestamp updated_at
    }

    TAGS {
        integer id PK
        string name UK
        integer usage_count
    }

    ROLES {
        integer id PK
        string name UK
        text permissions
    }
```

## API Endpoints - REST Layer

```mermaid
graph LR
    Client["Client"]

    subgraph "Health & Status"
        Health["GET /health"]
        Status["GET /status"]
    end

    subgraph "Users API"
        ListUsers["GET /api/users"]
        GetUser["GET /api/users/{id}"]
        CreateUser["POST /api/users"]
        UpdateUser["PUT /api/users/{id}"]
    end

    subgraph "Posts API"
        ListPosts["GET /api/posts"]
        GetPost["GET /api/posts/{id}"]
        CreatePost["POST /api/posts"]
        UpdatePost["PUT /api/posts/{id}"]
        GetUserPosts["GET /api/users/{id}/posts"]
    end

    subgraph "Comments API"
        ListComments["GET /api/comments"]
        GetComment["GET /api/comments/{id}"]
        CreateComment["POST /api/comments"]
        GetPostComments["GET /api/posts/{id}/comments"]
    end

    subgraph "Database"
        DB["PostgreSQL<br/>Connection Pool"]
    end

    Client --> Health
    Client --> ListUsers
    Client --> GetUser
    Client --> ListPosts
    Client --> GetPost

    Health --> DB
    ListUsers --> DB
    GetUser --> DB
    CreateUser --> DB
    ListPosts --> DB
    GetPost --> DB
    ListComments --> DB
    CreateComment --> DB
```

## GraphQL Schema Structure

```mermaid
graph LR
    Query["Query"]
    Mutation["Mutation"]

    subgraph "Query Operations"
        QUser["user(id: ID!): User"]
        QUsers["users(limit: Int offset: Int): [User!]"]
        QPost["post(id: ID!): Post"]
        QPosts["posts(limit: Int offset: Int): [Post!]"]
        QComments["comments(limit: Int offset: Int): [Comment!]"]
    end

    subgraph "Mutation Operations"
        MUser["createUser(name: String! email: String!): User!"]
        MPost["createPost(userId: ID! title: String! content: String!): Post!"]
        MComment["createComment(postId: ID! userId: ID! content: String!): Comment!"]
    end

    subgraph "Types"
        User["User<br/>{ id, name, email, posts[] }"]
        Post["Post<br/>{ id, title, content, author, comments[] }"]
        Comment["Comment<br/>{ id, content, author, post }"]
    end

    Query --> QUser
    Query --> QUsers
    Query --> QPost
    Query --> QPosts
    Query --> QComments

    Mutation --> MUser
    Mutation --> MPost
    Mutation --> MComment

    QUser --> User
    QUsers --> User
    QPost --> Post
    MUser --> User
    MPost --> Post
    MComment --> Comment
    User -.relatesTo.-> Post
    Post -.relatesTo.-> Comment
```

## Docker Compose Service Topology

```mermaid
graph TB
    subgraph "Database Services"
        Postgres["PostgreSQL 16<br/>port: 5433<br/>volume: postgres_data"]
        PgBouncer["PgBouncer<br/>Connection Pool<br/>port: 5434"]
    end

    subgraph "Python Frameworks"
        FastAPI["FastAPI<br/>port: 8003"]
        Flask["Flask<br/>port: 8004"]
        Strawberry["Strawberry<br/>port: 8011"]
        Graphene["Graphene<br/>port: 8002"]
    end

    subgraph "Node.js Frameworks"
        Apollo["Apollo Server<br/>port: 4002"]
        Express["Express REST<br/>port: 8005"]
        Fastify["Fastify<br/>port: 4001"]
    end

    subgraph "Go Frameworks"
        Gin["Gin REST<br/>port: 8006"]
        gqlgen["gqlgen<br/>port: 4010"]
    end

    subgraph "Rust Frameworks"
        Actix["Actix-web<br/>port: 8015"]
        AsyncGraphQL["Async-graphql<br/>port: 8016"]
    end

    subgraph "Java Frameworks"
        SpringBoot["Spring Boot<br/>port: 8010"]
    end

    PgBouncer --> Postgres
    FastAPI --> PgBouncer
    Flask --> PgBouncer
    Strawberry --> PgBouncer
    Graphene --> PgBouncer
    Apollo --> PgBouncer
    Express --> PgBouncer
    Fastify --> PgBouncer
    Gin --> PgBouncer
    gqlgen --> PgBouncer
    Actix --> PgBouncer
    AsyncGraphQL --> PgBouncer
    SpringBoot --> PgBouncer
```

## Virtual Environment Architecture

```mermaid
graph TB
    Root["Root venv<br/>Python 3.12<br/>Blog generation<br/>Makefiles"]

    Database["Database venv<br/>Python 3.11<br/>Schema migration<br/>Seed generation"]

    FastAPI["FastAPI venv<br/>Python 3.12<br/>FastAPI, asyncpg<br/>Pydantic"]

    Flask["Flask venv<br/>Python 3.12<br/>Flask, SQLAlchemy<br/>Psycopg2"]

    Strawberry["Strawberry venv<br/>Python 3.14<br/>Strawberry, asyncpg<br/>GraphQL"]

    Graphene["Graphene venv<br/>Python 3.14<br/>Graphene<br/>SQLAlchemy"]

    QA["QA venv<br/>Python 3.12<br/>pytest, httpx<br/>Framework validators"]

    Storage["External Storage<br/>/data/velocitybench-storage/venvs<br/>(symlinked)"]

    Root -.symlink.-> Storage
    Database -.symlink.-> Storage
    FastAPI -.symlink.-> Storage
    Flask -.symlink.-> Storage
    Strawberry -.symlink.-> Storage
    Graphene -.symlink.-> Storage
    QA -.symlink.-> Storage
```

## Testing Architecture

```mermaid
graph TB
    subgraph "Test Layers"
        Health["Health Checks<br/>(K8s probes)"]
        Integration["Integration Tests<br/>(Smoke, Full)"]
        QA["QA Validators<br/>(Schema, Query,<br/>N+1, Consistency)"]
        Performance["Performance Tests<br/>(Throughput,<br/>Latency, Memory)"]
        Regression["Regression Detection<br/>(Baseline comparison)"]
    end

    subgraph "Test Execution"
        Local["Local: ./tests/integration/"]
        CI["CI/CD: GitHub Actions"]
        Automated["Automated: Daily schedule"]
    end

    subgraph "Test Data"
        Seeds["Seed data<br/>(database/*)"]
        Fixtures["Fixtures<br/>(tests/qa/fixtures)"]
        Baselines["Baselines<br/>(tests/perf/results)"]
    end

    Health --> Local
    Integration --> Local
    QA --> Local
    Performance --> Local

    Local --> CI
    CI --> Automated

    Seeds --> Health
    Seeds --> Integration
    Seeds --> QA
    Seeds --> Performance

    Fixtures --> QA
    Baselines --> Regression

    Regression --> CI
```

## CI/CD Pipeline Flow

```mermaid
graph LR
    Push["git push"]

    subgraph "Tests"
        Unit["Unit Tests<br/>(Python)"]
        Integration["Integration<br/>Tests"]
        Lint["Code Quality<br/>(Ruff)"]
        Type["Type Check<br/>(ty)"]
    end

    subgraph "Security"
        Deps["Dependency<br/>Audit"]
        SBOM["SBOM<br/>Generation"]
        Bandit["Security<br/>Scan"]
    end

    subgraph "Performance"
        PerfTest["Perf Tests"]
        Regression["Regression<br/>Check"]
    end

    subgraph "Results"
        Pass["✅ PASS<br/>Ready to merge"]
        Fail["❌ FAIL<br/>Block merge"]
    end

    Push --> Unit
    Push --> Integration
    Push --> Lint
    Push --> Type
    Push --> Deps
    Push --> SBOM
    Push --> Bandit
    Push --> PerfTest

    Unit --> Regression
    Integration --> Regression
    Lint --> Regression
    Type --> Regression
    Deps --> Regression
    Bandit --> Regression

    PerfTest --> Regression
    Regression --> Pass
    Regression --> Fail
```

## Data Flow - Single Request

```mermaid
sequenceDiagram
    participant Client
    participant Framework
    participant Pool as Connection<br/>Pool
    participant DB as PostgreSQL

    Client->>Framework: GET /api/users/1
    activate Framework
    Framework->>Pool: request connection
    activate Pool
    Pool->>DB: acquire connection
    activate DB
    DB->>Pool: connection acquired
    deactivate DB
    Pool->>Framework: connection ready
    deactivate Pool

    Framework->>DB: SELECT * FROM users WHERE id=1
    activate DB
    DB->>DB: execute query
    DB->>Framework: user row
    deactivate DB

    Framework->>DB: SELECT * FROM posts WHERE user_id=1
    activate DB
    DB->>DB: execute query (with index)
    DB->>Framework: post rows
    deactivate DB

    Framework->>Pool: release connection
    Pool->>DB: return to pool
    deactivate Framework

    Framework->>Client: { user, posts[] }
    Note over Framework: Response serialization<br/>(JSON/GraphQL)
```

## Performance Optimization Layers

```mermaid
graph TB
    subgraph "Query Level"
        Index["Database Indexes<br/>(FK, unique keys)"]
        JoinStrategy["Join Strategy<br/>(eager, lazy, batch)"]
        Pagination["Pagination<br/>(limit, offset)"]
    end

    subgraph "Connection Level"
        Pool["Connection Pooling<br/>(PgBouncer)"]
        KeepAlive["Keep-Alive<br/>(persistent)"]
        Multiplexing["Multiplexing<br/>(C3P0, HikariCP)"]
    end

    subgraph "Framework Level"
        Cache["Response Caching<br/>(Redis, in-memory)"]
        Async["Async/Await<br/>(non-blocking)"]
        Batching["Query Batching<br/>(DataLoader)"]
    end

    subgraph "Application Level"
        Select["Select Fields<br/>(avoid SELECT *)"]
        Denorm["Denormalization<br/>(calculated fields)"]
        Aggregate["Aggregation<br/>(pre-computed stats)"]
    end

    subgraph "Infrastructure Level"
        CPU["CPU Optimization<br/>(tight loops)"]
        Memory["Memory Efficiency<br/>(streaming)"]
        Network["Network Latency<br/>(connection reuse)"]
    end
```

## Deployment Topology - Docker Compose

```mermaid
graph TB
    subgraph "Host System"
        Docker["Docker Engine"]
        Network["Docker Network<br/>(velocitybench_default)"]
        Storage["Volumes<br/>(postgres_data)"]
    end

    subgraph "Containers"
        Postgres["postgres:16-alpine<br/>Memory: 512MB<br/>CPU: 1 core"]
        Framework1["Framework 1<br/>Memory: 256MB<br/>CPU: 1 core"]
        Framework2["Framework 2<br/>Memory: 256MB<br/>CPU: 1 core"]
        Framework3["Framework 3<br/>Memory: 256MB<br/>CPU: 1 core"]
    end

    Docker --> Network
    Docker --> Storage
    Network --> Postgres
    Network --> Framework1
    Network --> Framework2
    Network --> Framework3
    Postgres --> Storage
```

## Key Design Decisions

### 1. Multi-Virtual Environment Architecture
- **Why**: Isolate framework dependencies, prevent conflicts
- **Trade-off**: More disk space vs cleaner isolation
- **Impact**: Can test 38 frameworks simultaneously

### 2. Centralized Connection Pooling
- **Why**: Reduce database connection overhead
- **Trade-off**: Single pool configuration for all frameworks
- **Impact**: More realistic production-like behavior

### 3. Trinity Pattern Schema
- **Why**: Realistic but minimal schema for benchmarking
- **Trade-off**: Not full real-world complexity
- **Impact**: Consistent, reproducible test data

### 4. Health Check System
- **Why**: Kubernetes readiness/liveness probes
- **Trade-off**: Adds 10-20ms overhead
- **Impact**: Production-ready observability

### 5. Six-Dimensional QA Testing
- **Why**: Comprehensive validation across multiple dimensions
- **Trade-off**: Longer test execution time
- **Impact**: Catches regressions early

---

## Related Documentation

- **[ADR-001: Multi-Framework Benchmarking Architecture](adr/ADR-001-multi-framework-architecture.md)**
- **[ADR-011: Trinity Pattern Implementation](adr/ADR-011-trinity-pattern.md)**
- **[REGRESSION_DETECTION_GUIDE.md](REGRESSION_DETECTION_GUIDE.md)**
- **[HEALTH_CHECKS.md](HEALTH_CHECKS.md)**

---

**Last Updated**: 2026-01-31
**Architecture Version**: 1.0
**Maintainers**: VelocityBench Core Team
