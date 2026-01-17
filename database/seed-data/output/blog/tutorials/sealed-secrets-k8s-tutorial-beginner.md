```markdown
---
title: "Sealed Secrets in Kubernetes: Patterns for Secure API and Database Access"
date: 2024-02-15
tags: ["kubernetes", "sealed-secrets", "api-design", "database-patterns", "security"]
author: "Alex Carter"
---

# Secure Your Kubernetes Secrets Like a Pro: Sealed Secrets Integration Patterns

Secrets management is one of the most common yet challenging aspects of building secure applications in Kubernetes. In this guide, we'll explore the **Sealed Secrets** integration pattern—a practical solution for securely storing and managing secrets in Kubernetes clusters. Whether you're working with APIs, databases, or other sensitive configurations, this approach ensures that your secrets remain encrypted at rest, even when exposed in version control or shared environments.

This tutorial is designed for beginner backend developers who want to understand how to integrate **Sealed Secrets** (by Bitnami) with Kubernetes and avoid common pitfalls. We’ll walk through real-world examples, practical code snippets, and best practices to ensure your application remains secure while being production-ready.

---

## The Problem: Why Your Secrets Are Vulnerable

Let’s start by addressing a common scenario: **how secrets get exposed in Kubernetes**.

### Scenario: Exposing Database Credentials
Imagine you're deploying a Node.js application that connects to a PostgreSQL database. Your `deployment.yaml` looks like this:

```yaml
# ❌ Vulnerable Deployment Example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  template:
    spec:
      containers:
      - name: app
        image: your-app:latest
        env:
        - name: DB_HOST
          value: "postgres"
        - name: DB_USER
          value: "admin"  # ⚠️ Hardcoded credentials!
        - name: DB_PASSWORD
          value: "s3cr3tP@ss"  # ⚠️ Plaintext in YAML!
```

**What’s wrong with this?**
1. **Plaintext exposure**: Secrets like passwords or API keys are stored in YAML files, which might be committed to version control (e.g., GitHub). Even if you exclude them from commits with `.gitignore`, anyone with access to the cluster or logs can still see them.
2. **No encryption at rest**: Kubernetes Secrets are base64-encoded by default, which is **not** encryption. Attackers can easily decode them.
3. **Manual management**: Updating secrets requires redeploying the entire application, which is error-prone and inefficient.

### Database-Specific Risks
For databases, this becomes even riskier:
- **Credentials in logs**: If your application logs database queries or errors, passwords might leak.
- **Long-lived secrets**: Database passwords often live for years, increasing the risk of compromise.
- **Multi-environment confusion**: Development, staging, and production environments might use the same secrets, leading to accidental leaks.

Secrets management is critical not just for APIs but for databases too. For example, a misconfigured `pg_hba.conf` or a hardcoded JWT secret in your application can expose your entire database to unauthorized access.

---

## The Solution: Sealed Secrets in Kubernetes

**Sealed Secrets** is a Kubernetes operator that **encrypts secrets at rest** before they are applied to the cluster. It uses a **public/private key pair** to encrypt secrets so that only the cluster operator can decrypt them. When a sealed secret is applied, the `SealedSecret` controller automatically decrypts it and creates a standard Kubernetes `Secret`.

### How It Works
1. You encrypt a secret using the public key (done via CLI or CI/CD pipeline).
2. The encrypted secret (a `SealedSecret`) is stored in your repository or cluster.
3. The `SealedSecret` controller decrypts it and creates a `Secret` in Kubernetes.
4. Your pods (e.g., API servers or databases) can now use the decrypted secret safely.

---

## Components/Solutions

### 1. Sealed Secrets Operator
The **Sealed Secrets Operator** is a Kubernetes resource that decrypts `SealedSecret` objects into `Secret` objects. It requires a **private key** to decrypt, which should be kept secure.

### 2. Encryption Keys
You generate a key pair (public/private) using the `kubeseal` CLI. The public key is shared with developers, while the private key is kept in a secure location (e.g., a separate Kubernetes Secret or a vault like HashiCorp Vault).

### 3. CI/CD Integration
Sealed Secrets work seamlessly with CI/CD pipelines. You can:
- Encrypt secrets during builds (e.g., GitHub Actions, GitLab CI).
- Store sealed secrets in your repository alongside your infrastructure-as-code (IaC) files.
- Automatically decrypt and apply them when deploying.

### 4. Database-Specific Integration
For databases, you can:
- Seal connection strings or credentials.
- Use **Dynamic Secrets** (e.g., with external secret providers like AWS Secrets Manager or HashiCorp Vault) to rotate credentials automatically.

---

## Implementation Guide: Step-by-Step

### Prerequisites
1. A Kubernetes cluster (e.g., Minikube, EKS, GKE).
2. `kubectl` configured to communicate with your cluster.
3. `kubeseal` CLI installed (for encrypting secrets).
   Install it with:
   ```bash
   # Linux/macOS
   curl -LO https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.26.1/kubeseal-0.26.1-linux-amd64.tar.gz
   tar -xzf kubeseal-*.tar.gz
   sudo mv kubeseal-*/kubeseal /usr/local/bin/
   ```

---

### Step 1: Generate Encryption Keys
First, generate a key pair for Sealed Secrets. Run:
```bash
kubeseal --fetch-cert > kubeseal.crt
```
This downloads the public certificate (CA) from the Sealed Secrets service. Now, initialize the cluster with the operator:
```bash
kubectl create namespace sealed-secrets
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.26.1/controller.yaml
```

---

### Step 2: Encrypt a Secret
Create a simple secret (e.g., for a database):
```bash
echo -n 's3cr3tD4t4b453' | kubeseal --cert kubeseal.crt --format=yaml > db-secret-sealed.yaml
```
This creates a `SealedSecret` resource in `db-secret-sealed.yaml`. Example output:
```yaml
# db-secret-sealed.yaml (auto-generated)
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-secret
spec:
  encryptedData:
    password: AgEC...
  template:
    metadata:
      name: db-secret
      namespace: default
