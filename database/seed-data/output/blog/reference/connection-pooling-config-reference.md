# **[Pattern] Connection Pool Configuration Reference Guide**

---

## **Overview**
The **Connection Pool Configuration** pattern optimizes database interactions by pre-allocating a pool of reusable connections rather than establishing a new connection for every database query. This reduces latency, improves performance, and minimizes resource overhead, especially in high-traffic applications. Connection pools manage connections efficiently by reusing them, recycling them when idle, and monitoring metrics like connection usage, errors, and throttling. This pattern is critical for applications interacting with resource-intensive databases (e.g., relational databases, document stores) where connection establishment is costly.

Key benefits include:
- **Reduced overhead**: Avoids repeated TCP handshakes and authentication.
- **Scalability**: Handles concurrent requests without constant resource exhaustion.
- **Failure resilience**: Graceful degradation when pool limits are exceeded.
- **Configurability**: Adjustable pool size, timeout settings, and validation strategies.

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                 |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Connection Pool**     | A cache of reusable database connections managed by a pool manager (e.g., HikariCP, Apache DBCP, c3p0).                                                                                                         |
| **Core Pool Size**      | Minimum number of connections maintained in the pool.                                                                                                                                                           |
| **Maximum Pool Size**   | Maximum number of connections the pool can allocate (e.g., to prevent resource exhaustion).                                                                                                                   |
| **Idle Timeout**        | Time (in seconds/milliseconds) after which idle connections are recycled or evicted.                                                                                                                      |
| **Validation Query**    | Optional SQL query executed periodically to verify connections are alive (reduces "zombie" connections).                                                                                                       |
| **Acquisition Timeout** | Maximum time (e.g., 30 seconds) to wait for a connection before failing (to avoid blocking applications).                                                                                                       |
| **Leak Detection**      | Mechanism to detect and log connections that weren’t returned to the pool (e.g., due to exceptions).                                                                                                           |
| **Metrics**             | Monitored metrics (e.g., active/inactive connections, wait time, error rates) via tools like Prometheus or embedded counters.                                                                                     |
| **Dynamic Scaling**     | Adjusts pool size based on runtime conditions (e.g., load, system health) via adaptive algorithms or external triggers.                                                                                          |

---

## **Schema Reference**

### **1. Core Configuration Attributes**
| **Attribute**            | **Type**       | **Description**                                                                                                                                                                                                 | **Default**          | **Example Values**                     |
|--------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|-----------------------------------------|
| `pool_name`              | String         | A descriptor (e.g., `primary_db`, `read_replica`) for logging/monitoring.                                                                                                                                       | *None*               | `"app_mysql_pool"`                      |
| `driver_class`           | String         | JDBC driver class (e.g., `com.mysql.cj.jdbc.Driver`).                                                                                                                                                           | *Required*           | `"org.postgresql.Driver"`               |
| `url`                    | String         | Database JDBC URL (e.g., `jdbc:postgresql://host:5432/db`).                                                                                                                                                     | *Required*           | `"jdbc:mysql://db:3306/app_database"`    |
| `username`               | String         | Database username.                                                                                                                                                                                                     | *Required*           | `"admin"`                               |
| `password`               | String         | Database password (use secrets management for production).                                                                                                                                                     | *Required*           | `"secure_password"`                     |
| `connection_timeout_ms`  | Integer (ms)   | Max time to establish a new connection.                                                                                                                                                                       | `10,000`             | `30,000`                                |

---

