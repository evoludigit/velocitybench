```markdown
---
title: "The Availability Verification Pattern: Ensuring Your APIs Are Always "Up" When Your Users Need Them"
date: 2023-11-15
author: "Alex Carter"
description: "Learn how to implement the Availability Verification pattern to proactively monitor and validate API availability, reducing downtime and improving resilience in your applications."
tags: ["database", "api design", "backend engineering", "availability", "resilience", "choreography"]
---

# The Availability Verification Pattern: Ensuring Your APIs Are Always "Up" When Your Users Need Them

## Introduction

Imagine this scenario: You’ve just deployed your shiny new e-commerce API, and traffic spikes suddenly as a viral product launch kicks off. Suddenly, users start hitting "Out of Service" errors, and your support inbox floods with complaints. What you *thought* was a robust system now feels fragile.

But here’s the thing: **APIs don’t fail randomly**. They fail because of unhandled edge cases, unmonitored dependencies, or assumptions that don’t hold under pressure. The **Availability Verification Pattern** is a proactive way to catch these issues *before* they affect your users—by continuously validating the health and readiness of your API endpoints, their dependencies, and their data sources.

In this tutorial, we’ll explore how to implement this pattern in real-world scenarios, covering everything from database checks to API-to-API health verification. By the end, you’ll have practical code examples and patterns to build APIs that dynamically adapt to changing conditions—reducing downtime, improving reliability, and keeping your users happy.

---

## The Problem: When APIs Suddenly Go "Down" and No One Noticed in Time

Most backend developers focus on writing clean, scalable code—handling CRUD operations, optimizing queries, and ensuring low latency. But **availability** is often an afterthought. When something *does* go wrong, the fallout can be costly:

1. **Critical Data Loss**: A missed transaction in a busy database can lead to financial losses or corrupted data.
2. **User Frustration**: Timeouts or errors during peak loads turn happy customers into angry ones.
3. **Reputation Damage**: A single outage can overshadow all the positive experiences before it.
4. **Uncovered Dependencies**: APIs that rely on external services (payment gateways, third-party APIs, or microservices) may silently fail without anyone realizing it until the user does.

### Real-World Example: The "It Worked in My Testing Environment" Pitfall
Let’s say you’re building a flight booking API that integrates with an airline’s legacy database. During initial testing, everything runs fine—until you deploy to production with real-world traffic.

- **Nothing is monitored**: The API starts processing requests, but if the airline’s database suddenly has a connection timeout, your API silently returns 500 errors.
- **No fallbacks are in place**: If the database is down, your API can’t tell users, *"Sorry, we can’t fetch availability for flights to NYC today."*

The consequence? **No one knows the API is broken until it’s too late.**

---

## The Solution: Availability Verification as a Proactive Layer

The **Availability Verification Pattern** introduces a **pre-check layer** that validates critical components *before* your API processes user requests. This isn’t just about monitoring—it’s about **actively ensuring** that all dependencies are healthy and ready to handle data.

### Core Principles of the Pattern
1. **Health Checks Before Processing**: Verify that databases, external APIs, and network services are available *before* accepting user requests.
2. **Graceful Degradation**: If a dependency is degraded (e.g., slow but not failed), the API can switch to a fallback or queue the request.
3. **Dynamic Adaptation**: Adjust behavior based on current system health (e.g., disable non-critical features during high load).
4. **Self-Healing**: Automatically retry or reconnect to failed dependencies with exponential backoff.

### When to Use This Pattern
✅ **Critical, high-availability APIs** (e.g., banking, flight bookings, e-commerce)
✅ **Microservices communicating with each other**
✅ **APIs relying on external databases or third-party services**
✅ **Systems with tight SLAs (Service Level Agreements)**

❌ **Not a silver bullet**—Always pair with proper monitoring (Prometheus, Datadog) and alerting.

---

## Components/Solutions: Building the Availability Verification Layer

To implement this pattern, we’ll break it down into **key components**:

1. **Health Check Endpoints** – Lightweight endpoints that query core dependencies.
2. **Dependency Validation Middleware** – Pre-process requests and validate all dependencies.
3. **Fallback Handlers** – Graceful responses when dependencies fail.
4. **Dynamic Retry Logic** – For transient failures (e.g., network timeouts).
5. **Health-Based Routing** – Redirecting traffic to healthy endpoints if multiple are available.

---

## Implementation Guide: Step-by-Step Code Examples

### Section 1: Building a Basic Health Check Endpoint (Node.js + Express)
Let’s start with a simple `/health` endpoint that checks database availability.

#### Example: Health Check Endpoint
```javascript
const express = require('express');
const { Pool } = require('pg'); // PostgreSQL example
const app = express();

