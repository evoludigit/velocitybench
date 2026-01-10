# **[Pattern] Async Web Frameworks (FastAPI/Quart) Reference Guide**

---

## **Overview**
This guide provides a structured reference for implementing and optimizing **asynchronous web frameworks** using **FastAPI** and **Quart**. Async frameworks enable non-blocking I/O operations, improving scalability and performance for high-concurrency applications. This pattern covers:
- Core concepts (async/await, event loops, routing)
- Best practices for dependency injection, error handling, and middleware
- Performance considerations (concurrency, database pooling)
- Integration with external services (APIs, gRPC, WebSockets)

Key frameworks:
- **FastAPI**: High-performance Python framework (built on Starlette & Pydantic).
- **Quart**: Async Flask-compatible framework (supports WebSockets, background tasks).

---

## **Schema Reference**

### **1. Core Components**
| Component          | Description                                                                 | Key Features                                                                 |
|--------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Async Request Handler** | Endpoint decorated with `@app.get`, `@app.post`, etc.                     | Uses `async def`; returns `Response` or `JSONResponse`.                     |
| **Dependency Injection** | Injection via `Depends()`, `provides()` for reusable logic.               | Avoids duplicated code; supports dependency scopes (`singleton`, `request`).  |
| **Middlewares**    | Async middleware for request/response processing.                          | Example: Logging, authentication, rate-limiting.                           |
| **Background Tasks** | Offload CPU-intensive tasks (e.g., `asyncio.create_task`).               | Runs in background; doesn’t block the event loop.                           |
| **WebSockets**     | Full-duplex communication via `websockets` library.                       | Used in FastAPI (via `WebSocket`) or Quart (native support).               |
| **Background Jobs** | Scheduled tasks (Celery, Airflow) or Quart’s `@quart.background`.         | Decouples long-running tasks from the main loop.                           |

---

### **2. Key Configuration Options**
| Setting               | Description                                                                 | Example Values/Implementation                          |
|-----------------------|-----------------------------------------------------------------------------|-------------------------------------------------------|
| **Event Loop**        | Python’s async I/O scheduler.                                               | Default: `asyncio.get_event_loop()`.                  |
| **Database Pooling**  | Async database connectors (e.g., `asyncpg`, `SQLAlchemy 2.0`).             | `DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"` |
| **Timeout Handling**  | Configure request timeouts (e.g., `timeout` in `@app.post`).               | `timeout=30` (default: None).                          |
| **Rate Limits**       | Quart’s `@quart.limit()` decorator or FastAPI’s `OPENAPI_PREFIX`.          | `limit="500 per day"`.                                |
| **Logging**           | Structured logging via `logging.config.dictConfig`.                       | `{"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}` |

---

### **3. Performance Metrics**
| Metric               | Recommended Value                        | Tools to Monitor                          |
|----------------------|------------------------------------------|-------------------------------------------|
| **Concurrency**      | Max workers = `(CPU cores + 1) * 2`.    | `uvicorn --workers 4` (FastAPI default).  |
| **DB Connection Pool** | 5–10 connections per worker.            | `SQLAlchemy engine = create_async_engine(url, pool_size=10)`. |
| **Event Loop Latency**| < 10ms per request (average).           | Use `tracemalloc` or `py-async-timeout`.   |

---

## **Implementation Details**

### **1. Routing & Endpoints**
#### **FastAPI Example**
```python
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated

app = FastAPI()

async def get_data(id: int):
    return {"id": id, "data": "value"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# Dependency Injection
User = Annotated[str, Depends(get_data)]
@app.get("/protected")
async def protected_route(user: User):
    return {"user": user}
```

#### **Quart Example**
```python
from quart import Quart, jsonify

app = Quart(__name__)

@app.get("/")
async def home():
    return jsonify({"message": "Hello, Quart!"})

@app.post("/post")
async def post_data(data: dict):
    return jsonify({"received": data})
```

---

### **2. Dependency Injection**
#### **FastAPI (Starlette-Style)**
```python
from fastapi import Depends, HTTPException

async def auth_user(token: str):
    if token != "secret":
        raise HTTPException(status_code=403, detail="Invalid token")
    return {"auth": True}

@app.get("/private")
async def private_route(user: dict = Depends(auth_user)):
    return {"data": "private", "auth": user}
```

#### **Quart (Flask-Style)**
```python
from quart import Quart, current_app

app = Quart(__name__)

@app.before_request
async def auth_check():
    if current_app.config["SECRET_KEY"] != request.headers.get("X-Secret"):
        raise HTTPException(403, "Unauthorized")
```

---

### **3. Middleware**
#### **FastAPI (Starlette Middleware)**
```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
)
```

#### **Quart (Custom Middleware)**
```python
from quart import Quart, request

app = Quart(__name__)

@app.before_request
async def log_request():
    print(f"Request: {request.method} {request.path}")
```

---

### **4. Background Tasks**
#### **FastAPI (Offload to Thread/Process)**
```python
import asyncio
from fastapi import BackgroundTasks

async def process_data(data: list):
    # Simulate long task
    await asyncio.sleep(2)
    print(f"Processed: {data}")

@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile):
    background_tasks.add_task(process_data, file.filename)
    return {"message": "File uploaded"}
```

