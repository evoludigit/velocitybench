# **Debugging API Setup: A Troubleshooting Guide**

## **Table of Contents**
1. **Introduction**
2. **Symptom Checklist**
3. **Common API Setup Issues & Fixes**
   - 3.1. **Authentication/Authorization Errors**
   - 3.2. **CORS (Cross-Origin Resource Sharing) Issues**
   - 3.3. **Dependency & Version Conflicts**
   - 3.4. **Database Connection Failures**
   - 3.5. **Rate Limiting & Throttling Problems**
   - 3.6. **Misconfigured Environment Variables**
   - 3.7. **API Response Timeouts**
   - 3.8. **Schema/Validation Errors**
4. **Debugging Tools & Techniques**
   - 4.1. **Logging & Monitoring**
   - 4.2. **API Testing Tools**
   - 4.3. **Network Inspection**
   - 4.4. **Database Debugging**
   - 4.5. **Profiler & Performance Analysis**
5. **Prevention Strategies**
6. **Conclusion**

---

## **1. Introduction**
APIs are the backbone of modern software architecture, enabling communication between microservices, clients, and third-party integrations. A properly configured API ensures seamless data exchange, security, and performance. However, misconfigurations, dependency issues, or environmental problems can lead to failures.

This guide provides a **practical, step-by-step approach** to diagnosing and resolving common API setup issues quickly.

---

## **2. Symptom Checklist**
Before diving into fixes, identify the root cause using this checklist:

| **Symptom**                     | **Possible Cause**                          | **Action** |
|---------------------------------|--------------------------------------------|------------|
| **401/403 Errors**              | Missing/invalid API keys, JWT, or OAuth tokens | Check auth headers, refresh tokens, and role-based permissions |
| **CORS Errors (403/405)**       | Incorrect `Access-Control-Allow-Origin` headers | Verify CORS middleware and allow requests from correct domains |
| **Dependency Errors (ModuleNotFound, Version Mismatch)** | Broken `requirements.txt`, `package.json`, or `Dockerfile` | Reinstall dependencies, update versions, or check `pip`/`npm` issues |
| **Database Connection Failures** | Wrong credentials, incorrect DB name/port, schema issues | Verify connection strings, network access, and DB health |
| **Rate Limited (429 Errors)**  | Missing API key, incorrect rate limits, or sudden traffic spikes | Check rate-limiting middleware (e.g., `flask-limiter`), adjust thresholds |
| **Environment Variable Errors** | Missing `.env` files, incorrect keys, or secrets leakage | Ensure variables are loaded, encrypted, and not hardcoded |
| **Timeout Errors (504, 502)**  | Slow DB queries, unoptimized code, or network latency | Use timeouts, optimize queries, and check network proxies |
| **Schema/Validation Failures**  | Incorrect JSON payloads, missing required fields | Validate requests with Pydantic (Python) or Joi (JavaScript) |
| **API Returns Empty Responses** | Caching issues, incorrect endpoints, or middleware blocking responses | Disable cache, verify endpoint logic, and check middleware |

---

## **3. Common API Setup Issues & Fixes**

### **3.1. Authentication/Authorization Errors (401, 403)**
**Symptoms:**
- `{"error": "Unauthorized"}` (401)
- `{"error": "Forbidden"}` (403)
- API returns empty or partially restricted data

**Possible Causes:**
- Missing API keys in headers (`X-API-Key`, `Authorization: Bearer <token>`)
- Invalid JWT/OAuth tokens
- Incorrect role-based access control (RBAC) rules

**Debugging Steps:**
1. **Check Request Headers**
   Ensure the API key or token is sent in the correct format:
   ```http
   GET /protected-endpoint HTTP/1.1
   Host: api.example.com
   Authorization: Bearer abc123xyz
   X-API-Key: secret-key-123
   ```

2. **Verify Token Validity**
   If using JWT:
   ```python
   from jwt import decode, ExpiredSignatureError
   try:
       decoded = decode(token, "SECRET_KEY", algorithms=["HS256"])
       print("Token is valid:", decoded)
   except ExpiredSignatureError:
       print("Token expired!")
   ```