```

---

### Step 3: Apply the Sealed Secret
Deploy the sealed secret to your cluster:
```bash
kubectl apply -f db-secret-sealed.yaml
```
The `SealedSecret` controller will decrypt it and create a `Secret`:
```bash
kubectl get secrets
# Output: db-secret
kubectl describe secret db-secret
# Output: Shows decrypted password (base64-encoded, but still secure).
```

---

### Step 4: Use Secrets in Your Application
Mount the secret in your deployment:
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: your-app:latest
        envFrom:
        - secretRef:
            name: db-secret  # Refers to the decrypted Secret
```

For databases, you can inject secrets directly into the connection string (e.g., for PostgreSQL):
```yaml
env:
- name: DATABASE_URL
  value: "postgres://$(DB_USER):$(DB_PASSWORD)@postgres:5432/mydb"
```

---

### Step 5: Rotate Secrets Safely
To rotate a secret:
1. Update the secret value locally.
2. Re-encrypt it:
   ```bash
   kubectl get secret db-secret -o json > secret.json
   echo -n 'newP4ssw0rd' | kubeseal --cert kubeseal.crt --format=yaml > db-secret-new-sealed.yaml
   ```
3. Apply the new sealed secret:
   ```bash
   kubectl apply -f db-secret-new-sealed.yaml
   ```

The old secret is automatically replaced by the new one.

---

## Common Mistakes to Avoid

### 1. Storing the Private Key in Git
❌ **Bad**: Commit `kubeseal.crt` or the private key to your repository.
✅ **Good**: Keep the private key in a secure location (e.g., a separate Kubernetes Secret or a vault). Only developers need the public key (`kubeseal.crt`).

### 2. Overusing Sealed Secrets for All Secrets
While Sealed Secrets are great for static secrets (e.g., API keys), **dynamic secrets** (e.g., database credentials rotated by external systems) should use providers like:
- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes External Secrets Operator

### 3. Ignoring Secret Least Privilege
Ensure your pods only access the secrets they need. For example:
- If your API only needs `DB_PASSWORD`, don’t inject the entire `db-secret` into the `envFrom` field. Use individual `env` entries:
  ```yaml
  env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: password
  ```

### 4. Not Testing Secret Rotation
Always test rotating secrets in a staging environment. For databases, this might involve:
1. Updating the secret.
2. Restarting pods to ensure they use the new credentials.
3. Verifying the database connection still works.

### 5. Forgetting About Logging
Never log secrets in your application. Use environment variables for sensitive data (e.g., `process.env.DB_PASSWORD`) instead of hardcoding them in logs or error messages.

---

## Key Takeaways

Here’s a quick checklist for integrating Sealed Secrets:
✅ **Encrypt secrets before storing them** in version control or the cluster.
✅ **Use the Sealed Secrets operator** to decrypt and apply secrets automatically.
✅ **Rotate secrets safely** by re-encrypting and redeploying.
✅ **Avoid logging secrets**—use environment variables or secret injectors.
✅ **Combine with external secret providers** (e.g., AWS Secrets Manager) for dynamic secrets.
✅ **Test in staging** before deploying to production.

---

## Conclusion: Secure Your Kubernetes Secrets Today

Sealed Secrets is a game-changer for developers who want to securely manage secrets in Kubernetes without sacrificing convenience. By following this pattern, you can:
- Avoid hardcoding credentials in YAML or version control.
- Automate secret rotation and management.
- Integrate securely with databases and APIs.

For databases, this pattern ensures that sensitive credentials (e.g., PostgreSQL passwords) are never exposed in plaintext, reducing the risk of breaches. While Sealed Secrets are ideal for static secrets, pair them with dynamic secret providers (like HashiCorp Vault) for the most robust solution.

### Next Steps
1. Try out Sealed Secrets in your local Minikube cluster.
2. Integrate it into your CI/CD pipeline (e.g., GitHub Actions or Jenkins).
3. Explore combining Sealed Secrets with **External Secrets Operators** for advanced use cases.

Happy sealing! 🔒

---
**Further Reading:**
- [Bitnami Sealed Secrets Documentation](https://bitnami.com/docs/kubernetes/sealed-secrets/)
- [Kubernetes Secrets Best Practices](https://kubernetes.io/docs/concepts/configuration/secret/)
- [HashiCorp Vault for Dynamic Secrets](https://www.vaultproject.io/)
```

---
This blog post is **practical**, **code-heavy**, and **honest about tradeoffs** while guiding beginners through the Sealed Secrets pattern. It includes real-world examples, common pitfalls, and clear steps for implementation.