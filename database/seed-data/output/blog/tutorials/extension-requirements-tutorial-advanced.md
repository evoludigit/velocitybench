```markdown
# **"Dependency Injection for Databases: The Extension Requirements Pattern"**

*How to Build Scalable Backends with PostGIS, pgvector, and More*

---

## **Introduction**

Back in the day, databases were simple: you stored data, ran queries, and called it a day. But today’s applications demand more. We need spatial indexing with **PostGIS**, vector search with **pgvector**, full-text search with **pg_trgm**, and even streaming analytics with **TimescaleDB**.

The challenge? These extensions aren’t just "nice-to-have" features—they’re **critical dependencies** for certain workflows. But how do we integrate them cleanly into our applications without making the database schema a tangled mess?

This is where the **Extension Requirements Pattern** comes in.

Instead of hardcoding dependencies into your application, you define what your app *needs* from the database—whether it’s a spatial extension, vector search, or a custom function—and let your infrastructure handle the rest. This approach makes your system **more modular, easier to maintain, and adaptable to different deployment environments** (local dev, staging, production, edge functions).

In this post, we’ll explore:
✅ **Why traditional database design falls short** when dealing with extensions
✅ **How the Extension Requirements Pattern solves this** with a clean, maintainable approach
✅ **Practical examples** using PostgreSQL, PostGIS, and pgvector
✅ **Tradeoffs and best practices** to keep in mind

Let’s dive in.

---

## **The Problem: Hardcoding Extensions Breaks Flexibility**

Most backend systems today use PostgreSQL as their primary database, but they often **assume** that certain extensions are installed—even if they aren’t. Here’s how this manifest:

### **1. Schema-Dependent Assumptions**
Your application might assume that **PostGIS** is available because it’s "common" for location-based apps. But what if:
- You’re deploying to a cloud database that doesn’t have PostGIS enabled by default?
- You’re using a lightweight PostgreSQL instance where extensions are disabled for performance?
- You’re running in a serverless environment where extensions are **not supported**?

```sql
-- This query will fail if PostGIS isn't installed!
SELECT ST_Distance(
    ST_SetSRID(ST_Point(-74.0060, 40.7128), 4326), -- Manhattan coordinates
    ST_SetSRID(ST_Point(-73.9650, 40.7800), 4326)  -- Central Park
);
```
**Result:** `ERROR: function st_distance(geometry, geometry) does not exist`

### **2. Deployment Nightmares**
If your application relies on extensions without checking, you risk:
- **Failed migrations** (e.g., `ALTER TABLE` assuming a function exists)
- **Downtime during deployments** (waiting for extensions to be installed)
- **Inconsistent behavior** across environments (dev vs. production)

### **3. Scalability Limits**
Some extensions (like **pgvector**) add significant overhead. If you **always** install them, you might:
- Pay for unnecessary compute power in production
- Slow down read-heavy workloads
- Complicate CI/CD pipelines with unnecessary dependencies

### **Real-World Example: The E-Commerce Location Search**
Imagine an e-commerce platform that needs:
- **PostGIS** for warehouse location management
- **pgvector** for product search by location-based recommendations

If your app assumes both are available, you’re in trouble if:
- A cloud provider only offers a **Basic PostgreSQL tier** without extensions
- Your **edge function** (like Cloudflare Workers) can’t install extensions
- You’re running in a **multi-tenant environment** where extensions must be managed per schema

---

## **The Solution: Extension Requirements Pattern**

The **Extension Requirements Pattern** is a way to **decouple your application logic from database extensions**. Instead of hardcoding assumptions, you:
1. **Declare what extensions your app needs** (e.g., `"PostGIS"`, `"pgvector"`).
2. **Check for their availability at runtime** (or at build time).
3. **Provide fallbacks** (e.g., disable location features if PostGIS isn’t available).
4. **Let your infrastructure enforce these requirements** (CI/CD, deployment scripts).

This pattern ensures:
✔ **No silent failures** (your app either works or gracefully degrades)
✔ **Better scalability** (only enable extensions when needed)
✔ **Easier migrations** (extensions are explicitly required, not assumed)

---

## **Components of the Solution**

### **1. The Extension Manifest (Static Definition)**
Define which extensions your app requires in a **configuration file** (e.g., `db_requirements.yml`):

```yaml
# db_requirements.yml
extensions:
  - name: postgis
    version: "3.4"  # Optional: Pin to a specific version
    required: true  # Can also be false for optional extensions
  - name: pgvector
    version: "0.6.1"
    required: true
  - name: pg_trgm  # Optional fallback for full-text search
    required: false
