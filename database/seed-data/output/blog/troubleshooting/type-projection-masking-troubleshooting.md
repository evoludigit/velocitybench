# **Debugging "Type Projection with Auth Masking": A Troubleshooting Guide**

## **Overview**
This guide helps debug issues with **Type Projection with Auth Masking**, a pattern used to enforce field-level security by dynamically projecting (filtering) response data based on user permissions. Misconfigurations here can lead to **unauthorized data exposure**, performance bottlenecks, or inconsistent security enforcement.

---

## **1. Symptom Checklist**
Before diving into debugging, verify whether you’re experiencing:

| **Symptom** | **Description** |
|-------------|----------------|
| **Data Leakage** | Users see fields they don’t have permission to access (e.g., `sensitiveField` in a read-only response). |
| **Nested Access Violations** | Nested objects contain unauthorized fields (e.g., `user.account.balance` when `user` is authorized but `account` is not). |
| **Empty Responses** | Valid fields are omitted entirely, breaking client expectations. |
| **Performance Degradation** | Slow responses due to excessive projection logic or inefficient permission checks. |
| **Inconsistent Behavior** | Some queries return masked data, others don’t, depending on context. |
| **Error Messages** | Unhandled exceptions (e.g., `NullPointerException` from missing fields, `AuthorizationException` from improper checks). |

If any of these apply, proceed to the **Common Issues & Fixes** section.

---

## **2. Common Issues & Fixes**
### **Issue 1: Incorrect Field Permissions**
**Symptom:**
Users access fields they shouldn’t (e.g., `deleteAt` in a `GET /users/{id}` response).

**Root Cause:**
- The projection logic doesn’t correctly apply auth rules.
- Permission checks are misconfigured (e.g., `@CanAccess` applied to the wrong method/field).
- GraphQL: Missing field-level directives (e.g., `@auth` in Apollo).

**Fixes:**
#### **GraphQL (Apollo/Hasura)**
```graphql
type User @auth(rules: [{ allow: { roles: ["admin"] } }]) {
  id: ID!
  name: String!
  sensitiveData: String @auth(rules: [{ allow: { roles: ["admin"] } }]) # Explicitly mask
}
```
**Fix:** Ensure **every sensitive field** has an explicit `@auth` rule. Default behavior (if omitted) may expose all fields.

#### **REST (NestJS/Spring Boot)**
```typescript
// NestJS: Apply field-level guards
@Get('/user/:id')
async getUser(@User() user: User, @Param('id') id: string) {
  const dbUser = await this.userService.findById(id);
  return this.authMaskingService.project(dbUser, user.role); // Mask sensitive fields
}
```
**Fix:** Use a **dedicated projection service** to apply masking logic consistently.

---

### **Issue 2: Nested Data Leakage**
**Symptom:**
A user can access `user.account.balance`, even though `account` is not authorized.

**Root Cause:**
- Deep nesting bypasses auth checks.
- Recursive projection isn’t implemented.

**Fix:**
**GraphQL (Apollo):**
```graphql
type User {
  id: ID!
  name: String!
  account: Account @auth(requires: { loggedIn: true })
}

type Account @auth(rules: [{ allow: { roles: ["admin"] } }]) {
  balance: Float!
}
```
**Fix:** Ensure **each nested type** has its own `@auth` rules. Use **deep object validation** in resolvers.

**REST (Spring Boot):**
```java
@GetMapping("/user/{id}")
public UserDTO getUser(@PathVariable Long id, @AuthenticationPrincipal UserPrincipal user) {
    UserEntity userEntity = userService.findById(id);
    return new UserDTO(
        userEntity.getId(),
        userEntity.getName(),
        authMaskingService.maskAccount(userEntity.getAccount(), user.getRole()) // Recursive masking
    );
}
```
**Fix:** Implement **recursive masking** in your projection service.

---

### **Issue 3: Performance Bottlenecks**
**Symptom:**
Slow responses due to excessive field checks or inefficient projection.

**Root Cause:**
- Permission checks run in loops (e.g., `forEach` over every field).
- GraphQL: Too many nested `@auth` rules.
- REST: N+1 queries from lazy-loaded masked fields.

**Fix:**
#### **Optimize GraphQL Projections**
```graphql
query GetUser($id: ID!) {
  user(id: $id) {
    id
    name
    # Only request authorized fields
    accountBalance @auth(requires: { roles: ["admin"] })
  }
}
```
**Fix:** Let the **client request only needed fields** (avoid over-fetching).

#### **REST: Pre-Mask in Service Layer**
```typescript
// Avoid checking permissions per HTTP call
const USER_MASKING_RULES = {
  admin: { exclude: [] },
  user: { exclude: ['sensitiveData'] }
};

async findUser(id: string, userRole: string) {
  const user = await this.userRepository.findById(id);
  return maskUser(user, USER_MASKING_RULES[userRole]);
}
```
**Fix:** **Pre-compute masks** and apply them at the service level, not in every controller.

---

### **Issue 4: Inconsistent Behavior**
**Symptom:**
Same query returns masked data in some requests, not others.

**Root Cause:**
- Auth context is lost (e.g., JWT token not passed correctly).
- Caching bypasses auth checks.
- Race conditions in async permission resolution.

**Fix:**
#### **Ensure Auth Context Propagation**
```typescript
// NestJS: Pass user role via DTO/interceptor
@Get('/user')
getUser(@User() user: User) {
  return this.userService.findById(user.id, user.role); // Role passed explicitly
}
```
**Fix:** **Never rely on hidden context**—pass auth data explicitly.

