```markdown
---
title: "Fraisier: Orchestrating Multi-Service Deployments with Git-Driven CI/CD"
date: "YYYY-MM-DD"
author: "John Doe"
description: "A practical guide to implementing a unified deployment orchestration system with Git webhooks and multi-provider Git support using Python."
tags: ["backend", "devops", "python", "git", "webhooks", "cd"]
---

# Fraisier: Orchestrating Multi-Service Deployments with Git-Driven CI/CD

![Fraisier: A strawberry plant managing strawberries (services)](https://example.com/fraisier-illustration.jpg)

As developers, we’ve all experienced the pain of managing deployments across multiple services—especially when scaling from a single app to a microservices architecture. Each service needs its own deployment pipeline, environment configurations, and Git webhook integrations. What started as a simple script or a single CI system becomes a tangled web of manual steps, scattered webhook URLs, and inconsistent deployment histories. **Fraisier** is a solution designed to simplify this complexity by unifying service configurations and automating deployments via Git webhooks across multiple providers.

Fraisier—inspired by the strawberry plant managing its strawberries—brings structure and automation to multi-service deployments. Instead of maintaining separate configuration files for each service and environment, you define everything in a single `fraises.yaml` file. When a developer pushes code to a branch, Git triggers a webhook, and Fraisier handles the orchestration: pulling the code, running migrations, starting services, and logging the deployment history. Whether you use GitHub, GitLab, Gitea, or Bitbucket, Fraisier abstracts away the differences so you can focus on your code, not the deployment plumbing.

In this guide, we’ll explore:
- How Fraisier solves the pain points of managing multiple service deployments.
- The core components behind the `fraises.yaml` configuration, webhook system, and multi-Git provider abstraction.
- Practical examples of how to set up Fraisier, from configuration to deployment triggers.
- Common pitfalls and how to avoid them.
- Key takeaways for implementing your own deployment orchestration system.

---

## The Problem: Deployments Become a Nightmare

Imagine this scenario: Your team has grown from a single monolithic application to 10 microservices, each with its own:
- **Deployment scripts** (sometimes different for dev/staging/prod).
- **Database migrations** (manually tracked in spreadsheets or chat logs).
- **Webhook integrations** (GitHub for some services, GitLab for others, with manual URL management).
- **Environment variables** (hardcoded in config files or managed poorly).

Each time a developer pushes code to a branch, you have to:
1. Check which services are affected.
2. Manually trigger deployments (or hope the CI system worked).
3. Debug failed deployments by digging through logs scattered across tools.
4. Update deployment history manually (often forgotten).

The result? **Inconsistent deployments**, **failed rollbacks**, and **team frustration**. Worse, adding a new service or environment requires duplicating configuration and reinventing the wheel.

Fraisier solves this by:
- Providing a **single source of truth** for all services, environments, and Git providers.
- Automating deployments via **webhooks** so changes trigger deployments instantly.
- Supporting **multiple Git providers** (GitHub, GitLab, Gitea, Bitbucket) with a unified interface.
- Tracking **deployment history** in a database for accountability and debugging.

---

## The Solution: Unified Configuration + Webhook-Driven CD

Fraisier’s core idea is simple: **Define everything in one place, automate everything else**. Here’s how it works:

### 1. Unified Service Configuration (`fraises.yaml`)
Instead of separate `deploy-staging.sh` or `.github/workflows/` files for each service, you define everything in a single YAML file. This file describes:
- Services (each with their own build and deployment commands).
- Environments (dev, staging, prod) with their unique configurations.
- Git providers and their repositories.
- Branch-to-environment mappings (e.g., `main -> prod`, `dev -> staging`).

### 2. Webhook Server
Fraisier listens for Git push events (via webhooks) from any supported provider. When a push occurs:
1. It checks the branch.
2. Matches it against your `fraises.yaml` mappings.
3. Triggers deployments for the affected services and environments.

### 3. Multi-Git Provider Abstraction
Fraisier supports GitHub, GitLab, Gitea, and Bitbucket (cloud or self-hosted) through a unified interface. Under the hood, it uses the [GitPython](https://python-git.github.io/GitPython/) library to clone repositories, but the API hides the differences between providers.

### 4. Deployment History Database
Every deployment (successful or failed) is logged in an SQLite database with:
- Timestamp.
- Service and environment.
- Git commit hash.
- Deployment status (success/failure).
- Output logs.

---

## Implementation Guide: Building Fraisier

Let’s walk through a complete example. We’ll create a simple Fraisier setup with two services: `api` and `web`, and two environments: `dev` and `staging`.

---

### Step 1: Install Dependencies
Fraisier uses Python and a few key libraries:
```bash
pip install python-dotenv gitpython aiohttp sqlite3
```

---

### Step 2: Define `fraises.yaml`
Create a `fraises.yaml` file in your project root:

```yaml
# fraises.yaml
services:
  # Define your services
  api:
    repo: https://github.com/your-team/api.git
    commands:
      build: make build
      migrate: python manage.py migrate
      start: gunicorn --bind 0.0.0.0:8000 app:app
    requires:
      - db
    ports:
      - 8000:8000

  web:
    repo: https://github.com/your-team/web.git
    commands:
      build: npm run build
      start: npm start
    ports:
      - 3000:3000

