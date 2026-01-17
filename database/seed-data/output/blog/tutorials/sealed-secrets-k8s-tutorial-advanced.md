```markdown
---
title: "Sealed Secrets in Kubernetes: Secure Configuration Without Compromising DevOps Flow"
date: "2023-11-15"
author: "Alex Mercer"
description: "A deep dive into Sealed Secrets integration patterns in Kubernetes, covering implementation, best practices, security tradeoffs, and real-world examples."
tags: ["kubernetes", "security", "devops", "sealed-secrets", "backend"]
---

# Sealed Secrets in Kubernetes: Secure Configuration Without Compromising DevOps Flow

As backend engineers, we’re constantly balancing security with operational efficiency. Storing credentials and secrets in plaintext YAML/JSON files in version control is a security misstep waiting to happen. Yet, manually managing secrets at runtime—or worse, hardcoding them in containers—is equally risky and cumbersome. This tension is at the heart of the **"Sealed Secrets"** pattern, a Kubernetes-native solution for securely version-controlling secrets without compromising your CI/CD pipelines.

In this post, we’ll explore how Sealed Secrets works, its integration patterns with Kubernetes, and how to implement it effectively. You’ll learn how to avoid common mistakes while weighing the tradeoffs of this approach. By the end, you’ll have a practical understanding of how to integrate sealed secrets into your workflow, balancing security, automation, and developer experience.

---

## The Problem: Secrets Management in Kubernetes Without Regret

Kubernetes excels at orchestration, but secrets management has historically been an afterthought. Here’s the reality:

1. **Plaintext in Git**: Secrets stored in Kubernetes manifests or CI/CD pipelines are exposed to accidental leaks during pull requests or commits.
   ```yaml
   # Example: Never do this!
   apiVersion: v1
   kind: Secret
   metadata:
     name: db-credentials
   data:
     username: dXNlcm5hbWU=  # "username" base64-encoded
     password: cGFzc3dvcmQ=  # "password" base64-encoded
   ```
   While base64 is not encryption, it’s often mistaken for secure storage.

2. **Runtime Hardcoding**: Injecting secrets directly into containers or pod specs bypasses Kubernetes native tools, leading to:
   - Inconsistencies across environments.
   - Difficulty rotating secrets.
   - Audit log gaps.

3. **Manual Workarounds**: Tools like `kubectl create secret` require managing `.env` files or shell scripts, increasing human error risk and slowing down deployments.

4. **CI/CD Bottlenecks**: Secrets must be injected into pipelines securely, often requiring extra steps like vaulted secrets or manual approvals, slowing down delivery.

5. **Vendored Secrets**: Some teams bake secrets into Docker images or init containers, making secrets immutable and impossible to revoke without rebuilding.

Sealed Secrets solves these problems by providing a **seal/unseal** mechanism that lets you store encrypted secrets in Git, while Kubernetes decrypts them only when needed. The key insight? You get the benefits of version control and automated deployments without sacrificing security.

---

## The Solution: Sealed Secrets Integration Patterns

Sealed Secrets achieves its magic through three core components:

1. **Sealed Secrets Operator**: A Kubernetes custom resource (CRD) that manages sealed secrets.
2. **Seals**: Encrypted representations of secrets, stored in plaintext YAML/JSON in Git.
3. **Unsealing**: Decrypting sealed secrets back into native Kubernetes secrets at runtime.

### How It Works
1. You create a **SealedSecret** (the sealed version) using the `kubeseal` CLI or API.
2. Commit the sealed secret to Git (it’s just base64-encoded encrypted data).
3. The **Sealed Secrets Operator** watches for these and decrypts them into real Secrets when the pods start.
4. Your pods can use these Secrets normally, but the original encrypted form remains in Git.

### Tradeoffs
| **Pros**                          | **Cons**                                      |
|-----------------------------------|-----------------------------------------------|
| Secrets stay in Git safely        | Requires a **secret key** (must be secured)   |
| No runtime secrets in manifests   | Key rotation is manual                        |
| Works with native Kubernetes tools | Operator must be running                     |
| No need for external vaults       | Not suitable for highly dynamic secrets      |

---

## Implementation Guide: Step-by-Step

### Prerequisites
- A Kubernetes cluster (Minikube, EKS, GKE, etc.).
- `kubectl` configured to access your cluster.
- `kubeseal` CLI installed (or access to a private binaries repository).
- `kubectl` access to create CRDs and deploy the operator.

---

### 1. Deploy the Sealed Secrets Operator
First, install the [Sealed Secrets CRD and operator](https://github.com/bitnami-labs/sealed-secrets) using Helm:

```sh
helm repo add sealed-secrets https://charts.bitnami.com/bitnami
helm install sealed-secrets sealed-secrets/sealed-secrets --version 1.11.0
```

Verify the deployment:
```sh
kubectl get pods -n sealed-secrets
# Look for sealed-secrets-controller
```

---

### 2. Encrypt a Secret with `kubeseal`
Generate a sealed secret for your `api-key` (or any secret). Here, we use an ephemeral seal key (not recommended for production):

```sh
# Generate a sealed secret from an existing secret
kubectl create secret generic db-credentials --from-literal=username=admin \
  --from-literal=password=secureP@ssword123 -n default

