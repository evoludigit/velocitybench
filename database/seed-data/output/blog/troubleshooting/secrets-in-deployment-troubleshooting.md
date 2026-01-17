# **Debugging Secrets in Deployment: A Troubleshooting Guide**
*Ensuring Secure Credential Management in Production*

---

## **1. Introduction**
The **"Secrets in Deployment"** pattern ensures that sensitive credentials (API keys, database passwords, certificates, etc.) are stored securely and injected dynamically into applications rather than hardcoded. Failure to implement this pattern correctly can lead to exposed secrets, compliance violations, and security breaches.

This guide provides a structured approach to diagnosing and fixing issues related to secrets management in deployments.

---

## **2. Symptom Checklist**
Before diving into debugging, verify if these symptoms exist in your system:

### **Security & Compliance Issues**
- [ ] Secrets (e.g., DB passwords, API keys) are hardcoded in source code, configs, or logs.
- [ ] Unauthorized access attempts via leaked secrets.
- [ ] Compliance violations (e.g., GDPR, SOC2) due to improper secret handling.
- [ ] Secrets are exposed in deployment artifacts (e.g., Docker images, logs).

### **Performance & Reliability Issues**
- [ ] Applications fail to connect to external services (e.g., databases, payment gateways).
- [ ] Unexpected timeouts or connection errors due to missing/invalid secrets.
- [ ] Environment variables not being injected at runtime.
- [ ] Secrets rotating but not updating in production (stale credentials).

### **Operational & Scaling Problems**
- [ ] Difficulty deploying secrets securely in multi-environment (dev/stage/prod) setups.
- [ ] Secrets management becomes a bottleneck during CI/CD pipelines.
- [ ] Manual secret updates lead to human errors.
- [ ] Secrets are not encrypted at rest or in transit.

### **Debugging-Friendly Symptoms**
- [ ] Logs show errors like `Missing required secret` or `Invalid API key`.
- [ ] Container images include secrets (checked via `docker history` or `skopeo inspect`).
- [ ] Secrets are hardcoded in config files (e.g., `application.yml`, `config.toml`).
- [ ] Secrets are committed to version control (e.g., Git, SVN).

---

## **3. Common Issues & Fixes**

### **Issue 1: Secrets Hardcoded in Code/Configs**
**Symptoms:**
- Secrets appear in `git log`, IDE autocompletion, or CI logs.
- Applications fail due to missing credentials when deployed.

**Root Cause:**
Developers or build pipelines inadvertently commit secrets.

**Fix:**
#### **For Application Code:**
- **Replace hardcoded secrets with environment variables or config files (outside Git).**
  ```python
  # ❌ Bad: Hardcoded secret
  import requests
  requests.post("https://api.example.com", auth=("user", "PASSWORD123"))

  # ✅ Good: Load from environment variable
  import os
  api_key = os.getenv("API_KEY")
  requests.post("https://api.example.com", headers={"Authorization": f"Bearer {api_key}"})
  ```

- **Use `.gitignore` to exclude sensitive files:**
  ```
  # .gitignore
  *.env
  config_prod.json
  ```

#### **For Build Artifacts:**
- **Scan images for secrets before deployment:**
  ```bash
  # Detect secrets in Docker image layers
  docker history --no-trunc <image-name> | grep -i "password\|key\|token"
  ```
- **Use tools like `trivy`, `grype`, or `docker-secretscan` to detect embedded secrets.**

---

### **Issue 2: Secrets Not Injected at Runtime**
**Symptoms:**
- `Environment variable not found` errors in logs.
- Applications crash due to missing credentials.

**Root Cause:**
- Secrets not passed to containers/Pods.
- Incorrect Kubernetes Secrets/Credentials Manager setup.

**Fix:**
#### **For Docker/Kubernetes:**
##### **Option 1: Use `envFrom` or `env` in Deployments**
```yaml
# ✅ Correct: Inject secrets via Kubernetes Secrets
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
  - name: my-app
    image: my-app:latest
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secrets
          key: password
```
**Verify injection:**
```bash
kubectl exec -it my-app -- env | grep DB_PASSWORD
```

##### **Option 2: Use a Secrets Manager (HashiCorp Vault, AWS Secrets Manager)**
```bash
# Example: Fetch secret securely via Vault agent
VAULT_ADDR="https://vault.example.com" vault kv get secret/db_password
```

##### **Option 3: Use CI/CD Secrets (GitHub Actions/GitLab CI)**
```yaml
# GitHub Actions example
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          echo "DB_PASSWORD=${{ secrets.DB_PASSWORD }}" > .env
          docker build --build-arg DB_PASSWORD=$DB_PASSWORD .
```

---

### **Issue 3: Secrets Exposed in Logs or Artifacts**
**Symptoms:**
- Secrets leak in container logs (`kubectl logs`).
- Secrets appear in build outputs (`docker buildx build`).