### **2. Pool Sizing Controls**
| **Attribute**            | **Type**       | **Description**                                                                                                                                                                                                 | **Default**          | **Example Values**                     |
|--------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `minimum_pool_size`      | Integer        | Minimum active connections in the pool.                                                                                                                                                                       | `5`                  | `10`                                    |
| `maximum_pool_size`      | Integer        | Maximum connections the pool can allocate (prevents resource starvation).                                                                                                                                    | `20`                 | `50`                                    |
| `initial_pool_size`      | Integer        | Connections pre-allocated at startup (reduces latency for initial requests).                                                                                                                                | `Equal to `minimum` | `15`                                    |
| `idle_timeout_ms`        | Integer (ms)   | Time before idle connections are recycled.                                                                                                                                                                   | `60,000` (1 min)     | `300,000` (5 min)                      |
| `lifo`                   | Boolean        | Whether to use Last-In-First-Out (LIFO) for connection allocation (default: `false` for FIFO).                                                                                                           | `false`              | `true`                                  |

---

### **3. Connection Validation & Lifecycle**
| **Attribute**            | **Type**       | **Description**                                                                                                                                                                                                 | **Default**          | **Example Values**                     |
|--------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `validation_query`       | String         | Query to verify a connection is alive (e.g., `SELECT 1`).                                                                                                                                                     | *None*               | `"SELECT 1 FROM dual"`                  |
| `validation_timeout_ms`  | Integer (ms)   | Timeout for validation queries.                                                                                                                                                                               | `5,000`              | `10,000`                                |
| `test_on_borrow`         | Boolean        | Validate connection when borrowed from the pool.                                                                                                                                                                | `false`              | `true`                                  |
| `test_on_return`         | Boolean        | Validate connection when returned to the pool.                                                                                                                                                                | `false`              | `true`                                  |
| `test_while_idle`        | Boolean        | Validate idle connections during eviction.                                                                                                                                                                   | `false`              | `true`                                  |
| `remove_abandoned`       | Boolean        | Remove connections marked as abandoned (unreturned).                                                                                                                                                          | `false`              | `true`                                  |
| `abandoned_timeout_ms`   | Integer (ms)   | Time before an unreturned connection is considered abandoned.                                                                                                                                                  | `60,000`             | `300,000`                               |

---

### **4. Performance & Error Handling**
| **Attribute**            | **Type**       | **Description**                                                                                                                                                                                                 | **Default**          | **Example Values**                     |
|--------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `max_lifetime_ms`        | Integer (ms)   | Max age of a connection before it’s evicted (prevents stale connections).                                                                                                                                      | `1800,000` (30 min)  | `5,400,000` (90 min)                   |
| `connection_init_timeout`| Integer (ms)   | Timeout for initializing a new connection.                                                                                                                                                                       | `1,000`              | `5,000`                                 |
| `acquisition_timeout_ms` | Integer (ms)   | Timeout for waiting to borrow a connection (avoids blocking).                                                                                                                                                 | `30,000`             | `60,000`                                |
| `fail_fast`              | Boolean        | Fail immediately if a connection fails validation (vs. retrying).                                                                                                                                                 | `false`              | `true`                                  |
| `unreturned_connection_timeout` | Integer (ms) | Time before logging a warning for an unreturned connection.                                                                                                                                                   | `60,000`             | `120,000`                               |

---

### **5. Advanced Features**
| **Attribute**            | **Type**       | **Description**                                                                                                                                                                                                 | **Default**          | **Example Values**                     |
|--------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `dynamic_scaling_enabled`| Boolean        | Enable/disable dynamic pool resizing (e.g., via JVM metrics).                                                                                                                                                   | `false`              | `true`                                  |
| `scaling_retry_delay_ms` | Integer (ms)   | Delay between scaling attempts.                                                                                                                                                                                 | `30,000`             | `60,000`                                |
| `scaling_min_size`       | Integer        | Minimum pool size during dynamic scaling.                                                                                                                                                                       | `Same as `minimum`` | `20`                                    |
| `scaling_max_size`       | Integer        | Maximum pool size during dynamic scaling.                                                                                                                                                                       | `Same as `maximum`` | `100`                                   |
| `metrics_interval_ms`    | Integer (ms)   | Frequency to collect pool metrics (e.g., for monitoring).                                                                                                                                                     | `60,000`             | `10,000`                                |

---

## **Query Examples**

### **1. Basic Connection Pool Setup (Java/HikariCP)**
```java
// Configure HikariCP pool
PoolConfig poolConfig = new PoolConfig();
poolConfig.setMinimumPoolSize(5);
poolConfig.setMaximumPoolSize(20);
poolConfig.setIdleTimeout(Duration.ofMinutes(5));
poolConfig.setConnectionTimeout(Duration.ofSeconds(30));
poolConfig.setValidationTimeout(Duration.ofSeconds(5));
poolConfig.setTestOnBorrow(true);
poolConfig.setAbandonedTimeout(Duration.ofMinutes(1));

HikariConfig config = new HikariConfig();
config.setJdbcUrl("jdbc:postgresql://localhost:5432/mydb");
config.setUsername("user");
config.setPassword("pass");
config.setDriverClassName("org.postgresql.Driver");
config.setPoolName("app_pool");
config.setPoolConfig(poolConfig);