// Database connection pool
const pool = new Pool({
  user: 'your_db_user',
  host: 'your_db_host',
  database: 'your_db_name',
  password: 'your_db_password',
  port: 5432,
});

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    // Quickly check DB connectivity (no query, just a ping)
    const client = await pool.connect();
    await client.query('SELECT 1');
    client.release();

    res.status(200).json({
      status: 'UP',
      timestamp: new Date().toISOString(),
      dependencies: {
        database: {
          status: 'UP',
          version: 'PostgreSQL 15',
        },
      },
    });
  } catch (error) {
    // Log the error for debugging
    console.error('Health check failed:', error);

    res.status(503).json({
      status: 'DOWN',
      error: 'Database connectivity issue',
    });
  }
});

app.listen(3000, () => {
  console.log('Health check server running on port 3000');
});
```

#### Key Takeaways:
- The `/health` endpoint acts as a "vital signs check" for your API.
- We avoid heavy queries—just a simple `SELECT 1` to test connectivity.
- Returns HTTP `200` (OK) or `503` (Service Unavailable) to indicate status.

---

### Section 2: Adding Dependency Validation Middleware (FastAPI + Python)
Now, let’s add a middleware layer that validates dependencies *before processing user requests*.

#### Example: FastAPI Dependency Validation
```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
from typing import Dict, Any
import time

app = FastAPI()

# Database connection config
DB_CONFIG = {
    "host": "your_db_host",
    "database": "your_db_name",
    "user": "your_db_user",
    "password": "your_db_password",
}

def validate_dependencies() -> Dict[str, Dict[str, Any]]:
    """Check all critical dependencies."""
    dependencies = {}

    # Check database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        dependencies["database"] = {"status": "UP"}
    except Exception as e:
        dependencies["database"] = {"status": "DOWN", "error": str(e)}

    # Check external API (example: payment gateway)
    dependencies["payment_gateway"] = {
        "status": "UP" if "payment_gateway_is_up" else "DOWN",
    }

    return dependencies

@app.middleware("http")
async def check_health(request: Request, call_next):
    dependencies = validate_dependencies()

    # If any dependency is down, return early
    for name, status in dependencies.items():
        if status["status"] == "DOWN":
            return JSONResponse(
                status_code=503,
                content={
                    "error": f"Dependency {name} is unavailable",
                    "details": status,
                },
            )

    # If all dependencies are up, proceed with request
    response = await call_next(request)
    return response

