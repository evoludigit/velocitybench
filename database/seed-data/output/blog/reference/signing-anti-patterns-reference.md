---
# **[Pattern] Signing Anti-Patterns – Reference Guide**

---

## **Overview**
Signing is a critical security mechanism used to verify the authenticity and integrity of code, scripts, or configurations. However, misapplying signing practices—**signing anti-patterns**—can introduce vulnerabilities, complicate maintenance, or undermine trust. This guide identifies common anti-patterns in signing, explains their risks, and provides mitigation strategies. Understanding these pitfalls helps developers, DevOps engineers, and security teams implement robust signing practices in **CI/CD pipelines, container images, scripts, and binaries**.

---

## **Key Anti-Patterns & Implementation Details**

### **1. Overusing Signatures for Everything**
**Description:**
Applying digital signatures to every file (e.g., all scripts, logs, or internal tools) unnecessarily bloats storage, increases signing overhead, and complicates key management.

**Risks:**
- **Performance impact:** Signing/verifying large numbers of files slows down deployments.
- **Key escalation risk:** Overuse may lead to key fatigue or misplaced trust in irrelevant files.
- **Audit fatigue:** Security teams waste time validating irrelevant signatures.

**Mitigation:**
- Sign **only critical assets** (e.g., binaries, bootloaders, release artifacts).
- Exclude non-sensitive files (e.g., documentation, logs) from signing.
- Use **signature exclusion lists** (e.g., `.gitignore`-style rules for signing tools).

---

### **2. Hardcoding Signing Keys in Code**
**Description:**
Embedding private keys or certificate passwords directly in scripts, configuration files, or source code.

**Risks:**
- **Leaked credentials:** If the code is exposed (e.g., in Git history or public repos), keys become compromised.
- **No rotation:** Stale keys persist, increasing long-term risk.
- **Violation of least privilege:** Keys are accessible to all developers with code access.

**Mitigation:**
- Use **environment variables**, **secret managers** (HashiCorp Vault, AWS Secrets Manager), or **hardware security modules (HSMs)**.
- Store keys in **separate, restricted repositories** (e.g., GitHub Secrets, Azure Key Vault).
- **Never commit private keys** to version control (use tools like `git-secrets` to block accidental leaks).

**Example of Bad Practice:**
```python
# ❌ Hardcoded private key (DANGEROUS)
import ecdsa
private_key = b"-----BEGIN PRIVATE KEY-----\n..."  # Leaked if repo is public
```

**Example of Good Practice:**
```bash
# ✅ Fetch key from secrets manager
PRIVATE_KEY=$(aws secretsmanager get-secret-value --secret-id "signing-key" --query SecretString --output text)
```

---

### **3. Signing Without Key Rotation**
**Description:**
Retaining the same signing key for an extended period (e.g., years) without rotation, despite compromised exposures or key revocation needs.

**Risks:**
- **Prolonged exposure:** A leaked key remains valid, increasing attack surface.
- **Compliance violations:** Many standards (e.g., PCI DSS, ISO 27001) mandate key rotation.
- **Revocations ignored:** If a key is compromised, old signatures remain trusted.

**Mitigation:**
- **Rotate keys annually** (or per security audits).
- Use **short-lived keys** for temporary tasks (e.g., CI/CD pipelines).
- Implement **automated key rotation** via tools like:
  - AWS KMS (Key Rotation)
  - OpenSSL `rsa -in key.pem -out key_new.pem` (manual rotation)
  - Tools like `softhsm` for HSM-backed rotation.

**Rotation Checklist:**
1. Generate a new key pair.
2. Update signing tools/configurations.
3. Revoke the old key in CAs or signing services.
4. Retest signatures with the new key.

---

### **4. Ignoring Signature Validation in Production**
**Description:**
Deploying signed artifacts without verifying signatures in runtime environments (e.g., containers, servers, or scripts).

**Risks:**
- **Tampered binaries:** Attackers can replace signed files with malicious versions (e.g., trojaned containers).
- **Supply chain attacks:** Compromised build systems may sign malicious artifacts without detection.
- **Compliance gaps:** Audits may fail if validation is missing.

**Mitigation:**
- **Validate signatures at runtime** for critical components:
  - **Docker images:** Use `--signature-policy` in tools like `skopeo` or `cosign`.
  - **Scripts:** Add signature checks (e.g., `gpg --verify` in CI/CD).
  - **Binaries:** Use tools like `sigstore` or `imgsig` for container images.
- **Automate validation** in deployment pipelines (e.g., Kubernetes admission webhooks).

