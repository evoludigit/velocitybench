# **Debugging CSRF Protection: A Troubleshooting Guide**

## **Title: Debugging [CSRF Protection]: A Troubleshooting Guide**

Cross-Site Request Forgery (CSRF) is a security vulnerability where an attacker tricks a user into submitting malicious requests on their behalf. Since browsers automatically include session cookies with cross-origin requests, an attacker can exploit this to perform unauthorized actions (e.g., money transfers, account changes) if the target site lacks proper CSRF protection.

This guide provides a structured approach to identifying, debugging, and fixing CSRF vulnerabilities in your backend application.

---

## **1. Symptom Checklist**
Check if your application is vulnerable to CSRF by verifying the following:

| **Symptom** | **How to Test** | **Expected Behavior** |
|------------|----------------|-------------------|
| **No CSRF Token Required for State-Changing Actions** | Attempt to submit a form or API request without a CSRF token (e.g., via curl or browser dev tools). | **Vulnerable:** The request succeeds without a token. |
| **Automatic Request Execution via Invisible Elements** | Inject an `<img>` tag, `<script>`, or `<iframe>` pointing to a state-changing endpoint (e.g., `<img src="bank.com/transfer?amount=1000">`). | **Vulnerable:** The request executes without user interaction. |
| **SameSite Cookie Misconfiguration** | Check if cookies are not set with `SameSite=Strict` or `SameSite=Lax`. | **Vulnerable:** Cookies are sent to cross-origin requests. |
| **Missing Double-Submit Cookie Pattern** | Intercept a form submission and verify if a CSRF token is required in both the request body and headers. | **Vulnerable:** Only one of the protection methods is enforced. |
| **API Endpoints Without CSRF Protection** | Test API calls (e.g., via Postman or curl) without CSRF headers. | **Vulnerable:** The API does not reject requests without CSRF validation. |

---

## **2. Common Issues & Fixes**
### **Issue 1: Missing CSRF Token in State-Changing Requests**
**Symptom:** Forms or API calls that modify user data (e.g., `POST /transfer`) do not require a CSRF token.

**Root Cause:**
- The frontend does not generate a CSRF token.
- The backend does not validate the token.

**Fix:**
#### **Option 1: CSRF Token in Headers (Recommended for APIs)**
1. **Frontend (e.g., React, Vue, or plain HTML):**
   Add a CSRF token to the request headers.
   ```javascript
   // Example: Fetch API with CSRF token
   fetch('/transfer', {
       method: 'POST',
       headers: {
           'Content-Type': 'application/json',
           'X-CSRF-Token': 'your_csrf_token_here' // Obtained from a session cookie or cookie
       },
       body: JSON.stringify({ amount: 1000, to: 'attacker' })
   });
   ```
   - Generate the token on the server and store it in a cookie:
     ```python
     # Flask Example
     from flask import Flask, make_response
     app = Flask(__name__)

     @app.before_request
     def before_request():
         if 'csrf_token' not in session:
             session['csrf_token'] = secrets.token_hex(16)
         response = make_response()
         response.set_cookie('csrf_token', session['csrf_token'])
         return response
     ```

2. **Backend (e.g., Flask, Express, Django):**
   Validate the CSRF token in the request headers.
   ```python
   # Flask Example
   from flask import request, abort

   @app.route('/transfer', methods=['POST'])
   def transfer():
       if request.headers.get('X-CSRF-Token') != request.cookies.get('csrf_token'):
           abort(403, "CSRF Token missing or invalid")
       # Process request
   ```

#### **Option 2: Double-Submit Cookie Pattern (For Forms)**
1. **Frontend:**
   Include the CSRF token in both the form body and a hidden input.
   ```html
   <form action="/transfer" method="POST">
       <input type="hidden" name="csrf_token" value="{{ csrf_token }}"> <!-- From session -->
       <input type="text" name="amount" value="1000">
       <button type="submit">Transfer</button>
   </form>
   ```

2. **Backend:**
   Validate the token from both the cookie and form data.
   ```python
   # Flask Example
   @app.route('/transfer', methods=['POST'])
   def transfer():
       token_from_cookie = request.cookies.get('csrf_token')
       token_from_form = request.form.get('csrf_token')
       if token_from_cookie != token_from_form:
           abort(403, "CSRF Token mismatch")
       # Process request
   ```

---

### **Issue 2: SameSite Cookie Not Configured**
**Symptom:** Cookies are sent to cross-origin requests, allowing CSRF attacks.

**Root Cause:**
- Cookies lack the `SameSite` attribute or are set to `SameSite=None`.

**Fix:**
Ensure cookies are restricted to same-site contexts:
```python
# Flask Example (Secure Cookie with SameSite)
response = make_response("Transfer successful")
response.set_cookie(
    'session_id',
    session_id,
    secure=True,          # Only sent over HTTPS
    samesite='Strict'     # Blocks cross-site requests (most secure)
    # samesite='Lax'      # Allows top-level navigations
)
```
- **`SameSite=Strict`:** Blocks all cross-site requests (most secure).
- **`SameSite=Lax`:** Allows top-level navigations (e.g., `<a href="...">`).
- **`SameSite=None`:** Allows cross-site requests (only use with `Secure` flag).

