# **[Pattern] Reference Guide: Signing Approaches**

---

## **1. Overview**
This reference guide outlines the **Signing Approaches** pattern—a structured method for securely validating transactions, documents, or API requests using cryptographic signatures. Signing ensures data integrity, authenticity, and non-repudiation by proving that a message or document originated from a trusted source and was not altered in transit.

The pattern defines **three core approaches**:
- **Pre-Signing (Static Keys)** – Signs data before deployment using a static private key.
- **Post-Signing (Dynamic Keys)** – Generates ephemeral signatures per request using temporary keys.
- **Chain Signing** – Combines multiple signatures (e.g., a private key + a timestamp authority) for hierarchical validation.

This guide covers **schema requirements, query parameters, implementation best practices, and related patterns** for each approach.

---

## **2. Schema Reference**

| **Component**               | **Description**                                                                                     | **Fields**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Signing Metadata**        | Metadata required for signature validation.                                                         | `algorithm` (str, e.g., `"ES256"`), `key_id` (str, e.g., `"user-123"`), `timestamp` (ISO 8601)  |
| **Pre-Signing Schema**      | Static key-based signing (e.g., RSA, ECDSA)                                                         | `private_key` (str, PEM/hex), `public_key` (str, PEM/hex), `signature` (str, hex)            |
| **Post-Signing Schema**     | Ephemeral key signing (e.g., JWT, EdDSA)                                                            | `ephemeral_key` (str, base64-encoded), `ephemeral_signature` (str, hex), `expiry` (timestamp) |
| **Chain Signing Schema**    | Multi-signature validation (e.g., timestamp authority + private key)                                | `level_1_signature` (str, hex), `level_2_signature` (str, hex), `authority_key` (str, PEM)    |
| **Validation Response**     | Output when validating a signature                                                                | `is_valid` (bool), `errors` (list, optional), `validated_by` (str, e.g., `"authority-456"`)      |

---

## **3. Query Examples**

### **3.1 Pre-Signing (Static Keys)**
**Use Case:** Securely sign a contract before deployment.
**Request:**
```http
POST /v1/signatures/pre-signed
Content-Type: application/json

{
  "data": "SigB8hY...",  # Base64-encoded payload
  "algorithm": "ES256",
  "private_key": "-----BEGIN PRIVATE KEY-----\n..."

}
```
**Response (Success):**
```json
{
  "signature": "3a4b5c...",
  "timestamp": "2023-10-25T12:00:00Z"
}
```

**Validation Query:**
```http
POST /v1/signatures/validate
Content-Type: application/json

{
  "data": "SigB8hY...",
  "signature": "3a4b5c...",
  "public_key": "-----BEGIN PUBLIC KEY-----..."
}
```
**Response:**
```json
{
  "is_valid": true,
  "validated_by": "root-authority-1"
}
```

---

### **3.2 Post-Signing (Dynamic Keys)**
**Use Case:** Sign a dynamic token (e.g., OAuth2) per request.
**Request:**
```http
POST /v1/signatures/ephemeral
Content-Type: application/json

{
  "data": "eyJhbGciOiJ...",
  "algorithm": "EdDSA"
}
```
**Response:**
```json
{
  "ephemeral_key": "base64:KJhG...",
  "ephemeral_signature": "hex:5f7a8b...",
  "expiry": "2023-10-25T12:15:00Z"
}
```

**Validation Query:**
```http
POST /v1/signatures/validate-dynamic
Content-Type: application/json

{
  "data": "eyJhbGciOiJ...",
  "ephemeral_key": "base64:KJhG...",
  "signature": "hex:5f7a8b..."
}
```
**Response:**
```json
{
  "is_valid": true,
  "expiry_remaining": "300s"
}
```

---

### **3.3 Chain Signing**
**Use Case:** Validate a document signed by both a private key and a timestamp authority.
**Request:**
```http
POST /v1/signatures/chain-validate
Content-Type: application/json

{
  "data": "ContractV1...",
  "level_1_signature": "hex:1a2b3c...",  # User's signature
  "level_2_signature": "hex:4d5e6f...",  # Timestamp authority's seal
  "authority_key": "-----BEGIN PUBLIC KEY-----..."
}
```
**Response:**
```json
{
  "is_valid": true,
  "chain_depth": 2,
  "validated_at": "2023-10-25T12:30:00Z"
}
```

---

## **4. Implementation Details**

### **4.1 Key Requirements**
- **Cryptographic Standards:**
  - Pre-Signing: **RSA, ECDSA (P-256/P-384)**.
  - Post-Signing: **EdDSA (Ed25519), HMAC-SHA256**.
  - Chain Signing: **Must support timestamp authorities** (RFC 3161-compliant).
- **Key Management:**
  - Store **private keys** in HSMs (Hardware Security Modules) or encrypted vaults.
  - Rotate keys periodically (e.g., monthly for ephemeral keys).

### **4.2 Validation Logic**
| **Approach**       | **Validation Steps**                                                                                     |
|--------------------|---------------------------------------------------------------------------------------------------------|
| **Pre-Signing**    | 1. Recover public key from `private_key`.<br>2. Verify signature using `algorithm` and `public_key`. |
| **Post-Signing**   | 1. Check `expiry` timestamp.<br>2. Verify `ephemeral_signature` using the provided `ephemeral_key`.   |
| **Chain Signing**  | 1. Validate `level_1_signature` with the user’s public key.<br>2. Validate `level_2_signature` with the authority’s key. |

### **4.3 Error Handling**
| **Error Code** | **Description**                                                                                     | **Example Response**                                                                 |
|-----------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| `INVALID_SIG`   | Signature mismatch or corrupted payload.                                                          | `{ "errors": ["Signature failed verification"] }`                                       |
| `KEY_REVOKED`   | Signing key has been revoked.                                                                     | `{ "errors": ["Key user-123 is revoked"] }`                                             |
| `EXPIRED_SIG`   | Ephemeral signature expired.                                                                    | `{ "errors": ["Signature expired at 2023-10-25T12:00:00Z"] }`                           |
| `UNSUPPORTED_ALGO` | Unsupported cryptographic algorithm (e.g., SHA1).                                                 | `{ "errors": ["Algorithm 'SHA1' is deprecated"] }`                                      |

---

## **5. Related Patterns**
1. **[Two-Factor Authentication (2FA)]**
   - Combines signing with TOTP/HOTP for enhanced security.

2. **[Zero-Knowledge Proofs (ZKP)]**
   - Use signing + ZKP for privacy-preserving validation (e.g., blockchain transactions).

3. **[Rate Limiting + Signing]**
   - Validate signatures while enforcing request quotas to prevent abuse.

4. **[Cryptographic Time Stamping]**
   - Extend chain signing with RFC 3161 timestamps for legal compliance.

5. **[API Gateway Authentication]**
   - Embed signatures in JWT tokens for service-to-service auth.

---

## **6. Best Practices**
- **For Pre-Signing:**
  - Use **short-lived static keys** (e.g., 90-day rotation).
  - Store keys in **separate secure environments** (e.g., AWS KMS, HashiCorp Vault).

- **For Post-Signing:**
  - Generate ephemeral keys **server-side** (avoid client-side risks).
  - Cache ephemeral keys with **short TTLs** (e.g., 5 minutes).

- **For Chain Signing:**
  - Audit timestamp authorities regularly.
  - Log all chain validation events for compliance.

---
**Last Updated:** `2023-10-25`
**Version:** `1.3`