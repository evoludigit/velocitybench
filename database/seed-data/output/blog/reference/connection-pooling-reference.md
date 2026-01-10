# **[Pattern] Database Connection Pooling – Reference Guide**

---

## **Overview**
Database connection pooling is an infrastructure technique that minimizes the overhead of establishing new database connections by reusing existing ones in a shared pool. Each connection is expensive to create (typically 20–100ms due to TCP handshakes, authentication, and SSL negotiation). By maintaining a pool of pre-configured connections, applications borrow connections when needed and return them afterward, reducing latency and improving scalability for high-throughput systems. This pattern is widely used in web applications, microservices, and distributed systems to balance resource usage efficiently.

Key benefits include:
- **Reduced latency**: Near-zero overhead for retrieving/returning connections.
- **Scalability**: Supports concurrency without unlimited connection creation.
- **Resource efficiency**: Limits active connections to a manageable number.
- **Connection management**: Automates validation, eviction of stale connections, and dynamic resizing.

---

## **Schema Reference**
Below is a conceptual schema of key components and their interactions in a connection pool system.

| **Component**          | **Role**                                                                                     | **Key Attributes**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Connection Pool**    | Maintains idle and active database connections in memory.                                    | - Min/max pool size                                                                                    |
|                        |                                                                                             | - Default connection timeout                                                                          |
|                        |                                                                                             | - Leak detection threshold (unused connections)                                                       |
| **Pool Manager**       | Handles the lifecycle of connections (borrowing, returning, cleanup).                       | - Borrow/return operations                                                                          |
|                        |                                                                                             | - Connection validation policy (e.g., ping frequency)                                               |
|                        |                                                                                             | - Dynamic pool resizing heuristics                                                                   |
| **Health Checker**     | Validates connections in the pool for livability.                                           | - Validation query (e.g., `SELECT 1`)                                                                |
|                        |                                                                                             | - Failure threshold (e.g., max retries before eviction)                                              |
| **Client Application** | Interacts with the pool to acquire/release connections.                                     | - Connection acquisition timeout                                                                      |
|                        |                                                                                             | - Transaction isolation level                                                                      |
| **Database**           | Target database system (e.g., PostgreSQL, MySQL, MongoDB).                                  | - Maximum allowed connections (server-side limit)                                                   |
| **Connection Factory** | Abstracts connection creation logic (e.g., JDBC, PgBouncer, or driver-specific).             | - Connection URL, credentials, and properties (e.g., `charset`, `timeZone`)                          |

---

## **Implementation Components**
### **1. Connection Pool Types**
| **Type**               | **Description**                                                                                     | **Use Case**                                                                                          |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **In-Process Pool**    | Managed by the application (e.g., HikariCP, Apache DBCP).                                        | Standalone applications, microservices                                                                |
| **Out-of-Process Pool**| Managed externally (e.g., PgBouncer for PostgreSQL, ProxySQL for MySQL).                       | Shared databases in cloud environments, multi-tenant architectures                                     |
| **Lightweight Pool**   | Minimal overhead (e.g., `jdbc:pool` in some drivers).                                             | Low-latency requirements, embedded systems                                                           |

---

### **2. Key Configuration Parameters**
| **Parameter**          | **Description**                                                                                   | **Example Values**                                                                                  |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| `minPoolSize`          | Minimum number of connections to keep in the pool.                                               | `5–10` (balanced for startup latency and resource usage)                                            |
| `maxPoolSize`          | Maximum connections allowed in the pool.                                                         | `10–50` (adjust based on database server limits)                                                    |
| `connectionTimeout`    | Time (ms) to wait before failing if a connection cannot be acquired.                             | `30,000` (30 seconds)                                                                               |
| `idleConnectionTestPeriod` | Interval (ms) for testing idle connections for validity.                                        | `60,000` (1 minute)                                                                                 |
| `validationQuery`      | Query to validate a connection is alive.                                                          | `SELECT 1` (for most databases)                                                                     |
| `maxLifetime`          | Maximum age (ms) of a connection before it is replaced.                                          | `1800,000` (30 minutes)                                                                              |
| `testOnBorrow`         | Test connections when borrowed from the pool.                                                    | `true`/`false` (recommended: `true`)                                                                |
| `testOnReturn`         | Test connections when returned to the pool.                                                      | `false` (usually unnecessary)                                                                         |
| `leakDetectionThreshold` | Time (ms) unused connections are tracked before reporting a leak.                              | `60,000` (1 minute)                                                                                 |

---

## **Code Examples**
### **1. Java (HikariCP)**
```java
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;

public class ConnectionPoolExample {
    public static void main(String[] args) {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:postgresql://localhost:5432/mydb");
        config.setUsername("user");
        config.setPassword("password");
        // Pool settings
        config.setMinimumIdle(5);
        config.setMaximumPoolSize(20);
        config.setConnectionTimeout(30000);
        config.setIdleTimeout(600000);
        config.setMaxLifetime(1800000);
        config.setValidationTimeout(5000);
        config.addDataSourceProperty("validationQuery", "SELECT 1");

        HikariDataSource dataSource = new HikariDataSource(config);

        // Borrow a connection (implicit in JDBC calls)
        try (Connection conn = dataSource.getConnection()) {
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery("SELECT * FROM users");
            // Process results...
        } // Connection is automatically returned to the pool
    }
}
```

---

### **2. Python (SQLAlchemy + psycopg2)**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Configure connection pool
engine = create_engine(
    "postgresql://user:password@localhost:5432/mydb",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,  # seconds
    pool_recycle=1800,  # seconds (max connection lifetime)
    pool_pre_ping=True  # Test connections on borrow
)

