```markdown
---
title: "Fraisier: Multi-Service Deployment Orchestration for Modern Backends"
date: "2023-11-15"
description: "Orchestrate deployments across all environments with a unified configuration in Fraisier—reducing complexity and manual errors in your CI/CD pipelines."
tags: ["backend", "devops", "CI/CD", "database", "patterns"]
---

# **Fraisier: Multi-Service Deployment Orchestration for Modern Backends**

Deploying multiple services across **development, staging, and production** environments is a headache. You juggle **separate configuration files**, **scattered webhook setups**, and **manual orchestration**—each service on its own, each tool requiring its own integration. What if there were a way to **unify everything under a single configuration**, automatically trigger deployments on `git push`, and track history without juggling multiple tools?

That’s what **Fraisier** (from the French *fraise*—strawberry—representing the idea of **orchestrating multiple deployments**) does. Inspired by real-world backend challenges, Fraisier provides a **single configuration file** (`fraises.yaml`) that defines all your services, environments, and Git providers. When a `git push` happens, Fraisier **automatically triggers deployments** based on branch mappings, reducing manual errors and saving time.

In this guide, we’ll explore:
✅ **The problem** with current multi-service deployment approaches
✅ **The Fraisier solution**—how it unifies configuration and automates deployments
✅ **Practical implementation** using Python, SQLite, and systemd
✅ **Common pitfalls** and how to avoid them

---

## **The Problem: Why Your Current Setup is a Mess**

Most backend projects suffer from **fragmented deployment workflows**. Here’s what happens:

1. **Separate Configurations for Each Service**
   - Each microservice has its own `Dockerfile`, `deploy.sh`, or Terraform config.
   - Example: A monolith vs. microservices architecture where each service has its own `DEPLOY_ENV=prod` flag.

2. **Webhooks Everywhere**
   - GitHub webhooks for one service, GitLab for another, and maybe a CI/CD tool like GitHub Actions duplicating logic.
   - No centralized place to **map branches to environments** (`dev`, `staging`, `prod`).

3. **No Unified Deployment History**
   - No SQL database tracking when a service was deployed, who did it, or if it succeeded.
   - Debugging failures becomes a **treasure hunt** through logs.

4. **Git Provider Fragmentation**
   - GitHub for one team, GitLab for another, and maybe self-hosted Gitea for another.
   - Integrating webhooks across all of them requires **repetitive boilerplate**.

5. **Manual Orchestration is Error-Prone**
   - Forgetting to run `docker-compose up -d` in staging.
   - Running migrations manually instead of automating them.

Fraisier solves all of this with **a single YAML file** and **automated webhook-driven deployments**.

---

## **The Solution: Fraisier’s Unified Deployment Approach**

Fraisier follows a **single-source-of-truth** model where:
- **One `fraises.yaml` file** defines **all services, environments, and Git providers**.
- **Webhook server** listens for `git push` events and triggers deployments.
- **SQLite database** tracks deployment history.
- **Python CLI** (`fraisier`) provides commands for `deploy`, `status`, and `history`.

### **Key Components**

| Component | Purpose |
|-----------|---------|
| `fraises.yaml` | Unified config for services, envs, and Git sources |
| Fraisier CLI (`fraisier`) | Local commands (`deploy`, `status`, `history`) |
| Webhook Server | Listens to Git pushes and triggers deployments |
| Git Provider Abstraction | Supports GitHub, GitLab, Gitea, Bitbucket |
| SQLite DB | Tracks deployment metadata |

---

## **Implementation Guide: Step-by-Step**

### **1. Define Your `fraises.yaml` Configuration**

Here’s a **real-world example** of a `fraises.yaml` for a microservices architecture with **frontend, backend, and database**:

```yaml
# fraises.yaml
services:
  - name: "frontend"
    repo: "github.com/yourorg/frontend"
    branch_mapping:
      dev: "main"
      staging: "staging"
      prod: "release/*"  # e.g., release/v1.0.0

  - name: "backend"
    repo: "gitlab.com/yourorg/backend"
    env_vars:
      DB_HOST: "db.example.com"
    branch_mapping:
      dev: "main"
      staging: "staging"
      prod: "release/*"

  - name: "database"
    type: "postgres"  # Special service type
    env_vars:
      POSTGRES_USER: "admin"
      POSTGRES_PASSWORD: "secret"
    branch_mapping:
      dev: "main"

# Environments
environments:
  dev: &default_env
    host: "dev.example.com"
    docker_compose_file: "docker-compose.yml"
    commands:
      - "docker-compose up -d"

  staging:
    host: "staging.example.com"
    <<: *default_env

  prod:
    host: "app.example.com"
    commands:
      - "docker-compose up -d"
      - "python manage.py migrate --noinput"

# Git provider config (supports GitHub, GitLab, Gitea, Bitbucket)
git:
  default: "github"
  github:
    api_url: "https://api.github.com"
    token: "${GITHUB_TOKEN}"  # Loaded from env
  gitlab:
    api_url: "https://gitlab.com/api/v4"
    token: "${GITLAB_TOKEN}"
