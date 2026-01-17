**[Pattern] Versioning Strategy Reference Guide**

---

### **Overview**
This guide outlines best practices for implementing **versioning strategies** in software systems, APIs, and databases. Proper versioning ensures backward and forward compatibility, minimizes disruption during updates, and simplifies maintenance. Common use cases include:
- **API versioning** (e.g., RESTful endpoints)
- **Database schema changes**
- **Library/package updates**
- **Configuration file formats**

This reference provides structured approaches (e.g., major/minor/patch, semantic versioning) and practical implementation tactics to avoid versioning pitfalls like **breaking changes** or **deprecated support**.

---

### **Schema Reference**
| **Category**               | **Key Attributes**                                                                 | **Recommended Values/Patterns**                                                                                     | **Example**                     |
|----------------------------|------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|---------------------------------|
| **Version Type**           | Major (Breaking Changes)                                                          | Incremented for incompatible changes (e.g., API deprecations, schema migrations).                                   | `v1.0.0` → `v2.0.0`             |
|                            | Minor (Backward-Compatible)                                                      | Incremented for new features/functionality without breaking existing code.                                         | `v1.0.0` → `v1.1.0`             |
|                            | Patch (Bug Fixes)                                                                | Incremented for fixes that don’t affect functionality.                                                         | `v1.1.0` → `v1.1.1`             |
| **Versioning Scheme**      | Semantic Versioning (`MAJOR.MINOR.PATCH`)                                        | Follows [SemVer 2.0.0](https://semver.org/) standards.                                                            | `3.2.1`                         |
|                            | Date-Based (`YYYY.MM.DD`)                                                         | Useful for non-semantic dependencies (e.g., internal tools).                                                    | `2023.10.15`                    |
|                            | Pre-Release/Build Metadata (`MAJOR.MINOR.PATCH-alpha`)                           | Indicate unstable or pre-release versions (e.g., `-dev`, `-beta`).                                               | `v1.0.0-beta`                   |
| **API Versioning Methods** | URL Path (`/v2/endpoint`)                                                        | Embed version in the URL for explicit client control.                                                            | `/api/v1/users`                 |
|                            | Query Parameter (`?version=1`)                                                    | Flexible but may require client-side checks.                                                                     | `/users?version=1`              |
|                            | Header (`Accept: application/vnd.company.v1+json`)                                | Standardized for REST APIs (e.g., via `Content-Type` or `Accept` headers).                                       | `Accept: vnd.acme.api.v1+json` |
|                            | Media Type (`Content-Type: application/vnd.company.v1+json`)                     | Used for content negotiation (e.g., APIs like GitHub).                                                          | `application/vnd.github.v3+json`|
|                            | Contract First (OpenAPI/Swagger)                                                 | Define versions in API contracts (e.g., Swagger YAML) to enforce consistency.                                   | `x-apis-gateway: v1`            |
| **Database Versioning**    | Schema Migration Files (`migrations/001_add_users_table.sql`)                     | Versioned SQL files for controlled database evolution.                                                          | `v1__add_users_table.py`        |
|                            | ALTER TABLE Statements                                                           | Use incremental `ALTER TABLE` for schema changes (avoid `CREATE TABLE`).                                        | `ALTER TABLE users ADD COLUMN id INT` |
| **Documentation Versioning**| Markdown Frontmatter (`--- version: "1.0" ---`)                                   | Embed version in documentation files (e.g., GitHub-flavored Markdown).                                          | `---\nversion: "2.0"\n---\n`     |
|                            | Redirects (`/v1/docs → /v2/docs`)                                                | Auto-redirect older docs to latest version.                                                                       | Nginx `rewrite ^/v1(/.*) $1 permanent;` |

---

### **Implementation Details**

#### **1. Semantic Versioning (SemVer)**
Adopt **SemVer** (`MAJOR.MINOR.PATCH`) for consistency:
- **Major**: Increment for breaking changes (e.g., API deprecations).
- **Minor**: Add backward-compatible features.
- **Patch**: Fix bugs without changing behavior.
- **Pre-release**: Use `-alpha`, `-beta`, or `-rc` for unstable versions.

**Example Workflow**:
```plaintext
v1.0.0 → v1.1.0 (new feature) → v1.1.1 (bug fix) → v2.0.0 (breaking change)
```

#### **2. API Versioning Strategies**
| **Method**               | **Pros**                                                                 | **Cons**                                                                 | **Best For**                          |
|--------------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------|---------------------------------------|
| **URL Path**             | Explicit; easy for clients to switch versions.                           | Harder to add new versions later (URL bloat).                           | Public APIs with long-term support. |
| **Query Parameter**      | Flexible; no URL changes.                                                | May confuse clients; harder to cache.                                   | Internal APIs or experimental features. |
| **Header**               | Standardized (e.g., `Accept`).                                           | Requires client-side version checks.                                     | RESTful APIs with content negotiation. |
| **Media Type**           | Semantic (e.g., `application/vnd.foo.v1+json`).                          | Complex for clients to parse.                                            | Highly versioned APIs (e.g., GitHub). |
| **Contract First**       | Enforced via OpenAPI/Swagger.                                           | Requires tooling (e.g., Swagger Editor).                                 | Enterprise APIs with strict governance. |

**Query Example (URL Path)**:
```http
GET /api/v2/users HTTP/1.1
Host: example.com
Accept: application/json
```
**Header Example**:
```http
GET /users HTTP/1.1
Host: example.com
Accept: application/vnd.company.api.v2+json
```

#### **3. Database Versioning**
- **Schema Migrations**: Use tools like **Alembic** (Python), **Flyway**, or **Liquibase** to track changes.
  ```sql
  -- migration/1628345600__add_created_at_column.sql
  ALTER TABLE users ADD COLUMN created_at TIMESTAMP;
  ```
- **Backward Compatibility**: Avoid dropping columns; use `NULL` or `DEFAULT` values.
- **Versioned Data**: Store version metadata in a `schema_versions` table:
  ```sql
  CREATE TABLE schema_versions (
      id SERIAL PRIMARY KEY,
      version VARCHAR(20) UNIQUE,
      applied_at TIMESTAMP DEFAULT NOW()
  );
  ```

#### **4. Handling Breaking Changes**
- **Deprecation Policy**:
  1. Announce deprecation in `vX.Y.Z` with a **deprecated** header.
     ```json
     {
       "id": 1,
       "deprecated": true,
       "message": "Use /v2/users instead by v3.0.0"
     }
     ```
  2. Deprecate in `vX.Y.Z+1`, remove in `vX+1.0.0`.
- **Graceful Fallback**: Provide alternative endpoints (e.g., `/v1/users` → `/v2/users`).

#### **5. Documentation Versioning**
- **Versioned Docs**: Use Git branches/tags (e.g., `gh-pages/v1`) or tools like **Docusaurus** with frontmatter.
  ```markdown
  ---
  version: "1.0"
  ---
  # API Reference
  ```
- **Auto-Redirects**: Configure Nginx/Apache to redirect old docs:
  ```nginx
  location /v1/docs {
      return 301 /v2/docs;
  }
  ```

---

### **Query Examples**
#### **1. API Versioning Query (cURL)**
```bash
# Request v1 endpoint
curl -H "Accept: application/vnd.company.api.v1+json" https://api.example.com/users

# Request v2 with query parameter
curl "https://api.example.com/users?v=2"
```

#### **2. Database Migration Check**
```sql
-- Check applied migrations
SELECT * FROM schema_versions ORDER BY applied_at DESC;
-- Output:
-- version  | applied_at
-- ---------+--------------------------
-- v1__add_users | 2023-10-15 10:00:00
-- v2__add_index  | 2023-10-16 14:30:00
```

#### **3. Client-Side Version Handling (JavaScript)**
```javascript
// Check Accept header dynamically
const version = 'v2';
fetch(`/api/${version}/users`, {
  headers: {
    'Accept': `application/vnd.company.api.${version}+json`
  }
}).then(response => response.json());
```

---

### **Related Patterns**
1. **[Backward Compatibility](https://refactoring.guru/design-patterns/backward-compatibility)**
   - Ensure new versions don’t break existing clients.
2. **[Graceful Degradation](https://refactoring.guru/design-patterns/graceful-degradation)**
   - Provide fallbacks for unsupported versions.
3. **[Feature Flags](https://martinfowler.com/articles/feature-toggle.html)**
   - Roll out changes incrementally without version bumps.
4. **[Immutable Data Structures](https://en.wikipedia.org/wiki/Persistent_data_structure)**
   - Use in databases/APIs to avoid modifying live data during updates.
5. **[API Gateway Patterns](https://www.apigee.com/)**
   - Manage versioning centrally (e.g., Kong, Apigee).

---
### **Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Risk**                                                                 | **Mitigation**                                      |
|---------------------------------|--------------------------------------------------------------------------|------------------------------------------------------|
| **No Versioning (Monolithic)** | All changes are breaking; clients can’t opt out.                         | Adopt SemVer or path-based versioning immediately.     |
| **Version in Body Only**        | Clients must parse responses for version; harder to cache.                 | Use headers/URLs for versioning.                      |
| **Unannounced Breaking Changes**| Clients fail silently or with cryptic errors.                           | Follow deprecation policies (e.g., 1-year notice).   |
| **Ignoring Deprecated Endpoints**| Leaves old clients stuck; increases support burden.                       | Remove deprecated endpoints after a grace period.     |

---
### **Tools & Libraries**
| **Purpose**               | **Tools**                                                                 |
|---------------------------|---------------------------------------------------------------------------|
| **API Versioning**        | Express Router (`/v1/route`), Kong, Apigee, AWS API Gateway.              |
| **SemVer Enforcement**    | `npm version` (packages), `poetry version` (Python), Maven (`groupId:artifactId:version`). |
| **Database Migrations**   | Alembic, Flyway, Liquibase, Django Migrations, Rails ActiveRecord.      |
| **Documentation**         | Docusaurus, MkDocs, Sphinx, Swagger UI.                                  |
| **Versioned HTTP Clients**| Retrofit (Android), Axios (JavaScript), `requests` (Python) with version headers. |

---
**Final Note**: Versioning is an **evergreen topic**; review your strategy quarterly. Balance stability (e.g., SemVer) with agility (e.g., feature flags) to adapt to evolving needs.