#### **Quart (Background Tasks)**
```python
from quart import Quart, current_app

@app.before_serving
async def setup_background():
    current_app.background = asyncio.create_task(long_running_task())

async def long_running_task():
    while True:
        print("Background task running...")
        await asyncio.sleep(5)
```

---

### **5. WebSockets**
#### **FastAPI (WebSocket Endpoint)**
```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

#### **Quart (Native WebSocket Support)**
```python
from quart import Quart, websocket

app = Quart(__name__)

@app.route("/ws")
async def ws():
    ws = await websocket()
    while True:
        msg = await ws.receive()
        await ws.send(f"Server: {msg}")
```

---

### **6. Database Integration (Async)**
#### **FastAPI + SQLAlchemy 2.0**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine("postgresql+asyncpg://user:pass@host/db")
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False)

@app.get("/users")
async def get_users():
    async with AsyncSessionLocal() as session:
        users = await session.execute("SELECT * FROM users")
        return users.fetchall()
```

#### **Quart + Asyncpg**
```python
from quart import Quart
import asyncpg

app = Quart(__name__)

@app.on_startup
async def setup_db():
    global pool
    pool = await asyncpg.create_pool("postgresql://user:pass@host/db")

@app.get("/db")
async def query_db():
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT * FROM users")
        return users
```

---

## **Query Examples**

### **1. FastAPI GET Request**
```bash
curl http://localhost:8000/items/1
# Output: {"item_id": 1}
```

### **2. Quart POST Request**
```bash
curl -X POST http://localhost:5000/post \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
# Output: {"received": {"key": "value"}}
```

### **3. WebSocket Communication (FastAPI)**
```bash
# Client-side (JavaScript):
const ws = new WebSocket("ws://localhost:8000/ws");
ws.send("Hello");
ws.onmessage = (e) => console.log(e.data); // "Echo: Hello"
```

### **4. Background Task Trigger**
```python
# FastAPI endpoint triggers background task
curl -X POST http://localhost:8000/upload \
  -F "file=@test.txt"
# Background task logs: "Processed: test.txt"
```

---

## **Best Practices**

1. **Dependency Injection**:
   - Use `Depends()` for reusable logic (e.g., auth, DB sessions).
   - Scope dependencies correctly (`request`, `session`, `singleton`).

2. **Error Handling**:
   - Catch async exceptions with `try/except` in endpoints.
   - Use `HTTPException` for API responses.

3. **Database**:
   - Use connection pooling (`SQLAlchemy`, `asyncpg`).
   - Avoid blocking the event loop with synchronous DB calls.

4. **Middleware**:
   - Order matters: Place auth middleware before rate-limiting.

5. **WebSockets**:
   - Validate messages before processing.
   - Close connections gracefully (`await ws.close()`).

6. **Performance**:
   - Monitor event loop latency with `asyncio.get_event_loop().call_soon`.
   - Limit concurrent workers (`uvicorn --workers 4`).

---

## **Related Patterns**

| Pattern                          | Description                                                                 | Integration Example                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **API Gateway**                  | Route requests to microservices.                                           | FastAPI acts as a gateway to Quart-backed services.                                   |
| **CQRS**                         | Separate read/write models for databases.                                  | Use Quart for async query handlers; FastAPI for write endpoints.                   |
| **Event-Driven Architecture**    | Decouple components via message queues (RabbitMQ, Kafka).                  | FastAPI emits events; Quart consumes via async consumers.                            |
| **GraphQL**                      | Query complex data structures.                                              | FastAPI + `strawberry` (GraphQL server).                                            |
| **Load Testing**                 | Simulate high traffic to validate scalability.                             | Use `locust` or `k6` with async endpoints.                                          |
| **Security**                     | OAuth2, JWT, rate-limiting.                                               | FastAPI `OAuth2PasswordBearer`; Quart `@quart.limit()`.                           |
| **Monitoring**                   | Track performance metrics (latency, errors).                              | Quart logs + Prometheus metrics via `quart-prometheus`.                            |

---

## **Troubleshooting**

| Issue                          | Cause                                    | Solution                                                                          |
|--------------------------------|------------------------------------------|-----------------------------------------------------------------------------------|
| **Event Loop Deadlock**        | Blocking calls (e.g., sync DB queries).   | Use async DB drivers (`asyncpg`, `SQLAlchemy 2.0`).                                |
| **Connection Pool Exhausted**  | Too many open DB connections.            | Increase `pool_size` in `create_async_engine`.                                   |
| **WebSocket Drops**           | No heartbeat/ping-pong.                 | Add `await ws.ping()` in WebSocket loop.                                          |
| **Slow Requests**              | CPU-bound tasks.                         | Offload to background tasks or workers (Celery).                                  |
| **Dependency Injection Errors**| Scoped dependencies leak.                | Use `scoped_session` or `request` scope for Quart/FastAPI dependencies.           |