#### **Invalidate Cached Responses**
```python
# Django: Use cache middleware that respects auth
from django.core.cache import caches

def get_user(request, id):
    cache_key = f"user_{id}"
    user = caches['default'].get(cache_key)
    if not user or not has_permission(request.user, 'view_user'):
        user = User.objects.get(id=id)
        caches['default'].set(cache_key, user, timeout=300)
    return user
```
**Fix:** **Cache with auth-aware TTL** or disable caching for sensitive fields.

---

### **Issue 5: Missing Permissions**
**Symptom:**
`403 Forbidden` or `Null` returned for all sensitive fields.

**Root Cause:**
- Default deny policy (e.g., all fields masked unless explicitly allowed).
- Missing fallback for unauthorized fields.

**Fix:**
**GraphQL (Allow by Default, Explicitly Deny):**
```graphql
type User {
  id: ID!
  name: String!
  secret: String @auth(requires: { roles: ["admin"] })
}
```
**Fix:** Use **explicit deny** for sensitive fields (GraphQL) or **explicit allow** (REST).

**REST (Default Deny):**
```typescript
// Spring Boot: Return empty object if unauthorized
@GetMapping("/user/{id}")
public ResponseEntity<Map<String, Object>> getUser(@PathVariable Long id, @AuthenticationPrincipal UserPrincipal user) {
    if (!userHasPermission(user, "view_user")) {
        return ResponseEntity.ok(Map.of("id", id)); // Only authorized fields
    }
    // Else: Full response
}
```
**Fix:** **Fallback to minimal safe data** (ID-only) instead of `403`.

---

## **3. Debugging Tools & Techniques**
### **Logging & Tracing**
- **GraphQL:** Enable Apollo Server’s `@auth` logging:
  ```javascript
  const server = new ApolloServer({
    typeDefs,
    resolvers,
    context: ({ req }) => ({ user: req.user }),
    debug: true, // Logs auth checks
  });
  ```
- **REST:** Log permission checks:
  ```typescript
  console.log(`Checking if ${user.role} can access ${fieldName}`); // Debug trace
  ```

### **Postman/Newman for Regression Testing**
- Test with **different user roles** to verify masking:
  ```json
  // Request 1: Admin (should see all fields)
  {
    "headers": { "Authorization": "Bearer admin-token" }
  }
  // Request 2: User (should see masked fields)
  {
    "headers": { "Authorization": "Bearer user-token" }
  }
  ```

### **Static Analysis**
- **GraphQL:** Use `graphql-codegen` to validate schema rules.
- **REST:** Lint with `tslint` for permission-aware code patterns.

### **Dynamic Testing (Chaos Engineering)**
- **Mutate auth headers** in flight (e.g., with **OAuth2 token testers**).
- **Simulate missing permissions** by overriding `UserPrincipal` in tests.

---

## **4. Prevention Strategies**
### **1. Enforce Schema-Level Security**
- **GraphQL:** Use **field-level directives** (`@auth`) in schema definition.
- **REST:** Define **explicit DTOs** for each role (e.g., `AdminUserDTO`, `UserDTO`).

### **2. Automated Permission Checks**
- **NestJS:** Use **interceptors** for auth masking:
  ```typescript
  @Injectable()
  class AuthMaskingInterceptor implements NestInterceptor {
    intercept(context: ExecutionContext, next: CallHandler) {
      const request = context.switchToHttp().getRequest();
      const user = request.user;
      const data = await next.handle().toPromise();
      return this.maskData(data, user.role);
    }
  }
  ```
- **Spring Boot:** Apply **AOP** for permission checks:
  ```java
  @Aspect
  @Component
  public class PermissionAspect {
      @Around("execution(* com.example.service.*.*(..)) && args(.., role)")
      public Object checkPermission(ProceedingJoinPoint pjp, String role) throws Throwable {
          if (!hasPermission(role, pjp.getSignature().getName())) {
              throw new SecurityException("Unauthorized");
          }
          return pjp.proceed();
      }
  }
  ```

### **3. Testing Framework Integration**
- **GraphQL:** Use **Apollo TestKit** to validate responses:
  ```javascript
  test('admin sees all fields', async () => {
    const adminQuery = gql`
      query { user { id, secret } }
    `;
    const { data } = await apolloClient.query({ query: adminQuery });
    expect(data.user.secret).toBeDefined();
  });
  ```
- **REST:** Mock auth in **Jest/Pytest** to test edge cases.

### **4. Documentation & Code Reviews**
- **Add comments** in code explaining masking rules:
  ```java
  /**
   * @return UserDTO with 'balance' masked if user is not ADMIN.
   * Example:
   *   ADMIN -> {id, name, balance: 1000}
   *   USER  -> {id, name, balance: null}
   */
  public UserDTO getUser(Long id) { ... }
  ```
- **Conduct security reviews** for auth-related changes.

### **5. Monitoring & Alerts**
- **Log unauthorized access attempts**:
  ```typescript
  if (!userHasPermission(user, 'access_field')) {
    logger.warn(`User ${user.id} tried accessing unauthorized field`);
  }
  ```
- **Set up alerts** for unexpected field exposure (e.g., Prometheus + Grafana).

---

## **5. Summary Checklist**
| **Action** | **Status** |
|------------|------------|
| Verify all sensitive fields have explicit auth rules. | ✅/❌ |
| Test nested data masking recursively. | ✅/❌ |
| Profile performance bottlenecks in projection logic. | ✅/❌ |
| Ensure auth context is propagated consistently. | ✅/❌ |
| Validate cached responses respect permissions. | ✅/❌ |
| Implement automated tests for different roles. | ✅/❌ |
| Add logging for permission denials. | ✅/❌ |

---
**Final Note:** The **Type Projection with Auth Masking** pattern is powerful but brittle. **Test edge cases ruthlessly**, log permission checks, and **automate validation** where possible. If issues persist, start with **logging** and **Postman tests** before diving into complex debugging.