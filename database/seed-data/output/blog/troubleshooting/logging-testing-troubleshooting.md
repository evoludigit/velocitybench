# **Debugging Logging & Testing: A Practical Troubleshooting Guide**

## **Introduction**
Logging and testing are critical components of robust backend systems. When they fail, it can lead to:
- **Undetected bugs** during development
- **Poor observability** in production
- **Failed deployments** due to missing assertions

This guide helps you quickly diagnose and resolve common issues with **logging patterns** (e.g., structured logging, async logging) and **testing patterns** (unit, integration, E2E).

---

# **🔍 Symptom Checklist**

| **Symptom** | **Possible Cause** |
|------------|-------------------|
| Logs are missing entirely | Incorrect logging level, broken logger configuration, or log output path issues |
| Logs are not structured (unreadable) | Missing JSON formatting, wrong log level, or improper log parser |
| Tests fail intermittently | Flaky tests, missing mocks, or incorrect test assertions |
| Logs appear delayed | Async logging not properly flushed or buffered |
| Unit tests pass, but E2E fails | Missing integration layer checks or untracked side effects |
| High CPU/memory usage during logging | Unbounded log buffering, improper log rotation, or slow log sinks |
| Tests run too slowly | Unoptimized test cases, excessive database interactions, or slow mocks |

---

# **⚡ Common Issues & Fixes**

---

## **1. Logging Issues**

### **Issue: Logs Not Being Written**
#### **Symptoms:**
- No logs appear in console/file
- Application crashes silently with no debug output

#### **Common Causes & Fixes:**

| **Cause** | **Debugging Steps** | **Fix** |
|----------|-------------------|--------|
| Incorrect log level | `logger.debug("Test");` may not show if level is `INFO` | Set correct level: `logger.setLevel(Level.DEBUG)` (Java) / `logging.config.level = DEBUG` (Python) |
| Broken logger config | Missing `logback.xml` (Java) or `logging.ini` (Python) | Verify config file is loaded: `logger.info("Config loaded?")` |
| Log file path wrong | App writes to `/tmp/logs/` but it doesn’t exist | Ensure directory exists: `mkdir -p /var/log/app` |
| Log sink not configured | No handler in Python or no appender in Java | Add proper handler: `FileHandler("app.log")` (Java) / `FileHandler('app.log', mode='a')` (Python) |
| Async logging not flushed | Logs buffered but not written immediately | Force flush: `logger.shutdown()` before app exit (Java) / `logging.shutdown()` (Python) |

#### **Example Fix (Python - Structured Logging)**
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()  # Console logs
    ]
)
logger = logging.getLogger(__name__)

logger.debug({"event": "test", "status": "running"})  # Now logs properly
```

---

### **Issue: Structured Logs Not Parsable**
#### **Symptoms:**
- Logs appear as `INFO: {"error": "failed"}` (unstructured)
- No correlation between logs and metrics

#### **Fix: Use Proper JSON Logging**
```python
# Python (structlog example)
import structlog
logger = structlog.get_logger()
logger.info("user_login", user_id=123, status="success")

# Java (Logback with JSON)
<configuration>
    <appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="net.logstash.logback.encoder.LogstashEncoder"/>
    </appender>
</configuration>
```

---

### **Issue: Logs Too Slow (Performance Bottleneck)**
#### **Symptoms:**
- High CPU on log-heavy endpoints
- Delays in response times

#### **Fix: Async Logging with Batching**
```java
// Java (AsyncLogAppender)
<appender name="ASYNC" class="ch.qos.logback.classic.AsyncAppender">
    <appender-ref ref="FILE" />
    <queueSize>1000</queueSize>  <!-- Batch logs -->
</appender>

<Root level="DEBUG">
    <appender-ref ref="ASYNC" />
</Root>
```

```python
# Python (async logging with Python 3.7+)
import logging
import asyncio

async def log_async(message):
    async with aiofiles.open("app.log", 'a') as f:
        await f.write(message + '\n')