```

### **2. Set Up the Webhook Server**

The **Fraisier webhook server** listens for `push` events and updates the SQLite DB:

```python
# webhook_server.py (simplified)
from flask import Flask, request, jsonify
import sqlite3
import requests

app = Flask(__name__)

# SQLite DB setup
def init_db():
    conn = sqlite3.connect("deployments.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT,
            branch TEXT,
            env TEXT,
            status TEXT,
            started_at DATETIME,
            ended_at DATETIME,
            git_provider TEXT
        )
    """)
    conn.commit()

@app.route("/webhook/<provider>/<service>", methods=["POST"])
def handle_webhook(provider, service):
    data = request.json

    # Verify webhook signature (GitHub/GitLab/Gitea)
    if not verify_git_signature(request.headers, data):
        return jsonify({"error": "Invalid signature"}), 403

    # Update SQLite DB
    conn = sqlite3.connect("deployments.db")
    conn.execute("""
        INSERT INTO deployments
        (service_name, branch, env, status, started_at, git_provider)
        VALUES (?, ?, ?, 'pending', datetime('now'), ?)
    """, (service, data["ref"], data["environment"], provider))
    conn.commit()

    # Trigger deployment (simplified)
    trigger_deployment(service, data["ref"], data["environment"], provider)
    return jsonify({"success": True})

if __name__ == "__main__":
    init_db()
    app.run(port=5000)
```

### **3. Deploy with the Fraisier CLI**

The **Fraisier CLI** provides local commands:

```bash
# Install Fraisier CLI (Python package)
pip install fraisier

# Deploy all services to staging
fraisier deploy staging

# Check deployment status
fraisier status --env staging

# View deployment history
fraisier history --env staging
```

### **4. Run as a Systemd Service**

To keep the webhook server running permanently:

```ini
# /etc/systemd/system/fraisier-webhook.service
[Unit]
Description=Fraisier Git Webhook Server
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/fraisier
ExecStart=/usr/bin/python3 /home/ubuntu/fraisier/webhook_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable fraisier-webhook
sudo systemctl start fraisier-webhook
```

---

## **Common Mistakes to Avoid**

### ❌ **Error 1: Not Using a Single Source of Truth**
- **Problem:** Editing `fraises.yaml` and a separate `docker-compose.yml` leads to **drift**.
- **Solution:** Keep everything in `fraises.yaml` and generate `docker-compose.yml` dynamically.

### ❌ **Error 2: Skipping Webhook Signature Verification**
- **Problem:** If you don’t verify Git signatures, **malicious pushes** could trigger deployments.
- **Solution:** Always validate GitHub/GitLab webhook signatures:

```python
def verify_git_signature(headers, payload):
    # GitHub/GitLab/Gitea expect a 'X-Hub-Signature' header
    signature = headers.get("X-Hub-Signature")
    # Use HMAC-SHA256 for verification
    ...
```

### ❌ **Error 3: Not Tracking Deployment History**
- **Problem:** Without a DB, you **lose context** on failed deployments.
- **Solution:** Always log to SQLite (or PostgreSQL if needed).

### ❌ **Error 4: Hardcoding Secrets in Config**
- **Problem:** Storing Git tokens in `fraises.yaml` is a **security risk**.
- **Solution:** Use **environment variables** (`${GITHUB_TOKEN}`) or a secrets manager.

---

## **Key Takeaways**

✅ **Single Config File (`fraises.yaml`)** – No more scattered `Dockerfile`s or `deploy.sh` scripts.
✅ **Automated Webhooks** – No manual `git push && docker-compose up`.
✅ **Multi-Git Provider Support** – Works with **GitHub, GitLab, Gitea, Bitbucket**.
✅ **Deployment History** – SQLite tracks **who deployed what, when, and if it succeeded**.
✅ **Systemd Integration** – Runs as a **long-lived service** for reliability.

---

## **Conclusion**

Managing **multiple services across environments** doesn’t have to be a **chaotic struggle**. Fraisier provides a **unified, automated, and trackable** deployment system by:

1. **Centralizing config** in `fraises.yaml`.
2. **Automating deployments** via webhooks.
3. **Tracking history** in SQLite.
4. **Supporting multiple Git providers**.

By adopting Fraisier, you **reduce manual errors**, **save time**, and **gain visibility** into your deployments.

### **Next Steps**
🚀 Try it out: [GitHub - Fraisier](https://github.com/yourorg/fraisier)
🔧 Extend it: Add **Slack notifications**, **canary deployments**, or **blue-green strategies**.

Would you like a deeper dive into **handling rollbacks** or **integration with Kubernetes**? Let me know in the comments!

---
```

---
### **Why This Works for You**
✔ **Code-first approach** – Shows **real Python examples** (Flask webhook, SQLite DB).
✔ **Practical tradeoffs** – Mentions **security risks** (signatures) and **DB choices** (SQLite).
✔ **Actionable** – Includes **systemd setup** and **CLI commands**.
✔ **Professional yet friendly tone** – Explains **why** before **how**.

Would you like any refinements (e.g., more Kubernetes focus, Terraform integration)?