# Security Policy

VelocityBench is a **benchmarking and development tool**, not a production application. This document outlines the security model, reporting procedures, and guidelines.

## Table of Contents

- [Security Model](#security-model)
- [Scope](#scope)
- [Known Limitations](#known-limitations)
- [Reporting Security Issues](#reporting-security-issues)
- [Dependency Management](#dependency-management)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## Security Model

### Intended Use

VelocityBench is designed for:
- ✅ Framework benchmarking in controlled environments
- ✅ Local development and testing
- ✅ Research and comparison of framework implementations
- ✅ Educational purposes and learning

VelocityBench is **NOT** intended for:
- ❌ Production use with real user data
- ❌ Internet-facing deployments without additional security layers
- ❌ Handling sensitive or personally identifiable information (PII)
- ❌ Production-grade security requirements

### Security by Design

#### 1. No Authentication/Authorization

**Rationale**: VelocityBench is designed for testability. Removing authentication allows:
- Anyone to run and validate the suite
- Fair performance comparison (no auth overhead)
- Faster local setup and iteration

**When to add**: If deploying any framework beyond localhost, implement authentication at the reverse proxy or application level.

#### 2. Hardcoded Test Data

**Rationale**: Reduces setup complexity and enables reproducible benchmarks.

**Security consideration**: Use different database credentials and isolation for production deployments.

#### 3. No Rate Limiting

**Rationale**: Benchmarks need to measure true throughput without throttling.

**When to add**: Production deployments must implement rate limiting at the infrastructure layer (reverse proxy, API gateway).

#### 4. Simple Database Setup

**Rationale**: Minimal dependencies make the tool accessible to developers of all backgrounds.

**In production**: Use strong credentials, encrypted connections, and proper access controls.

---

## Scope

### What We Secure

✅ **Code Quality**
- Type hints on all functions
- Linting with Ruff (16 rules)
- Formatted code (88 char line length)

✅ **Framework Test Safety**
- Unit tests for all frameworks
- Integration tests
- Coverage tracking (70% minimum)

✅ **Dependency Security**
- Regular dependency updates
- Vulnerability scanning in CI/CD
- Minimal, focused dependencies

✅ **Data Handling**
- No sensitive data storage
- Environment-based configuration
- Secrets excluded from git

### What We DON'T Provide

❌ **Production-Grade Security**
- No encryption-at-rest
- No encryption-in-transit by default
- No authentication/authorization
- No audit logging
- No rate limiting

These **must** be added by the user when deploying beyond localhost.

---

## Known Limitations

### 1. Network Security

**Limitation**: Frameworks run on localhost without TLS/SSL by default.

**Mitigation**:
```bash
# For development: acceptable
# For any network exposure: add reverse proxy with TLS
# Example with nginx:
upstream framework {
    server localhost:8000;
}

server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;

    location / {
        proxy_pass http://framework;
    }
}
```

### 2. Database Security

**Limitation**: PostgreSQL uses hardcoded credentials (user: `benchmark`, password: `password`).

**Mitigation**:
```bash
# In .env for production deployments
DB_USER=secure_user
DB_PASSWORD=$(openssl rand -base64 32)  # Strong random password
DB_HOST=postgresql.internal  # Not exposed to internet
DB_SSL=require  # Enforce encrypted connections
```

### 3. No Input Validation

**Limitation**: Benchmarking frameworks intentionally minimize validation to test API layers.

**Mitigation**: Deploy behind request validation layer:
```bash
# Use API gateway or WAF
# - CloudFlare
- AWS API Gateway
- Kong
- Nginx + ModSecurity
```

### 4. Framework Dependencies

**Limitation**: Each framework brings its own dependency ecosystem.

**Mitigation**:
- Run `pip audit` / `npm audit` regularly
- Keep dependencies updated
- Use virtual environments (project already does this)

---

## Reporting Security Issues

### DO NOT Create Public GitHub Issues

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. **Report** via [GitHub Security Advisories](https://github.com/evoludigit/velocitybench/security/advisories)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if applicable)

### Expected Response Time

- **Critical**: 24 hours
- **High**: 3 days
- **Medium**: 1 week
- **Low**: Best effort

### Disclosure Timeline

Once a fix is developed:
1. We prepare a release
2. Users are notified
3. Fix is published
4. Security advisory is posted (if applicable)

---

## Dependency Management

### Vulnerable Dependencies

We continuously monitor for vulnerabilities using:

```bash
# Python
pip audit                    # Check Python dependencies
pip audit --fix             # Auto-fix vulnerabilities

# Node.js
npm audit                   # Check JavaScript dependencies
npm audit fix               # Auto-fix vulnerabilities

# General
git dependency updates every 2 weeks
```

### Minimum Viable Dependencies

VelocityBench keeps dependencies minimal:

**Core (Root)**:
- `requests` - HTTP client
- `pyyaml` - Configuration parsing

**Database**:
- `psycopg2-binary` - PostgreSQL driver
- `sqlalchemy` - ORM (if used)

**Frameworks**: As specified per framework

### Removing Dependencies

Before adding a dependency, ask:
- Is it necessary for core functionality?
- Does it have a smaller alternative?
- What's the maintenance status?
- Any known security issues?

---

## Best Practices

### For Development

```bash
# 1. Use virtual environments (project enforces this)
python -m venv venv
source venv/bin/activate

# 2. Keep dependencies updated
pip install --upgrade -r requirements.txt
pip audit

# 3. Never commit .env files
# .gitignore already excludes: .env, .env.local, .env.*.local

# 4. Use pre-commit hooks
pre-commit install
pre-commit run --all-files

# 5. Run linting and type checks
make quality
```

### For Framework Implementations

```python
# ✅ DO: Validate input at boundaries
def create_user(email: str) -> User:
    """Create a user.

    Args:
        email: User email (validated by caller)
    """
    if not is_valid_email(email):
        raise ValueError(f"Invalid email: {email}")
    return User(email=email)

# ❌ DON'T: Hardcode credentials in framework code
API_KEY = "sk-1234567890abcdef"  # WRONG

# ✅ DO: Use environment variables
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")
```

### For Database Operations

```python
# ✅ DO: Use parameterized queries (ORMs handle this)
user = User.query.filter_by(id=user_id).first()

# ❌ DON'T: String interpolation (SQL injection risk)
query = f"SELECT * FROM users WHERE id={user_id}"
```

---

## Security Checklist

Before deploying VelocityBench beyond localhost:

- [ ] **Authentication**: Add auth layer (OAuth, JWT, etc.)
- [ ] **Authorization**: Implement role-based access control
- [ ] **Transport Security**: TLS/SSL encryption for all traffic
- [ ] **Database Security**: Strong credentials, encrypted connections
- [ ] **Input Validation**: Add request validation layer
- [ ] **Output Encoding**: Prevent injection attacks
- [ ] **Logging**: Audit trail of important events
- [ ] **Monitoring**: Health checks, error tracking
- [ ] **Backup/Recovery**: Regular backups, disaster recovery plan
- [ ] **Secrets Management**: Use vault for credentials
- [ ] **Dependency Scanning**: Regular security audits
- [ ] **WAF/DDoS Protection**: If publicly accessible

---

## FAQ

### Q: Is VelocityBench safe to use?

**A**: For its intended purpose (local benchmarking and development) - yes. It's safe to run locally on your machine.

For any network exposure beyond localhost - no. Add security layers first.

### Q: Can I run VelocityBench on the internet?

**A**: Not without significant security hardening:
- Add authentication (OAuth, JWT)
- Use TLS/SSL encryption
- Implement rate limiting
- Add WAF/DDoS protection
- Use strong database credentials
- Implement request validation

### Q: What if I find a security bug?

**A**: Email security details (don't post publicly). Include:
- What's vulnerable
- How to reproduce
- What impact it has
- How to fix it

### Q: Are there any hardcoded secrets in the code?

**A**: No. The project uses:
- Environment variables for configuration
- Default test credentials (not secrets)
- `.gitignore` to prevent secret commits

### Q: What about the frameworks - are they secure?

**A**: Frameworks implement security relative to their purpose:
- REST APIs: Basic request/response handling
- GraphQL: Query execution without authorization
- Each framework can be hardened per security requirements

### Q: How do I report a non-security issue?

**A**: Use GitHub Issues (public reporting is fine for non-security bugs).

### Q: Is data encrypted?

**A**: No, VelocityBench doesn't implement encryption:
- Database: Plaintext (add TLS for network exposure)
- API: No TLS by default (add reverse proxy with SSL)
- Data at rest: Plaintext (add disk encryption if needed)

### Q: What about PII (personal data)?

**A**: Don't use real PII in VelocityBench. The test data is:
- Generated/synthetic
- Non-sensitive
- Appropriate only for testing

---

## Security Contacts

For security issues:
- 🔒 Report via [GitHub Security Advisories](https://github.com/evoludigit/velocitybench/security/advisories)
- 🐛 Non-security bugs: [GitHub Issues](https://github.com/evoludigit/velocitybench/issues)

For general questions:
- 📖 See [DEVELOPMENT.md](DEVELOPMENT.md)
- 🤔 See [FAQ](#faq) above

---

## Resources

- [OWASP Top 10](https://owasp.org/Top10/)
- [Secure Coding Practices](https://cheatsheetseries.owasp.org/)
- [Dependency Security](https://safety.readthedocs.io/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/sql-syntax.html)

---

**Remember**: VelocityBench is a **development tool**. It's secure for local use but requires hardening before production deployment.