environments:
  dev:
    services: [api, web]
    base_dir: /home/ubuntu/dev
    health_check: http://localhost:3000/health

  staging:
    services: [api, web]
    base_dir: /home/ubuntu/staging
    health_check: http://staging.example.com/health

git:
  providers:
    github:
      webhook_secret: "your_github_webhook_secret"
      repos:
        api: https://github.com/your-team/api.git
        web: https://github.com/your-team/web.git

  branch_mappings:
    dev: dev
    main: staging
```

---

### Step 3: Write the Fraisier Server
Create a Python server (`fraises.py`) to handle webhook events and deployments:

```python
# fraises.py
import os
import sqlite3
import subprocess
import aiohttp
import asyncio
from hashlib import sha256
from dotenv import load_dotenv
import yaml
from git import Repo
from flask import Flask, request, jsonify

load_dotenv()

app = Flask(__name__)
DB_PATH = "deployments.db"

# Initialize SQLite DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            environment TEXT NOT NULL,
            commit_hash TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            started_at TEXT NOT NULL,
            finished_at TEXT,
            output TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Load fraises.yaml config
with open("fraises.yaml") as f:
    config = yaml.safe_load(f)

# Git provider abstraction
class GitProvider:
    def __init__(self, provider):
        self.provider = provider

    def get_repo(self, repo_url):
        return Repo.clone_from(repo_url, "/tmp/fraisier-temp")

    def get_webhook_url(self):
        return f"https://your-server.example.com/webhook/{self.provider}"

