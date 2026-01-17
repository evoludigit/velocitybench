# **[Pattern] Output Encoding & Escaping Reference Guide**

---

## **1. Overview**
Output Encoding & Escaping is a **security-critical pattern** designed to prevent **cross-site scripting (XSS), cross-site request forgery (CSRF), SQL injection**, and other injection attacks by ensuring safe rendering of untrusted data in responses. This pattern ensures that user-generated content is **properly escaped or encoded** before being output to HTML, JavaScript, URLs, or other contexts where it could be interpreted maliciously.

Key principles include:
- **Context-aware escaping** (HTML, JavaScript, CSS, URLs, etc.)
- **Sanitization vs. Encoding**: Differentiating between sanitization (removing dangerous content) and escaping (making content safe in a specific context).
- **Use of built-in libraries** (e.g., `htmlspecialchars()` in PHP, `DOMPurify` for JS, Angular’s `sanitizer`).
- **Defense in depth** by combining escaping with input validation and output sanitization.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Principles**
| **Concept**               | **Definition**                                                                                                                                                                                                 | **Example Use Case**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Contextual Escaping**   | Adjusting encoding based on the output context (HTML, JavaScript, URLs, etc.).                                                                                                                               | Escaping `<script>` as `&lt;script&gt;` in HTML. |
| **Sanitization**          | Stripping potentially dangerous code (e.g., `<script>` tags) before rendering.                                                                                                                              | Removing all JS tags from user comments.       |
| **Encoding Schemes**      | Different encoding rules for different contexts (e.g., double-encoding for JavaScript URLs).                                                                                                                   | `encodeURIComponent()` for URLs vs. `htmlspecialchars()` for HTML. |
| **"DoS Protection"**      | Limiting output length or rates to prevent denial-of-service via excessive escaping.                                                                                                                         | Capping rendered comment length at 10 KB.      |
| **Defense in Depth**      | Combining escaping with input validation (e.g., regex patterns) and output sanitization (e.g., `DOMPurify`).                                                                                                | Validate email format + escape HTML output.    |

---

### **2.2 Common Threats & Mitigations**
| **Threat**               | **Vulnerability**                          | **Mitigation**                                                                                     |
|--------------------------|-------------------------------------------|---------------------------------------------------------------------------------------------------|
| **XSS (Cross-Site Scripting)** | User input rendered as HTML/JS without escaping. | Use `htmlspecialchars()` (PHP), `textContent` (JS), or `DOMPurify`.                            |
| **SQL Injection**        | Untrusted data in SQL queries.            | **Never escape SQL!** Use prepared statements (`?` placeholders) or ORMs like Hibernate.          |
| **URL/Query Parameter Pollution** | Untrusted data in URLs or requests.    | Use `encodeURIComponent()` for URLs; validate input server-side.                                |
| **Cross-Site Request Forgery (CSRF)** | Malicious links forcing authenticated actions. | Use CSRF tokens; ensure forms submit to trusted domains.                                         |
| **HTML Injection**       | Embedding `<img src="xss.js">` in forms.   | Sanitize HTML output (e.g., allow only `<b>`, `<i>` tags).                                        |

---

### **2.3 Encoding Schemes by Context**
| **Context**          | **Encoding Method**               | **PHP Example**                          | **JavaScript Example**                     | **Notes**                                  |
|----------------------|-----------------------------------|------------------------------------------|--------------------------------------------|--------------------------------------------|
| **HTML**             | HTML entities                     | `htmlspecialchars($user_input, ENT_QUOTES)` | `document.body.innerText = input;`          | Avoid `innerHTML`; prefer `textContent`.   |
| **JavaScript**       | Double-encoding (for URLs)        | `json_encode($user_input)`               | `JSON.stringify(input).replace(/"/g, '\\"')` | Use `textContent` over `innerHTML`.         |
| **CSS**              | CSS entity encoding               | `addslashes($user_input)`                | `input.replace(/([!"#$%&()*+,./:;<=>?@[\]^`{|}~])/g, '\\$1')` | Avoid `style="..."` with user input.       |
| **URLs**             | `encodeURIComponent()`            | `urlencode($user_input)`                 | `encodeURIComponent(input)`                | Safe for query strings (e.g., `?q=hello`). |
| **XML**              | XML entity encoding               | `htmlspecialchars($user_input, ENT_XML1)`   | `new DOMParser().parseFromString(...)`      | Use for APIs (e.g., SOAP, RSS).            |
| **JSON**             | JSON.stringify + escaping          | `json_encode($user_input)`               | `JSON.stringify(input)`                    | Avoid `eval()` with untrusted JSON.        |

---

### **2.4 Step-by-Step Implementation**
1. **Identify Context**
   Determine where untrusted data will render (HTML, JS, URL, etc.).

2. **Choose Encoding Method**
   Select the appropriate encoding scheme (see table above).

3. **Apply Encoding**
   Use language-specific functions (e.g., `htmlspecialchars()` in PHP, `textContent` in JS).

4. **Sanitize if Needed**
   Use libraries like `DOMPurify` (JS) or `htmlpurifier` (PHP) to strip malicious tags.

5. **Validate Input**
   Reject malformed data (e.g., SQL injection attempts) via regex or libraries like `validator.js`.

6. **Test Thoroughly**
   Use tools like **OWASP ZAP**, **Burp Suite**, or **XSS scanners** to verify escaping.

---

## **3. Schema Reference**
Below is a **scannable reference table** for encoding functions by language/framework:

| **Language/Framework** | **HTML Escaping**               | **JavaScript Escaping**          | **URL Encoding**               | **XML Escaping**               | **Notes**                          |
|------------------------|----------------------------------|-----------------------------------|---------------------------------|---------------------------------|------------------------------------|
| **PHP**                | `htmlspecialchars($input, ENT_QUOTES)` | `json_encode($input)`             | `urlencode($input)`             | `htmlspecialchars($input, ENT_XML1)` | Prefer `json_encode` for JS.       |
| **JavaScript (Native)** | `DOMPurify.sanitize(input)`      | `textContent` (no encoding needed)| `encodeURIComponent(input)`     | `escapeXml(input)` (custom)     | `DOMPurify` strips dangerous HTML.  |
| **Angular**            | `{{ safeInput | sanitize }}` (with `DomSanitizer`) | `JsonPipe` (for JSON)            | `encodeURIComponent(input)`     | N/A                                | Use `| sanitize` pipe.              |
| **React**              | `DangerouslySetInnerHTML` (avoid) | `textContent`                      | `encodeURIComponent(input)`     | N/A                                | Avoid `innerHTML`; use `textContent`. |
| **Python (Flask/Django)** | `mark_safe(html.escape(input))` | `json.dumps(input)`               | `urllib.parse.quote(input)`     | `xml.sax.saxutils.escape(input)` | Django’s `mark_safe` + `escape`.   |
| **Node.js (Express)**  | `DOMPurify.sanitize(input)`      | `JSON.stringify(input)`           | `encodeURIComponent(input)`     | N/A                                | Requires `DOMPurify` install.        |

---

## **4. Query Examples**

### **4.1 Escaping User Input in HTML (PHP)**
```php
<?php
$user_input = '<script>alert("XSS")</script>';
$safe_output = htmlspecialchars($user_input, ENT_QUOTES, 'UTF-8');
// Outputs: &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;
echo $safe_output;
?>
```

### **4.2 Safe JavaScript Rendering (JavaScript)**
```javascript
// SAFE: Use textContent (automatically escapes)
const userInput = '<script>alert("Hacked!")</script>';
document.getElementById('output').textContent = userInput;