---

### **Issue 3: API Endpoints Lack CSRF Protection**
**Symptom:** API calls (e.g., `POST /update-profile`) can be spoofed.

**Root Cause:**
- APIs are exposed to the public internet without CSRF validation.

**Fix:**
- **For Internal APIs (Backend-to-Backend):** Use `SameSite=Lax` + authentication (JWT, API keys).
- **For User-Facing APIs:** Enforce CSRF tokens (as in **Option 1** above).
- **For Public APIs:** Avoid state-changing requests; use read-only endpoints where possible.

---

## **3. Debugging Tools & Techniques**
### **Tools for CSRF Testing**
| **Tool** | **Purpose** | **How to Use** |
|----------|------------|----------------|
| **Burp Suite** | Intercept and modify requests to test CSRF. | Configure Burp as a proxy, submit a form, and observe if the request succeeds without a CSRF token. |
| **OWASP ZAP** | Automated CSRF scanner. | Run a scan against your application to detect missing CSRF tokens. |
| **Browser Dev Tools (Network Tab)** | Inspect request headers/cookies. | Submit a form/API call and check if `csrf_token` is missing or mismatched. |
| **cURL** | Test CSRF vulnerabilities directly. | ```bash curl -H "Origin: https://evil.com" -H "Referer: https://evil.com" -X POST http://bank.com/transfer -d "amount=1000" ``` |
| **CSRF Proxy (e.g., `csurf`)** | Automatically injects CSRF tokens. | Configure your app to use a middleware like `csurf` (Node.js) or `django-csrf` (Python). |

### **Debugging Steps**
1. **Intercept a Form/API Submission:**
   - Use Burp Suite or browser dev tools to capture the request.
   - Check if the request includes:
     - A CSRF token in headers (`X-CSRF-Token`).
     - A CSRF token in the request body (form field).
     - A matching cookie (`csrf_token`).

2. **Test Without CSRF Protection:**
   - Remove the CSRF token from the request and resubmit.
   - If the request succeeds, your app is vulnerable.

3. **Check Cookie Attributes:**
   - Use `curl -I http://your-site.com` to inspect `Set-Cookie` headers.
   - Verify `SameSite` and `Secure` flags are set correctly.

4. **Simulate a CSRF Attack:**
   - Create a malicious page (`evil.com`) with:
     ```html
     <img src="bank.com/transfer?amount=1000&to=attacker" />
     ```
   - If money is transferred, your app lacks CSRF protection.

---

## **4. Prevention Strategies**
### **Best Practices**
1. **Always Enforce CSRF Tokens for State-Changing Actions**
   - Use **CSRF tokens in headers** for APIs.
   - Use the **double-submit cookie pattern** for forms.

2. **Set `SameSite` Attribute on Cookies**
   - Prefer `SameSite=Strict` for maximum security.
   - Avoid `SameSite=None` unless necessary (e.g., embedding iframes).

3. **Use Secure Cookies**
   - Always set `Secure=True` (HTTPS only).
   - Set `HttpOnly` to prevent XSS-based cookie theft.

4. **Implement Rate Limiting**
   - Block rapid-fire requests to prevent brute-force attacks.

5. **Log and Monitor Suspicious Activity**
   - Track failed CSRF token validations.
   - Alert on unusual transfer patterns.

6. **Educate Frontend Developers**
   - Ensure they include CSRF tokens in all state-changing requests.

### **Example: Secure Flask App Setup**
```python
from flask import Flask, request, session, make_response, abort
import secrets

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.before_request
def before_request():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    response = make_response()
    response.set_cookie(
        'csrf_token',
        session['csrf_token'],
        secure=True,
        samesite='Strict'
    )
    return response

@app.route('/transfer', methods=['POST'])
def transfer():
    token_from_header = request.headers.get('X-CSRF-Token')
    token_from_cookie = request.cookies.get('csrf_token')

    if not token_from_header or token_from_header != token_from_cookie:
        abort(403, "CSRF Token required")

    # Process transfer
    return "Transfer successful"
```

---

## **5. Summary & Takeaways**
| **Problem** | **Quick Fix** | **Tool to Use** |
|------------|--------------|----------------|
| No CSRF token in requests | Add `X-CSRF-Token` header or hidden form field | Burp Suite, Dev Tools |
| Cookies sent cross-site | Set `SameSite=Strict` | `curl -I` to inspect headers |
| API lacks CSRF protection | Enforce token validation | OWASP ZAP |
| Double-submit cookie mismatch | Ensure cookie and form token match | Manual inspection |

### **Final Checks**
✅ All state-changing endpoints require a CSRF token.
✅ Cookies are `SameSite=Strict` and `Secure`.
✅ API calls include `X-CSRF-Token` header.
✅ Tested with Burp Suite/OWASP ZAP to confirm no vulnerabilities.

By following this guide, you can systematically debug and eliminate CSRF vulnerabilities in your backend. **Always test in staging before production!**