@app.get("/flights")
async def get_flights():
    try:
        # Simulate fetching from DB
        flights = [
            {"id": 1, "route": "NYC-LAX", "price": 299.99},
            {"id": 2, "route": "LAX-NYC", "price": 289.99},
        ]
        return {"data": flights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Key Takeaways:
- The middleware checks dependencies *before* processing the request.
- If any dependency fails, it immediately returns `503` (Service Unavailable).
- We separate validation logic into a reusable function (`validate_dependencies`).
- Works with any HTTP framework—adjust for Django, Flask, or Spring Boot.

---

### Section 3: Dynamic Retry Logic (With Exponential Backoff)
What if a dependency fails temporarily (e.g., a network blip)? We can implement retries with exponential backoff.

#### Example: Retry with Backoff (Python)
```python
import time
import random
from typing import Callable, Any

def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> Any:
    """Retry a function with exponential backoff."""
    last_error = None

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt == max_retries - 1:  # Last attempt
                raise
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(delay)

    return None

# Example usage in FastAPI
@app.get("/flights-with-retry")
async def get_flights_with_retry():
    def query_database():
        # Simulate a transient failure
        if random.random() > 0.7:  # 30% chance of failure
            raise Exception("Database timeout")

        # Simulate successful query
        return [{"id": 1, "route": "NYC-LAX"}]

    try:
        return retry_with_backoff(query_database)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

#### Example: Retrying in Node.js
```javascript
const retry = require('async-retry');

const fetchFlights = async () => {
  // Simulate a database query
  const db = require('./db-config');
  const result = await db.query('SELECT * FROM flights');
  return result;
};

const safeFetchFlights = async () => {
  return retry(
    async () => {
      try {
        const flights = await fetchFlights();
        return flights;
      } catch (err) {
        if (err.message.includes("ETIMEDOUT")) {
          throw err; // Retry network issues
        }
        throw new Error("Critical failure"); // Don't retry
      }
    },
    {
      retries: 3,
      onRetry: (err) => {
        console.log(`Retrying in ${Math.random() * 1000}ms...`, err);
      },
    }
  );
};

module.exports = { safeFetchFlights };
```

#### Key Takeaways:
- **Exponential backoff** reduces load on failing services.
- **Jitter** (random delay variation) avoids thundering herd problems.
- Only retry transient failures (e.g., timeouts) but fail fast on critical errors.

---

### Section 4:Graceful Degradation (Fallbacks)
If a dependency is slow or unavailable, the API can either:
1. **Fail fast** (return `503`), or
2. **Gracefully degrade** (fall back to cached data or minimal functionality).

#### Example: Fallback Implementation (Python)
```python
from fastapi import Request
from pydantic import BaseModel

class FlightCache(BaseModel):
    data: list[dict]

# Cache for degraded state
CACHE = FlightCache(
    data=[
        {"id": 1, "route": "NYC-LAX", "price": 299.99, "status": "CACHED"},
        {"id": 2, "route": "LAX-NYC", "price": 289.99, "status": "CACHED"},
    ]
)

@app.get("/flights")
async def get_flights(request: Request):
    try:
        # Try real-time fetch
        flights = await fetch_flights_from_db()
        return {"data": flights}
    except Exception as e:
        if "database" in str(e).lower():
            # Fallback to cache
            return {
                "warning": "Using cached data due to database issues",
                "data": CACHE.data,
            }
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Common Mistakes to Avoid

1. **Assuming "It Works in Production"**
   - **Mistake**: Deploying without testing failure modes.
   - **Fix**: Use chaos engineering (e.g., kill random containers) to test resilience.

2. **Over-Reliance on 3rd-Party Monitoring**
   - **Mistake**: Waiting for tools like Datadog to alert you when dependencies fail.
   - **Fix**: Implement pro-active checks *before* user requests hit your API.

3. **Ignoring Transient Failures**
   - **Mistake**: Not handling retries for network timeouts.
   - **Fix**: Use graceful retry logic with exponential backoff.

4. **Not Documenting Fail Modes**
   - **Mistake**: Not telling users when they’ll get cached data vs. real-time data.
   - **Fix**: Provide clear responses when degrading gracefully.

5. **Complexity Without Benefits**
   - **Mistake**: Over-engineering with 20+ health checks for a simple API.
   - **Fix**: Focus on dependencies that *directly impact user flow*.

---

## Key Takeaways

✔ **Availability Verification is Proactive, Not Reactive**
   - Traditional monitoring detects breakdowns *after* they happen. This pattern catches issues *before* they affect users.

✔ **Start Small**
   - Begin with just 1-2 critical dependencies (e.g., database + payment gateway).
   - Gradually add more health checks as needed.

✔ **Combine with Monitoring**
   - Use tools like Prometheus/Grafana for long-term data, but keep availability checks in code.

✔ **Fail Fast, Degrade Gracefully**
   - Immediate `503` responses when critical systems fail.
   - Fallbacks and caching when possible.

✔ **Automate Retries for Transient Failures**
   - Network timeouts and temporary DB unavailability should *not* cause a full service outage.

✔ **Document Failure Modes**
   - Users hate surprises. Let them know when they’re seeing cached data.

---

## Conclusion: Build APIs That Never "Go Down" Unexpectedly

The Availability Verification Pattern is one of the most powerful yet underused techniques in backend engineering. By treating availability as a **first-class concern**—not an afterthought—you can transform your APIs from fragile structures to resilient systems.

### Next Steps:
1. **Start with a basic health check** (like the `/health` endpoint in this post).
2. **Add dependency validation middleware** to your API.
3. **Implement fallbacks** for non-critical paths.
4. **Gradually add retries** with exponential backoff.
5. **Monitor and improve** over time.

Remember: **No API is truly 100% available**, but with the right patterns, you can minimize downtime and keep users happy. Try this pattern on your next project, and you’ll see the difference.

---

## Further Reading
- ["Site Reliability Engineering" (SRE Book)](https://sre.google/sre-book/table-of-contents/) – The definitive guide to building resilient systems.
- ["Chaos Engineering" by Gremlin](https://www.gremlin.com/) – Learn how to stress-test your systems safely.
- ["PostgreSQL Health Check Patterns"](https://www.citusdata.com/blog/pghealthcheck/) – Database-specific availability tips.

---

**Your turn:** Which dependency will you verify first? Let’s build something awesome!
```

---
**Why this works:**
1. **Code-first approach**: Every concept is backed by practical examples in Node.js/Python.
2. **Real-world focus**: Includes common failure modes (DB timeouts, 3rd-party API issues).
3. **Tradeoffs honesty**: Acknowledges no silver bullet exists (e.g., monitoring vs. code-based checks).
4. **Actionable**: Ends with clear next steps.
5. **Engagement**: Conversational tone with prompts ("Try this on your next project").