```

### **2. Runtime Checks (Dynamic Verification)**
At startup, your app should verify that all required extensions are installed. Here’s how to do it in **Python (using `psycopg2`)**:

```python
# db_requirements.py
import psycopg2
from typing import List, Dict

def check_extensions(connection_params: Dict, requirements: List[Dict]) -> bool:
    """Verify that all required extensions are installed."""
    try:
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()

        for req in requirements:
            if req["required"] and not is_extension_installed(cursor, req["name"]):
                print(f"Error: Extension '{req['name']}' is required but not installed.")
                return False

        conn.close()
        return True

    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def is_extension_installed(cursor, extension_name: str) -> bool:
    """Check if an extension is installed."""
    cursor.execute("SELECT * FROM pg_available_extensions WHERE name = %s;", (extension_name,))
    return cursor.fetchone() is not None
```

### **3. Fallback Logic (Graceful Degradation)**
If an extension is missing, your app should **fall back gracefully**. For example:

```python
# location_service.py
from db_requirements import check_extensions

def initialize_location_service():
    connection_params = {"dbname": "app_db", "user": "dev", "password": "secret"}

    requirements = [
        {"name": "postgis", "required": True},
        {"name": "pg_trgm", "required": False}  # Optional for text search
    ]

    if not check_extensions(connection_params, requirements):
        print("Skipping location features due to missing extensions.")
        return None

    # If we got here, extensions are available—proceed normally
    return LocationService(connection_params)
```

### **4. Infrastructure Enforcement (CI/CD & Deployment)**
Your deployment pipeline should **enforce** these requirements:
- **CI Checks:** Run `check_extensions()` in your test suite.
- **Deployment Scripts:** Install missing extensions before migrations.
- **Cloud Provider Policies:** Restrict databases to only allow extensions that your app declares.

Example **Terraform** snippet to ensure only allowed extensions are installed:

```hcl
resource "aws_db_instance" "app_db" {
  engine        = "postgres"
  engine_version = "15.3"
  allocated_storage = 20

  # Only allow extensions that match db_requirements.yml
  tags = {
    AllowedExtensions = "postgis,pgvector"
  }
}
```

---

## **Implementation Guide: Step-by-Step**

### **Step 1: Define Your Extension Requirements**
Start by listing all extensions your app **absolutely needs** and which are **optional**.

```yaml
# db_requirements.yml
extensions:
  - name: "postgis"
    version: "3.4"
    required: true
  - name: "pgvector"
    version: "0.6.1"
    required: true
  - name: "timescaledb-timescaledb"
    required: false  # Only needed for time-series data
```

### **Step 2: Write Runtime Checks**
Implement a function to verify extensions at startup.

```python
# db_checker.py
import psycopg2
import yaml
from typing import Dict

def load_requirements(file_path: str) -> Dict:
    with open(file_path) as f:
        return yaml.safe_load(f)["extensions"]

def verify_database(connection_params: Dict, requirements: Dict) -> bool:
    conn = psycopg2.connect(**connection_params)
    cursor = conn.cursor()

    for ext in requirements:
        if ext["required"] and not check_extension(cursor, ext["name"]):
            print(f"CRITICAL: Required extension '{ext['name']}' missing!")
            return False

    conn.close()
    return True
```

### **Step 3: Integrate with Your Application**
Modify your app’s initialization to respect these constraints.

```python
# app/__init__.py
from db_checker import load_requirements, verify_database

def initialize():
    requirements = load_requirements("db_requirements.yml")
    connection_params = {"dbname": "app", "user": "app", "password": "pass"}

    if not verify_database(connection_params, requirements):
        raise RuntimeError("Database extensions not available—exiting.")

    # Proceed with normal app startup
    print("Database extensions verified. Starting app...")
