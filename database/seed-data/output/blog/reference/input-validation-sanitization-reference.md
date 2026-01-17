# **[Pattern] Input Validation & Sanitization: Reference Guide**

---
## **Overview**
Input Validation & Sanitization is a critical security pattern designed to mitigate injection attacks (e.g., SQL, NoSQL, HTML, XSS, OS, or LDAP injection) and other malicious input-based vulnerabilities. This pattern ensures that user-provided data adheres to expected formats, is free of malicious payloads, and is properly escaped or transformed before processing. By enforcing strict validation rules and sanitizing inputs, systems can prevent unauthorized code execution, data corruption, and data breaches. The pattern combines **validation** (checking input against defined rules) and **sanitization** (removing or escaping harmful characters) to create a robust defense layer against injection attacks and malformed data.

---

## **Key Concepts**
The pattern relies on three foundational principles:

| **Concept**         | **Definition**                                                                                                                                                     | **Example**                                                                                     |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Validation**       | Verifying input against predefined rules (e.g., length, type, format, presence of allowed characters) to ensure correctness.                                      | Rejecting a username with special characters (`@#$`) if only alphanumeric are allowed.       |
| **Sanitization**     | Removing or escaping dangerous characters (e.g., `<`, `>`, `;`, `'` for SQL injection) or transforming input to neutralize threats.                              | Escaping `<script>` in user comments to prevent XSS.                                            |
| **Whitelisting**     | Only allowing explicitly permitted characters or formats (more secure than blacklisting).                                                              | Permitting only `A-Z`, `a-z`, `0-9`, and `-` in usernames.                                     |
| **Defense in Depth** | Combining validation, sanitization, and application-level protections (e.g., ORM queries, parameterized statements).                                            | Using prepared statements alongside input validation.                                          |
| **Context Awareness**| Treating input differently based on its use case (e.g., database queries vs. HTML output).                                                                | Escaping SQL for queries but not HTML for display.                                               |

---

## **Implementation Details**
### **1. Validation Strategies**
Validate inputs against these rules:
- **Presence**: Input must exist (e.g., non-empty required fields).
- **Type**: Correct data type (e.g., integer for age, email for email fields).
- **Format**: Compliance with patterns (e.g., `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$` for emails).
- **Length**: Minimum/maximum character limits.
- **Whitelist**: Only allow predefined characters (e.g., `[A-Za-z0-9]` for usernames).
- **Blacklist (if necessary)**: Prohibit known malicious patterns (e.g., SQL keywords like `DROP TABLE`).