/*
UNSAFE: innerHTML can execute scripts
document.getElementById('output').innerHTML = userInput;
*/
```

### **4.3 URL-Safe Encoding (Python)**
```python
from urllib.parse import quote

user_input = "hello world! <script>"
safe_url = quote(user_input)
# Output: hello%20world%21%20%3Cscript%3E
print(safe_url)
```

### **4.4 Sanitizing HTML with DOMPurify (JavaScript)**
```javascript
import DOMPurify from 'dompurify';

const dirtyHTML = '<div style="background: red"><script>alert("XSS")</script></div>';
const cleanHTML = DOMPurify.sanitize(dirtyHTML);
// Output: <div style="background: red"></div>
document.write(cleanHTML);
```

### **4.5 SQL Injection Prevention (PHP with Prepared Statements)**
```php
$stmt = $pdo->prepare("SELECT * FROM users WHERE email = ?");
$stmt->execute([$user_input]); // SAFE: Parameterized query
```

---

## **5. Related Patterns**
- **[Input Validation]** – Validate data before processing (e.g., regex for emails).
- **[Sanitization]** – Strip dangerous content (e.g., `DOMPurify`, `htmlpurifier`).
- **[Content Security Policy (CSP)]** – Restrict sources for scripts/styles (defense in depth).
- **[Preventing CSRF]** – Use tokens (`_csrf` fields) in forms.
- **[Secure Headers]** – Set `X-XSS-Protection`, `Content-Security-Policy` in HTTP responses.
- **[ORM Usage]** – Always use ORMs (e.g., Hibernate, Sequelize) to avoid SQL injection.

---

## **6. Tools & Libraries**
| **Tool/Library**       | **Purpose**                                                                 | **Language**       |
|------------------------|-----------------------------------------------------------------------------|--------------------|
| **DOMPurify**          | Sanitize HTML to prevent XSS.                                               | JavaScript        |
| **htmlpurifier**       | PHP-based HTML sanitizer.                                                   | PHP                |
| **htmlspecialchars()**  | Basic HTML escaping in PHP.                                                 | PHP                |
| **Angular `DomSanitizer`** | Securely render HTML in Angular apps.                                      | TypeScript/Angular |
| **React `DangerouslySetInnerHTML`** | Use sparingly; prefer `textContent`.                                      | JavaScript/React   |
| **OWASP ESAPI**        | Encoding library for Java/.NET/others.                                       | Multi-language     |
| **Python `bleach`**    | HTML sanitizer for Python.                                                  | Python             |

---

## **7. Best Practices Checklist**
1. [ ] **Contextual Escaping**: Always escape data based on output context (HTML, JS, URL).
2. [ ] **Avoid `innerHTML`/`eval()`**: Use `textContent` or `textContent` alternatives.
3. [ ] **Sanitize HTML**: Use `DOMPurify` or `htmlpurifier` for untrusted HTML.
4. [ ] **Use Prepared Statements**: Never concatenate SQL queries with user input.
5. [ ] **Validate Input**: Reject malformed data (e.g., SQL keywords, JS tags).
6. [ ] **Test with Tools**: Use OWASP ZAP or Burp Suite to scan for XSS/SQLi.
7. [ ] **Defense in Depth**: Combine escaping with CSP headers and CSRF tokens.
8. [ ] **Rate-Limit Output**: Prevent DoS via excessive escaping (e.g., 10 KB max).
9. [ ] **Document Assumptions**: Clearly note which libraries/tools are used for escaping.
10. [ ] **Keep Libraries Updated**: Patch vulnerabilities in `DOMPurify`, `htmlpurifier`, etc.

---
**⚠️ Warning**: This pattern **does not replace input validation**. Always validate data on the server side.

---
**📌 Key Takeaway**:
*"Escape output, validate input, and sanitize when necessary—but never trust user-provided data."*