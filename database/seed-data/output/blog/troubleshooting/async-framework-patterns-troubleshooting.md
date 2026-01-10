# **Debugging Async Framework Patterns (FastAPI, Quart): A Troubleshooting Guide**

## **1. Introduction**
Async frameworks like **FastAPI** and **Quart** (async Flask equivalent) are powerful for building high-performance, scalable web applications. However, improper implementation can lead to performance bottlenecks, reliability issues, and integration problems. This guide covers common symptoms, debugging techniques, and fixes for async framework misconfigurations.

---

## **2. Symptom Checklist**
Before diving into debugging, check if these symptoms apply:

| **Symptom**                          | **Possible Cause**                          |
|--------------------------------------|--------------------------------------------|
| High latency in requests             | Blocking I/O operations                     |
| 502 Bad Gateway errors               | Unhandled exceptions in async routes       |
| Database deadlocks                   | Blocking database queries in async context |
| Slow response times                  | Missing `await` in non-async dependencies  |
| Connection leaks                     | Unclosed async resources (DB, HTTP clients)|
| Memory leaks                         | Unreleased async contexts/generators       |
| High CPU usage despite async         | Missing `async def` or blocking loops      |
| Difficulty scaling                    | No proper concurrency limits                |
| Integration issues with async libs    | Mixed sync/async dependencies              |

If multiple symptoms appear, prioritize **blocking I/O operations** and **unawaited coroutines**.

---

## **3. Common Issues & Fixes**

### **3.1. Blocking Operations in Async Context**
**Symptom:** High latency, slow responses even with async.
**Cause:** Sync functions (e.g., `requests.get()`, `time.sleep()`) block event loops.

#### **Fix: Convert sync calls to async**
```python
# ❌ Blocking call (BAD)
import requests

@app.get("/")
async def sync_blocking():
    response = requests.get("https://api.example.com")  # Blocks event loop
    return response.json()

# ✅ Async alternative (GOOD)
import httpx

@app.get("/")
async def async_call():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")  # Non-blocking
    return response.json()
```

**Key Libraries:**
- `httpx` (replaces `requests`)
- `aiohttp` (async HTTP client)
- `aiopg` (async PostgreSQL)
- `motor` (async MongoDB)

---

### **3.2. Unhandled Exceptions in Async Routes**
**Symptom:** 502 Bad Gateway, no error logs.
**Cause:** Async exceptions crash the ASGI server silently.

#### **Fix: Use `try/except` and proper error handling**
```python
# ❌ No error handling (BAD)
@app.get("/data")
async def fetch_data():
    data = await async_db.query("SELECT * FROM users")
    return data

# ✅ Proper error handling (GOOD)
from fastapi import HTTPException

@app.get("/data")
async def fetch_data():
    try:
        data = await async_db.query("SELECT * FROM users")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Logging:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def handle_exception(request, exc):
    logger.error(f"Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"}
    )
```

---

### **3.3. Database Connection Leaks**
**Symptom:** Random 503 errors, memory growth.
**Cause:** Async DB connections not closed properly.

#### **Fix: Use `async with` and connection pooling**
```python
# ❌ Manual connection (BAD)
async def fetch_user(user_id):
    conn = await asyncpg.connect("postgres://user:pass@localhost/db")
    data = await conn.fetch("SELECT * FROM users WHERE id = $1", user_id)
    return data  # Connection not closed!

# ✅ Proper connection handling (GOOD)
async def fetch_user(user_id):
    async with asyncpg.create_pool("postgres://user:pass@localhost/db") as pool:
        async with pool.acquire() as conn:
            data = await conn.fetch("SELECT * FROM users WHERE id = $1", user_id)
        return data
```

**Key Fixes:**
- Always use connection pools (`asyncpg.create_pool()`, `aiomysql.create_pool()`).
- Avoid manual `conn.close()`—use `async with`.
- Set `max_size` and `min_size` in pools to prevent leaks.

---

### **3.4. Missing `await` in Async Code**
**Symptom:** Silent failures, no error logs.
**Cause:** Forgetting `await` in async functions.

#### **Fix: Check for `await` in all coroutines**
```python
# ❌ Missing await (BAD)
async def fetch_data():
    data = some_async_function()  # No await → runs immediately

# ✅ Proper await (GOOD)
async def fetch_data():
    data = await some_async_function()  # Correct
```

**Debugging Tip:**
Run with `uvicorn --log-config logging.conf` to see unawaited coroutines in logs.

---

### **3.5. Memory Leaks from Async Generators**
**Symptom:** Slow performance, high memory usage.
**Cause:** Unclosed async generators (e.g., `async for` loops).

#### **Fix: Properly close generators**
```python
# ❌ Unclosed generator (BAD)
async def stream_data():
    async for chunk in some_async_generator():
        yield chunk  # Generator never closed

# ✅ Safe generator (GOOD)
async def stream_data():
    async with some_async_generator() as gen:
        async for chunk in gen:
            yield chunk  # Generator closed
```

**Common Culprits:**
- `aiofiles.AsyncFile` (must use `async with`).
- Custom async generators (ensure `__aexit__` closes resources).

---

### **3.6. No Concurrency Limits**
**Symptom:** System crashes under load.
**Cause:** No rate limiting or semaphore controls.

#### **Fix: Use `asyncio.Semaphore`**
```python
from fastapi import Request
from fastapi.responses import JSONResponse
import asyncio

max_concurrent_requests = 10
semaphore = asyncio.Semaphore(max_concurrent_requests)

@app.get("/heavy-task")
async def heavy_task(request: Request):
    async with semaphore:
        return await process_request(request)
```

**Alternative:** Use `httpx.Client(timeout=30.0)` with connection limits.

---