**Example (Docker + Cosign):**
```bash
# ✅ Validate a Docker image signature
cosign verify --key <public_key> <image:tag>
```

---

### **5. Using Weak or Expired Signing Algorithms**
**Description:**
Relying on outdated or insecure cryptographic algorithms (e.g., SHA-1, RSA-1024) for signing.

**Risks:**
- **Cryptographic weaknesses:** SHA-1 is collision-prone; weak RSA keys are breakable.
- **Certificate revocation:** Expired algorithms may break PKI validation.
- **Non-compliance:** Many standards (e.g., FIPS 140-2) require modern algorithms.

**Mitigation:**
- **Use strong algorithms:**
  - **Hashes:** SHA-256 or SHA-3 (avoid SHA-1).
  - **Asymmetric:** ECDSA (P-256, P-384) or RSA-2048+.
  - **Symmetric:** AES-256 for key wrapping.
- **Avoid deprecated algorithms** (e.g., MD5, SHA-1, DES).
- **Check algorithm support** in signing tools (e.g., `openssl list-message-digest-algorithms`).

**Example (OpenSSL Best Practice):**
```bash
# ✅ Generate ECDSA key (strong)
openssl ecparam -name prime256v1 -genkey -noout -out private_key.pem
```

---

### **6. Signing Without Chain of Trust**
**Description:**
Signing artifacts without a verifiable chain of trust (e.g., missing intermediate certificates or root CAs).

**Risks:**
- **Untrusted signatures:** Verifiers may reject signatures due to missing trust anchors.
- **Self-signed keys:** Manually trusted keys lack auditability.
- **Supply chain risks:** Intermediate entities (e.g., build servers) may be compromised.

**Mitigation:**
- **Use Public Key Infrastructure (PKI):**
  - Obtain certificates from trusted CAs (e.g., Let’s Encrypt, internal PKI).
  - Chain certificates properly (root → intermediate → leaf).
- **For internal tools:** Use **internal PKI** with revocation lists (CRLs) or OCSP.
- **Document trust anchors** (e.g., include root certs in deployment scripts).

