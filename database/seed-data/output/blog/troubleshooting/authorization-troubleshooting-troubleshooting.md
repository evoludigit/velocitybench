# **Debugging Authorization: A Troubleshooting Guide**

---

## **1. Introduction**
Authorization errors often manifest as **denied access, unexpected permission failures, or inconsistent role-based behavior**. Unlike authentication (which verifies *who* the user is), authorization determines *what* they can do. Debugging authorization issues requires checking **policy logic, role assignments, token claims, and backend integrations**.

This guide provides a **systematic approach** to diagnose and resolve authorization-related problems efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these common symptoms:

### **Symptoms of Authorization Failure**
| Symptom | Description | Likely Cause |
|---------|------------|-------------|
| **403 Forbidden** (HTTP) | User receives "Insufficient permissions" | Incorrect role assignment, policy misconfiguration, or JWT claims mismatch |
| **500 Internal Server Error** | Server fails to process auth logic | Logic error in `can()`/`check()` methods, database query failure |
| **Inconsistent Permissions** | Same user gets different access across requests | Caching issues, stale role assignments, or race conditions |
| **Role-Based Logic Fails** | User with `admin` role cannot manage resources | Role hierarchy mismatch, policy override, or hardcoded checks |
| **Token Validation Errors** | JWT claims missing or corrupted | Improper token generation, claim expiration, or signing key mismatch |
| **No Error Logs** | System silently rejects requests | Missing middleware, loggers disabled, or error swallowing |

**Quick Check:**
- Is the error **client-side (403)** or **server-side (500)**?
- Does the issue affect **all users** or **specific roles**?
- Are **logs silent** or **inconsistent**?

---

## **3. Common Issues & Fixes**

### **3.1 Role Assignment Mismatch**
**Symptom:**
A user with `admin` role cannot perform an action, even though they should.

**Root Cause:**
- Incorrect role assignment in the database.
- Role not properly loaded from the session/token.

**Solution (Laravel Example):**
```php
// Check if user has correct role
if (!user()->hasRole('admin')) {
    throw new \Symfony\Component\HttpKernel\Exception\AccessDeniedHttpException();
}

// Verify role is loaded (e.g., from database)
$user->roles; // Ensure this returns ['admin']
```

**Debugging Steps:**
1. **Check DB:**
   ```sql
   SELECT * FROM roles WHERE user_id = ? AND name = 'admin';
   ```
2. **Log Role Assignment:**
   ```php
   \Log::info('User roles: ' . json_encode(user()->roles));
   ```

---

### **3.2 Policy Logic Error**
**Symptom:**
A `can()` check fails, but no clear reason in logs.

**Root Cause:**
- Policy method logic is incorrect.
- Missing `@throws` on denial.

**Solution (Laravel Policy Example):**
```php
// Correct: Explicitly deny access
public function update(User $user, Post $post) {
    return $user->id === $post->user_id;
}

// Incorrect: Silent failure (no log)
public function delete(User $user, Post $post) {
    return true; // Missing proper check
}
```

**Debugging Steps:**
1. **Enable Policy Logging:**
   ```php
   \Log::debug('Policy check: ' . json_encode([
       'user' => user()->id,
       'resource' => $post->id,
   ]));
   ```
2. **Test Policy in Tinker:**
   ```php
   $user = User::find(1); $post = Post::find(10);
   app(AdminPolicy::class)->update($user, $post);
   ```

---

### **3.3 JWT Claim Mismatch**
**Symptom:**
User gets access beyond their role (e.g., `admin` behaves as `superadmin`).

**Root Cause:**
- Custom JWT claims not properly validated.
- Overriding roles in code.

**Solution (Laravel Passport Example):**
```php
// Ensure claims are validated
public function handle($request, Closure $next) {
    $user = $request->user();
    if (!in_array('admin', $user->getAttribute('roles'))) {
        return response()->json(['error' => 'Forbidden'], 403);
    }
    return $next($request);
}
```

**Debugging Steps:**
1. **Inspect Token:**
   ```bash
   jwt decode <token> --secret your-secret
   ```
2. **Check Custom Fields:**
   ```php
   $tokenClaims = JWT::decode($token, key('secret'));
   \Log::info('JWT roles: ' . $tokenClaims->roles);
   ```

---

### **3.4 Caching Issues**
**Symptom:**
Permissions change, but users still see old access.

**Root Cause:**
- Role cache not cleared.
- Middleware caching user permissions.

**Solution (Laravel Example):**
```php
// Clear role cache explicitly
Cache::forget('user-roles-1');

// Or use cache tags
Cache::tags(['user:1'])->flush();
```

**Debugging Steps:**
1. **Check Cache Store:**
   ```php
   Cache::get('roles-cache');
   ```
2. **Test Without Cache:**
   ```bash
   php artisan cache:clear
   ```

---

### **3.5 Database Query Failures**
**Symptom:**
Role assignments not loaded from DB.

**Root Cause:**
- Query returns empty results.
- `with()` relation not loaded.

**Solution (Laravel Example):**
```php
// Ensure eager loading
$user = User::with(['roles'])->find($id);

// Debug query
\Log::debug($user->roles);
```

**Debugging Steps:**
1. **Check Raw SQL:**
   ```php
   \Log::debug(User::with(['roles'])->find($id)->getQuery()->toSql());
   ```
2. **Test SQL Directly:**
   ```sql
   SELECT * FROM roles WHERE user_id = ?;
   ```

---

## **4. Debugging Tools & Techniques**

### **4.1 Logging & Monitoring**
- **Log Authorization Decisions:**
  ```php
  \Log::debug('User {id} has access to {resource}', [
      'user_id' => user()->id,
      'resource' => $resource->id,
      'allowed' => $policy->check($user, $resource),
  ]);
  ```
- **Use Sentry/Loggly for Error Tracking:**
  ```php
  Sentry::captureException(new \AccessDeniedException());
  ```

### **4.2 API Mocking**
- **Test Policies Without Real DB:**
  ```php
  $fakeUser = User::factory()->create(['roles' => ['admin']]);
  $this->actingAs($fakeUser);
  ```

### **4.3 Static Analysis**
- **Laravel Fortify/Panic:**
  ```bash
  php artisan vendor:publish --tag=laravel-fortify-panic-views
  ```
- **Check Policy Contracts:**
  ```php
  // Ensure all policies extend BasePolicy
  class AdminPolicy extends BasePolicy { ... }
  ```

### **4.4 Postman Collection Testing**
- **Test Endpoints with Different Roles:**
  ```json
  {
    "headers": {
      "Authorization": "Bearer {{admin_token}}"
    }
  }
  ```

---

## **5. Prevention Strategies**

### **5.1 Code Practices**
1. **Fail Fast:** Always log and throw exceptions for auth failures.
2. **Immutable Roles:** Use enums or constants for roles.
3. **Unit Test Policies:**
   ```php
   public function test_admin_can_delete_post() {
       $user = User::factory()->create(['roles' => ['admin']]);
       $post = Post::factory()->create();
       $this->actingAs($user)->assertCan('delete', $post);
   }
   ```

### **5.2 Infrastructure**
1. **Rate-Limit Auth Endpoints:**
   ```php
   Route::middleware('throttle:auth')->group([...]);
   ```
2. **Use Redis for Caching Roles:**
   ```php
   Cache::driver('redis');
   ```

### **5.3 Documentation**
- **Document Role Hierarchy:**
  ```mermaid
  graph LR
      Guest --> User
      User --> Member
      Member --> Admin
  ```
- **Add Permissions to API Docs:**
  ```yaml
  /api/posts
    get:
      security: ["BearerAuth"]
      responses:
        403: "Unauthorized (missing 'read:posts')"
  ```

---

## **6. Summary of Fixes by Symptom**
| **Symptom** | **Quick Fix** |
|-------------|--------------|
| **403 Forbidden** | Check `can()`/`check()` logic, JWT claims, role assignments |
| **500 Server Error** | Debug policy methods, DB queries, middleware |
| **Inconsistent Permissions** | Clear cache, check race conditions |
| **Role Not Recognized** | Verify role exists in DB, eager load |
| **Token Issues** | Validate claims, regenerate token |

---

## **7. Final Checklist**
✅ **Verify logs** (server + client)
✅ **Test policies in isolation** (Tinker/unit tests)
✅ **Check DB consistency** (roles, permissions)
✅ **Validate token claims** (`jwt decode`)
✅ **Clear caches** if permissions seem outdated

By following this structured approach, you can **quickly identify and resolve authorization issues** without extensive trial-and-error.