# Usage: Connections are managed automatically
with engine.connect() as conn:
    result = conn.execute("SELECT * FROM users")
    for row in result:
        print(row)
```

---

### **3. Node.js (Knex.js)**
```javascript
const knex = require('knex')({
    client: 'pg',
    connection: {
        host: 'localhost',
        port: 5432,
        user: 'user',
        password: 'password',
        database: 'mydb'
    },
    pool: {
        min: 2,
        max: 10,
        afterCreate: (conn, done) => {
            conn.query('SELECT 1', (err) => {
                if (err) console.error('Connection validation failed');
                done();
            });
        }
    }
});

// Usage
knex('users').select('*').then(rows => console.log(rows))
    .finally(() => knex.destroy()); // Closes the pool
```

---

### **4. Out-of-Process Pool (PgBouncer - PostgreSQL)**
Configure PgBouncer (`pgbouncer.ini`):
```
[databases]
mydb = host=localhost port=5432 dbname=mydb

[pgbouncer]
pool_mode = transaction
default_pool_size = 20
max_client_conn = 100
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
```

Client application (Python):
```python
engine = create_engine("postgresql://user:password@localhost:6432/mydb")
```

---

## **Query Examples**
### **1. Pool Statistics (HikariCP)**
```java
// Get pool metrics
PoolStats stats = dataSource.getHikariPoolMXBean().getPoolStats();
System.out.println("Active connections: " + stats.getActiveConnections());
System.out.println("Idle connections: " + stats.getIdleConnections());
```

### **2. Monitor Pool Health (SQLAlchemy)**
```python
from sqlalchemy import inspect

inspector = inspect(engine)
print("Pool size:", inspector.get_pool_size())
print("Pool status:", inspector.get_pool_status())
```

### **3. Dynamic Resizing (Knex.js)**
```javascript
// Adjust pool size dynamically
knex.destroy(); // Close existing pool
const newKnex = knex.update({
    pool: { min: 5, max: 30 }
});
```

---

## **Best Practices**
1. **Tune Pool Size**:
   - Start with `minPoolSize` = 2–5 and `maxPoolSize` = 2x–5x the expected concurrent users.
   - Monitor `activeConnections` vs. `maxPoolSize` to avoid over/under-provisioning.

2. **Connection Validation**:
   - Use `validationQuery` (e.g., `SELECT 1`) to detect stale connections.
   - Enable `testOnBorrow` to catch failures early.

3. **Connection Lifetime**:
   - Set `maxLifetime` to prevent long-lived connections from degrading performance (e.g., 30 minutes).

4. **Error Handling**:
   - Implement retry logic for temporary failures (e.g., `SQLTransientException`).
   - Log connection leaks with `leakDetectionThreshold`.

5. **Database Limits**:
   - Respect the server-side `max_connections` (e.g., PostgreSQL’s `max_connections` setting).

6. **Security**:
   - Use SSL for connections in production.
   - Rotate credentials periodically.

---

## **Common Pitfalls**
| **Pitfall**                          | **Symptom**                          | **Solution**                                                                                      |
|---------------------------------------|--------------------------------------|--------------------------------------------------------------------------------------------------|
| **Pool exhaustion**                   | `SQLRecoverableException` (timeout) | Increase `maxPoolSize` or optimize queries to reduce connection hold times.                     |
| **Connection leaks**                  | Growing pool size over time          | Set `leakDetectionThreshold` and monitor unused connections.                                      |
| **Stale connections**                 | `SQLNonTransientConnectionException` | Use `idleConnectionTestPeriod` and `validationQuery`.                                             |
| **Over-provisioning**                 | High memory usage                    | Adjust `minPoolSize` and `maxPoolSize` based on workload metrics.                                |
| **Slow queries blocking connections** | Long `activeConnections`              | Optimize slow queries or reduce transaction isolation levels.                                    |

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                                     |
|----------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Lazy Initialization](https://refactoring.guru/design-patterns/lazy-initialization)** | Delay pool creation until first use.                                                               | Applications with unpredictable startup times or resource constraints.                             |
| **[Connection Resilience](https://martinfowler.com/articles/patterns-of-distributed-systems.html#ConnectionResilience)** | Handle transient failures (e.g., retries, circuit breakers).    | Distributed systems with unreliable database connectivity.                                           |
| **[Caching](https://refactoring.guru/patterns/caching)** | Cache query results to reduce database load.                                                        | Read-heavy workloads with low update frequency.                                                   |
| **[Sharding](https://refactoring.guru/patterns/sharding)** | Split data across multiple database instances to scale horizontally.                              | High-write or high-throughput systems exceeding single-node limits.                                |
| **[Queue-Based Asynchronous Processing](https://docs.microsoft.com/en-us/azure/architecture/patterns/queue-based-asynchronous-processing)** | Offload database operations to a queue (e.g., RabbitMQ).                                     | Long-running transactions or background processing.                                               |

---

## **Further Reading**
- [HikariCP Documentation](https://github.com/brettwooldridge/HikariCP)
- [SQLAlchemy Pooling](https://docs.sqlalchemy.org/en/14/core/pooling.html)
- [PgBouncer](https://www.pgbouncer.org/)
- [Connection Pooling in Microservices (Martin Fowler)](https://martinfowler.com/articles/lazy-loading-connections.html)

---
**Last Updated:** [Date]
**Author:** [Your Name/Organization]