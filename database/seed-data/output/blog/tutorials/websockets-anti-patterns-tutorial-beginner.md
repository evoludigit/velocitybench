```markdown
---
title: "WebSockets Anti-Patterns: What Not to Do When Building Real-Time Apps"
description: "A beginner-friendly guide to common WebSocket mistakes, their pitfalls, and how to avoid them. Learn from real-world examples and best practices."
date: 2023-11-15
tags: ["backend", "websockets", "api design", "real-time", "anti-patterns"]
---

# **WebSockets Anti-Patterns: What Not to Do When Building Real-Time Apps**

Real-time applications—like chat apps, live dashboards, or collaborative editing tools—relish on WebSockets. But despite their power, WebSockets are notoriously tricky to implement correctly. Many developers stumble into anti-patterns that lead to scalability issues, memory leaks, or security holes.

In this guide, I’ll walk you through **common WebSocket anti-patterns**, why they’re bad, and how to fix them. We’ll use **Python (FastAPI + WebSockets)** for examples, but the lessons apply to any backend framework (Node.js, Java, Go, etc.).

---

## **The Problem: Why WebSockets Are Tricky**

WebSockets are a **persistent, bidirectional** connection between client and server. Unlike HTTP, they maintain state and allow real-time data exchange. But this simplicity hides pitfalls:

1. **Connection Management**: If you don’t track active connections properly, your server can become a memory hog (e.g., storing thousands of unused connections).
2. **Event Flooding**: Clients may send/ receive too many messages, overwhelming the server or client.
3. **Error Handling**: WebSockets hide errors silently, causing silent failures (e.g., a dropped connection).
4. **Scalability**: Without load balancing or clustering, WebSocket servers become bottlenecks.
5. **Security**: Lack of authentication or rate limiting can lead to abuse.

These anti-patterns often emerge from a lack of **statefulness management**, **proper cleanup**, or **real-world traffic considerations**.

---

## **The Solution: Avoiding WebSocket Anti-Patterns**

The key is to **design for scale, robustness, and cleanup**. Below, we’ll tackle **five critical anti-patterns** with code examples and fixes.

---

## **Anti-Pattern 1: Not Closing Connections Properly**

### **The Problem**
If you don’t close WebSocket connections when they’re no longer needed, your server **leaks memory**. A single chat app with 10,000 users and a memory leak could crash after hours.

### **Bad Example (Memory Leak)**
```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```
**Why it’s bad**: The loop never ends, and the connection stays open forever.

### **Good Fix: Close Connections Explicitly**
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
```
**Key Fix**:
- Use `try/except` to catch `WebSocketDisconnect`.
- Log disconnections for debugging.

---

## **Anti-Pattern 2: Storing All Connections Globally**

### **The Problem**
Many beginners store **all WebSocket connections in a global list**. This can lead to:
- **Memory bloat** (millions of connections).
- **Race conditions** (multiple threads modifying the list).
- **Crashes** if the list grows too large.

### **Bad Example (Global List)**
```python
active_connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Broadcast: {data}")
    finally:
        active_connections.remove(websocket)  # Race condition risk!
```
**Why it’s bad**:
- No thread safety.
- `remove()` can fail if the connection is already gone.

### **Good Fix: Use a Set or Database**
```python
active_connections = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    active_connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            async with asyncio.Lock():  # Thread-safe add/remove
                for conn in active_connections:
                    await conn.send_text(f"Broadcast: {data}")
    finally:
        active_connections.discard(websocket)  # Safe removal
```
**Key Fixes**:
- Use a **`set`** for O(1) lookups/removals.
- Add **thread-safe operations** (`asyncio.Lock`).
- Consider a **database-backed connection store** for large-scale apps (e.g., Redis).

---

## **Anti-Pattern 3: No Rate Limiting or Authentication**

### **The Problem**
WebSockets are **stateless by default**, making them easy to misuse:
- **Spam attacks**: A single client sends 10,000 messages/sec.
- **No authentication**: Anyone can join the WebSocket room.

### **Bad Example (Unprotected)**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Public message: {data}")
```
**Why it’s bad**:
- No rate limiting.
- No user validation.

### **Good Fix: Add Auth & Rate Limiting**
```python
from fastapi import Depends, HTTPException, WebSocket
from fastapi.security import HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
security = HTTPBearer()

@app.websocket("/ws")
@limiter.limit("5/minute")  # 5 messages/minute
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Depends(security)
):
    if token.credentials != "secret_token":
        raise HTTPException(status_code=403, detail="Invalid token")

    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Secure message: {data}")
