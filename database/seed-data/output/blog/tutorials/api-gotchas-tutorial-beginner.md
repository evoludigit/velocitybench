```markdown
# **"API Gotchas: The Silent Killers of Your Backend (And How to Avoid Them)"**

*Why your API might be breaking silently—and how to catch those sneaky edge cases before users notice.*

Building APIs is like constructing a bridge: it looks solid until the first heavy truck drives over it. One wrong assumption, missed edge case, or poorly documented behavior can send clients (and users) crashing into unexpected errors.

As a backend developer, you’ve probably heard "APIs should be simple" or "just follow the REST conventions." But life isn’t that easy. Real-world APIs deal with:
- **Timezones vs. timestamps** (when is UTC really "now"?)
- **Empty responses vs. errors** (should `204 No Content` mean success or failure?)
- **Pagination quirks** (what happens when the page size is `0`?)
- **CORS misconfigurations** (why your frontend suddenly stops working)

These are **API gotchas**—subtle bugs that lurk in the shadows of your API design until they bite you. And unlike syntax errors, they’re sneaky. They might work fine in your local tests but fail in production when real-world traffic hits.

In this guide, we’ll cover the most common API gotchas, how they break things, and **practical solutions** to build **robust, user-friendly APIs**. Let’s dive in.

---

## **The Problem: Why APIs Fail Silently (And Why It’s Your Fault)**

APIs are the contracts between your backend and the rest of the world. But unlike a signed agreement, they’re often **implicitly documented** in your code, tests, and developer notes. When an API doesn’t behave as expected, the blame game starts:

- *"The frontend broke it!"* → (You didn’t validate input properly.)
- *"The client’s API changed!"* → (You didn’t document breaking changes.)
- *"It worked in Postman!"* → (Postman is not production traffic.)

Here’s the reality: **Most API failures aren’t due to bugs—they’re due to ignored gotchas.**

### **Real-World Examples of API Gotchas Gone Wrong**
1. **Twitter’s API Rate Limiting (2013)**
   - Twitter’s API allowed developers to make **150 requests per 15-minute window** per IP.
   - A bot that scraped tweets at the **exact limit** (150 requests) could still trigger rate limits due to **network delays**.
   - Result? Legitimate users were blocked because the API didn’t account for **real-world timing inconsistencies**.

2. **GitHub’s Deprecated API Endpoint (2018)**
   - GitHub deprecated an endpoint (`user/repos`) but kept it **half-working** for years.
   - Developers relying on it got ** intermittent 404 errors** instead of a clear deprecation warning.
   - Result? **Thousands of apps broke silently** before the change was enforced.

3. **Facebook’s Graph API Pagination Bug (2020)**
   - Facebook’s `/me/friends` endpoint sometimes returned **empty results** after pagination.
   - The issue? **Race conditions** when fetching large datasets.
   - Result? **Apps relied on false "no more data" responses**, leading to stale friend lists.

These aren’t isolated cases—they’re **textbook examples of API gotchas** that could’ve been prevented with better design.

---

## **The Solution: How to Hunt Down API Gotchas Before They Bite You**

The good news? **Most API gotchas are preventable** if you approach them systematically. The key is:

1. **Assume the worst-case scenario** (because your users will find it).
2. **Test like a hacker** (not just a developer).
3. **Document like you owe it to future you** (or your next intern).

We’ll break this into **five critical areas** where gotchas hide:

| **Gotcha Category**       | **Common Pitfalls**                          | **How to Fix It**                          |
|---------------------------|---------------------------------------------|--------------------------------------------|
| **Input Validation**      | Missing, malformed, or unexpected data      | Strict schemas, openAPI/Swagger docs      |
| **Error Handling**        | Vague errors, no retries, inconsistent codes| Standardized error formats (RFC 7807)     |
| **Pagination & Limits**   | Off-by-one errors, infinite loops           | Clear pagination metadata, rate limits    |
| **Concurrency & Race Conditions** | Timeouts, stale data                | Idempotency keys, optimistic locking      |
| **Security & Permissions** | Overly permissive endpoints, CORS misconfigs | JWT validation, proper CORS headers       |

Let’s tackle each one with **code examples** and **real-world fixes**.

---

## **1. Input Validation: "But My API Worked in Postman!"**

### **The Problem: "It’s Just a String, Right?"**
APIs are **not** like local functions—they deal with **untrusted data** from:
- Frontend forms
- Third-party integrations
- Mobile apps
- Scripts

If you don’t validate input, you’ll get:
- **SQL injection** (if you `INSERT` user input directly into a query)
- **Denial-of-service (DoS)** (if a client sends a `GET /users?limit=1000000`)
- **Log sprawl** (if a client sends `name="<script>alert('hacked')</script>"`)

### **The Solution: Strict Input Validation**
#### **Example 1: SQL Injection (Bad)**
```python
# ❌ UNSAFE - Direct string interpolation in SQL
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return result
```
**What could go wrong?**
- A user enters `1; DROP TABLE users; --` → **Database deleted!**
- A user enters `1 OR 1=1 --` → **Returns ALL users**

#### **Example 2: SQL Injection (Safe - Using Parameterized Queries)**
```python
# ✅ SAFE - Parameterized query
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    result = db.execute(query, (user_id,))  # Note the comma!
    return result
