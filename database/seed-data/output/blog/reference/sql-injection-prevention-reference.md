# **[Pattern] SQL Injection Prevention Reference Guide**

---

## **Overview**
SQL injection (SQLi) is a code injection technique where attackers exploit vulnerable input fields to manipulate database queries, leading to unauthorized data access, data theft, or database corruption. This **SQL Injection Prevention** pattern mitigates risks by enforcing strict input validation and utilizing **parameterized queries** (prepared statements), ensuring user inputs are treated as data—not executable code. Adopting this pattern reduces exposure to exploits, aligns with **OWASP Top 10** security principles, and adheres to **defense-in-depth** strategies. Compliance with **PCI DSS, ISO 27001**, or **HIPAA** often mandates such protections, making this a critical component of secure software development.

---

## **Schema Reference**
Below is a table outlining the key components of SQL injection prevention in application architectures.

| **Component**               | **Description**                                                                                                                                                     | **Implementation Notes**                                                                                                                                                     | **Example**                                                                                     |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **User Input Handling**     | Validates and sanitizes inputs to reject malicious payloads (e.g., SQL keywords, excessive length).                                                                      | Use **whitelisting** for known-safe values (e.g., alphanumeric-only fields). Enforce strict type specifications (e.g., `VARCHAR(50)` for passwords).                      | `IF input ~ '^[A-Za-z0-9]+$' THEN continue ELSE reject` (pseudo-code)                          |
| **Parameterized Queries**   | Separates SQL logic from data via placeholders (`?`, `@param`) to prevent injection.                                                                              | Supported by all major DBMS (MySQL, PostgreSQL, SQL Server, Oracle). Avoid string concatenation (`"SELECT * FROM users WHERE id='" + userInput + "'"`).                  | `SELECT * FROM users WHERE id = ?` (bind `?` with `userId = 123`)                              |
| **ORM/Query Builder**       | Automates parameterization through robust frameworks (e.g., SQLAlchemy, Hibernate, Entity Framework).                                                            | ORMs abstract low-level SQL operations, reducing risk of manual errors. Audit ORM-generated queries for anomalies.                                                       | `db.execute("SELECT * FROM posts WHERE author = :author", {"author": "Alice"})` (SQLAlchemy)   |
| **Stored Procedure**        | Encapsulates queries with predefined parameters, limiting user-controlled input exposure.                                                                         | Use sparingly; ensure procedures validate all inputs internally.                                                                                                           | `CALL get_user_profile(?, ?)` (bind `@userId` and `@accessToken`)                              |
| **Input Validation Rules**  | Defines constraints (e.g., length, format, regex) per field.                                                                                                        | Combine with **context-aware validation** (e.g., email format for `@email` fields).                                                                                       | `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$` (email regex)                              |
| **Database-Level Protections** | Uses **least privilege** accounts, **row-level security (RLS)**, and **audit logs** to limit damage if injection occurs.                                          | Restrict user permissions (e.g., `SELECT` only, no `DROP TABLE`). Monitor suspicious queries via auditing tools.                                                          | `GRANT SELECT ON users TO app_user;` (PostgreSQL)                                                 |
| **Error Handling**          | Avoids leaking database errors (e.g., "Syntax error near 'OR'") to prevent exploitation of hints.                                                                     | Use generic messages (e.g., "Invalid query") and log detailed errors internally.                                                                                            | `try { ... } catch (Exception e) { log.error(e); response.status(400).message("Invalid input") }` |

---

## **Query Examples**

### **✅ Secure Implementation (Parameterized Queries)**
#### **1. Basic Parameterized Query (MySQL)**
```sql
-- Vulnerable (CONCATENATION)
SELECT * FROM users WHERE username = 'admin' OR '1'='1';

-- Secure (Parameterized)
PREPARE user_query FROM 'SELECT * FROM users WHERE username = ?';
SET @username = 'admin';
EXECUTE user_query USING @username;
```
**Code Example (Python with `mysql-connector`):**
```python
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

#### **2. ORM Usage (SQLAlchemy)**
```python
from sqlalchemy import create_engine, text
engine = create_engine("postgresql://user:pass@localhost/db")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM posts WHERE title = :title"), {"title": "SQL Injection Prevention"})
```

#### **3. Stored Procedure (SQL Server)**
```sql
-- Procedure definition
CREATE PROCEDURE get_post(@post_id INT)
AS
    SELECT * FROM posts WHERE id = @post_id;

