# ADR-006: Authentication-by-Design Exclusion

**Status**: Accepted
**Date**: 2025-01-30
**Author**: VelocityBench Team

## Context

VelocityBench is designed to benchmark the performance characteristics of different API frameworks across multiple languages. A common question arises: "Why don't the implementations include authentication and authorization?"

The challenges with including authentication:

1. **Fair Comparison**: Different auth strategies (JWT, OAuth2, session-based, API keys) have vastly different performance characteristics
2. **Implementation Complexity**: Each framework has different auth middleware/libraries with varying maturity levels
3. **Setup Friction**: Authentication adds significant setup complexity (secret management, token generation, user management)
4. **Benchmarking Focus**: We want to measure framework routing, serialization, and database query performance, not authentication overhead
5. **Security Misconceptions**: Including auth might suggest these implementations are production-ready (they are NOT)

## Decision

**Explicitly exclude authentication and authorization from all framework implementations.**

### What This Means

1. **No authentication middleware** in any framework implementation
2. **No authorization checks** on any endpoint
3. **Public endpoints only** - all data is accessible without credentials
4. **Clear documentation** that these implementations are NOT production-ready
5. **Security disclaimer** in README and SECURITY.md

### What We Document Instead

- **SECURITY.md**: Clearly states these are benchmarking implementations, not production templates
- **README.md**: Prominent warning about lack of authentication
- **INTENDED_USE.md**: Explains the tool is for framework comparison, not deployment

### Example Implementation

```python
# FastAPI - NO authentication
@app.get("/users")
async def get_users():
    return await db.fetch_all("SELECT * FROM v_users")

# NOT production-ready - no:
# - Authentication check
# - Authorization for data access
# - Rate limiting
# - Input validation beyond basic types
```

## Consequences

### Positive

✅ **Fair Benchmarking**: All frameworks tested under identical (no-auth) conditions
✅ **Simple Setup**: Developers can run benchmarks without configuring auth systems
✅ **Clear Metrics**: Performance numbers reflect routing + DB, not auth overhead
✅ **Rapid Development**: Adding new frameworks is faster without auth boilerplate
✅ **Focus**: Keeps codebase focused on framework comparison, not security best practices
✅ **Educational**: Shows pure framework performance without confounding variables

### Negative

❌ **Not Production-Ready**: Implementations cannot be deployed as-is to production
❌ **Incomplete Examples**: Developers looking for auth patterns must look elsewhere
❌ **Security Education Gap**: Doesn't teach authentication best practices
❌ **Potential Misuse**: Someone might deploy these implementations publicly without adding auth
❌ **Unrealistic Workloads**: Real apps always have auth overhead

## Alternatives Considered

### Alternative 1: Include Basic Authentication

- **Approach**: Add simple JWT or API key authentication to all frameworks
- **Pros**: More realistic, demonstrates auth patterns, production-closer
- **Cons**:
  - Unfair comparison (implementation quality varies across frameworks)
  - Adds 20-30% complexity to each framework
  - Requires secret management in benchmarking setup
  - Auth performance varies wildly (bcrypt cost, JWT signing algorithm)
- **Rejected**: Violates fair benchmarking principle

### Alternative 2: Optional Authentication Layer

- **Approach**: Provide auth as a pluggable module that can be enabled/disabled
- **Pros**: Best of both worlds - benchmarks without auth, examples with auth
- **Cons**:
  - 2x maintenance burden (maintain auth and no-auth code paths)
  - Complexity in framework integrations
  - Still doesn't solve "which auth strategy" problem
- **Rejected**: Maintenance complexity not worth the benefit

### Alternative 3: Reverse Proxy Authentication

- **Approach**: Put all frameworks behind a reverse proxy (nginx, Envoy) with auth
- **Pros**: Uniform auth layer, no per-framework implementation
- **Cons**:
  - Adds network hop (affects benchmarks)
  - Proxy becomes single point of failure
  - Doesn't help developers learn framework-specific auth
- **Rejected**: Adds latency and complexity to benchmarking

### Alternative 4: Separate "Production Templates" Repository

- **Approach**: Create a separate repo with production-ready implementations (with auth)
- **Pros**: Clean separation of concerns, production examples available
- **Cons**:
  - Double maintenance burden
  - Templates drift from benchmarks
  - Not the goal of VelocityBench
- **Rejected**: Out of scope for this project

## Related Decisions

- **ADR-001**: Trinity Pattern - Focus on data layer, not application layer concerns
- **ADR-002**: Framework Isolation - Each framework is self-contained, simplifying no-auth decision
- **ADR-003**: Multi-Language Support - Adding auth across 8 languages would be significant overhead

## Implementation Status

✅ **Complete** - All 39 frameworks have no authentication

## Security Documentation

This decision is prominently documented in:

1. **SECURITY.md** (lines 15-30):
   ```markdown
   ## What VelocityBench Is NOT

   - ❌ Production-ready API templates
   - ❌ Security best practice examples
   - ❌ Deployment-ready applications

   VelocityBench implementations intentionally exclude:
   - Authentication and authorization
   - Rate limiting
   - Input sanitization beyond basic type checking
   - HTTPS/TLS configuration
   - Secret management
   ```

2. **README.md** - Warning badge and security notice

3. **INTENDED_USE.md** - Detailed explanation of benchmarking vs. production use

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - Security risks these implementations don't address
- [SECURITY.md](../../SECURITY.md) - VelocityBench security model
- [Benchmarking Best Practices](https://www.brendangregg.com/methodology.html) - Fair comparison principles
- [Trinity Pattern (ADR-001)](001-trinity-pattern.md) - Data layer focus
