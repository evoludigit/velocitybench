# **Debugging the `fn_*` Naming Convention: A Troubleshooting Guide**

## **Introduction**
The `fn_{action}_{entity}` naming convention is a structured approach to function naming that improves readability, maintainability, and consistency across a codebase. Despite its benefits, misapplication can lead to confusion, especially in large or evolving systems.

This guide covers:
1. **Symptom Checklist** – How to recognize issues with this pattern.
2. **Common Issues & Fixes** – Practical code examples for correction.
3. **Debugging Tools & Techniques** – Methods to audit and enforce consistency.
4. **Prevention Strategies** – Best practices to avoid future problems.

---

## **1. Symptom Checklist**
Before debugging, verify if the following issues exist:

| Symptom | Description |
|---------|------------|
| **Inconsistent Prefixes** | Some functions use `fn_`, others use `do_`, `perform_`, or no prefix. |
| **Ambiguous Actions** | Functions use unclear verbs (`update`, `modify`, `change`). |
| **Incorrect Pluralization** | Entity names are singular (`User`) but in plural form (`Users` in function names). |
| **Overly Long Names** | Functions exceed 50+ characters, reducing readability. |
| **Function Parameters Mismatch** | Parameters don’t logically align with action+entity (e.g., `fn_get_all_users()` vs. `fn_activate_user(id)`). |
| **Duplicate Functions** | Multiple functions with similar names but different behaviors (e.g., `fn_save_order()` vs. `fn_submit_order()`). |

**Action:** If more than 2-3 symptoms apply, proceed to debugging.

---

## **2. Common Issues & Fixes**

### **Issue 1: Non-Standard Prefixes**
**Symptoms:**
- Functions use `do_` instead of `fn_`.
- Some are prefixed, others are not.

**Fix:**
Standardize on `fn_` consistently.

**Before:**
```javascript
// Inconsistent prefixes
function doLoginUser(email, password) {}    // ❌
function logoutUser() {}                   // ❌
function fnGetUserById(id) {}               // ✅ (but inconsistent with others)
```

**After:**
```javascript
// Consistent `fn_` prefix
function fnLoginUser(email, password) {}    // ✅
function fnLogoutUser(id) {}                // ✅
function fnGetUserById(id) {}               // ✅
```

**Debugging Tip:**
Use **regEx searches** in your IDE:
- Find all `function [^fn_]` to spot non-standard prefixes.

---

### **Issue 2: Ambiguous Action Verbs**
**Symptoms:**
- `update`, `modify`, `change` are too vague.
- No clear distinction between CRUD operations.

**Fix:**
Use explicit verbs:
- **Create:** `fnCreateUser()`
- **Read:** `fnGetUser()`
- **Update:** `fnUpdateUserProfile()`
- **Delete:** `fnDeleteUserAccount()`

**Before:**
```javascript
function modifyUserSettings(userId, settings) {}  // ❌ Too vague
```

**After:**
```javascript
function fnUpdateUserSettings(userId, settings) {}  // ✅ Clear intent
```

**Debugging Tip:**
Run a **static analysis tool** (e.g., ESLint with custom rules) to flag ambiguous verbs.

---

### **Issue 3: Incorrect Entity Pluralization**
**Symptoms:**
- `fn_get_all_users` where `User` is singular in code.
- `fn_save_order_item` vs. `fn_saveOrderItem` (mixed casing).

**Fix:**
Ensure entity naming aligns with class names.

**Before:**
```javascript
class User { ... }
function fn_get_all_users() {}  // ❌ (should be `User` not `users`)
```

**After:**
```javascript
class User { ... }
function fnGetAllUsers() {}     // ✅ (if returning multiple)
function fnGetUser(id) {}       // ✅ (singular for single entity)
```

**Debugging Tip:**
Use **linter rules** to warn on mismatched plurals (e.g., `eslint-plugin-naming`).

---

### **Issue 4: Overly Long Function Names**
**Symptoms:**
- Function names exceed 40+ characters.
- Hard to read in logs or IDE autocompletion.

**Fix:**
Trim names while keeping clarity:
- Instead of `fnCalculateAndReturnTotalDiscountForUserOrder()`, use:
  ```javascript
  function fnApplyUserOrderDiscount(orderId, discountPercent) {}  // ✅
  ```

**Before:**
```javascript
function fnDetermineAndApplyMaximumPossibleDiscountBasedOnUserOrderHistory(orderId) {}  // ❌
```

