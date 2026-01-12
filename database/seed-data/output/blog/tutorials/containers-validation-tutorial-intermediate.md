```markdown
# **Containers Validation Pattern: Structuring Data Validation for Scalability and Maintainability**

*How to validate nested data gracefully—without code duplication, performance bottlenecks, or ugly error messages.*

---

## **Introduction**

As your API grows, so does the complexity of the data it handles. Early on, you might validate inputs with simple checks in controller methods or outright rely on database constraints. But when your requests include nested objects, arrays of validation rules, or cross-field dependencies (e.g., verifying a password matches another field), things quickly spiral into spaghetti code.

This is where the **Containers Validation pattern** shines. Instead of scattering validation logic across controllers, services, or even frontend code, you group related validation rules into **dedicated containers**—reusable, testable, and maintainable components. This pattern helps you:
- **Centralize validation rules** (no duplicate checks).
- **Separate validation from business logic** (cleaner controllers).
- **Handle nested data elegantly** (arrays, objects, and recursive validation).
- **Provide rich error feedback** (user-friendly messages).

In this guide, we’ll explore how to implement this pattern in practice, using **Node.js with TypeScript** and **Express** as our example stack (but the concepts apply to any language/framework).

---

## **The Problem: Validation Spaghetti**

Imagine a signup flow with these requirements:

1. A user must provide a valid email and password.
2. The email must not conflict with existing users.
3. The password must:
   - Be at least 8 characters long.
   - Contain at least one uppercase letter.
   - Contain at least one digit.
4. If the user is a "premium" type, they must provide a `premiumPlanId`.
5. All fields must be non-empty.

### **Current Approach (Without Containers Validation)**
Without a structured approach, you might end up with:

```javascript
// controllers/userController.js
async function createUser(req, res) {
  const { email, password, premiumPlanId } = req.body;

  // Rule 1: Email must be non-empty
  if (!email) return res.status(400).json({ error: "Email is required" });

  // Rule 2: Email format validation (simplified)
  if (!/^\S+@\S+\.\S+$/.test(email)) {
    return res.status(400).json({ error: "Invalid email format" });
  }

  // Rule 3: Password rules
  const hasUpperCase = password.match(/[A-Z]/);
  const hasDigit = password.match(/\d/);
  if (password.length < 8 || !hasUpperCase || !hasDigit) {
    return res.status(400).json({
      error: "Password must be at least 8 chars with uppercase and a digit",
    });
  }

  // Rule 4: Premium check (simplified)
  if (req.body.type === "premium" && !premiumPlanId) {
    return res.status(400).json({ error: "Premium plan ID is required" });
  }

  // Database check (simplified)
  const existingUser = await db.query("SELECT * FROM users WHERE email = ?", [email]);
  if (existingUser.length) {
    return res.status(400).json({ error: "Email already in use" });
  }

  // ... business logic
}
```

### **Problems with This Approach**
1. **Controller Bloat**: The method grows unmanageably long.
2. **Repetition**: Validation logic repeats across endpoints (e.g., `login`, `updateUser`).
3. **Hard to Maintain**: Adding a new rule (e.g., "password must not contain the username") requires digging through code.
4. **Poor Error Messages**: Generic errors like `"Invalid email format"` don’t help users.
5. **No Reusability**: Validation rules aren’t reusable across services (e.g., the same rules should apply to password reset flows).

---

## **The Solution: Containers Validation**

The **Containers Validation** pattern organizes validation logic into **dedicated containers** that:
1. Define **rules** for data shapes (e.g., `UserSignup`, `UserUpdate`).
2. **Group related rules** (e.g., password rules, email rules).
3. **Generate structured errors** with clear messages.
4. **Support nested validation** (arrays, objects, recursive checks).

### **Key Components**
| Component          | Responsibility                                                                 |
|--------------------|-------------------------------------------------------------------------------|
| **Validator**      | Core class that applies rules to data and collects errors.                   |
| **Rule**           | Represents a single validation rule (e.g., `MustBeEmail`, `MustMatchPassword`). |
| **RuleGroup**      | Combines rules for a specific domain (e.g., `PasswordRules`).                 |
| **ValidationContainer** | Groups related rules under a name (e.g., `UserSignupContainer`).          |

---

## **Implementation Guide**

### **Step 1: Define the Validator Base Class**
This class will handle the core logic of applying rules and collecting errors.

```typescript
// src/validators/validator.ts
import { ValidationError } from "./validation-error";

export abstract class Validator<T> {
  protected errors: ValidationError[] = [];

  abstract validate(data: Partial<T>): void;

  getErrors(): ValidationError[] {
    return this.errors;
  }

  protected addError(field: string, message: string): void {
    this.errors.push(new ValidationError(field, message));
  }

  protected isValid(): boolean {
    return this.errors.length === 0;
  }
}
```

### **Step 2: Create Rule Classes**
Each rule checks a specific condition and adds errors when violated.

```typescript
// src/validators/rules/email-rule.ts
import { Validator } from "../validator";

export class MustBeEmailRule extends Validator<string> {
  validate(email: string): void {
    if (!email) {
      this.addError("email", "Email is required");
      return;
    }

    if (!/^\S+@\S+\.\S+$/.test(email)) {
      this.addError("email", "Invalid email format");
    }
  }
}

// src/validators/rules/password-rule.ts
import { Validator } from "../validator";