// Initialize pool
HikariDataSource dataSource = new HikariDataSource(config);

// Usage
try (Connection conn = dataSource.getConnection()) {
    Statement stmt = conn.createStatement();
    ResultSet rs = stmt.executeQuery("SELECT * FROM users");
    // Process results...
} catch (SQLException e) {
    // Handle error (e.g., log to metrics)
}
```

---

### **2. Dynamic Scaling (Spring Boot + HikariCP)**
```properties
# application.properties
spring.datasource.hikari.minimum-idle=10
spring.datasource.hikari.maximum-pool-size=50
spring.datasource.hikari.dynamic-scaling.enabled=true
spring.datasource.hikari.dynamic-scaling.minimum-size=15
spring.datasource.hikari.dynamic-scaling.maximum-size=100
spring.datasource.hikari.dynamic-scaling.retry-delay=30000
```

```java
@Configuration
public class HikariConfigDynamicScaling {
    @PostConstruct
    public void enableDynamicScaling() {
        // Custom logic to adjust pool size based on metrics (e.g., CPU usage)
        HikariDataSource dataSource = (HikariDataSource) applicationContext.getBean("dataSource");
        HikariPoolMXBean poolMXBean = dataSource.getHikariPoolMXBean();

        // Example: Scale up if active connections < 70% of max
        if (poolMXBean.getActiveConnections() < 0.7 * poolMXBean.getMaximumPoolSize()) {
            poolMXBean.addPool();
        }
    }
}
```

---

### **3. SQL Validation Query**
```sql
-- Example validation query (runs periodically to check connection health)
SELECT 1 AS validation_result FROM information_schema.schemas WHERE schema_name = 'public';
```

---

### **4. Monitoring & Metrics (Prometheus)**
```java
// Expose HikariCP metrics to Prometheus
@Bean
public MetricsServlet metricsServlet() {
    MetricsServlet servlet = new MetricsServlet();
    servlet.setMetricsRegistry(registry);
    return servlet;
}

@Bean
public DataSource dataSource() {
    HikariDataSource ds = new HikariDataSource();
    // ... configure pool ...
    return ds;
}