**Root Cause:**
- Logs or build outputs include sensitive data.
- Secrets not redacted in monitoring tools.

**Fix:**
#### **For Container Logs:**
- **Redact secrets in logs using `json-file` driver + logrotate:**
  ```bash
  docker run --log-opt max-size=10m --log-opt max-file=3 app
  ```
- **Use tools like `logrus` (Go) or `structlog` to redact secrets:**
  ```go
  logger := log.WithFields(log.Fields{
      "user_id": userID,
      "secret": redact("API_KEY"), // Custom redaction function
  })
  ```

#### **For Docker Builds:**
- **Use `--secret` with BuildKit (Docker 18.09+):**
  ```bash
  DOCKER_BUILDKIT=1 docker build --secret id=db_password,src=./secret.txt .
  ```
- **Avoid `ARG` in Dockerfiles (or use `--build-arg` securely):**
  ```dockerfile
  # ❌ Bad: Build-time secret
  ARG DB_PASSWORD
  ENV DB_PASSWORD=$DB_PASSWORD

  # ✅ Good: Runtime-only secret
  ENV DB_PASSWORD=${DB_PASSWORD}
  ```

---

### **Issue 4: Stale Secrets After Rotation**
**Symptoms:**
- Applications use old credentials post-rotation.
- Failed deployments due to `Access Denied`.

**Root Cause:**
- Secrets not updated in all environments (dev/stage/prod).
- Cached secrets in databases or local files.

**Fix:**
#### **Automate Secret Rotation:**
- **Use tools like:**
  - **AWS Secrets Manager + Lambda** (auto-rotate DB passwords).
  - **HashiCorp Vault + KV Secret Engine** (auto-rotate API keys).
  - **Kubernetes External Secrets Operator** (sync secrets from Vault/AWS).

#### **Example: AWS Secrets Manager Rotation**
```python
# Python client to rotate and fetch new secret
import boto3
from botocore.exceptions import ClientError

def rotate_secret(secret_name):
    client = boto3.client('secretsmanager')
    try:
        response = client.update_secret(
            SecretId=secret_name,
            SecretString='new_password_123'
        )
    except ClientError as e:
        print(f"Error rotating secret: {e}")
```

#### **Clear Caches:**
- **Restart affected services:**
  ```bash
  kubectl rollout restart deployment/my-app
  ```
- **Invalidate caches (Redis, CDN, etc.):**
  ```bash
  redis-cli FLUSHALL  # ⚠️ Use with caution in production
  ```

---

### **Issue 5: Secrets Not Encrypted at Rest**
**Symptoms:**
- Secrets stored in plaintext in databases/filesystems.
- Compliance audits flag unencrypted secrets.

**Root Cause:**
- Missing encryption for secrets in transit/rest.
- Secrets stored in cleartext in local files.

**Fix:**
#### **Encrypt Secrets at Rest:**
- **Use filesystem encryption (LUKS, AWS EBS encryption).**
- **Encrypt secrets in databases:**
  ```sql
  -- PostgreSQL example: Encrypt sensitive columns
  CREATE EXTENSION pgcrypto;
  INSERT INTO users VALUES (1, crypt('password123', gen_salt('bf')));
  ```
- **Use HashiCorp Vault for dynamic secrets:**
  ```bash
  vault kv put secret/db credentials=my_encrypted_password
  ```

#### **Encrypt Secrets in Transit:**
- **Use TLS for all secret transfers (Kubernetes, API calls).**
- **Example: Kubernetes TLS for Secrets:**
  ```yaml
  apiVersion: v1
  kind: Secret
  metadata:
    name: my-tls-secret
  type: kubernetes.io/tls
  data:
    tls.crt: base64-encoded-cert
    tls.key: base64-encoded-key
  ```

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**       | **Purpose**                                                                 | **Example Command/Usage**                          |
|--------------------------|-----------------------------------------------------------------------------|----------------------------------------------------|
| **`docker history`**     | Check for secrets embedded in Docker images.                              | `docker history --no-trunc my-image`               |
| **`trivy image scan`**   | Scan images for hardcoded secrets.                                          | `trivy image --severity HIGH,CRITICAL my-image`    |
| **`kubectl get secrets`**| List Kubernetes Secrets in a namespace.                                   | `kubectl get secrets -n my-namespace`              |
| **`vault kv get`**       | Retrieve secrets from HashiCorp Vault.                                    | `vault kv get secret/db_password`                  |
| **`aws secretsmanager get-secret-value`** | Fetch secrets from AWS Secrets Manager. | `aws secretsmanager get-secret-value --secret-id db-password` |
| **`jq`**                 | Parse JSON logs for secrets (e.g., Kubernetes events).                    | `kubectl get events -o json | jq '.items[].message'` |
| **`grep`/`awk`**         | Search logs for sensitive patterns.                                        | `grep -i "password\|key\|token" /var/log/app.log`|
| **`stern`**              | Stream logs from multiple Pods (Kubernetes).                               | `stern my-app -n my-namespace`                    |
| **`kubectl describe pod`** | Check why a Pod fails to mount secrets.                                   | `kubectl describe pod my-app-pod`                  |
| **`envsubst`**           | Test template injection (e.g., Docker-compose).                            | `envsubst < config.template > config.prod`          |
| **`aws logs tail`**      | Monitor AWS Lambda/ECS logs for secret leaks.                             | `aws logs tail /aws/lambda/my-function --follow`  |
| **`git grep`**           | Find committed secrets in the repo.                                        | `git grep -i "password\|key\|token" --cached`     |

