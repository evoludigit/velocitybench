# **Debugging Sealed Secrets Kubernetes Integration: A Troubleshooting Guide**

Sealed Secrets is a popular tool for securing Kubernetes secrets by encrypting them outside the cluster, ensuring that only the Kubernetes API server can decrypt them. While this pattern improves security, misconfigurations can lead to **performance bottlenecks, reliability issues, or scalability challenges**. This guide will help diagnose and resolve common problems efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, verify the following symptoms:

| **Symptom** | **Description** | **Possible Cause** |
|-------------|----------------|-------------------|
| **Failed Pod Deployments** | Pods fail to start with errors like `Failed to fetch secret`, `Permission Denied`, or `InvalidSealedSecret` | Incorrect RBAC, missing CA certs, or misconfigured `SealedSecretController` |
| **High CPU/Memory Usage** | `SealedSecretController` consumes excessive resources | Misconfigured replication controller, too many secrets being processed |
| **Slow Secret Decryption** | Long delays in secret decryption or pod startup | Insufficient decryptor pod replicas, slow external key management (EKS, Vault) |
| **Secrets Not Being Decrypted** | Secrets remain in `SealedSecret` form; plaintext secrets never appear | Incorrect `SealedSecret` annotations, missing `kubernetes.io/sealed-secrets` label |
| **RBAC Errors** | `forbidden` errors when applying sealed secrets | Missing `SealedSecretController` RBAC roles or incorrect `ServiceAccount` bindings |
| **External Key Rotation Issues** | Secrets fail to decrypt after key rotation | Outdated CA certs, misconfigured `external-secrets` or `cluster-secret` backends |
| **Network Latency in Decryption** | High latency when fetching secrets from external systems (Vault, HashiCorp KMS) | Network timeouts, misconfigured proxy settings, or slow external service |

---

## **2. Common Issues and Fixes**

### **Issue 1: Sealed Secrets Not Being Decrypted**
**Symptoms:**
- Pods fail with `Failed to fetch secret: secrets "my-secret" not found`
- `kubectl get sealedsecret` shows sealed secrets but no corresponding Kubernetes secrets

**Root Cause:**
- Missing `kubernetes.io/sealed-secrets` annotation
- Incorrect `SealedSecret` controller configuration
- Decryptor pods not running or misconfigured

**Debugging Steps & Fixes:**

#### **Check if the SealedSecret Controller is Running**
```sh
kubectl get pods -n sealed-secrets
```
- If missing, apply the controller:
  ```sh
  kubectl apply -f https://github.com/bitnami/sealed-secrets/releases/latest/download/controller.yaml
  ```

#### **Verify the SealedSecret CRD is Present**
```sh
kubectl get crd sealedsecrets.bitnami.com
```
- If missing, install the CRD:
  ```sh
  kubectl apply -f https://github.com/bitnami/sealed-secrets/releases/latest/download/crd.yaml
  ```

#### **Check the SealedSecret YAML for Correct Annotations**
Example of a **well-formatted** `SealedSecret`:
```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: my-secret
  namespace: my-app
spec:
  encryptedData:
    username: <base64-encrypted-data>
    password: <base64-encrypted-data>
  template:
    metadata:
      labels:
        app: my-app
    type: Opaque
```
✅ **Fix:** Ensure the correct annotations and encrypted data are present.

---

### **Issue 2: RBAC Errors Preventing Decryption**
**Symptoms:**
- `forbidden: User "system:serviceaccount:default:sealed-secrets" cannot list sealedsecrets.bitnami.com`
- Pods fail with `Permission denied`

**Root Cause:**
- Missing or incorrect `Role`/`ClusterRole` bindings
- `ServiceAccount` not properly linked to the controller

**Debugging Steps & Fixes:**

#### **Check RBAC Roles**
```sh
kubectl get roles -n sealed-secrets
kubectl get clusterroles -n sealed-secrets
```
- Ensure the `SealedSecretController` has the correct permissions:
  ```yaml
  apiVersion: rbac.authorization.k8s.io/v1
  kind: Role
  metadata:
    name: sealed-secret-reader
    namespace: sealed-secrets
  rules:
  - apiGroups: ["bitnami.com"]
    resources: ["sealedsecrets"]
    verbs: ["get", "list", "watch"]
  ```

#### **Verify ServiceAccount Bindings**
```sh
kubectl get serviceaccount sealed-secrets-controller -n sealed-secrets
kubectl describe rolebinding sealed-secret-reader -n sealed-secrets
```
✅ **Fix:** Ensure the `ServiceAccount` is bound to the correct `Role`/`ClusterRole`.

---

### **Issue 3: Performance Bottlenecks (High CPU/Memory Usage)**
**Symptoms:**
- `SealedSecretController` pods consume **>50% CPU**
- Slow secret decryption (~10s+ delay)

**Root Cause:**
- Too many secrets being processed at once
- External key provider (Vault, AWS KMS) is slow
- Insufficient `SealedSecretController` replicas