```

### **Step 4: Handle Fallbacks in Business Logic**
If an extension is missing, provide **alternative implementations**.

```python
# location_service.py
class LocationService:
    def __init__(self, conn):
        self.conn = conn
        self.supports_spatial = self._has_postgis()

    def _has_postgis(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'postgis'")
        return cursor.fetchone() is not None

    def calculate_distance(self, geom1, geom2):
        if self.supports_spatial:
            # Use PostGIS for fast spatial queries
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT ST_Distance(%s, %s) AS distance
                FROM (VALUES (%s, %s)) AS t(geom1, geom2)
            """, (geom1, geom2, geom1, geom2))
            return cursor.fetchone()[0]
        else:
            # Fallback to a slower, non-spatial method
            return self._calculate_distance_legacy(geom1, geom2)
```

### **Step 5: Enforce in CI/CD**
Add a **pre-deployment check** in your pipeline.

```bash
# .github/workflows/deploy.yml
steps:
  - name: Check database extensions
    run: |
      python3 db_checker.py --conn "host=db.example.com user=deploy" --requirements db_requirements.yml
```

---

## **Common Mistakes to Avoid**

### **1. Assuming Extensions Are Installed by Default**
❌ **Bad:** Hardcoding SQL that assumes PostGIS exists.
✅ **Good:** Always check with `SELECT 1 FROM pg_extension WHERE extname = 'postgis'`.

### **2. Ignoring Version Requirements**
Extensions may not be compatible across versions. Always **pin versions** in your requirements.

```yaml
# Bad: No version specified → unpredictable behavior
extensions:
  - name: "postgis"

# Good: Explicit version
extensions:
  - name: "postgis"
    version: "3.4"
```

### **3. Not Providing Fallbacks**
If an extension is missing, **your app should degrade gracefully**, not crash.

```python
# Bad: Hard fail
if not has_postgis():
    raise Exception("PostGIS is required!")

# Good: Provide a fallback
if not has_postgis():
    use_fallback_search_algorithm()
```

### **4. Overloading the Database with Unnecessary Extensions**
Not all workloads need **pgvector + PostGIS + TimescaleDB**. Only install what you **actually use**.

### **5. Forgetting to Document Requirements**
If your team (or future you) doesn’t know which extensions are required, they’ll **break things**.

```markdown
# DB REQUIREMENTS

| Extension     | Version | Required | Purpose                          |
|---------------|---------|----------|----------------------------------|
| postgis       | 3.4     | Yes      | Spatial queries                  |
| pgvector      | 0.6.1   | Yes      | Vector search                    |
| pg_trgm       |         | No       | Full-text search fallback        |
```

---

## **Key Takeaways**

✅ **Decouple your app from database extensions**—don’t assume they’re installed.
✅ **Define requirements explicitly** (version + mandatory/optional).
✅ **Check extensions at runtime** (or build time) before making assumptions.
✅ **Provide fallbacks** for missing extensions (e.g., disable features).
✅ **Enforce requirements in CI/CD** to prevent deployment surprises.
✅ **Document your extension dependencies** for future maintainers.

---

## **Conclusion: Build Resilient, Scalable Backends**

The **Extension Requirements Pattern** isn’t just about avoiding errors—it’s about **building systems that work anywhere, from local dev to edge functions to cloud databases**.

By treating extensions as **dependencies** (not "nice-to-haves"), you:
✔ **Avoid silent failures** in production
✔ **Optimize resource usage** (don’t enable everything everywhere)
✔ **Make migrations safer** (no hidden assumptions)
✔ **Future-proof your app** (easier to swap databases or extend features)

### **Next Steps**
1. **Audit your current database schema**—what extensions do you assume?
2. **Define a `db_requirements.yml`** for your app.
3. **Implement runtime checks** in your app startup.
4. **Update CI/CD** to enforce these requirements.
5. **Refactor legacy code** that makes hard assumptions.

Start small—maybe just for **PostGIS** or **pgvector**—but once you adopt this pattern, your database interactions will become **more predictable and maintainable**.

---
**What’s your biggest pain point with database extensions?** Are you still assuming they’re installed? Share your struggles (or successes!) in the comments—I’d love to hear how you handle this in production.

---
```