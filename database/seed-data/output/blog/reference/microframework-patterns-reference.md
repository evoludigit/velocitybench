# **[Pattern] Microframework Patterns (Flask, Express.js) – Reference Guide**

---

## **1. Overview**
Microframeworks like **Flask (Python)** and **Express.js (Node.js)** prioritize simplicity, flexibility, and minimalism by abstracting only the most essential web application concerns (routing, middleware, request/response handling). Unlike full-stack frameworks (e.g., Django, Laravel), microframeworks require developers to handle database interactions, templating, and authentication independently, enabling fine-grained control.

Designed for rapid prototyping, APIs, and lightweight applications, these frameworks emphasize:
- **Modularity**: Integrate libraries (e.g., Jinja2 for Flask, EJS/Pug for Express) as needed.
- **Performance**: Minimal overhead with fast startup and routing.
- **Scalability**: Easily extend with third-party middleware (e.g., Flask-RESTful, Express Router).
- **Community Ecosystem**: Rich plugins for databases (SQLAlchemy, Sequelize), caching (Redis), and security (Helmet, Flask-Talisman).

This guide covers key implementation patterns, architectural trade-offs, and best practices for building robust applications with Flask/Express.

---

## **2. Schema Reference**

| **Component**          | **Flask**                          | **Express.js**                     | **Purpose**                                                                 |
|------------------------|------------------------------------|------------------------------------|-----------------------------------------------------------------------------|
| **Routing**            | `@app.route()`                     | `app.get()`, `app.post()`          | Declares HTTP methods (GET-POST-PUT-DELETE) and URL paths.                  |
| **Middleware**         | `@app.before_request` / decorators | `app.use()`                        | Pre/post-processing for requests/responses (e.g., auth, logging).            |
| **Request Handling**   | `request.args`, `request.json`     | `req.query`, `req.body`            | Accesses URL params, form data, or JSON payloads.                           |
| **Response**           | `return render_template()`, `jsonify()` | `res.send()`, `res.json()`   | Renders views (templates) or JSON responses.                                |
| **Templating**         | Jinja2 (default)                   | EJS, Pug, or custom engines        | Dynamic HTML rendering (e.g., `<% include header %>` in EJS).                |
| **Database Abstraction** | SQLAlchemy, Flask-SQLAlchemy      | Sequelize, TypeORM, raw SQL        | ORM support (optional; raw queries also supported).                         |
| **Async Support**      | `Flask-Redis`, `Celery`            | `async/await`, `Promise`           | Background tasks/jobs (e.g., `app.use(async (req, res) => {...})`).       |
| **Static Files**       | `app.static_folder`                | `express.static()`                 | Serves CSS/JS/images (e.g., `app.use(express.static('public'))`).          |
| **Configuration**      | `app.config`                       | `app.set()` / environment vars     | Centralized settings (e.g., `DEBUG=True`, `PORT=3000`).                      |
| **Error Handling**     | `@app.errorhandler`                | `app.use((err, req, res, next) => {})` | Custom error responses (e.g., 404, 500 pages).                              |
| **Testing**            | `pytest`, `Flask-Testing`          | `Supertest`, `Jest`                | Unit/integration tests (e.g., `chai.expect(res.status).to.equal(200)`).  |
| **Security**           | Flask-Talisman (HTTPS), Flask-Limiter | Helmet, `cors()`, rate-limiting   | Protects against CSRF, XSS, and DoS.                                        |

---

## **3. Query Examples**

### **3.1 Routing**
**Flask:**
```python
from flask import Flask

app = Flask(__name__)

# Basic route
@app.route('/users')
def get_users():
    return {'users': ['Alice', 'Bob']}

# Dynamic route with params
@app.route('/users/<int:user_id>')
def get_user(user_id):
    return {'id': user_id, 'name': 'Alice'}
```

**Express.js:**
```javascript
const express = require('express');
const app = express();

app.get('/users', (req, res) => {
  res.json({ users: ['Alice', 'Bob'] });
});

app.get('/users/:userId', (req, res) => {
  res.json({ id: req.params.userId, name: 'Alice' });
});
```

---

### **3.2 Middleware**
**Flask (Request Logging):**
```python
@app.before_request
def log_request():
    print(f"Request: {request.method} {request.path}")
```

**Express.js (Logger Middleware):**
```javascript
const morgan = require('morgan');
app.use(morgan('combined')); // Logs request details
```

---

### **3.3 Dynamic Responses**
**Flask (JSON + Templating):**
```python
from flask import render_template, jsonify

@app.route('/api/user')
def api_user():
    return jsonify({'name': 'Alice'})

@app.route('/profile')
def profile():
    return render_template('user.html', name='Alice')
```

**Express.js (JSON + Render):**
```javascript
app.get('/profile', (req, res) => {
  res.render('user', { name: 'Alice' }); // EJS template
});

app.get('/api/user', (req, res) => {
  res.json({ name: 'Alice' });
});
```

---