export class PasswordRules extends Validator<string> {
  validate(password: string): void {
    if (!password) {
      this.addError("password", "Password is required");
      return;
    }

    if (password.length < 8) {
      this.addError("password", "Password must be at least 8 characters");
    }

    if (!/[A-Z]/.test(password)) {
      this.addError("password", "Password must contain an uppercase letter");
    }

    if (!/\d/.test(password)) {
      this.addError("password", "Password must contain a digit");
    }
  }
}

// src/validators/rules/premium-rule.ts
import { Validator } from "../validator";

export class MustProvidePremiumPlan extends Validator<{ premiumPlanId?: string }> {
  validate(data: { premiumPlanId?: string }): void {
    if (data.type === "premium" && !data.premiumPlanId) {
      this.addError("premiumPlanId", "Premium plan ID is required");
    }
  }
}
```

### **Step 3: Create a Validation Container**
Containers group related rules and provide a clean interface for validation.

```typescript
// src/validators/containers/user-signup-container.ts
import { Validator } from "../validator";
import { MustBeEmailRule } from "../rules/email-rule";
import { PasswordRules } from "../rules/password-rule";
import { MustProvidePremiumPlan } from "../rules/premium-rule";

interface UserSignupInput {
  email: string;
  password: string;
  type?: "premium";
  premiumPlanId?: string;
}

export class UserSignupContainer extends Validator<UserSignupInput> {
  private emailRule = new MustBeEmailRule();
  private passwordRules = new PasswordRules();
  private premiumRule = new MustProvidePremiumPlan();

  validate(data: UserSignupInput): void {
    // Email validation
    this.emailRule.validate(data.email);

    // Password validation
    this.passwordRules.validate(data.password);

    // Premium type validation
    this.premiumRule.validate({ ...data, type: data.type });
  }

  getErrors(): ValidationError[] {
    return this.errors;
  }
}
```

### **Step 4: Use the Container in Your Controller**
Now your controller becomes clean and focused on business logic.

```typescript
// controllers/userController.ts
import { UserSignupContainer } from "../validators/containers/user-signup-container";

async function createUser(req, res) {
  const container = new UserSignupContainer();
  container.validate(req.body);

  if (!container.isValid()) {
    return res.status(400).json({ errors: container.getErrors() });
  }

  // Business logic & database calls
  const user = await db.query(
    "INSERT INTO users (email, password_hash) VALUES (?, ?) RETURNING *",
    [req.body.email, hashedPassword]
  );

  res.status(201).json(user);
}
```

### **Step 5: Handle Nested Data (Arrays/Objects)**
For nested validation (e.g., validating an array of user roles), extend the container pattern:

```typescript
// src/validators/containers/role-container.ts
import { Validator } from "../validator";

export class RoleContainer extends Validator<{ roles: string[] }> {
  validate(data: { roles: string[] }): void {
    const validRoles = ["admin", "user", "editor"];
    data.roles.forEach((role, index) => {
      if (!validRoles.includes(role)) {
        this.addError(`roles[${index}]`, "Invalid role");
      }
    });
  }
}
```

### **Step 6: Database-Side Validation (Optional)**
For extra safety, validate against the database schema. For example, in PostgreSQL:

```sql
-- Create a table with constraints
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  type VARCHAR(20),
  premium_plan_id VARCHAR(36),
  CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$')
);
```

---

## **Common Mistakes to Avoid**

1. **Overcomplicating Rules**
   - ❌ Don’t create a separate rule class for every tiny check (e.g., `MustBeNonEmpty`).
   - ✅ Use generic rules (`MustMatchPattern`) and combine them.

2. **Ignoring Performance**
   - ❌ Validate everything on every request, even if it’s redundant.
   - ✅ Cache validation results where possible (e.g., memoize regex checks).

3. **Poor Error Messages**
   - ❌ Generic errors: `"Invalid input"`.
   - ✅ Specific errors: `"Password must contain at least one uppercase letter"`.

4. **Not Handling Nested Data**
   - ❌ Skip validation for arrays/objects inside payloads.
   - ✅ Extend containers to handle nested structures (e.g., `UserWithRolesContainer`).

5. **Tight Coupling to Business Logic**
   - ❌ Mix validation with business rules (e.g., "if user is premium, validate premium ID").
   - ✅ Keep containers focused on input validation.

---

## **Key Takeaways**
✅ **Centralize validation** – Move rules out of controllers.
✅ **Reuse containers** – Apply the same rules across endpoints.
✅ **Group related rules** – Use `RuleGroup` or `Container` for domains (e.g., `UserSignup`).
✅ **Provide clear errors** – Help users fix issues with specific messages.
✅ **Handle nested data** – Extend containers for objects/arrays.
✅ **Combine with DB constraints** – Use schema constraints for extra safety.

---

## **Conclusion**

The **Containers Validation pattern** transforms messy, scattered validation into a maintainable, reusable system. By separating validation logic from business logic, you reduce technical debt, improve error handling, and make your API more scalable.

### **Next Steps**
1. **Start small**: Apply this pattern to one complex endpoint first.
2. **Expand incrementally**: Add nested validation as needed.
3. **Test thoroughly**: Validate edge cases (empty inputs, malformed data).
4. **Consider libraries**: If reinventing the wheel feels tedious, explore libraries like:
   - [Zod](https://github.com/colinhacks/zod) (TypeScript-first validation)
   - [Joi](https://joi.dev/) (JavaScript)
   - [Lucid](https://lucide.io/) (for database-aware validation)

Validation isn’t glamorous, but it’s the foundation of a robust API. By investing time in structured validation, you’ll save hours of debugging in the long run.

Happy coding! 🚀
```

---
**Appendix: Full Code Repository**
For a complete implementation, check out this [GitHub repo](https://github.com/your-repo/containers-validation-pattern).