```
**Key Fixes**:
- Use **JWT/HTTP tokens** for auth.
- Apply **rate limiting** (e.g., `slowapi`).
- Combine with **HTTP headers** for security.

---

## **Anti-Pattern 4: Ignoring Pong/Ping**

### **The Problem**
WebSockets use **Ping/Pong** to detect dead connections. If ignored:
- **Zombie connections** stay open but don’t respond.
- **False positives**: The server thinks a client is alive when it’s not.

### **Bad Example (No Ping Check)**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Response: {data}")
```
**Why it’s bad**: No heartbeat check.

### **Good Fix: Enforce Ping/Pong**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    last_activity = time.time()

    while True:
        try:
            # Send ping every 30 seconds
            if time.time() - last_activity > 30:
                await websocket.ping(b"ping")
                last_activity = time.time()

            data = await websocket.receive_text()
            last_activity = time.time()
            await websocket.send_text(f"Response: {data}")
        except WebSocketDisconnect:
            break
```
**Key Fix**:
- **Periodic pings** (e.g., every 30 sec).
- **Timeout handling** (close idle connections).

---

## **Anti-Pattern 5: Not Handling Errors Gracefully**

### **The Problem**
WebSockets hide errors silently. If a client disconnects unexpectedly:
- The server may crash.
- Debugging becomes impossible.

### **Bad Example (No Error Handling)**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```
**Why it’s bad**: Crashes on unexpected disconnections.

### **Good Fix: Log & Recover Errors**
```python
import logging

logging.basicConfig(level=logging.INFO)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        while True:
            try:
                data = await websocket.receive_text()
                await websocket.send_text(f"Echo: {data}")
            except Exception as e:
                logging.error(f"Error: {e}")
                break
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        await websocket.close(code=1000, reason="Server error")
```
**Key Fixes**:
- **Structured logging** (e.g., `logging.error`).
- **Graceful disconnection** on errors.

---

## **Implementation Guide: Building a Robust WebSocket Server**

Here’s a **checklist** for a production-ready WebSocket setup:

1. **Connection Management**
   - Use a **set/dict** to store active connections.
   - Implement **thread-safe** operations (`asyncio.Lock`).

2. **Scalability**
   - **Load balance** (e.g., Nginx with `proxy_pass`).
   - Use **clustering** (e.g., Redis for shared state).

3. **Security**
   - **Authenticate** (JWT, OAuth).
   - **Rate limit** (e.g., `slowapi`).
   - **HTTPS** (WebSocket over `wss://`).

4. **Error Handling**
   - Log **all disconnections**.
   - Handle **Ping/Pong** properly.

5. **Cleanup**
   - **Close connections** on `WebSocketDisconnect`.
   - **Garbage collect** stale connections.

---

## **Common Mistakes to Avoid**

| **Anti-Pattern**               | **Why It’s Bad**                          | **Fix**                                  |
|----------------------------------|-------------------------------------------|------------------------------------------|
| No connection cleanup           | Memory leaks                            | Use `try/finally` + `WebSocketDisconnect` |
| Global connection lists          | Race conditions, crashes                 | Use `set` + locks or a database          |
| No authentication               | Security breaches                        | Use JWT/OAuth                           |
| Ignoring Ping/Pong               | Zombie connections                       | Enforce heartbeats every 30 sec          |
| No error logging                | Silent failures                          | Log with `logging.error`                |
| No rate limiting                | Abuse/spam                              | Use `slowapi`                           |

---

## **Key Takeaways**

✅ **Always close connections** (`try/finally`).
✅ **Store connections safely** (`set` + locks).
✅ **Authenticate & rate-limit** (`JWT` + `slowapi`).
✅ **Handle Ping/Pong** (prevent zombie connections).
✅ **Log errors** (debugging is critical).
✅ **Scale properly** (load balancing, clustering).

---

## **Conclusion**

WebSockets are powerful but **fragile**. Avoiding anti-patterns means:
- **Designing for cleanup** (no global leaks).
- **Securing connections** (auth + rate limiting).
- **Monitoring errors** (logging, Ping/Pong).

Start small, test under load, and **iteratively improve**. For large-scale apps, consider **Redis pub/sub** or **message brokers** (Kafka) alongside WebSockets.

Now go build a **scalable, secure** real-time app—without the anti-patterns!

---
**Further Reading**:
- [FastAPI WebSockets Docs](https://fastapi.tiangolo.com/advanced/websockets/)
- [Redis Pub/Sub for Scalability](https://redis.io/topics/pubsub)
- [SlowAPI Rate Limiting](https://github.com/dabapps/slowapi)
```