3. **Check Middleware (Flask/FastAPI Example)**
   ```python
   # Flask
   from flask_httpauth import HTTPBasicAuth
   auth = HTTPBasicAuth()

   @auth.verify_password
   def verify_password(username, password):
       if username == "admin" and password == "securepass":
           return username
       return None

   @auth.error_handler
   def unauthorized():
       return {"error": "Unauthorized"}, 401
   ```

   ```python
   # FastAPI (JWT)
   from fastapi import Depends, HTTPException, status
   from fastapi.security import OAuth2PasswordBearer

   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

   async def get_current_user(token: str = Depends(oauth2_scheme)):
       try:
           payload = decode(token, "SECRET_KEY", algorithms=["HS256"])
           return payload["sub"]
       except Exception:
           raise HTTPException(status_code=401, detail="Invalid token")
   ```

### **3.2. CORS Errors (403, 405)**
**Symptoms:**
- Browser console errors: `No 'Access-Control-Allow-Origin' header`
- `405 Method Not Allowed` (if preflight OPTIONS fails)

**Possible Causes:**
- Missing CORS middleware
- Incorrect `Access-Control-Allow-Origin` header
- Missing preflight (`OPTIONS`) handling

**Fixes:**
**Flask Example:**
```python
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

@app.route("/api/data")
def get_data():
    return jsonify({"data": "test"})
```

**FastAPI Example:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/data")
def read_data():
    return {"message": "Hello, CORS works!"}
```

### **3.3. Dependency & Version Conflicts**
**Symptoms:**
- `ModuleNotFoundError` (Python)
- `Cannot find module 'some-package'` (Node.js)
- `Docker build fails` due to missing dependencies

**Fixes:**
1. **Check `requirements.txt` / `package.json`**
   ```bash
   pip install -r requirements.txt  # Python
   npm install                     # Node.js
   ```

2. **Resolve Version Conflicts (Python)**
   ```bash
   pip install "package==1.0.0"  # Pin exact version
   ```

3. **Use `docker-compose` or `Dockerfile` Corrections**
   ```dockerfile
   # Example Dockerfile
   FROM python:3.9
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   ```

### **3.4. Database Connection Failures**
**Symptoms:**
- `Connection refused` (PostgreSQL/MySQL)
- `TimeoutError` (MongoDB)
- `Invalid credentials` errors

**Debugging Steps:**
1. **Verify Connection String**
   ```python
   # Wrong: Missing host/port
   db = MongoClient()  # ❌ Fails

   # Correct: With credentials & host
   db = MongoClient("mongodb://user:pass@localhost:27017/dbname?authSource=admin")
   ```

2. **Check DB Health**
   - Ping the DB manually:
     ```bash
     mysql -h localhost -u root -p
     ```
   - Test MongoDB connection:
     ```javascript
     mongo --host localhost --port 27017 --username root --password pass
     ```

3. **Enable Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   db = MongoClient("mongodb://localhost:27017", connect=False)
   db.admin.command("ping")  # Test connection
   ```

### **3.5. Rate Limiting & Throttling**
**Symptoms:**
- `429 Too Many Requests`
- API slows down under load

**Fixes:**
1. **Configure Rate Limiting (Flask-Limiter Example)**
   ```python
   from flask_limiter import Limiter
   from flask_limiter.util import get_remote_address

   limiter = Limiter(
       app=app,
       key_func=get_remote_address,
       default_limits=["200 per day", "50 per hour"]
   )

   @app.route("/api/data")
   @limiter.limit("10 per minute")
   def get_data():
       return jsonify({"data": "limited"})
   ```

2. **Use Redis for Distributed Rate Limiting**
   ```python
   from flask_limiter.storage import RedisStorage
   redis_client = RedisStorage(host="redis", port=6379, db=0)
   limiter = Limiter(storage=redis_client)
   ```

### **3.6. Misconfigured Environment Variables**
**Symptoms:**
- `OSError: [Errno 2] No such file or directory` (missing `.env`)
- Hardcoded secrets in code
- Variables not loading in Docker

**Fixes:**
1. **Load `.env` Correctly (Python Example)**
   ```python
   from dotenv import load_dotenv
   import os

   load_dotenv()  # Load from .env file
   DB_URL = os.getenv("DATABASE_URL", "fallback_url")
   ```

2. **Docker `.env` Handling**
   ```env
   # .env file
   DB_HOST=localhost
   DB_PORT=5432
   ```

   ```dockerfile
   # Dockerfile
   ENV DB_HOST=${DB_HOST}
   ENV DB_PORT=${DB_PORT}
   ```

### **3.7. API Response Timeouts**
**Symptoms:**
- `504 Gateway Timeout` (FastAPI/Flask)
- Slow DB queries (>5s)
- Request hangs indefinitely

**Fixes:**
1. **Set Timeout in Flask/FastAPI**
   ```python
   # Flask
   app.config['TIMEOUT'] = 5  # Seconds

   # FastAPI (with Uvicorn)
   uvicorn.run(app, timeout_keep_alive=30)
   ```