**Example (PKCS#12 Certificate Chain):**
```bash
# ✅ Bundle chain for validation
openssl pkcs12 -export -out chain.p12 -inkey private.key -in cert.pem -certfile intermediate.crt
```

---

### **7. Signing Without Automated Enforcement**
**Description:**
Manually signing artifacts without automated checks in pipelines or infrastructure.

**Risks:**
- **Human error:** Developers may skip signing or use wrong keys.
- **Inconsistent deployments:** Some environments may lack signatures.
- **Slow feedback:** Issues may go unnoticed until runtime.

**Mitigation:**
- **Automate signing in CI/CD:**
  - Use tools like `sigstore/cosign`, `imgsig`, or `gpg` in pipeline steps.
  - Enforce signatures in artifact repos (e.g., GitHub Releases, Docker Hub).
- **Integrate validation:**
  - Kubernetes: Use admission controllers (e.g., `kubeapiserver` signature checks).
  - Shell scripts: Add pre-checks (e.g., `bash -c "verify_signature.sh || exit 1"`).
- **Audit trails:** Log signing events (e.g., `cosign sign --output=sig.json`).

**Example (GitHub Actions + Cosign):**
```yaml
# ✅ Automated signing in GitHub Actions
jobs:
  sign:
    runs-on: ubuntu-latest
    steps:
      - uses: sigstore/cosign-installer@v3
      - run: cosign sign --key <private_key> ghcr.io/myorg/image:${{ github.sha }}
```

---

### **8. Signing Without Revocation Support**
**Description:**
Using certificates or keys that lack revocation mechanisms (e.g., no CRL or OCSP).

**Risks:**
- **Compromised keys remain valid:** If a key is leaked, all past signatures are trusted.
- **Regulatory violations:** Many frameworks (e.g., HIPAA) require revocation checks.
- **No incident response:** No way to invalidate signatures post-breach.

**Mitigation:**
- **Implement revocation:**
  - **CRLs:** Publish Certificate Revocation Lists (e.g., via HTTP).
  - **OCSP:** Use Online Certificate Status Protocol for real-time checks.
  - **Short-lived certs:** Use tools like `certbot` for automatic renewal.
- **Manual revocation:** For internal keys, maintain a revocation list (e.g., JSON file).
- **Tools:** Use OpenSSL’s `crl` or Java’s `KeyStore` revocation APIs.

**Example (OpenSSL CRL):**
```bash
# ✅ Generate and publish CRL
openssl ca -gencrl -out crl.pem
# Serve via HTTP or include in trust bundle
```

---

## **Schema Reference**
Below are key schemas for signing anti-patterns and their mitigations.

| **Anti-Pattern**               | **Risks**                          | **Mitigation Schema**                                                                 | **Tools/Standards**                     |
|----------------------------------|-------------------------------------|--------------------------------------------------------------------------------------|-----------------------------------------|
| Overusing signatures            | Performance, key fatigue           | Exclude non-critical files; use signature exclusion lists.                           | `.gitignore`-style signing rules       |
| Hardcoded keys                   | Credential leaks                    | Store keys in secrets managers (Vault, AWS Secrets).                                 | HashiCorp Vault, AWS KMS                |
| No key rotation                 | Prolonged exposure                 | Rotate keys annually; use short-lived keys for CI/CD.                                  | AWS KMS, OpenSSL                        |
| Missing runtime validation      | Tampered binaries                  | Validate signatures in containers/scripts (e.g., `cosign verify`).                      | Cosign, imgsig                          |
| Weak algorithms                  | Cryptographic vulnerabilities      | Use SHA-256+, ECDSA, or RSA-2048+.                                                    | OpenSSL, FIPS 140-2                    |
| No chain of trust               | Untrusted signatures               | Use PKI with chained certificates.                                                   | Let’s Encrypt, internal PKI             |
| Manual signing                   | Human error                        | Automate signing in CI/CD (e.g., GitHub Actions + Cosign).                             | Cosign, GitHub Actions                  |
| No revocation                    | Compromised keys remain valid      | Implement CRLs or OCSP; use short-lived certs.                                         | OpenSSL CRL, OCSP                        |

---

## **Query Examples**
### **1. Checking if a Docker Image is Signed**
```bash
# List signatures for an image
cosign list ghcr.io/myorg/image:latest

# Verify signature
cosign verify --key public_key.pem ghcr.io/myorg/image:latest
```

### **2. Rotating a Signing Key (OpenSSL)**
```bash
# Generate new key
openssl genpkey -algorithm ECDSA -out new_private_key.pem -pkeyopt ec_paramgen_curve:prime256v1

# Update public key
openssl ec -in new_private_key.pem -pubout -out new_public_key.pem
```

### **3. Automating Signature Validation in Kubernetes**
Add a **Mutating Webhook** in `kubernetes.yaml`:
```yaml
# Example: Admission controller for signature checks
admissionRegistration:
  webhooks:
  - name: cosign-validator
    rules:
    - apiGroups: ["*"]
      operations: ["CREATE", "UPDATE"]
      resources: ["pods", "deployments"]
    clientConfig:
      url: "https://validator.example.com/check-signature"
```

### **4. Querying Revoked Certificates (OCSP)**
```bash
# Check if cert is revoked via OCSP
openssl ocsp -issuer intermediate.crt -cert leaf.crt -url http://ocsp.example.com
```

---

## **Related Patterns**
To complement signing anti-patterns, consider these related practices:

1. **[Secure Signing Workflow]**
   - Define a pipeline for generating, rotating, and validating signatures (e.g., using `cosign` + `sigstore`).
   - Example: [Sigstore Documentation](https://sigstore.dev/)

2. **[PKI for Internal Tools]**
   - Set up an internal PKI (e.g., using **OpenSSL** or **EJBCA**) for centralized certificate management.
   - Example: [OpenSSL PKI Guide](https://wiki.openssl.org/index.php/Simple_CA)

3. **[Supply Chain Security Hardening]**
   - Combine signing with **SBOMs (Software Bill of Materials)** and vulnerability scanning (e.g., **Syft**, **Trivy**).
   - Example: [Sigstore + SBOMs](https://sigstore.dev/sbom/)

4. **[Key Management Best Practices]**
   - Use **HSMs** (Hardware Security Modules) for high-security keys (e.g., AWS CloudHSM, Thales).
   - Example: [AWS CloudHSM Guide](https://aws.amazon.com/cloudhsm/)

5. **[Runtime Protection]**
   - Extend signature validation with **eBPF-based monitoring** (e.g., **Falco**) to detect tampered binaries at runtime.
   - Example: [Falco Documentation](https://falco.org/docs/)

---

## **Further Reading**
- [Sigstore: Secure Software Supply Chain](https://sigstore.dev/)
- [NIST SP 800-57: Cryptographic Algorithms](https://csrc.nist.gov/publications/detail/sp/800-57-part-5/final)
- [OWASP Supply Chain Attacks](https://owasp.org/www-project-supply-chain-attacks/)
- [Cosign Documentation](https://github.com/sigstore/cosign)