# Export the secret in YAML
kubectl get secret db-credentials -n default -o yaml > db-secret.yaml

# Encrypt the secret into a SealedSecret
kubeseal --format=yaml < db-secret.yaml | kubectl apply -f -
```

#### Output Example (`sealed-secret.yaml`)
```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-credentials  # Must match the original secret name
  namespace: default
  annotations:
    sealedsecrets.bitnami.com/SealedSecretKey: "-----BEGIN RSA PRIVATE KEY-----...\n-----END RSA PRIVATE KEY-----"
spec:
  encryptedData:
    password: "U2FsdGVkX1+...")
    username: "U2FsdGVkX1+..."
```

- **Key Insight**: The `SealedSecret` is a YAML file with encrypted data. Commit this to Git.

---

### 3. Deploy Your App with the SealedSecret
Your application can now reference the original secret name (`db-credentials`). The operator decrypts it as needed.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: my-app
        image: my-app:latest
        envFrom:
        - secretRef:
            name: db-credentials  # The sealed secret will be decrypted
```

---

### 4. Secret Rotation
To rotate a secret, update the original secret, then re-encrypt it with `kubeseal` and redeploy the sealed secret. The operator will automatically update the live Secrets.

---

## Best Practices

### 1. Use a Dedicated Secret Key
Never use an ephemeral key in production. Instead, use a cluster-wide seal key stored in Kubernetes Secrets:

```sh
# Create a sealed secret for the key
kubeseal --format=yaml --cert key.crt --key key.key < key-secret.yaml | kubectl apply -f -
```

### 2. Audit Regularly
Run `kubectl get sealedsecrets` periodically to ensure no stale sealed secrets exist.

### 3. Integrate with CI/CD
Use `kubeseal` in your CI pipeline to encrypt secrets in a secret step:
```yaml
# Example GitHub Actions step
- name: Encrypt secrets
  run: |
    kubeseal --cert=sealed-secrets-key.crt --key=sealed-secrets-key.key < db-secret.yaml > sealed-db-secret.yaml
    echo "sealed-db-secret.yaml" >> $GITHUB_STEP_SUMMARY
    git add sealed-db-secret.yaml
```

### 4. Leverage Image Signing
If your app is containerized, add `imagePolicyWebhook` to enforce only images signed with your private key can access secrets.

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Ignoring Key Rotation
If you lose or compromise your seal key, all secrets are inaccessible. Always rotate keys periodically and back up the private key securely.

### ❌ Mistake 2: Overcomplicating the Seal Key Storage
Avoid storing the private key in multiple places (e.g., Git, cloud storage). Use a restricted Kubernetes Secret with RBAC permissions.

### ❌ Mistake 3: Using `kubectl create secret` Directly
Always seal secrets before committing them to Git. Mixing sealed and direct secrets leads to inconsistency.

### ❌ Mistake 4: Forgetting to Clean Up
Sealed secrets persist even after deleting the original secret. Explicitly delete sealed secrets when updating them.

---

## Key Takeaways
- **Sealed Secrets** lets you store encrypted secrets in Git without exposing them in plaintext.
- The **operator** decrypts secrets only when needed at runtime.
- **Seal keys** must be protected—rotate them and avoid ephemeral keys in production.
- **CI/CD integration** is seamless; just encrypt secrets before merging.
- **Audit regularly** to avoid stale or orphaned sealed secrets.

---

## Conclusion

Sealed Secrets is a pragmatic solution for teams that want to version-control Kubernetes secrets without sacrificing security. By integrating it into your DevOps workflow, you can automate deployments while keeping your secrets safe. The tradeoffs (like key management) are manageable with proper tooling and processes.

For advanced use cases, consider combining Sealed Secrets with HashiCorp Vault or AWS Secrets Manager for dynamic secrets. But for most teams, this pattern provides an elegant balance of security and operational efficiency.

**Next Steps:**
1. Try encrypting a demo secret with `kubeseal`.
2. Experiment with rotating a sealed secret and verifying the operator updates the live secret.
3. Explore integrating Sealed Secrets into your CI/CD pipeline.

Happy sealing!
```

---
**GitLab CI Example** (for reference):
```yaml
stages:
  - prepare
  - deploy

prepare-secrets:
  stage: prepare
  script:
    - kubeseal --cert=${SEAL_CERT} --key=${SEAL_KEY} < db-secret.yaml > sealed-db-secret.yaml
    - git add sealed-db-secret.yaml

deploy:
  stage: deploy
  script:
    - kubectl apply -f sealed-db-secret.yaml
```