**After:**
```javascript
function fnApplyDiscountToUserOrder(orderId, discountCode) {}  // ✅
```

**Debugging Tip:**
Use **Git blame + line length counter** to find long functions.

---

### **Issue 5: Parameter Mismatch with Action**
**Symptoms:**
- `fnGetAllUsers()` but only returns one user.
- `fnActivateUser()` but requires `email` instead of `userId`.

**Fix:**
Ensure parameters logically match the action+entity.

**Before:**
```javascript
// Returns all users but named incorrectly
function fnGetSingleUser(userId) {}  // ❌ Misleading
```

**After:**
```javascript
// Clear intent
function fnGetUserById(id) {}  // ✅
```

**Debugging Tip:**
Use **type hints** (TypeScript/Java) to enforce parameter validation.

---

### **Issue 6: Duplicate Functions**
**Symptoms:**
- `fnSaveOrder()` and `fnSubmitOrder()` do the same thing.
- Low test coverage leads to hidden duplicates.

**Fix:**
Refactor duplicates into a single, well-named function.

**Before:**
```javascript
// Duplicate functions
function fnSaveOrder(orderDetails) {
  saveToDatabase(orderDetails);
}

function fnSubmitOrder(orderDetails) {
  saveToDatabase(orderDetails);  // ❌ Same logic
}
```

**After:**
```javascript
function fnSubmitOrder(orderDetails) {  // ✅ Unified
  saveToDatabase(orderDetails);
}
```

**Debugging Tip:**
Use **code similarity tools** (e.g., [Simian](https://www.simiancode.com/) for Java).

---

## **3. Debugging Tools & Techniques**

| Tool/Technique | Purpose | Example |
|---------------|---------|---------|
| **IDE Search (RegEx)** | Find all function names not matching `fn_*` | `^(fn_\w+)` |
| **ESLint Plugins** | Enforce naming conventions | `eslint-plugin-naming` |
| **Git Blame** | Identify where bad patterns were introduced | `git blame fnGetAllUsers.js` |
| **Static Analysis (SonarQube)** | Detect naming inconsistencies | [SonarQube Rules](https://rules.sonarsource.com/java/) |
| **Code Similarity Checkers** | Find duplicate functions | [Simian](https://www.simiancode.com/) |
| **Pre-Commit Hooks** | Block commits with naming violations | `husky + lint-staged` |

---

## **4. Prevention Strategies**

### **1. Enforce Naming in CI/CD**
- Add a **pre-commit hook** that checks for `fn_*` compliance.
- Fail builds if naming rules are violated.

**Example (ESLint rule):**
```javascript
// .eslintrc.js
module.exports = {
  rules: {
    "naming-conventional-functions": [
      "error",
      { "prefix": "fn_" }  // Enforce `fn_` prefix
    ]
  }
};
```

### **2. Use TypeScript/Java for Stronger Enforcement**
- TypeScript interfaces enforce parameter consistency.
- Java generics prevent inconsistent entity types.

**Example (TypeScript):**
```typescript
interface UserRepository {
  fnGetUserById(id: string): Promise<User>;  // ✅ Type-safe
  fnLoginUser(credentials: { email: string }): Promise<User>;  // ✅
}
```

### **3. Document the Convention**
- Add a **CODEOWNERS file** explaining the `fn_*` rule.
- Include a **README named conventions** section.

### **4. Rotate Code Reviews**
- Have peers review pull requests for naming consistency.
- Use **GitHub/GitLab templates** to remind reviewers.

### **5. Automate Refactoring**
- Use **VS Code extensions** to refactor functions:
  - **Refactor This** (Chrome)
  - **Rename Symbol** (VS Code)

---

## **5. Final Checklist for Resolution**
✅ **Naming Consistency:** All functions use `fn_`.
✅ **Clear Actions:** Verbs are explicit (create, get, update, delete).
✅ **Entity Alignment:** Entity names match class names.
✅ **Parameter Logic:** Parameters match function intent.
✅ **No Duplicates:** No duplicate or near-duplicate functions.
✅ **Automated Enforcement:** CI/CD blocks violations.

---

## **Conclusion**
The `fn_*` naming convention improves code clarity but requires discipline. By following this guide:
1. **Audit** for inconsistencies.
2. **Fix** issues systematically.
3. **Enforce** conventions via tools.
4. **Prevent** regressions with automation.

**Next Steps:**
- Run a **codebase audit** using the tools above.
- **Refactor** the worst offenders first.
- **Set up CI checks** to maintain consistency.