**Tools/Libraries**:
- **Regex**: For format validation (e.g., `/^\d{3}-\d{2}-\d{4}$/` for SSNs).
- **Built-in APIs**: Use language-specific validators (e.g., Python’s `re`, JavaScript’s `isValidEmail()`).
- **Third-party**: Libraries like [OWASP ESAPI](https://owasp.org/www-project-enterprise-security-api/), [Express Validator](https://express-validator.github.io/) (Node.js), or [Java Validator](https://beanvalidation.org/).

---

### **2. Sanitization Techniques**
Sanitize inputs based on their context:

| **Context**          | **Sanitization Method**                                                                                     | **Example**                                                                                     |
|----------------------|-------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **SQL Database**     | Escape special characters or use **prepared statements** (parameterized queries).                        | `SELECT * FROM users WHERE username = ?` (instead of concatenating input).                     |
| **HTML Output**      | Escape HTML entities (`&`, `<`, `>`, `"`, `'`).                                                         | Convert `<script>` to `&lt;script&gt;`.                                                         |
| **URLs**             | Encode special characters (e.g., spaces to `%20`, `/` to `%2F`).                                          | `http://example.com/search?q=query with%20spaces`.                                            |
| **XML**              | Escape XML tags (`<`, `>`, `&`, `"`, `'`).                                                               | Convert `<root><user>admin</user></root>` to valid XML.                                        |
| **LDAP**             | Escape LDAP-specific characters (e.g., `*` for wildcards).                                               | Escape `*admin*` to `\*admin\*`.                                                               |
| **Command Injection**| Restrict shell commands to whitelisted paths or use safe alternatives (e.g., `exec()` in Python).       | Reject `rm -rf /` or use `os.system()` with caution.                                           |

**Tools/Libraries**:
- **SQL**: ORMs (e.g., SQLAlchemy, Hibernate), ORM frameworks, or libraries like [SQL Injection Kit](https://github.com/atnos/orm_sql_injection_kit).
- **HTML**: [DOMPurify](https://github.com/cure53/DOMPurify) (JavaScript), [htmlpurifier](https://github.com/HTMLPurifier/HTMLPurifier) (PHP).
- **General**: [OWASP Java Encoder](https://owasp.org/www-community/OWASP_Java_Encoder_Project), [Python `html.escape()`](https://docs.python.org/3/library/html.html#html.escape).

---

### **3. Schema Reference**
Define validation rules per input field using this schema:

| **Field**       | **Type**       | **Rules**                                                                                     | **Example Valid Input**       | **Example Invalid Input** |
|-----------------|----------------|-----------------------------------------------------------------------------------------------|--------------------------------|---------------------------|
| `username`      | `string`       | Length: 3–20, whitelist: `[A-Za-z0-9_]`                                                         | `john_doe123`                   | `john@doe`, `john#doe`    |
| `email`         | `string`       | Format: `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$`                                   | `user@example.com`             | `user@example`            |
| `password`      | `string`       | Length: 8+, contains at least 1 uppercase, 1 lowercase, 1 number, 1 special char.           | `Passw0rd!`                    | `password`, `Pass123`      |
| `age`           | `integer`      | Range: 0–120                                                                                   | `25`                            | `-5`, `abc`               |
| `search_query`  | `string`       | Length: ≤100, blacklist: SQL keywords (`DROP`, `UNION`)                                          | `how to cook pasta`            | `DROP TABLE users`        |
| `file_upload`   | `file`         | Whitelist extensions: `.jpg`, `.png`, size: ≤5MB                                              | `image.jpg`                     | `script.py`, `big_file.zip`|

---

### **4. Query Examples**
#### **Validation Example (Python with `re`)**
```python
import re

def validate_email(email):
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return bool(re.fullmatch(pattern, email))

# Usage
print(validate_email("user@example.com"))  # True
print(validate_email("user@example"))      # False
```

#### **Sanitization Example (SQL Injection Prevention)**
**Unsafe (Concatenation):**
```sql
-- Vulnerable to SQL injection
query = "SELECT * FROM users WHERE username = '" + user_input + "';"
```

**Safe (Prepared Statement):**
```python
# Using SQLAlchemy (Python)
from sqlalchemy import text

query = text("SELECT * FROM users WHERE username = :username")
result = db.session.execute(query, {"username": user_input})
```

#### **Sanitization Example (HTML Escaping)**
**Unsafe (Raw Input):**
```html
<!-- XSS vulnerability -->
<p>{{ user_input }}</p>
```

**Safe (Escaped):**
```python
# Python
from html import escape
safe_html = escape(user_input)
<p>{{ safe_html }}</p>
```

---

## **Requirements & Best Practices**
1. **Validate on the Server Side**:
   - Never rely solely on client-side validation (e.g., JavaScript). Always validate and sanitize server-side.

2. **Use Whitelisting Over Blacklisting**:
   - Whitelists are more secure because they explicitly allow only safe characters/patterns.

3. **Escape Contextually**:
   - Apply the appropriate escape function based on the output context (SQL, HTML, XML, etc.).

4. **Fail Securely**:
   - Reject invalid inputs with clear error messages (avoid leaking system details).

5. **Log Suspicious Activity**:
   - Monitor failed validations/sanitizations for potential attacks.

6. **Update Libraries Regularly**:
   - Keep validation/sanitization libraries (e.g., `htmlpurifier`, `express-validator`) up to date for patches.

7. **Defense in Depth**:
   - Combine validation, sanitization, and application-layer protections (e.g., ORMs, input filters).

8. **Test with Fuzz Testing**:
   - Use tools like [OWASP ZAP](https://www.zaproxy.org/) or [sqlmap](https://sqlmap.org/) to test for injection vulnerabilities.

9. **Document Assumptions**:
   - Clearly document expected input formats and validation rules for developers.

10. **Avoid Dynamic Code Execution**:
    - Never use `eval()`, `system()`, or `exec()` with untrusted input.

---

## **Query Examples for Common Use Cases**
### **1. Validating and Sanitizing User Input for a Login Form**
```python
import re

def validate_login(username, password):
    # Validation
    if not re.fullmatch(r'^[A-Za-z0-9_]{3,20}$', username):
        raise ValueError("Invalid username format.")
    if not re.fullmatch(r'^(?=.*[A-Z])(?=.*\d).{8,}$', password):
        raise ValueError("Password must be 8+ chars with uppercase and number.")

    # Sanitization (e.g., trim whitespace)
    username = username.strip()

    # Proceed with login logic
    return True
```

### **2. Sanitizing HTML for Display**
```python
# JavaScript (DOMPurify)
const cleanHtml = DOMPurify.sanitize(userInput);
document.body.innerHTML = cleanHtml;
```

### **3. Preventing SQL Injection in a Comment System**
```python
# Python with SQLAlchemy
from sqlalchemy import text

def save_comment(comment):
    # Validate length
    if len(comment) > 1000:
        raise ValueError("Comment too long.")

    # Sanitize (escape if needed; ORM handles this automatically)
    query = text("INSERT INTO comments (text) VALUES (:text)")
    db.session.execute(query, {"text": comment})
    db.session.commit()
```

### **4. Whitelisting File Uploads**
```python
ALLOWED_EXTENSIONS = {'.jpg', '.png', '.gif'}

def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Usage
if not is_allowed_file(user_uploaded_file.name):
    raise ValueError("Invalid file type.")
```

---

## **Error Handling**
| **Scenario**               | **Action**                                                                                         |
|----------------------------|--------------------------------------------------------------------------------------------------|
| Invalid input (validation) | Return HTTP 400 Bad Request with a generic message (e.g., "Invalid input").                     |
| Sanitization failure       | Log the error and reject the input (e.g., "Malformed payload detected.").                      |
| Rate-limiting exceeded     | Return HTTP 429 Too Many Requests.                                                               |
| Suspicious activity        | Log details (without exposing system info) and flag for review.                                |

---
## **Related Patterns**
1. **[Authentication & Authorization](https://docs.oasis-open.org/security/ws-trust/200512/ws-trust-core-1.3-os.pdf)**
   - Works with Input Validation to ensure only authenticated users submit valid inputs.

2. **[Rate Limiting & Throttling](https://cheatsheetseries.owasp.org/cheatsheets/Rate_Limiting_Cheat_Sheet.html)**
   - Complements Input Validation by limiting attempts for malicious inputs.

3. **[ORM & Parameterized Queries](https://docs.sqlalchemy.org/en/14/orm/query.html)**
   - Provides built-in protection against SQL injection when combined with validation.

4. **[Content Security Policy (CSP)](https://content-security-policy.com/)**
   - Mitigates XSS by restricting sources of scripts and other resources.

5. **[Logging & Monitoring](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)**
   - Helps detect and respond to validation/sanitization failures.

6. **[Secure Coding Guidelines](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_in_Java.html)**
   - Provides broader best practices for secure software development.

7. **[Web Application Firewall (WAF)](https://www.cloudflare.com/learning/waf/what-is-a-web-application-firewall/)**
   - Acts as an additional layer of defense for unvalidated inputs.

---
## **Further Reading**
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [OWASP Sanitization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html#prepared-statements)
- [CWE-20: Improper Input Validation](https://cwe.mitre.org/data/definitions/20.html)
- [CWE-79: Improper Neutralization of Input During Web Page Generation (Cross-site Scripting)](https://cwe.mitre.org/data/definitions/79.html)

---
## **Tools & Libraries**
| **Purpose**               | **Tools/Libraries**                                                                                     |
|---------------------------|----------------------------------------------------------------------------------------------------------|
| Validation                | Python: `re`, `pydantic`; JavaScript: `express-validator`, `joi`; Java: Hibernate Validator.           |
| SQL Sanitization          | SQLAlchemy, Hibernate, Django ORM.                                                                     |
| HTML Sanitization         | DOMPurify (JS), htmlpurifier (PHP), `html.escape` (Python).                                             |
| File Uploads              | Python: `werkzeug.utils.secure_filename`; Node.js: `multer` with file filters.                         |
| Fuzz Testing              | OWASP ZAP, sqlmap, Burp Suite.                                                                         |
| Security Headers          | CSP (Content Security Policy), XSS filters.                                                             |