// Map Hikari metrics to Prometheus
@Bean
public MetricWriter metricWriter() {
    return new MetricWriter() {
        @Override
        public void write(Metric metric) {
            // Emit metrics like:
            // hikari_pool_connections_active{pool="app_pool"} 5.0
        }
    };
}
```

---

## **Error Handling & Diagnostics**

| **Error Scenario**               | **Root Cause**                          | **Solution**                                                                                                                                                                                                 |
|-----------------------------------|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Connection Timeout**           | Pool exhausted or slow database.       | Increase `maximum_pool_size` or optimize queries. Check `acquisition_timeout_ms`.                                                                                                                      |
| **Validation Failure**           | Stale/dropped connection.              | Set `validation_query` and increase `max_lifetime_ms`. Enable `test_on_borrow`.                                                                                                                          |
| **Leaked Connections**           | Unclosed `Connection` statements.      | Use try-with-resources. Enable `remove_abandoned` and `abandoned_timeout_ms`.                                                                                                                             |
| **High Wait Time**               | Pool underutilized.                    | Adjust `minimum_pool_size` or enable dynamic scaling. Monitor `poolmxbean.getWaitTime()`.                                                                                                                  |
| **Connection Refused**           | Database down or misconfigured URL.    | Verify `url`, `username`, `password`. Check logs for connection errors.                                                                                                                                        |
| **Too Many Connections**         | Pool size too large.                   | Reduce `maximum_pool_size` or tune application queries (e.g., batch operations).                                                                                                                          |

---

## **Related Patterns**

1. **Database Sharding**
   - *Purpose*: Distribute database load across multiple servers.
   - *Connection Pool Integration*: Each shard can have its own connection pool with isolated configuration (e.g., `pool_name="shard_1_pool"`).
   - *Example*: Use a pool per shard to manage read/write splits.

2. **Lazy Loading with Connection Pooling**
   - *Purpose*: Delay connection initialization until needed (e.g., for rare operations).
   - *Implementation*: Set `initial_pool_size=0` and rely on `minimum_pool_size` to grow as needed. Useful for microservices with sporadic traffic.
   - *Trade-off*: Higher latency for first requests; simpler setup.

3. **Connection Pool Circuit Breaker**
   - *Purpose*: Temporarily disable the pool if errors exceed a threshold (e.g., 5 failures in 10 seconds).
   - *Tools*: Integrate with Hystrix or Resilience4j to fail fast and retry later.
   - *Example*:
     ```java
     @CircuitBreaker(name = "dbPool", fallbackMethod = "fallbackQuery")
     public List<User> queryUsers(ConnectionPool pool) {
         // Use pool.getConnection()...
     }
     ```

4. **Asynchronous Query Processing**
   - *Purpose*: Offload queries to a separate thread pool to avoid blocking the main pool.
   - *Implementation*: Use `CompletableFuture` or RxJava to execute queries asynchronously.
   - *Example*:
     ```java
     CompletableFuture.supplyAsync(() -> {
         try (Connection conn = pool.getConnection()) {
             return conn.prepareStatement("SELECT * FROM users").executeQuery();
         }
     }, Executors.newFixedThreadPool(4));
     ```

5. **Read Replica Routing**
   - *Purpose*: Distribute read queries to replicas to reduce load on the primary.
   - *Connection Pool Integration*: Maintain separate pools for primary/writes and replicas/reads.
   - *Example*:
     ```java
     // Primary pool (writes)
     PoolConfig primaryConfig = new PoolConfig();
     primaryConfig.setPoolName("primary_pool");
     primaryConfig.setMaximumPoolSize(10);

     // Replica pool (reads)
     PoolConfig replicaConfig = new PoolConfig();
     replicaConfig.setPoolName("replica_pool");
     replicaConfig.setMaximumPoolSize(30);
     ```

6. **Connection Pool Tagging**
   - *Purpose*: Categorize connections forauditing or routing (e.g., "admin_pool" vs. "guest_pool").
   - *Implementation*: Use custom `PoolConfig.setPoolName()` and extend pool managers to track tags.
   - *Example*:
     ```java
     HikariConfig adminConfig = new HikariConfig();
     adminConfig.setPoolName("admin_pool");
     adminConfig.setUsername("admin_user");
     ```

7. **Connection Pool Stress Testing**
   - *Purpose*: Validate pool behavior under load.
   - *Tools*: Use JMeter or Gatling to simulate concurrent connections.
   - *Metrics to Monitor*:
     - `active_connections` > `maximum_pool_size` (indicates leaks).
     - `wait_time` spikes (indicates contention).
     - `error_rate` > 0 (indicates connection issues).

---

## **Best Practices**
1. **Tune Pool Size Proactively**:
   - Start with `minimum_pool_size = 5` and `maximum_pool_size = 2×minimum`.
   - Use tools like **VisualVM** or **YourKit** to profile connection usage.

2. **Balance Validation Overhead**:
   - Enable `validation_query` only if connections frequently fail (e.g., after network partitions).
   - Set `validation_timeout_ms` to a reasonable value (e.g., 5 seconds).

3. **Monitor Aggressively**:
   - Track `poolmxbean` metrics (e.g., `activeConnections`, `waitTime`, `errorCount`).
   - Set up alerts for:
     - `activeConnections` approaching `maximumPoolSize`.
     - `waitTime` > `acquisitionTimeoutMs` (10% of threshold).

4. **Secure Credentials**:
   - Never hardcode passwords. Use **Spring Cloud Config**, **AWS Secrets Manager**, or **Vault**.
   - Example:
     ```java
     @Value("${db.password}")
     private String password;
     ```

5. **Handle Graceful Degradation**:
   - Implement retry logic for transient failures (e.g., `SQLErrorCode.UNKNOWN_TRANSACTION`).
   - Example:
     ```java
     @Retry(maxAttempts = 3, backoff = @Backoff(delay = 1000))
     public void saveUser(User user) throws SQLException {
         try (Connection conn = pool.getConnection()) {
             // Save logic...
         }
     }
     ```

6. **Avoid Over-Initialization**:
   - Set `initial_pool_size` to `minimum_pool_size` if startup latency is acceptable.
   - For low-traffic apps, start with `initial_pool_size=0` and let the pool grow dynamically.

7. **Document Pool Limits**:
