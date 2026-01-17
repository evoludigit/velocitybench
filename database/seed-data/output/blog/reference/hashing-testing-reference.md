# **[Pattern] Hashing Testing Reference Guide**

---

## **Overview**
Hashing Testing is a security-focused pattern used to validate input integrity and detect tampering by comparing a computed hash of input data against a stored or expected value. This pattern is critical in preventing injection attacks, ensuring data consistency, and verifying system-level operations like cryptographic signatures. By leveraging hashing algorithms (e.g., SHA-256, HMAC), this approach guarantees that even minor changes to data will produce a drastically different hash, exposing unauthorized modifications. Common use cases include:
- Validating user input (e.g., API requests).
- Checking file integrity (e.g., checksum verification).
- Securing authentication tokens and session data.

---

## **Key Concepts**
### **Core Principles**
1. **Hashing**: A one-way function that converts input (data, passwords, tokens) into a fixed-size hash value (e.g., `SHA-256("password") = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"`).
2. **Deterministic Output**: The same input always produces the same hash.
3. **Irreversibility**: Hashes are unidirectional (cannot derive the original input from the hash).
4. **Collision Resistance**: Minimal probability of two different inputs producing the same hash.

### **Common Algorithms**
| **Algorithm** | **Use Case**                          | **Security Level**       | **Output Size (bits)** |
|---------------|---------------------------------------|--------------------------|-----------------------|
| SHA-1         | Legacy systems (avoid for new use)   | Weak                    | 160                   |
| SHA-256       | Cryptographic verification           | Strong                  | 256                   |
| SHA-512       | High-security applications           | Very Strong             | 512                   |
| HMAC-SHA256   | Keyed hashing (e.g., authentication)  | Strong                  | 256                   |

---

## **Implementation Details**
### **Schema Reference**
Use the following schema to structure hashing tests in your system:

| **Field**               | **Type**       | **Description**                                                                 | **Example**                                  |
|-------------------------|---------------|---------------------------------------------------------------------------------|---------------------------------------------|
| `input_data`            | `String`      | Raw data to be hashed (e.g., API payload, file content).                          | `"user_id=123&token=abc123"`                |
| `algorithm`             | `Enum`        | Hashing algorithm (e.g., `SHA-256`, `HMAC-SHA256`).                               | `"SHA-256"`                                 |
| `secret_key`            | `String` (opt)| For HMAC: A shared secret used to generate a keyed hash.                         | `"my_super_secret"`                         |
| `expected_hash`         | `String`      | Stored/computed hash value for comparison.                                       | `"5e884898da28047151d0e56f8dc6292773603d0d"` |
| `salt`                  | `String` (opt)| Random data added to input to prevent rainbow table attacks (e.g., passwords).    | `"random_salt_123"`                         |
| `hashing_context`       | `Object` (opt)| Additional metadata (e.g., headers, flags) for context-specific hashing.         | `{ "version": "2.0" }`                      |
| `result`                | `Boolean`     | `true` if `input_data` hash matches `expected_hash`; `false` otherwise.         | `true`                                      |

---

### **Implementation Steps**
1. **Generate a Hash**:
   ```javascript
   import crypto from 'crypto';

   function computeHash(input, algorithm = 'sha256', secretKey = null, salt = '') {
     const data = salt ? Buffer.from(salt + input) : Buffer.from(input);
     const hash = crypto.createHash(algorithm);

     if (secretKey) {
       hash.update(data, 'utf8');
       hash.update(secretKey);
     } else {
       hash.update(data);
     }
     return hash.digest('hex');
   }
   ```

2. **Compare Hashes**:
   ```javascript
   function verifyHash(input, expectedHash, algorithm, secretKey = null, salt = '') {
     const computedHash = computeHash(input, algorithm, secretKey, salt);
     return computedHash === expectedHash;
   }
   ```

3. **Integrate with Testing Frameworks**:
   - **Unit Testing**: Mock inputs and validate hashes using assertions.
     ```javascript
     const assert = require('assert');
     assert.equal(verifyHash("test", "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"), true);
     ```
   - **API Testing**: Use tools like Postman or Newman to send requests and verify response hashes.
   - **CI/CD Pipelines**: Automate hash verification in deployment stages.

---

## **Query Examples**
### **1. Validate API Request Data**
**Use Case**: Ensure no tampering with request payloads.
**Schema**:
```json
{
  "input_data": "user_id=123&token=abc123",
  "algorithm": "HMAC-SHA256",
  "secret_key": "server_key_123",
  "expected_hash": "a1b2c3..."
}
```
**Implementation**:
```javascript
const requestData = "user_id=123&token=abc123";
const hash = computeHash(requestData, "hmac-sha256", "server_key_123");
if (!verifyHash(requestData, "a1b2c3...", "hmac-sha256", "server_key_123")) {
  throw new Error("Tampered request detected!");
}
```

### **2. Check File Integrity**
**Use Case**: Verify downloaded files haven’t been altered.
**Schema**:
```json
{
  "input_data": "file_content...", // Binary or text content of the file
  "algorithm": "SHA-256",
  "expected_hash": "d41d8cd98f00b204e9800998ecf8427e..."
}
```
**Implementation**:
```javascript
const fs = require('fs');
const fileContent = fs.readFileSync('download.zip', 'utf8');
const fileHash = computeHash(fileContent, 'sha256');
if (!verifyHash(fileContent, "d41d8cd98f00b204e9800998ecf8427e...", 'sha256')) {
  console.error("File integrity check failed!");
}
```

### **3. Secure Password Storage**
**Use Case**: Hash passwords with salts to prevent brute-force attacks.
**Schema**:
```json
{
  "input_data": "user_password",
  "algorithm": "SHA-256",
  "salt": "random_salt_123",
  "expected_hash": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824" // hashed "user_password"
}
```
**Implementation**:
```javascript
const password = "user_password";
const salt = generateRandomSalt(); // Use a secure random generator
const storedHash = computeHash(password, 'sha256', null, salt);
verifyHash(password, storedHash, 'sha256', null, salt); // Verify during login
```

---

## **Best Practices**
1. **Use Strong Algorithms**: Prefer SHA-256 or SHA-512 over SHA-1.
2. **Salting**: Always add salts to hashed data (e.g., passwords) to mitigate rainbow table attacks.
3. **Key Management**: For HMAC, securely store and rotate secret keys.
4. **Performance**: Cache hashes when possible to avoid recomputation.
5. **Logging**: Log hash verification failures for auditing (avoid storing raw input data).
6. **Testing**: Include hash testing in unit, integration, and security testing phases.

---

## **Error Handling**
| **Error Scenario**               | **Solution**                                                                 |
|-----------------------------------|------------------------------------------------------------------------------|
| Incorrect algorithm selection     | Validate algorithm compatibility (e.g., HMAC requires a secret key).         |
| Missing secret key (HMAC)        | Return `401 Unauthorized` or reject the request.                            |
| Hash mismatch                     | Log as a potential security incident; deny access or reject the request.    |
| Performance bottlenecks           | Optimize hashing logic (e.g., parallel processing for large files).          |

---

## **Related Patterns**
1. **[Cryptographic Signatures]**
   - Use signatures (e.g., RSA, ECDSA) for non-repudiation alongside hashing.
   - Example: Combine HMAC with digital signatures for API authentication.

2. **[Input Validation]**
   - Pair hashing with strict input validation to reject malformed data early.
   - Example: Validate a user ID before hashing to ensure it meets criteria.

3. **[Secure Token Generation]**
   - Generate time-limited tokens (e.g., JWT) with HMAC hashing for security.
   - Example: Use `HMAC-SHA256` to sign JWT tokens with a shared secret.

4. **[Checksum Verification]**
   - Use lightweight checksums (e.g., CRC32) for non-cryptographic data integrity (e.g., file transfers).

5. **[Rate Limiting for Hashing Endpoints]**
   - Protect hash verification endpoints from brute-force attacks by limiting requests per IP.

---
## **Example Workflow**
1. **Client** sends a request with `input_data` and `expected_hash`.
2. **Server** computes the hash using the provided algorithm/secret.
3. **Server** compares the computed hash with `expected_hash`.
   - If they match: Proceed with the request (e.g., update database).
   - If they don’t match: Reject the request and log the failure.

---
## **Tools & Libraries**
| **Language** | **Library**                          | **Description**                                  |
|--------------|--------------------------------------|--------------------------------------------------|
| JavaScript   | `crypto` (Node.js)                   | Built-in hashing utilities.                      |
| Python       | `hashlib`                            | Supports SHA, HMAC, and other algorithms.        |
| Java         | `java.security.MessageDigest`        | Standard Java hashing framework.                 |
| C#           | `System.Security.Cryptography`       | .NET’s cryptographic services.                   |
| Go           | `crypto/sha256`, `crypto/hmac`       | Efficient hashing utilities.                     |

---
## **Further Reading**
- [OWASP Hashing Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Hashing_Cheat_Sheet.html)
- [NIST Special Publication 800-131A](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131A.pdf) (Recommendations for Hash Functions)
- [HMAC RFC 2104](https://tools.ietf.org/html/rfc2104)