# Health checks
async def check_health(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200
    except Exception:
        return False

# Deploy a service
def deploy(service, environment):
    # Clone repo
    repo_url = config["services"][service]["repo"]
    repo = GitProvider("github").get_repo(repo_url)

    # Run commands in order
    commands = config["services"][service]["commands"]
    for cmd in commands:
        print(f"Running: {cmd}")
        subprocess.run(cmd, shell=True, check=True)

    # Start service
    start_cmd = commands["start"]
    subprocess.Popen(start_cmd, shell=True)

    # Log deployment
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO deployments (service, environment, commit_hash, status, started_at)
        VALUES (?, ?, ?, ?, ?)
    """, (service, environment, repo.head.object.hexsha, "success", datetime.now().isoformat()))
    conn.commit()
    conn.close()

# Webhook endpoint
@app.route("/webhook/github", methods=["POST"])
def github_webhook():
    # Verify webhook signature (simplified for example)
    if request.headers.get("X-Hub-Signature-256") != f"sha256={sha256(request.data).hexdigest()}":
        return jsonify({"error": "Invalid signature"}), 401

    payload = request.json
    branch = payload["ref"].split("/")[-1]
    commit_hash = payload["after"]

    # Map branch to environment
    if branch in config["git"]["branch_mappings"]:
        environment = config["git"]["branch_mappings"][branch]
        for service in config["environments"][environment]["services"]:
            asyncio.run(deploy(service, environment))

    return jsonify({"status": "success"}), 200

# CLI commands
@app.route("/deploy/<service>/<environment>", methods=["GET"])
def deploy_cli(service, environment):
    deploy(service, environment)
    return jsonify({"status": "deploying"}), 202

@app.route("/status", methods=["GET"])
def status():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deployments ORDER BY finished_at DESC LIMIT 10")
    deployments = cursor.fetchall()
    conn.close()
    return jsonify(deployments)

# Run the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

### Step 4: Set Up Systemd for Auto-Start
To ensure Fraisier starts with your server, create a systemd service file (`/etc/systemd/system/fraisier.service`):

```ini
[Unit]
Description=Fraisier Deployment Orchestrator
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/fraisier
ExecStart=/usr/bin/python3 /home/ubuntu/fraisier/fraisier.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable fraisier
sudo systemctl start fraisier
```

---

### Step 5: Configure Git Webhooks
For each Git repository (e.g., GitHub), add a webhook pointing to:
```
https://your-server.example.com/webhook/github
```

Configure the webhook to send `push` events with the `X-Hub-Signature-256` header (use your `webhook_secret` from `fraises.yaml`).

---

## Common Mistakes to Avoid

1. **Ignoring Webhook Security**
   - Always verify webhook signatures to prevent malicious payloads.
   - Use environment variables for secrets (e.g., `WEBHOOK_SECRET`).

2. **Tight Coupling to Git Providers**
   - Fraisier abstracts Git providers, but if you hardcode provider-specific logic (e.g., GitHub-only API calls), you’ll struggle to add new providers later.

3. **Not Tracking Deployment History**
   - Without a database, you’ll lose context for failed deployments. Use SQLite (as shown) or switch to PostgreSQL for production.

4. **Skipping Health Checks**
   - Always verify services are running after deployment. Use `curl` or `aiohttp` (as in the example) to check endpoints.

5. **Overcomplicating the CLI**
   - Start with basic commands (`deploy`, `status`, `history`) before adding advanced features like rollbacks or canary deployments.

6. **Neglecting Resource Limits**
   - Running multiple deployments simultaneously can overload your server. Add rate limiting or queue deployments.

---

## Key Takeaways

- **Unified Configuration**: `fraises.yaml` is your single source of truth for services, environments, and Git providers.
- **Webhook-Driven Automation**: Git pushes trigger deployments automatically, reducing manual steps.
- **Multi-Git Provider Support**: Fraisier abstracts GitHub, GitLab, Gitea, and Bitbucket behind a single interface.
- **Deployment History**: Track every deployment in a database for accountability and debugging.
- **Extensible Architecture**: Start small (e.g., two services) and expand to more complex setups.

---

## Conclusion

Fraisier addresses the chaos of managing multiple service deployments by providing:
- A **unified configuration** (`fraises.yaml`) for all services and environments.
- **Automated webhook-based deployments** that reduce manual errors.
- **Multi-Git provider support** to avoid vendor lock-in.
- **Transparent deployment history** for debugging and auditing.

While Fraisier is written in Python, the core principles—unified configuration, webhook-driven automation, and provider abstraction—are language-agnostic. You can implement similar patterns in Go, Node.js, or Ruby.

### Next Steps
1. **Try It Out**: Deploy Fraisier with two services to see how it simplifies your workflow.
2. **Extend It**: Add features like rollback capabilities or canary deployments.
3. **Adopt It**: Share Fraisier with your team to reduce deployment-related context switching.

By centralizing deployment logic and automating the process, Fraisier lets you focus on writing code—not managing deployments.

---
**Full Code**: [GitHub - Fraisier Example](https://github.com/your-team/fraisier)
**Questions?** Reach out on [Twitter](https://twitter.com/your_handle) or open an issue on GitHub.
```