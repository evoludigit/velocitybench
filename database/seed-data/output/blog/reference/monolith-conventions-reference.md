# **[Pattern] Monolith Conventions Reference Guide**

---

## **1. Overview**
The **Monolith Conventions** pattern defines standardized rules for structuring large, tightly coupled applications (monoliths) to improve maintainability, collaboration, and scalability. Unlike distributed microservices, monoliths retain a single codebase, but conventions ensure consistency in:
- **Project layout** (e.g., `src/{domain}/`)
- **Dependency management** (e.g., explicit module boundaries)
- **Naming conventions** (e.g., `UserService` vs. `user_service`)
- **Configuration** (e.g., environment-specific files)
- **Testing** (e.g., modular test suites)
- **Build processes** (e.g., incremental compilation).

This pattern balances the simplicity of monoliths with discipline, reducing technical debt and enabling incremental refactoring toward microservices if needed. It’s ideal for teams working on domain-driven design, bounded contexts, or legacy systems requiring gradual modernization.

---

## **2. Schema Reference**

| **Category**          | **Convention**                                                                 | **Examples**                                                                 | **Rationale**                                                                 |
|-----------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Project Structure** | **Domain-based directories**                                                    | `/src/core-auth`, `/src/reporting`, `/src/api`                                  | Keeps related code together while isolating concerns.                        |
|                       | **Explicit module files**                                                      | `core-auth.module.ts`, `reporting.mod`                                        | Defines clear boundaries for builds/dependencies.                           |
| **Naming**            | **PascalCase for classes/services**                                            | `UserRepository`, `OrderProcessor`                                            | Consistent with object-oriented principles.                                  |
|                       | **snake_case for config files, env vars**                                     | `settings.env`, `DATABASE_URL`                                                | Follows Unix conventions for system files/tooling.                          |
|                       | **Verb-noun for endpoints**                                                    | `GET /users`, `POST /orders`                                                  | RESTful clarity; avoids ambiguity.                                           |
| **Dependencies**      | **Explicit `package.json`/`pom.xml` dependencies**                           | `dependencies: { "@core/auth": "^1.0.0" }`                                   | Prevents transitive dependency bloat.                                        |
|                       | **No circular imports**                                                        |                                                                                | Enforces modularity; detects at compile time.                                |
| **Configuration**     | **Environment-specific files**                                                 | `config/dev.json`, `config/prod.yaml`                                         | Separates staging/production settings from code.                             |
|                       | **Feature flags in config**                                                    | `{ "experimental": { "new-payment-gateway": true } }`                         | Enables gradual rollouts.                                                  |
| **Testing**           | **Modular test suites per module**                                             | `/test/core-auth/`, `/test/reporting/`                                        | Isolates test failures to specific areas.                                   |
|                       | **Integration tests in `/integration/`**                                      | `/integration/api-user-scenarios.js`                                          | Validates module interactions without full app deployment.                   |
| **Build Process**     | **Incremental compilation**                                                    | `tsc --watch --module-resolution node`                                        | Speeds up development cycles.                                                |
|                       | **Dockerized build environments**                                              | `Dockerfile.dev` with multi-stage builds                                     | Ensures consistent builds across teams.                                     |

---
**Note:** Adjust schemas per language/framework (e.g., Python’s `src/` vs. Ruby’s `lib/`).

---

## **3. Query Examples**

### **3.1 Directory Structure Queries**
**Question:** *How do I locate the `User` module?*
**Answer:**
```
src/
├── core-auth/               # Domain: Authentication
│   └── users/
│       ├── user.service.ts  # Business logic
│       ├── user.repository.ts # Data access
│       └── test/           # Unit tests
```

**Question:** *Where are environment variables loaded?*
**Answer:**
- **Default:** `config/${ENV}.env` (e.g., `config/prod.env`).
- **Fallback:** `.env` (local overrides only).

---

### **3.2 Dependency Management**
**Question:** *How do I add a new dependency to `core-auth`?*
**Steps:**
1. Edit `core-auth/package.json`:
   ```json
   {
     "dependencies": {
       "crypto-js": "^4.1.1"
     }
   }
   ```
2. Update `root/package.json` dependencies (if needed):
   ```json
   {
     "dependencies": {
       "@core/auth": "file:../core-auth"
     }
   }
   ```

**Question:** *How to check for circular dependencies?*
**Tools:**
- **TypeScript:** `tsc --noEmitOnError --emitDeclarationOnly`.
- **Java:** `mvn dependency:analyze` (Maven).

---

### **3.3 Build/Deployment**
**Question:** *How to build only the `reporting` module?*
**Command:**
```bash
cd src/reporting && npm run build
# Output: dist/reporting/
```

**Question:** *What’s the convention for Docker images?*
**Tagging:**
- `monolith-core-auth:dev-1.0.0` (development).
- `monolith-core-auth:prod-1.0.0` (production, with multi-stage optimizations).

---
**Example `Dockerfile` (dev):**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY src/reporting/ ./reporting
RUN npm install
CMD ["npm", "run", "dev"]
```

---

### **3.4 Testing**
**Question:** *How to run all tests for `core-auth`?*
**Command:**
```bash
cd src/core-auth && npm test
# Output: Coverage HTML in `/coverage/core-auth/`
```

**Question:** *Where are integration tests stored?*
**Location:**
```
src/
├── core-auth/
│   └── integration/
│       └── user-auth-flow.test.ts  # Tests user auth + database
```

---

## **4. Implementation Checklist**
1. **Initialize Structure:**
   ```bash
   mkdir -p src/{core-auth,reporting,api} && \
   touch src/core-auth/package.json
   ```
2. **Add Module Entry Points:**
   - `core-auth/module.ts` (exports services).
   - `reporting/mod.py` (Python example).
3. **Configure Environment Files:**
   - `config/dev.json` (local), `config/prod.env` (CI/CD).
4. **Enforce Naming:**
   - Use `eslint-config-airbnb` (JS/TS) or `pylint` (Python) to enforce conventions.
5. **Write Tests:**
   - Unit tests in `/test/`, integration tests in `/integration/`.
6. **Document Boundaries:**
   - Add `src/core-auth/BOUNDARIES.md` with:
     - Dependent modules.
     - Public API contracts.

---

## **5. Edge Cases & Mitigations**
| **Issue**                     | **Mitigation**                                                                 |
|--------------------------------|-------------------------------------------------------------------------------|
| **Module bloat**               | Split into submodules (e.g., `src/core-auth/users/`, `src/core-auth/roles/`)  |
| **Slow builds**                | Use `--watch` for dev, incremental builds for CI.                             |
| **Config conflicts**           | Prioritize: `.env` > `config/${ENV}.env` > default config.                     |
| **Legacy code integration**     | Wrap old code in `src/legacy/` with clear deprecation timelines.              |

---

## **6. Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Bounded Context**       | Further divides monolith domains (e.g., `order-service` vs. `inventory`). | When domains grow too large or diverge in tech stack.                           |
| **Feature Flags**         | Enables gradual release of modules.                                          | For experimental features or canary deployments.                                |
| **Layered Architecture**  | Separates presentation, business, and data layers.                           | For complex domains needing separation of concerns.                            |
| **Microservices (Future)**| eventual refactoring target.                                                 | When modules grow independent of each other (e.g., `core-auth` vs. `billing`).  |

---
**See Also:**
- [Domain-Driven Design (DDD)](https://domainlanguage.com/ddd/)
- [12-Factor App](https://12factor.net/) (for conventions beyond monoliths).

---
**Last Updated:** [Date]
**Owners:** [Team/DevOps]