**Debugging Steps & Fixes:**

#### **Scale Up the SealedSecretController**
```yaml
spec:
  replicas: 3  # Default is 1; increase if under heavy load
```
Apply with:
```sh
kubectl apply -f sealed-secrets-controller.yaml
```

#### **Check External Key Provider Latency**
If using **Vault or HashiCorp KMS**, verify:
- Network connectivity (`kubectl exec -it <pod> -- curl -v vault.example.com`)
- Vault token permissions (ensure `kubernetes` auth method is correctly configured)
- KMS API throttling limits

✅ **Fix:** Optimize external key provider settings or switch to **local encryption (AEAD)** if possible.

---

### **Issue 4: Secrets Not Updating After Key Rotation**
**Symptoms:**
- Secrets decrypt successfully initially but fail after key rotation
- Errors like `x509: certificate has expired`

**Root Cause:**
- Outdated **CA bundle** in the decryptor
- Missing **refresh mechanism** for external secrets

**Debugging Steps & Fixes:**

#### **Check CA Certificate Validity**
```sh
kubectl exec -it sealed-secrets-controller-xxx -n sealed-secrets -- openssl x509 -in /etc/sealed-secrets/ca.pem -text -noout
```
✅ **Fix:** Update the CA bundle:
```sh
kubectl patch secret sealed-secrets-controller -n sealed-secrets --type='json' -p='[{"op": "replace", "path": "/data/ca.pem", "value": "<new-ca-crt-base64>"}]'
```

#### **Use External Secrets Operator for Dynamic Updates**
If using **Vault**, ensure the `ExternalSecret` controller syncs keys:
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: vault-secrets
spec:
  refreshInterval: "1h"  # Auto-refresh every hour
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: my-secret
```

---

## **3. Debugging Tools and Techniques**

### **Logging & Metrics**
- **Check controller logs:**
  ```sh
  kubectl logs sealed-secrets-controller-xxx -n sealed-secrets -f
  ```
- **Enable Prometheus metrics** (if using `kubectl metrics`):
  ```yaml
  # Add to sealed-secrets-controller Deployment
  resources:
    limits:
      cpu: "1"
      memory: "512Mi"
  ```

### **Network Diagnostics**
- **Test external key provider connectivity:**
  ```sh
  kubectl exec -it sealed-secrets-controller-xxx -n sealed-secrets -- curl -v https://vault.example.com/v1/secret/data/my-secret
  ```
- **Check DNS resolution:**
  ```sh
  kubectl exec -it sealed-secrets-controller-xxx -n sealed-secrets -- nslookup vault.example.com
  ```

### **Debugging `kubectl` Commands**
- **Verify sealed secret decryption manually:**
  ```sh
  kubectl get sealedsecret my-secret -o yaml | yq '.spec.encryptedData' > encrypted_data.yaml
  kubectl sealed-secrets decrypt --config sealed-secrets-controller.yaml encrypted_data.yaml
  ```

---

## **4. Prevention Strategies**

### **Best Practices for Sealed Secrets**
✅ **Use Local Encryption (AEAD) When Possible**
- Avoid external dependencies (Vault, KMS) for high-performance setups.
- Example:
  ```yaml
  sealed-secrets-controller:
    spec:
      encryption:
        local: true
  ```

✅ **Optimize Replica Count**
- Set `replicas: 3` if processing **>100 secrets/sec**.

✅ **Use `ExternalSecret` for Dynamic Key Rotation**
- Integrate with **HashiCorp Vault** or **AWS Secrets Manager** for auto-updates.

✅ **Monitor Controller Health**
- Set up **Prometheus + Alertmanager** to alert on high CPU/memory.

✅ **Test Failover Scenarios**
- Simulate CA expiration and verify **automatic rollover**.

---

## **5. Final Checklist for Resolution**
| **Step** | **Action** | **Expected Result** |
|----------|------------|---------------------|
| ✅ RBAC Check | Verify `Role`/`ClusterRole` | No `forbidden` errors |
| ✅ Controller Health | `kubectl get pods -n sealed-secrets` | All pods `Running` |
| ✅ Secret Decryption | `kubectl get sealedsecret` → `kubectl get secret` | Plaintext secret appears |
| ✅ Performance Test | Benchmark decryption time | <2s latency |
| ✅ Key Rotation Test | Rotate CA/Vault key | Secrets decrypt successfully |

---

## **Conclusion**
Sealed Secrets is a powerful but **configuration-sensitive** pattern. Most issues stem from **RBAC misconfigurations, missing CA certificates, or external key provider delays**. By following this guide, you should be able to:
✔ Quickly diagnose **failed decryptions**
✔ Optimize **performance bottlenecks**
✔ Prevent **scalability issues**
✔ Ensure **secure key rotation**

If problems persist, check the [Bitnami Sealed Secrets GitHub](https://github.com/bitnami/sealed-secrets) for updates and community discussions. For production environments, consider **monitoring with Prometheus + Grafana** for real-time insights.