### **3.4 Database Interaction (SQLAlchemy vs. Sequelize)**
**Flask (SQLAlchemy):**
```python
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))

@app.route('/users')
def users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'name': u.name} for u in users])
```

**Express.js (Sequelize):**
```javascript
const { Sequelize, DataTypes } = require('sequelize');
const sequelize = new Sequelize('database', 'user', 'pass', {
  host: 'localhost',
  dialect: 'mysql'
});

const User = sequelize.define('User', {
  name: DataTypes.STRING
});

app.get('/users', async (req, res) => {
  const users = await User.findAll();
  res.json(users.map(u => ({ id: u.id, name: u.name })));
});
```

---

### **3.5 Error Handling**
**Flask:**
```python
@app.errorhandler(404)
def not_found(error):
    return {"error": "Not found"}, 404

@app.errorhandler(500)
def server_error(error):
    return {"error": "Internal server error"}, 500
```

**Express.js:**
```javascript
app.use((err, req, res, next) => {
  if (err.name === 'ValidationError') {
    return res.status(400).json({ error: err.message });
  }
  res.status(500).json({ error: 'Internal server error' });
});
```

---

### **3.6 Async Operations**
**Flask (Celery Background Job):**
```python
from celery import Celery
celery = Celery(app.name, broker='redis://localhost:6379/0')

@celery.task
def send_email(to, message):
    # Async email logic
    pass

@app.route('/notify')
def notify():
    send_email.delay('user@example.com', 'Hello!')
    return 'Email sent in background'
```

**Express.js (`async/await`):**
```javascript
app.get('/long-task', async (req, res) => {
  try {
    const result = await longRunningTask();
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
```

---

## **4. Best Practices**

### **4.1 Modular Design**
- **Flask**: Use `flask-blueprints` for modular routes (e.g., `users.py`, `auth.py`).
- **Express.js**: Split into folders (e.g., `routes/users.js`, `controllers/userController.js`).

### **4.2 Dependency Injection**
- Avoid global variables. Pass dependencies (e.g., DB client) via constructor:
  ```python
  class UserService:
      def __init__(self, db):
          self.db = db
  ```

### **4.3 Security**
- **Flask**:
  - Enable `FLASK_ENV=production` and set `SECRET_KEY`.
  - Use `Flask-Talisman` for HTTPS enforcement.
- **Express.js**:
  - Use `helmet()` to secure headers.
  - Validate inputs (e.g., `express-validator`).

### **4.4 Testing**
- **Flask**: Test routes with `flask.testing.TestCase`.
- **Express.js**: Use `supertest` for API testing:
  ```javascript
  const request = require('supertest')(app);
  test('GET /users', async () => {
    const res = await request.get('/users');
    expect(res.statusCode).toBe(200);
  });
  ```

### **4.5 Performance**
- **Cache**: Use `Flask-Caching` or `express-cache` for frequent queries.
- **Async**: Offload I/O-bound tasks (e.g., DB calls) to async handlers.

### **4.6 Deployment**
- **Flask**: Use `gunicorn` + `nginx`:
  ```bash
  gunicorn -w 4 -b 0.0.0.0:8000 app:app
  ```
- **Express.js**: Deploy with `PM2` for clustering:
  ```bash
  pm2 start app.js -i max
  ```

---

## **5. Related Patterns**

| **Pattern**               | **Purpose**                                                                 | **Integration with Microframeworks**                          |
|---------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------|
| **RESTful API Design**    | Standardized API structure (resources, HTTP methods).                      | Core to Flask-RESTful/Express Router.                         |
| **Middleware Chaining**   | Layered request/response processing (e.g., auth, logging).                | Built-in in Flask (`@app.before_request`) and Express (`app.use`). |
| **CQRS**                  | Separates read/write operations for scalability.                           | Useful with Flask-SQLAlchemy/Sequelize for complex queries.   |
| **Event-Driven Architecture** | Decouples components via events (e.g., Pub/Sub).                         | Pair with Celery (Flask) or `node-events` (Express).          |
| **Container Orchestration** | Manages microservices (e.g., Docker, Kubernetes).                         | Flask/Express apps containerized as lightweight services.    |
| **JWT Authentication**    | Stateless token-based auth.                                                | Implement via `flask-jwt-extended` or `jsonwebtoken` (Express).|
| **GraphQL**               | Flexible querying vs. REST’s fixed endpoints.                            | Add `flask-graphql` or `apollo-server-express`.               |

---

## **6. Trade-offs**
| **Pros**                          | **Cons**                                  |
|-----------------------------------|-------------------------------------------|
| Lightweight, fast startup         | No built-in ORM/templating (requires plugins) |
| Highly configurable               | Steeper learning curve for beginners     |
| Ideal for APIs/microservices      | Less "batteries-included" than full-stack frameworks |

---
**Key Takeaway**: Microframeworks excel in scalability and flexibility but demand disciplined architecture. Use them for APIs, prototypes, or modular services where control outweighs convenience.