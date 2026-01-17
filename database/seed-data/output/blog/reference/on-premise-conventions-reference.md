# **[Pattern] On-Premise Conventions Reference Guide**

## **Overview**
The **On-Premise Conventions Pattern** defines standardized naming, structuring, and deployment rules for systems, applications, and infrastructure hosted within an organization’s private data center or on-premise servers. This pattern ensures consistency in naming, documentation, and operational practices, reducing ambiguity and improving maintainability across on-premise environments. It applies to **server naming, module deployment, file paths, database schemas, and configuration files** while accounting for legacy systems and hybrid cloud/on-premise setups.

---

## **Implementation Details**

### **Core Principles**
1. **Consistency** – Uniform naming and structuring across teams and projects.
2. **Clarity** – Self-documenting conventions for quick identification and troubleshooting.
3. **Extensibility** – Supports future scaling without breaking existing systems.
4. **Compliance** – Aligns with organizational security and governance policies.

### **Key Components**
| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Naming Conventions** | Standardized prefixes/suffixes for servers, services, and databases.    |
| **Directory Structure** | Organized file paths for modularity and scalability.                   |
| **Configuration Rules** | Guidelines for environment variables, scripts, and deployment files.    |
| **Documentation Standards** | Mandatory metadata (e.g., version, last modified, owner) in artifacts. |

---

## **Schema Reference**

### **1. Server Naming Convention**
| Prefix | Example           | Purpose                                             |
|--------|-------------------|-----------------------------------------------------|
| `DB-`  | `DB-ORDER-SQL-01` | Dedicated database servers (e.g., SQL, Oracle).      |
| `APP-` | `APP-USER-SERV-02`| Application servers (e.g., web, API, microservices).|
| `UTIL-`| `UTIL-LOG-MON-03` | Utility servers (e.g., monitoring, logging).        |
| `VPC-` | `VPC-NET-SG-01`   | Networking components (e.g., subnets, security groups). |

**Format:**
`[TYPE]-[ROLE]-[TECH]-[INSTANCE]` (e.g., `APP-CART-ASPNET-02`)

---

### **2. File/Directory Structure**
| Path Component      | Rule                                                                   |
|---------------------|-------------------------------------------------------------------------|
| **Root (`/onpremise`)** | Centralized root for all on-premise assets.                          |
| **Environment Folders** | `/dev`, `/staging`, `/prod` (case-sensitive).                         |
| **Application Modules** | `/services/{appname}/` (e.g., `/services/order-processing/`)           |
| **Versioning**      | `/v{major}.{minor}.{patch}` (e.g., `/v1.2.3/`) in module paths.         |
| **Configuration Files** | `config.{env}.json` (e.g., `config.prod.json`) in each module.         |

**Example:**
```
/onpremise/dev/services/order-processing/v2.1.0/
└── config.dev.json
```

---

### **3. Database Schema Naming**
| Convention          | Example               | Purpose                                             |
|---------------------|-----------------------|-----------------------------------------------------|
| **Table Prefixes**  | `app_` or `user_`     | Avoids conflicts (e.g., `app_orders`, `user_profiles`).|
| **Primary Keys**    | `id` (auto-increment) | Standardized naming for primary key columns.         |
| **Foreign Keys**    | `order_id`            | Links tables unambiguously (e.g., `customer_order`).   |

**Schema Naming Rule:**
`[app_prefix]_[table_type]_[desc]` (e.g., `cmr_customer`).

---

### **4. Configuration Rules**
| Rule                  | Example                                                                 |
|-----------------------|-------------------------------------------------------------------------|
| **Environment Variables** | Prefix with `ONPREM_` (e.g., `ONPREM_DB_HOST=db-order-sql-01`).          |
| **Script Naming**     | `deploy-{env}.sh` (e.g., `deploy-prod.sh`).                              |
| **Logging**           | Centralized log paths: `/var/log/onpremise/{appname}/`.                  |

**Example Environment File (`config.env`):**
```ini
ONPREM_APP_NAME=order-service
ONPREM_DB_HOST=DB-ORDER-SQL-01
ONPREM_LOG_LEVEL=debug
```

---

## **Query Examples**

### **1. Finding a Database Server**
**Use Case:** Locate the server hosting the `sales` database.
**Query (CLI):**
```bash
# Search server names by prefix
grep "DB-" /etc/hosts | grep "sales"
```
**Output:**
```
DB-SALES-MSSQL-01 192.168.1.10
```

---

### **2. Validating File Structure**
**Use Case:** Verify if `/onpremise/prod/services/>` follows convention.
**Command:**
```bash
find /onpremise/prod/services/ -type d -name "v*" -maxdepth 1
```
**Expected Output:**
```
/onpremise/prod/services/v1.2.3
```

---

### **3. Checking Database Table Names**
**Use Case:** List tables with the `app_` prefix.
**SQL Query:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public' AND table_name LIKE 'app_%';
```

---

### **4. Parsing Server Naming**
**Use Case:** Extract role from `APP-CART-ASPNET-02`.
**Script (Python):**
```python
server = "APP-CART-ASPNET-02"
role = server.split('-')[1]  # Output: "CART"
```

---

## **Requirements Compliance**

| Requirement               | Implementation Notes                                                                 |
|---------------------------|-------------------------------------------------------------------------------------|
| **NIST SP 800-61**        | Use unique identifiers (e.g., instance numbers) to prevent naming collisions.         |
| **ISO 27001**             | Document all conventions in a **Policy Manual** (e.g., `ONPREM_CONV-001`).         |
| **Legacy System Integration** | Map old names to new conventions (e.g., `OLD-DB` → `DB-OLD-DB-01`).                   |

---

## **Related Patterns**

1. **[Hybrid Cloud Conventions]**
   - Extends on-premise rules for cloud-hosted components (e.g., AWS/Azure).

2. **[Infrastructure as Code (IaC) Templates]**
   - Automates deployment using **Terraform** or **Ansible** with on-premise conventions.

3. **[Microservices Deployment]**
   - Applies naming to service registries and containerized deployments (e.g., Docker/Kubernetes).

4. **[Access Control Policies]**
   - Defines RBAC roles (e.g., `onprem-admin`, `onprem-readonly`) for server access.

5. **[Audit Logging Standards]**
   - Mandates logging paths and retention policies for compliance (e.g., `/var/log/audit/`).

---
**Next Steps:**
- Train teams on the **Schema Reference** during onboarding.
- Enforce conventions via **CI/CD pipelines** (e.g., fail builds for misnamed resources).
- Review quarterly for updates (e.g., new prefixes as systems scale).