# **[Pattern] SQLite Single-File Database Reference Guide**

---

## **1. Overview**
The **SQLite Single-File Database** pattern leverages SQLite’s embedded, serverless database engine to store structured data in a single, self-contained file. This pattern is ideal for lightweight, portable applications requiring persistent data storage without complex infrastructure. The database file (`*.db` or `*.sqlite`) acts as both storage backend and schema container, supporting ACID-compliant transactions while minimizing dependencies.

Key advantages:
- **Single-file simplicity**: No separate server or client components; the DB file is the sole data endpoint.
- **Zero-config setup**: No installation required—just link the SQLite library (C) or leverage built-in drivers (Python, Java, etc.).
- **Cross-platform compatibility**: Works on mobile, desktop, and embedded systems.
- **SQL-based**: Uses standard ANSI SQL for schema definition and queries, with optional extensions (e.g., FTS5, JSON1).

Use cases:
- Local caching (e.g., offline apps, browser extensions).
- Configuration storage (e.g., app settings).
- Lightweight analytics or logging.
- Portable data formats (e.g., export/import via SQLite file).

---

## **2. Schema Reference**

SQLite databases are schema-less by default but enforce constraints via SQL declarations. Below are common table structures and their attributes.

| **Component**       | **Description**                                                                                     | **Syntax Example**                          | **Notes**                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Database File**   | The container for all tables, indices, and triggers.                                                | `myapp.db`                                  | Single binary file (typically <1MB overhead).                                                 |
| **Tables**          | Collections of rows with columns (supports `CREATE TABLE` syntax).                                 | `CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL);` | Columns: `INTEGER`, `TEXT`, `REAL`, `BLOB`, or custom types (e.g., `VIRTUAL` for FTS).       |
| **Indices**         | Optimize read performance on frequently queried columns.                                            | `CREATE INDEX idx_name ON users(name);`      | Automatic indices on `PRIMARY KEY` columns.                                                      |
| **Triggers**        | Automate actions (e.g., logging, validation) on `INSERT/UPDATE/DELETE`.                          | `CREATE TRIGGER after_insert AFTER INSERT ON users WHEN NEW.id > 100 BEGIN ... END;` | Requires `BEGIN TRANSACTION`/`COMMIT` wrappers.                                                 |
| **Views**           | Virtual tables derived from other tables (no stored data).                                          | `CREATE VIEW active_users AS SELECT * FROM users WHERE status = 'active';` | Useful for encapsulation.                                                                     |
| **Foreign Keys**    | Enforce referential integrity between tables (enabled via `PRAGMA`).                               | `FOREIGN KEY (user_id) REFERENCES users(id)`  | Requires `PRAGMA foreign_keys = ON;` in the app.                                               |
| **Extensions**      | Optional modules (e.g., FTS for full-text search, JSON1 for JSON support).                         | `LOAD Extension 'sqlite_fts3';`               | Compile-time or runtime enablement (depends on SQLite version).                                |

---

## **3. Query Examples**

### **3.1 Core CRUD Operations**
```sql
-- Create a table (default schema: "main")
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert data (batch inserts via `INSERT OR IGNORE`/`REPLACE`)
INSERT INTO products (name, price) VALUES ('Laptop', 999.99);
INSERT OR IGNORE INTO products (name) VALUES ('Monitor');  -- Skip if duplicate
```

### **3.2 Transactions**
```sql
-- Explicit transaction (atomicity)
BEGIN TRANSACTION;
INSERT INTO products VALUES (1, 'Keyboard', 50.00);
UPDATE products SET price = 45.00 WHERE id = 1;
COMMIT;  -- Rollback with `ROLLBACK` if errors occur
```

### **3.3 Advanced Queries**
```sql
-- Join tables (SQLite supports `INNER`, `LEFT`, etc.)
SELECT u.name, p.name AS product
FROM users u
LEFT JOIN purchases p ON u.id = p.user_id
WHERE u.active = 1;

-- Aggregations
SELECT AVG(price) AS avg_price FROM products WHERE category = 'electronics';

-- Window functions (via SQLite’s `GROUP BY` or extensions like `sqlite_window_functions`)
SELECT
    name,
    price,
    AVG(price) OVER (PARTITION BY category) AS category_avg
FROM products;
```

### **3.4 Schema Evolution**
```sql
-- Add a column (SQLite handles NULLs gracefully)
ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 10;

-- Rename a column (requires temporary table)
BEGIN;
CREATE TABLE products_temp AS SELECT name, price, stock FROM products;
DROP TABLE products;
CREATE TABLE products AS SELECT name, price, stock FROM products_temp;
DROP TABLE products_temp;
COMMIT;
```

### **3.5 Native Extensions**
```sql
-- Enable full-text search (FTS5)
LOAD Extension('sqlite_fts5');
CREATE VIRTUAL TABLE product_search USING fts5(name, description);
-- Insert into virtual table (indexed automatically)
INSERT INTO product_search VALUES ('Laptop', 'High-performance machine');
```