-- Call
EXEC get_post @post_id = 42;
```

#### **4. Input Validation (Java with Jakarta Validation)**
```java
@NotNull
@Size(min = 1, max = 50)
@Pattern(regexp = "^[a-zA-Z0-9_]+$")
private String username;
```

---

### **❌ Vulnerable Implementations (Avoid These)**
#### **1. String Concatenation (Classic Injection)**
```sql
# Dangerous: User input directly embedded
query = "SELECT * FROM users WHERE username = '" + user_input + "'"
```
**Exploit:**
```sql
username = "admin' --"
# Result: SELECT * FROM users WHERE username = 'admin' --'
# Any user's data is returned.
```

#### **2. Dynamic SQL with User Input (PHP)**
```php
// Vulnerable
$query = "SELECT * FROM users WHERE email = '" . $_GET['email'] . "'";
$result = mysqli_query($conn, $query);
```
**Exploit:**
```url
http://example.com/search.php?email=admin' OR '1'='1
```

#### **3. Bypassing Input Validation**
```python
# Whitelisting fails if attacker uses non-ASCII characters
user_input = "admin' #"
if user_input.isalpha():  # False due to "'"
    # Proceeds (likely incorrect check)
```

---

## **Implementation Best Practices**
1. **Default to Parameterized Queries**
   - Always prefer ORMs/query builders over raw SQL.
   - Use **prepared statements** with placeholders (`?`, `@param`, `:name`).

2. **Validate on Both Ends**
   - Validate **client-side** for UX (e.g., regex in JavaScript).
   - **Server-side validation is mandatory** (trust no client input).

3. **Use Least-Privilege Database Accounts**
   - Avoid `root`/`sa` credentials. Grant only necessary permissions (e.g., `SELECT`, `INSERT`).

4. **Log and Monitor Queries**
   - Enable database auditing to detect unusual patterns (e.g., `UNION SELECT`).

5. **Keep Dependencies Updated**
   - Patches for database drivers (e.g., `mysql-connector`, `psycopg2`) often address injection flaws.

6. **Escape Only When Necessary**
   - Use **library-provided escaping** (e.g., `mysql_real_escape_string` in PHP as a **last resort**).

---

## **Tools and Libraries**
| **Tool/Library**          | **Purpose**                                                                 | **Language/DB Support**                          |
|---------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **SQLAlchemy**            | ORM with parameterized queries.                                            | Python (PostgreSQL, MySQL, SQLite, etc.)          |
| **Hibernate**             | Java ORM with JPA annotations for security.                                 | Java (MySQL, Oracle, etc.)                       |
| **Entity Framework**      | .NET ORM with built-in injection protection.                                 | C# (SQL Server, PostgreSQL)                      |
| **PDO (PHP)**             | Parameterized queries via `PDO::prepare()`.                                 | PHP (MySQL, SQLite)                              |
| **psycopg2 (PostgreSQL)** | Secure PostgreSQL adapter for Python.                                       | Python (PostgreSQL)                              |
| **OWASP ESAPI**           | Input validation and encoding utilities.                                     | Java, .NET, PHP                                  |
| **Linters (e.g., SQLFluff)** | Detects vulnerable SQL patterns in code.                                    | Cross-platform                                  |

---

## **Testing and Verification**
1. **Static Analysis**
   - Use tools like **SonarQube**, **Checkmarx**, or **Semgrep** to scan for injection patterns.

2. **Dynamic Analysis**
   - **OWASP ZAP** or **Burp Suite** to simulate SQLi attacks.
   - Test edge cases (e.g., `' OR '1'='1`, `UNION SELECT`).

3. **Unit Tests**
   - Validate parameterized queries with mock databases (e.g., **SQLite in-memory**).
   ```python
   # Example: pytest with pytest-mysql
   def test_parameterized_query():
       with mysql.connect() as conn:
           conn.execute("INSERT INTO users (username) VALUES (?)", ("test",))
           assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
   ```

4. **Penetration Testing**
   - Engage third-party security teams to perform **black-box testing**.

---

## **Common Misconceptions**
| **Misconception**                          | **Reality**                                                                 |
|---------------------------------------------|-----------------------------------------------------------------------------|
| *"Input validation alone prevents SQLi."*   | Validation fails against **second-order injection** (e.g., stored XSS + SQLi). **Parameterization is required.** |
| *"Escaping characters is secure."*          | Escaping is **DB-specific** and often **inadequate** (e.g., `mysql_real_escape_string` fails with UTF-8).          |
| *"ORMs are 100% immune."*                   | ORMs can generate **dynamic SQL** if misused (e.g., raw `EXECUTE()` calls). |
| *"Client-side checks are enough."*          | Client-side is **easily bypassed** (e.g., DevTools, modified requests).    |

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                                                                                                                                                 | **Interaction with SQL Injection Prevention**                                                                                     |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| **[Input Validation](https://refactoring.guru/design-patterns/input-validation)** | Validates user input against business rules (e.g., regex, length checks).                                                                                                                                   | **Complements** SQL injection prevention by rejecting malformed inputs before they reach the database.                          |
| **[Data Access Object (DAO)](https://refactoring.guru/design-patterns/DAO)** | Abstracts database operations to simplify security (e.g., parameterized queries in DAO methods).                                                                                                          | **Reduces** exposure by centralizing query logic and enforcing consistent parameterization.                                       |
| **[Procedural Abstraction](https://refactoring.guru/design-patterns/procedural-abstraction)** | Encapsulates database logic in procedures/functions to limit direct SQL exposure.                                                                                                                      | **Minimizes** risk by restricting user input to predefined parameters in stored procedures.                                       |
| **[Rate Limiting](https://refactoring.guru/design-patterns/rate-limiting)** | Throttles suspicious queries (e.g., repeated injections).                                                                                                                                                   | **Detects** brute-force SQLi attempts and mitigates denial-of-service risks.                                                      |
| **[Audit Logging](https://refactoring.guru/design-patterns/audit-logging)** | Logs all database operations for forensic analysis.                                                                                                                                                         | **Enables** post-exploit analysis if SQLi occurs (e.g., identifying the attacker’s query).                                      |

---

## **Example: Full Secure Workflow**
1. **Frontend (React)**
   ```jsx
   const [email, setEmail] = useState("");
   const handleSubmit = (e) => {
     if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return; // Basic regex
     fetch("/login", { method: "POST", body: JSON.stringify({ email }) });
   };
   ```

2. **Backend (Node.js with Express + pg)**
   ```javascript
   const { Pool } = require("pg");
   const pool = new Pool();

   app.post("/login", async (req, res) => {
     const { email } = req.body;
     if (!email || typeof email !== "string") return res.status(400).send("Invalid input");

     // Parameterized query
     const query = "SELECT * FROM users WHERE email = $1";
     const result = await pool.query(query, [email]);

     if (result.rows.length) return res.send("Success");
     res.status(404).send("User not found");
   });
   ```

3. **Database (PostgreSQL)**
   ```sql
   -- Only allows the email parameter as data (no SQL execution)
   CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255) UNIQUE);
   ```

---

## **Troubleshooting**
| **Issue**                          | **Cause**                                      | **Solution**                                                                                                                                 |
|-------------------------------------|-------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **"Parameter skipped" errors**      | Incorrect binding types (e.g., `NULL` vs `int`).  | Ensure parameter types match the query (e.g., `?` for `INT`, `:name` for `VARCHAR`).                                                      |
| **Performance degradation**         | ORM overhead or excessive logging.               | Profile queries with tools like **pgBadger** (PostgreSQL) or **MySQL Query Profiler**. Optimize with indexes.                              |
| **False positives in validation**   | Overly restrictive regex.                        | Test with **positive/negative test cases** (e.g., `admin@example.com`, `admin@example..com`).                                               |
| **Stored procedures fail**          | Missing transaction handling.                   | Wrap procedures in transactions or use `SET NOCOUNT ON` (SQL Server) to suppress result sets.                                              |

---

## **Further Reading**
- [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)
- [SQL Injection: From Attack to Prevention (Paper)](https://www.owasp.org/index.php/SQL_Injection_Prevention_Cheat_Sheet)
- **Books**: *The Web Application Hacker’s Handbook* (Dafydd Stuttard), *SQL Injection Attacks and Defense* (Andrew Hoffman).