```
**Alternative (ORM Approach - Python SQLAlchemy):**
```python
from sqlalchemy import create_engine, text

def get_user(user_id):
    engine = create_engine("postgresql://user:pass@localhost/db")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})
        return result.fetchone()
```

#### **Example 3: Schema Validation (JSON API - OpenAPI)**
```yaml
# openapi.yaml (Swagger/OpenAPI spec)
paths:
  /users:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                  minLength: 1
                  maxLength: 100
                email:
                  type: string
                  format: email
              required: [name, email]
```
**Why this matters:**
- **Frontend devs** get autocompletion (if using Postman/Redoc).
- **You catch typos early** (e.g., `email: "invalid"` returns `400 Bad Request`).

#### **Example 4: Rate Limiting (Preventing DoS)**
```python
# Flask example with rate limiting
from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/api/data")
@limiter.limit("10 per minute")
def fetch_data():
    return {"data": "success"}
```
**What this prevents:**
- A script calling `/api/data` **100 times per second** → **429 Too Many Requests**.
- You can also **whitelist trusted IPs** or use **API keys**.

---

## **2. Error Handling: "500 Server Error" Isn’t Helpful**

### **The Problem: Vague Errors = User Confusion**
When your API returns:
```json
{
  "error": "Something went wrong"
}
```
Your users (or their engineers) will:
1. **Assume it’s a bug** (when it’s a missing field).
2. **Spam your support** (because they have no idea what to fix).
3. **Waste time debugging** (while your API silently fails).

### **The Solution: Standardized, Descriptive Errors**
#### **Example 1: RFC 7807 (Problem Details) Format**
```json
{
  "type": "https://api.example.com/problem/user-not-found",
  "title": "User not found",
  "status": 404,
  "detail": "A user with ID '123' was not found.",
  "instance": "/api/users/123"
}
```
**Why this is better:**
- **Machinery-friendly**: Tools like Postman/Insomnia can parse this.
- **Human-friendly**: Clear, actionable messages.

#### **Example 2: Python (FastAPI) Error Handling**
```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str

@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    if not user.email.endswith("@example.com"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email must end with '@example.com'"
        )
    return {"message": "User created", "user": user}
```
**Example Response:**
```json
{
  "detail": "Email must end with '@example.com'"
}
```

#### **Example 3: Database-Specific Errors (PostgreSQL)**
```python
# ✅ Handle specific PostgreSQL errors
try:
    query = "UPDATE accounts SET balance = balance - 100 WHERE id = %s"
    db.execute(query, (account_id,))
except psycopg2.IntegrityError as e:
    if "foreign key constraint" in str(e):
        raise HTTPException(
            status_code=400,
            detail="Insufficient funds"
        )
    else:
        raise HTTPException(status_code=500, detail="Database error")
```

**Key Takeaway:**
- **Never return `500 Internal Server Error` for client mistakes.**
- **Use specific HTTP status codes** (`400 Bad Request`, `404 Not Found`, `429 Too Many Requests`).
- **Log errors internally** (but don’t leak them to clients).

---

## **3. Pagination & Limits: "I Only Asked for 10 Items!"**

### **The Problem: Off-by-One Errors & Infinite Loops**
Pagination is **tricky** because:
- **Page size = 0** → Should it return **empty** or an error?
- **Last page** → Should it return **fewer items** than requested?
- **Missing `page`/`limit` params** → Should it default to `1/10`?

### **The Solution: Consistent Pagination Metadata**
#### **Example 1: Correct Pagination Response (GitHub Style)**
```json
{
  "data": [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
  ],
  "pagination": {
    "total_items": 100,
    "total_pages": 10,
    "current_page": 1,
    "items_per_page": 2,
    "has_next_page": true,
    "next_page": 2
  }
}
```
**Why this works:**
- Clients know **if there’s more data**.
- They can **optimize their fetches** (e.g., `has_next_page: false` → stop polling).

#### **Example 2: Python (FastAPI) Pagination**
```python
from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional

app = FastAPI()

@app.get("/users", response_model=List[dict])
async def get_users(
    page: int = Query(1, gt=0),
    limit: int = Query(10, le=100)
):
    # Validate input
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100")

    # Fetch data (pseudo-code)
    offset = (page - 1) * limit
    users = db.query("SELECT * FROM users LIMIT ? OFFSET ?", (limit, offset))
    return users
```

#### **Example 3: Handle Edge Cases**
```python
# ✅ Handle zero limit
if limit == 0:
    return {"data": [], "pagination": {"total_items": 0}}

# ✅ Handle negative page
if page < 1:
    raise HTTPException(status_code=400, detail="Page must be >= 1")
```

**Common Mistakes to Avoid:**
❌ **No `page`/`limit` defaults** → Return `400 Bad Request`.
❌ **Off-by-one errors** → `OFFSET 0 LIMIT 10` is correct; `OFFSET 1 LIMIT 10` skips the first item.
❌ **No `total_items`** → Clients can’t detect empty results vs. "no more data."

---

## **4. Concurrency & Race Conditions: "It Works in My Tests!"**

### **The Problem: Time is Your Worst Enemy**
APIs are **not** single-threaded. Race conditions happen when:
- Two requests **simultaneously** update the same resource.
- A request **times out** mid-operation.
- A background job **interferes** with a real-time query.

### **The Solution: Idempotency & Retry Safety**
#### **Example 1: Idempotent Requests (Prevent Duplicate Charges)**
```python
# ✅ Use an idempotency key (Stripe-style)
@app.post("/payments")
def create_payment(
    amount: float,
    idempotency_key: str,
    current_user: User = Depends(get_current_user)
):
    if not session.get("processed_" + idempotency_key):
        session["processed_" + idempotency_key] = True  # Mark as processed
        payment = process_payment(amount, current_user)
        return payment
    return {"status": "already processed"}
```

#### **Example 2: Optimistic Locking (Prevent Lost Updates)**
```python
# ✅ Version-based locking (PostgreSQL)
@app.patch("/users/{user_id}")
def update_user(user_id: int, data: dict):
    query = """
        UPDATE users
        SET name = %s
        WHERE id = %s AND version = %s
        RETURNING version
    """
    new_version = data.pop("version", None)
    if not new_version:
        # Fetch current version first
        current_user = db.get_user(user_id)
        new_version = current_user.version + 1

    result = db.execute(
        query,
        (data["name"], user_id, current_user.version)
    )

    if not result:
        raise HTTPException(status_code=409, detail="Conflict: User was updated by another request")
    return {"success": True}
```

#### **Example 3: Retryable vs. Non-Retryable Errors**
| **Error Type**       | **Should Client Retry?** | **HTTP Status** | **Example** |
|----------------------|--------------------------|-----------------|-------------|
| Temporary DB failure | ✅ Yes                   | 503 Service Unavailable | `db.connect_error` |
| Invalid input        | ❌ No                    | 400 Bad Request | Missing required field |
| Rate limit exceeded  | ✅ Yes (with delay)      | 429 Too Many Requests | `Retry-After: 60` |

**Python (Using `tenacity` for Retries):**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_external_api():
    try:
        response = requests.get("https://api.example.com/data")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 503:
            retry  # Retry on temporary failures
        raise  # Don’t retry on permanent errors
```

---

## **5. Security & Permissions: "But It’s Just a GET Request!"**

### **The Problem: "If It’s Public, It’s Safe"**
Even **GET requests** can be exploited if:
- **CORS is misconfigured** (frontend leaks data).
- **JWT is not verified** (anyone can impersonate).
- **Permissions are too broad** (user `A` can delete `B`'s data).

### **The Solution: Defense in Depth**
#### **Example 1: Proper CORS Headers (Flask)**
```python
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(
    app,
    resources={
        "/api/*": {
            "origins": ["https://your-frontend.com", "https://trusted-api.com"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    }
)

@app.route("/api/data")
def get_data():
    return jsonify({"data": "protected"})
```
**Why this matters:**
- Prevents **XSS attacks** (malicious scripts stealing data).
- Restricts **where** your API can be called from.

#### **Example 2: JWT Validation (FastAPI)**
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

app = FastAPI()
SECRET_KEY = "your-secret-key"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get