2. **Optimize Slow Queries (PostgreSQL Example)**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM users WHERE id = $1;  -- Check execution plan
   ```

   ```python
   # Use async DB calls (Python)
   from asyncpg import create_pool

   pool = await create_pool("postgresql://user:pass@localhost/db")
   async with pool.acquire() as conn:
       result = await conn.fetch("SELECT * FROM users WHERE id = $1", 1)
   ```

### **3.8. Schema/Validation Errors**
**Symptoms:**
- `422 Unprocessable Entity` (FastAPI)
- JSON schema mismatch
- Missing required fields

**Fixes (FastAPI/Pydantic Example)**
```python
from pydantic import BaseModel, ValidationError
from fastapi import FastAPI, HTTPException

app = FastAPI()

class UserCreate(BaseModel):
    username: str
    email: str

@app.post("/users")
async def create_user(user: UserCreate):
    try:
        # Pydantic validates schema
        return {"message": f"User {user.username} created!"}
    except ValidationError as e:
        raise HTTPException(422, str(e))
```

---

## **4. Debugging Tools & Techniques**

### **4.1. Logging & Monitoring**
- **Python:** `logging`, `structlog`, `Sentry`
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  logger = logging.getLogger(__name__)
  logger.debug("Debugging request: %s", request.json)
  ```

- **FastAPI:** Built-in logging + `uvicorn` logs
  ```bash
  uvicorn main:app --log-config log_config.json
  ```

- **Monitoring:** Prometheus + Grafana, Datadog, New Relic

### **4.2. API Testing Tools**
| Tool          | Purpose                          | Example Usage |
|---------------|----------------------------------|----------------|
| **Postman**   | Manual API testing               | Send HTTP requests with headers |
| **Swagger UI**| Interactive API docs             | `/docs` (FastAPI) |
| **curl**      | Command-line API testing         | `curl -X POST -H "Content-Type: application/json" -d '{"key":"val"}' http://api.example.com` |
| **pytest**    | Automated API tests              | `pytest test_api.py` |

### **4.3. Network Inspection**
- **Inspect Requests (Browser DevTools)**
  - Check headers, payloads, and responses in **Network tab**.
- **Wireshark / tcpdump**
  ```bash
  sudo tcpdump -i any port 8000 -A  # Capture API traffic
  ```

### **4.4. Database Debugging**
- **Slow Query Logs (PostgreSQL)**
  ```sql
  SELECT query, rows, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
  ```
- **MongoDB Profiler**
  ```javascript
  db.setProfilingLevel(1, { slowms: 100 })  // Log slow queries (>100ms)
  ```

### **4.5. Profiler & Performance Analysis**
- **Python Profilers:** `cProfile`, `Py-Spy`
  ```bash
  python -m cProfile -s time main.py
  ```
- **FastAPI / Uvicorn Metrics**
  ```python
  from fastapi import FastAPI
  app = FastAPI()
  @app.get("/metrics")
  async def metrics():
      return {"status": "ok"}  # Integrate with Prometheus
  ```

---

## **5. Prevention Strategies**
| Strategy | Implementation |
|----------|----------------|
| **Use Dependency Management Tools** | `pip-tools`, `poetry`, `npm ci` |
| **Environment Separation** | `.env`, Docker secrets, Kubernetes ConfigMaps |
| **Automated Testing** | `pytest`, `supertest`, `pytest-asyncio` |
| **Rate Limiting by Default** | Configure limits early in development |
| **Input Validation** | Pydantic (Python), Joi (JavaScript) |
| **Logging & Monitoring** | Centralized logs (ELK, Loki) |
| **Infrastructure as Code (IaC)** | Terraform, Ansible for API servers |

---

## **6. Conclusion**
API setup issues can be frustrating, but a **structured debugging approach** helps resolve them efficiently. Follow this guide to:
1. **Identify symptoms** quickly.
2. **Apply fixes** with code examples.
3. **Use debugging tools** for deep inspection.
4. **Prevent recurring issues** with best practices.

By maintaining clean environments, proper logging, and automated testing, you can **minimize downtime** and ensure **scalable, reliable APIs**.

---
**Next Steps:**
- Run a **load test** (`locust`, `k6`) to identify bottlenecks.
- Set up **alerts** for API failures (Slack, PagerDuty).
- Document **API contracts** (OpenAPI/Swagger).

Would you like a deeper dive into any specific section?