asyncio.run(log_async("Test log"))
```

---

## **2. Testing Issues**

### **Issue: Flaky Tests**
#### **Symptoms:**
- Tests pass locally but fail in CI
- Random failures (e.g., race conditions)

#### **Fix: Add Stability Checks**
```python
# Python (pytest with retries)
import pytest
from pytest_rerunfailures import RerunFailed

@pytest.mark.retry(3)  # Retry 3 times on failure
def test_flaky_api():
    response = requests.get("http://api.example.com")
    assert response.status_code == 200
```

```java
// Java (TestNG with retry)
@Test(retryAnalyzer = RetryAnalyzer.class)
public void testFlakyEndpoint() {
    assertEquals(200, client.executeRequest().getStatusCode());
}
```

---

### **Issue: Missing Test Coverage**
#### **Symptoms:**
- Low test coverage (e.g., <80% in SonarQube)
- Undetected regressions

#### **Fix: Add Missing Test Cases**
```python
# Python (pytest coverage)
import pytest
import coverage

@pytest.fixture
def coverage_report():
    cov = coverage.Coverage()
    cov.start()
    yield cov
    cov.stop()
    cov.save()
```

```bash
# Run coverage check
pytest --cov=./ --cov-report=xml
```

---

### **Issue: Slow Integration Tests**
#### **Symptoms:**
- Tests take >10s to run
- Database slows down under test load

#### **Fix: Use Test Containers & Mocking**
```python
# Python (Testcontainers for DB)
import testcontainers.postgres
from fastapi.testclient import TestClient

@pytest.fixture
def test_db():
    with testcontainers.postgres.PostgresContainer("postgres:13") as postgres:
        yield postgres.get_connection_url()

def test_db_connection(test_db):
    engine = create_engine(test_db)
    with engine.connect() as conn:
        assert conn.execute("SELECT 1")
```

```java
// Java (Testcontainers)
@DynamicPropertySource
static void properties(Map<String, Object> props) {
    PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:13");
    postgres.start();
    props.put("spring.datasource.url", postgres.getJdbcUrl());
}
```

---

# **🛠 Debugging Tools & Techniques**

| **Tool** | **Use Case** | **Example Command** |
|----------|-------------|-------------------|
| **`journalctl`** | Debug systemd logs | `journalctl -u myapp --no-pager` |
| **`strace`** | Check syscall issues | `strace -f python myapp.py > debug.txt` |
| **`logrotate`** | Analyze log rotation | `grep -i error /var/log/app.log*` |
| **`pytest --cov`** | Check test coverage | `pytest --cov=src --cov-report=html` |
| **`locust`** | Load test API endpoints | `locust -f script.py` |
| **`Python -m faulthandler`** | Crash debugging | `PYTHONFAULTHANDLER=1 python myapp.py` |

---

# **🚀 Prevention Strategies**

### **1. For Logging:**
✅ **Use Structured Logging** – Always log in JSON format for observability.
✅ **Set Log Retention** – Rotate logs (`logrotate`) to avoid disk issues.
✅ **Monitor Log Volume** – Alert if logs exceed expected rates (e.g., 1GB/day).
✅ **Sanitize Sensitive Data** – Mask PII before logging (`{"user": "***}`).

### **2. For Testing:**
✅ **Isolate Tests** – Use dependency injection for mocking.
✅ **Parallelize Tests** – Run unit tests in parallel (`pytest-xdist`).
✅ **Add CI Gatekeeper** – Block merges if coverage drops below 80%.
✅ **Test Edge Cases** – Include null checks, error boundaries, and race conditions.

---

# **🔚 Final Checklist Before Deployment**
1. ✅ **Logs:** Verify structured logging, proper levels, and rotation.
2. ✅ **Tests:** Ensure 100% coverage for critical paths, run locally & CI.
3. ✅ **Performance:** Check logs/tests don’t slow down the system.
4. ✅ **Observability:** Ensure metrics (e.g., Prometheus) align with logs.

---
**Next Steps:**
- Review logs with `grep | awk` for patterns.
- Run `pytest --maxfail=3 -v` to catch flakiness early.
- Use `tail -f /var/log/app.log` for real-time debugging.

This guide keeps debugging **fast and actionable**. If a symptom isn’t here, check your configuration or consider a deeper dive into the language/framework docs. 🚀