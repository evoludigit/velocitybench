```markdown
# **Fraisier: Orchestrating Multi-Service Deployments Like a Pro**

Deploying multiple services across development, staging, and production environments can feel like juggling flaming torches while riding a unicycle. Each service requires its own configuration, deployment workflows, and Git webhook integrations—without a unified system, things quickly become messy. That’s where **Fraisier** comes in.

Fraisier (a nod to the French word for "strawberry") is a deployment orchestration pattern that lets you manage **multiple services** from a single configuration file (`fraises.yaml`). It abstracts away Git provider differences (GitHub, GitLab, Gitea, Bitbucket), automates deployments via webhooks, and tracks deployment history. Think of it as a **strawberry farmer (Fraisier)** tending to a field of services (fraises), where every plant gets the right amount of water (deployments) at the right time—automatically.

In this guide, I’ll walk you through:
✅ The problem with managing multiple services manually
✅ How Fraisier solves it with a unified approach
✅ Practical examples in Python (using `fraises.yaml` and Git webhooks)
✅ How to implement it for real-world use cases
✅ Common pitfalls and how to avoid them

---

## **The Problem: Deploying Multiple Services Without a Garden**

Imagine running a small SaaS with three services:
- **Auth Service** (handles user logins)
- **Payments Service** (processes transactions)
- **Analytics Service** (tracks user behavior)

Each service:
- Runs in **dev**, **staging**, and **prod** environments
- Has its own **Git repository** (GitHub, GitLab, or Gitea)
- Needs **different deployment scripts** (Docker, Kubernetes, or plain ol’ `systemd`)
- Requires **webhook integrations** to trigger builds on `git push`

### **The Manual Nightmare**
Without a central system, you’re stuck with:
- **Separate deployment commands** for each service:
  ```bash
  # Dev environment
  ./deploy-auth.sh dev
  ./deploy-payments.sh dev

  # Prod environment
  ./deploy-auth.sh prod
  ./deploy-payments.sh prod
  ```
- **Scattered Git webhooks** (each service’s repo has its own webhook URL pointing to a different script).
- **No deployment history** (just logs and manual notes in a spreadsheet).
- **No consistency** (each service might use a different Git provider, requiring different webhook payloads).

### **The Consequences**
- **Human error** (accidentally deploying to production instead of staging).
- **Inconsistent environments** (dev looks nothing like staging).
- **Slow feedback loops** (manual deployments take forever).
- **Hard to debug** (no centralized logs or history).

Fraisier fixes this by **centralizing everything**—configuration, deployments, and webhook handling.

---

## **The Solution: Fraisier - One Config, All Services**

Fraisier follows these core principles:
✔ **Single Source of Truth** (`fraises.yaml`) – Everything is defined in one file.
✔ **Git Provider Abstraction** – Works with GitHub, GitLab, Gitea, Bitbucket.
✔ **Webhook-Driven Deployments** – Automatically trigger deployments on `git push`.
✔ **Deployment History** – Track success/failure, timing, and logs.
✔ **CLI for Manual Control** – Deploy, rollback, or check status via `fraise` command.

---

## **How Fraisier Works (Step-by-Step)**

### **1. Define Services in `fraises.yaml`**
This file contains:
- **Service names** (e.g., `auth`, `payments`)
- **Git repositories** (URL, webhook URL, branch mappings)
- **Deployment commands** (e.g., `docker-compose up` or `python manage.py migrate`)
- **Environment variables** (DB credentials, API keys)
- **Health checks** (to verify deployments succeeded)

#### **Example `fraises.yaml`**
```yaml
services:
  auth:
    git:
      provider: github
      repo_url: https://github.com/yourorg/auth.git
      webhook_url: https://your-server.com/webhook/auth
      branches:
        main: prod
        dev: staging
        feature/*: dev
    deploy:
      command: "docker-compose -f docker-compose.yml up -d"
      env:
        DB_HOST: "db-service"
        SECRET_KEY: "{{ env.AUTH_SECRET }}"
    health:
      url: "http://localhost:8000/health"
      timeout: 10s

  payments:
    git:
      provider: gitlab
      repo_url: https://gitlab.com/yourorg/payments.git
      webhook_url: https://your-server.com/webhook/payments
      branches:
        main: prod
        staging: staging
    deploy:
      command: "./deploy.sh"
      env:
        STRIPE_KEY: "{{ env.STRIPE_SECRET }}"
    health:
      url: "http://payments-service:5000/health"
```

### **2. Webhook Server (Event-Driven Deployments)**
When a Git push happens, the provider sends a webhook to Fraisier’s server:
```python
# Pseudocode for webhook handling
@app.route("/webhook/<service>")
def handle_webhook(service, event):
    deployment = deploy_service(service, event["branch"])
    if deployment.success:
        return {"status": "success"}
    else:
        return {"status": "failed"}, 500
```

### **3. Deployment Execution**
Fraisier runs the service’s `deploy.command` in the correct environment:
```bash
# Inside Fraisier's Python code
def deploy_service(service_name, branch):
    service = fraises_config.services[service_name]
    env_vars = service["deploy"]["env"]

    # Replace env vars like {{ env.AUTH_SECRET }}
    env_vars = replace_env_vars(env_vars)

    # Run the deploy command
    subprocess.run(
        service["deploy"]["command"],
        env=env_vars,
        check=True
    )
```

### **4. Health Checks & Rollbacks**
After deployment, Fraisier checks if the service is healthy:
```python
def check_health(service_name):
    health_url = fraises_config.services[service_name]["health"]["url"]
    timeout = fraises_config.services[service_name]["health"]["timeout"]

    try:
        requests.get(health_url, timeout=timeout)
        return True
    except requests.exceptions.RequestException:
        return False
```

### **5. Database for Deployment History**
Fraisier stores deployment logs in SQLite:
```sql
CREATE TABLE deployments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    branch TEXT NOT NULL,
    env TEXT NOT NULL,
    status TEXT NOT NULL,  -- "success", "failed", "pending"
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    logs TEXT
);
```
Example logs:
```json
{
  "service": "auth",
  "branch": "feature/login",
  "env": "staging",
  "status": "success",
  "logs": "[2024-02-15 14:30:00] Starting deployment...",
  "timestamp": "2024-02-15 14:30:10"
}
```

---

## **Implementation Guide: Building Fraisier in Python**

### **1. Setup the Project**
```bash
mkdir fraisier
cd fraisier
python -m venv venv
source venv/bin/activate  # (or `venv\Scripts\activate` on Windows)
pip install fastapi uvicorn python-dotenv pygit2
```

### **2. Create `fraises.yaml`**
```yaml
# fraises.yaml
services:
  auth:
    git:
      provider: github
      repo_url: https://github.com/yourorg/auth.git
      webhook_url: http://localhost:8000/webhook/auth
      branches:
        main: prod
        dev: staging
    deploy:
      command: "docker-compose -f docker-compose.yml up -d"
    health:
      url: "http://localhost:8000/auth/health"
      timeout: 10s
```

### **3. Build the Webhook Server**
```python
# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import subprocess
import yaml
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

app = FastAPI()

# Load Fraisier config
with open("fraises.yaml", "r") as f:
    fraises_config = yaml.safe_load(f)

class GitEvent(BaseModel):
    ref: str
    branch: str

@app.post("/webhook/{service}")
async def handle_webhook(service: str, request: Request):
    event = await request.json()
    branch = event["ref"].split("/")[-1]  # Extract branch from ref

    # Find the environment (e.g., "main" -> "prod")
    env = None
    for branch_rule, env in fraises_config["services"][service]["git"]["branches"].items():
        if branch.startswith(branch_rule):
            break

    try:
        # Run deployment
        subprocess.run(
            fraises_config["services"][service]["deploy"]["command"],
            shell=True,
            check=True,
            env=os.environ | fraises_config["services"][service]["deploy"].get("env", {})
        )
        return JSONResponse({"status": "success"})
    except subprocess.CalledProcessError:
        return JSONResponse({"status": "failed"}, status_code=500)
```

### **4. Run the Server**
```bash
uvicorn main:app --reload
```
Now, when you push to GitHub/GitLab, the webhook will trigger deployments!

### **5. Add Systemd for Production**
Create a service file (`/etc/systemd/system/fraisier.service`):
```ini
[Unit]
Description=Fraisier Deployment Orchestrator
After=network.target

[Service]
User=fraiser
WorkingDirectory=/home/fraiser/fraisier
Environment="PYTHONPATH=/home/fraiser/fraisier"
ExecStart=/home/fraiser/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```
Then:
```bash
sudo systemctl enable --now fraisier
```

### **6. Add Database Migrations**
Use `sqlite-utils` to manage the `deployments` table:
```bash
pip install sqlite-utils
sqlite-utils create fraises.db \
  "CREATE TABLE deployments(id INTEGER PRIMARY KEY, service TEXT, branch TEXT, env TEXT, status TEXT, timestamp DATETIME, logs TEXT)"
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Not Testing Webhooks Locally**
- **Problem:** Webhook payloads vary by Git provider (GitHub vs GitLab).
- **Fix:** Use tools like [ngrok](https://ngrok.com) to expose your local server and test with mock events:
  ```bash
  ngrok http 8000
  ```
  Then configure GitHub/GitLab to send webhooks to `https://your-ngrok-url.ngrok.io/webhook/{service}`.

### **❌ Mistake 2: Hardcoding Secrets**
- **Problem:** Storing secrets in `fraises.yaml` is dangerous.
- **Fix:** Use environment variables (e.g., `{{ env.DB_PASSWORD }}`) and a `.env` file:
  ```env
  # .env
  AUTH_SECRET=supersecret123
  STRIPE_SECRET=sk_test_123
  ```
  Then load them in Python:
  ```python
  from dotenv import load_dotenv
  load_dotenv()
  ```

### **❌ Mistake 3: Ignoring Health Checks**
- **Problem:** A deployment might "succeed" but fail silently.
- **Fix:** Always include a `health.url` in `fraises.yaml` and check it after deployment.

### **❌ Mistake 4: No Rollback Strategy**
- **Problem:** If a deployment breaks, you might be stuck.
- **Fix:** Add a rollback command (e.g., `docker-compose down` for Docker services).

---

## **Key Takeaways**
✅ **Centralized Configuration** – `fraises.yaml` is the single source of truth.
✅ **Git Provider Agnostic** – Works with GitHub, GitLab, Gitea, Bitbucket.
✅ **Automated Deployments** – Webhooks trigger builds on `git push`.
✅ **Deployment History** – SQLite tracks every deployment’s success/failure.
✅ **CLI for Manual Control** – Deploy, rollback, or check status with `fraise` commands.
✅ **Health Checks** – Ensure services are running correctly after deployment.

---

## **Conclusion: Fraisier = Less Headaches, More Strawberries**
Managing multiple services manually is like trying to grow a strawberry patch without a garden—it’s messy, inconsistent, and hard to scale. **Fraisier turns that into a well-tended field**, where every strawberry (service) gets the right care (deployments) at the right time.

### **Next Steps**
1. **Start small** – Add one service to `fraises.yaml` and test webhooks.
2. **Gradually migrate** – Move one service at a time to avoid downtime.
3. **Add monitoring** – Use Prometheus/Grafana to track deployment metrics.
4. **Extend Fraisier** – Add features like **blue-green deployments** or **canary releases**.

### **Final Thought**
Fraisier isn’t perfect—it’s **a tool, not a silver bullet**. It works best for:
- Teams managing **3+ services**.
- Environments with **multiple Git providers**.
- Developers who want **less manual work**.

If you’re running a tiny project with one service, you might not need it. But if you’re juggling multiple services and want **consistency, automation, and peace of mind**, Fraisier is a game-changer.

Now go forth and **orchestrate your deployments like a pro**!

---
**🚀 Further Reading**
- [Python FastAPI Docs](https://fastapi.tiangolo.com)
- [Systemd Service Files](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [SQLite Utilities](https://sqlite-utils.readthedocs.io)
```