---

## **4. Implementation Details**

### **4.1 Key Concepts**
- **WAL Mode**: Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) improves concurrency for read-heavy workloads.
- **Page Size**: Default is 4,096 bytes; adjust with `PRAGMA page_size = 8192;` for large BLOBs.
- **Memory Cache**: SQLite caches data in RAM (`PRAGMA cache_size = -2000;` for ~2MB cache).
- **Encryption**: Use `sqlite3_encrypt` (C API) or third-party extensions (e.g., `sqlite-autocrypt`).
- **Backup**: Copy the `.db` file or use `sqlite3_db_file_control` for incremental backups.

### **4.2 Performance Tips**
| **Optimization**               | **Action**                                                                 | **Impact**                          |
|---------------------------------|-----------------------------------------------------------------------------|-------------------------------------|
| **Indices**                     | Add indices on frequently queried columns.                                | Faster `SELECT` queries.            |
| **Vacuum**                      | Run `VACUUM;` periodically to reclaim space.                              | Shrinks file size.                  |
| **Transactions**                | Batch writes in single transactions.                                       | Reduces disk I/O.                   |
| **AUTOINCREMENT**               | Avoid for high-volume tables (use `UUID()` or `RANDOM()` instead).         | Prevents integer overflow issues.   |
| **Schema Design**               | Normalize where possible; denormalize for read performance.                | Trade-off between storage and speed.|

### **4.3 Error Handling**
- **Autovacuum**: Enable with `PRAGMA autovacuum = ON;` to auto-shrink after deletes.
- **Busy Timeout**: Handle locks with `PRAGMA busy_timeout = 5000;` (ms).
- **Corruption**: Use `sqlite3_recover` (C API) or backups if the file is corrupted.

---

## **5. Query Examples (Language-Specific)**
### **5.1 Python (sqlite3 Module)**
```python
import sqlite3

conn = sqlite3.connect('myapp.db')
cursor = conn.cursor()

# Schema setup
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        task TEXT NOT NULL,
        completed BOOLEAN DEFAULT 0
    )
""")

# CRUD
cursor.execute("INSERT INTO tasks VALUES (?, ?, ?)", (1, "Buy groceries", 0))
conn.commit()

# Query
cursor.execute("SELECT * FROM tasks WHERE completed = 0")
print(cursor.fetchall())
conn.close()
```

### **5.2 Java (SQLite-Java)**
```java
import android.database.sqlite.SQLiteDatabase;

SQLiteDatabase db = this.openOrCreateDatabase("myapp.db", MODE_PRIVATE, null);
db.execSQL("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)");

db.beginTransaction();
ContentValues values = new ContentValues();
values.put("name", "Alice");
db.insert("users", null, values);
db.setTransactionSuccessful();
db.endTransaction();
```

### **5.3 JavaScript (browser)**
```javascript
const db = openDatabase('myapp.db', '1.0', 'Test Database', 2 * 1024 * 1024);

// Schema
db.transaction(tx => {
    tx.executeSql('CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, value TEXT)');
});

// Write
db.transaction(tx => {
    tx.executeSql('INSERT INTO items VALUES (?, ?)', [1, 'Sample Data']);
});
```

---

## **6. Related Patterns**

| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Embedded NoSQL (LMDB)](LMDB.md)** | Key-value store with faster reads/writes than SQLite (no SQL support).         | High-speed key-value access (e.g., caching).     |
| **[Client-Server DB](PostgreSQL.md)** | Traditional relational DB with separate client/server components.              | Scalable, multi-user applications.               |
| **[In-Memory DB](SQLite-InMemory.md)** | SQLite mode where data resides in RAM (lost on shutdown).                     | Temporary data (e.g., session storage).          |
| **[Immutable DB (RocksDB)](RocksDB.md)** | Write-once-read-many database for large-scale analytics.                      | Read-heavy workloads (e.g., logs, time-series).   |
| **[ORM Wrapper](SQLAlchemy.md)**  | Object-relational mapping layer (e.g., SQLAlchemy, Django ORM).               | Python apps needing Pythonic database access.    |

---

## **7. Common Pitfalls**
1. **No Server**: SQLite lacks replication/clustering; use separate files for sharding.
2. **File Locking**: Avoid concurrent writes from multiple processes (use `PRAGMA busy_timeout`).
3. **Schema Migrations**: Automate schema changes (e.g., Alembic for Python).
4. **BLOBs**: Large binary data bloat the file; compress or store externally.
5. **Extensions**: Not all SQLite flavors support extensions (e.g., FTS5 may need compilation).

---
**Appendix**:
- [SQLite Official Docs](https://www.sqlite.org/docs.html)
- [SQLite Schema Migration Guide](https://sqlite.org/lang_altertable.html)