### **3.7. Mixed Sync/Async Dependencies**
**Symptom:** `TypeError: object is not coroutine`.
**Cause:** Sync dependencies passed to async routes.

#### **Fix: Use `asyncio.to_thread()` or rewrite dependencies**
```python
# ❌ Sync dependency in async (BAD)
from fastapi import Depends
import time

async def sync_dependency():
    time.sleep(1)  # Blocks event loop
    return "data"

@app.get("/")
async def root(dependency=Depends(sync_dependency)):
    return dependency

# ✅ Avoid sync in async (GOOD)
async def async_dependency():
    await asyncio.sleep(1)  # Non-blocking
    return "data"

# OR: Offload sync work
from fastapi import Depends
import asyncio

async def sync_offload(func):
    def wrapper(*args, **kwargs):
        return asyncio.to_thread(func, *args, **kwargs)
    return wrapper

@sync_offload
def blocking_func():
    time.sleep(1)
    return "data"

@app.get("/")
async def root(dependency=Depends(blocking_func)):
    return dependency
```

---

## **4. Debugging Tools & Techniques**

### **4.1. Logging & Logging Middleware**
**Key Tools:**
- `logging` module (structured logs).
- `fastapi.middleware` (custom logging middleware).

**Example:**
```python
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("uvicorn.error")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response
```

**Log Levels:**
- `DEBUG` (detailed async calls).
- `INFO` (request/response tracking).
- `ERROR` (unhandled exceptions).

---

### **4.2. Profiling Async Performance**
**Tools:**
- `asyncio` debugging (`python -m asyncio --debug`).
- `tracemalloc` (memory leaks).
- `py-spy` (sampling profiler).

**Command:**
```bash
# Check async event loop
python -m asyncio --debug

# Profile memory leaks
tracemalloc.start()
asyncio.run(app())
snapshot = tracemalloc.take_snapshot()
tracemalloc.stop()
```

---

### **4.3. ASGI Debugging (Uvicorn/Hypercorn)**
**Key Flags:**
- `--log-config` (custom logging).
- `--reload` (development).
- `--workers` (test scaling).

**Example:**
```bash
uvicorn main:app --log-config logging.conf --workers 4 --reload
```

**Check logs for:**
- Unhandled exceptions (`--log-level debug`).
- Worker crashes (`--limit-concurrency 50`).

---

### **4.4. Debugging Database Queries**
**Tools:**
- `aiomysql` / `asyncpg` logging.
- `SQLAlchemy` async debugging.

**Example (asyncpg):**
```python
import asyncpg

asyncpg.set_log_handler(
    lambda log: logging.debug(f"DBLog: {log}"),
    logging.DEBUG
)
```

---

### **4.5. Postmortem Debugging (502 Errors)**
**Steps:**
1. Check ASGI server logs (`--log-level debug`).
2. Run with `--no-access-log` to focus on errors.
3. Use `try/except` in `main()`:
   ```python
   import traceback
   from fastapi import FastAPI
   app = FastAPI()

   async def lifespan(app: FastAPI):
       try:
           yield
       except Exception as e:
           print(traceback.format_exc())

   uvicorn.run(app, lifespan=lifespan)
   ```

---

## **5. Prevention Strategies**

### **5.1. Coding Standards**
✅ **Always mark async routes with `async def`.**
✅ **Use `await` for all coroutines.**
✅ **Avoid sync code in async paths (use `asyncio.to_thread()`).**
✅ **Close async resources (`async with`).**

### **5.2. Dependency Management**
✅ **Use async DB clients (`aiomysql`, `asyncpg`).**
✅ **Pool connections (avoid manual opens/closes).**
✅ **Rate-limit heavy operations (`Semaphore`).**

### **5.3. Testing & QA**
✅ **Test async routes with `pytest-asyncio`.**
✅ **Load-test with `locust` or `k6`.**
✅ **Mock async dependencies (`unittest.mock`).**

**Example Test:**
```python
import pytest
from main import app
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_async_route():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
```

### **5.4. Deployment Best Practices**
✅ **Use ASGI servers (`uvicorn`, `hypercorn`).**
✅ **Set `--workers` based on CPU cores.**
✅ **Enable `--relog` for auto-restart on crashes.**
✅ **Monitor with `Prometheus` + `Grafana`.**

**Example Uvicorn Command:**
```bash
uvicorn main:app \
  --workers 4 \
  --host 0.0.0.0 \
  --port 8000 \
  --relog \
  --log-config logging.conf
```

### **5.5. Monitoring & Alerts**
✅ **Monitor event loop latency (`uvicorn.metrics`).**
✅ **Alert on `5XX` errors (Datadog, Sentry).**
✅ **Track slow requests (`--slow-log` in Uvicorn).**

**Uvicorn Slow Log Example:**
```bash
uvicorn main:app --slow-log 5.0
# Logs requests >5s
```

---

## **6. Conclusion**
Async frameworks like **FastAPI** and **Quart** require discipline in:
1. **Avoiding blocking operations.**
2. **Properly handling async/await.**
3. **Closing resources correctly.**
4. **Monitoring and testing.**

**Quick Fixes Summary:**
| **Issue**               | **Fix**                          |
|-------------------------|----------------------------------|
| Blocking I/O            | Use `httpx`, `aiohttp`           |
| Unhandled exceptions    | `try/except` + middleware        |
| DB leaks                | Connection pooling (`asyncpg`)    |
| Missing `await`         | Check all async functions        |
| Memory leaks            | Close generators (`async with`)   |
| No concurrency limit    | `asyncio.Semaphore`              |

**Next Steps:**
- Audit your async code for blocking calls.
- Implement proper logging and error handling.
- Load-test under production-like conditions.

By following this guide, you’ll resolve most async framework issues efficiently. Happy debugging! 🚀