---

## **5. Prevention Strategies**

### **1. Enforce Secrets Management Policies**
- **Never commit secrets to version control.**
  - Use `.gitignore` for `*.env`, `secrets.yaml`.
  - Run `git secrets` to scan for accidental commits.
- **Restrict secret access via IAM roles (AWS) or RBAC (Kubernetes).**
  ```yaml
  # Kubernetes RBAC example
  apiVersion: rbac.authorization.k8s.io/v1
  kind: Role
  metadata:
    name: secret-reader
  rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list"]
  ```

### **2. Automate Secrets Workflow**
- **Use CI/CD pipelines to inject secrets securely.**
  - Example: GitHub Actions with `secrets`:
    ```yaml
    env:
      DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
    ```
- **Rotate secrets periodically (auto-rotation).**
  - Example: AWS Secrets Manager rotation.
  ```bash
  aws secretsmanager schedule-replication-change --source-arn arn:aws:secretsmanager:us-east-1:123456789012:secret:mydb-password
  ```

### **3. Secure Deployment Artifacts**
- **Scan images for secrets before push:**
  ```bash
  trivy image my-image --exit-code 1
  ```
- **Use multi-stage Docker builds to avoid baking secrets into final images.**
  ```dockerfile
  # Stage 1: Build without secrets
  FROM node:18 as builder
  WORKDIR /app
  COPY package*.json ./
  RUN npm install

  # Stage 2: Run with secrets (mounted via buildkit)
  FROM node:18-alpine
  WORKDIR /app
  COPY --from=builder /app .
  RUN --mount=type=secret,id=db_password,target=/run/secrets/db_password \
      npm run build
  ```
- **Sign and verify images (Cosign, Notary).**
  ```bash
  cosign sign --key cosign.key my-image
  ```

### **4. Monitor and Alert on Secret Leaks**
- **Use SIEM tools (Splunk, Datadog) to detect secret exposure.**
  - Example: Alert on `password` in logs.
- **Audit Kubernetes Secrets regularly:**
  ```bash
  kubectl get secrets --all-namespaces -o json > secrets-audit.json
  ```
- **Enable Vault audit logs:**
  ```hcl
  # Vault HCL config
  storage "file" {
    path = "/vault/audit"
  }
  ```

### **5. Educate Teams on Secure Practices**
- **Conduct training on:**
  - Never hardcoding secrets.
  - Using `vault`, `AWS Secrets Manager`, or `Kubernetes Secrets`.
  - Rotating secrets periodically.
- **Run "secret hunt" exercises** to simulate leaks.
- **Document secrets management processes** in runbooks.

### **6. Use Infrastructure as Code (IaC) for Secrets**
- **Define secrets in templates (Terraform, Pulumi).**
  ```hcl
  # Terraform example: Encrypted secrets backend
  terraform {
    backend "s3" {
      bucket         = "my-tf-state"
      key            = "path/to/secrets.tfstate"
      encrypt        = true
      dynamodb_table = "terraform-locks"
    }
  }
  ```
- **Use `sops` to encrypt secrets in configs:**
  ```bash
  sops --encrypt --kms "arn:aws:kms:us-east-1:123456789012:key/abcd1234" secrets.yaml > secrets.encrypted.yaml
  ```

---

## **6. Final Checklist for Secret Security**
| **Task**                          | **Done?** |
|------------------------------------|-----------|
| Secrets are **never hardcoded** in code/configs. | ☐ |
| Secrets are **injected at runtime** (env vars, configs). | ☐ |
| Secrets are **rotated automatically**. | ☐ |
| Secrets are **encrypted at rest**. | ☐ |
| Secrets are **not exposed in logs/artifacts**. | ☐ |
| Secrets are **scanned before deployment**. | ☐ |
| Secrets access is **restricted via IAM/RBAC**. | ☐ |
| Secrets are **monitored for leaks**. | ☐ |
| Team is **trained on secure secrets handling**. | ☐ |

---

## **7. Further Reading**
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [HashiCorp Vault Secrets Management](https://www.vaultproject.io/docs/secrets)
- [Kubernetes Secrets Documentation](https://kubernetes.io/docs/concepts/configuration/secret/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

---
**Debugging secrets in deployment requires discipline, automation, and vigilance. Follow this guide to secure your credentials and prevent leaks. If issues persist, prioritize auditing, tooling, and team training.**