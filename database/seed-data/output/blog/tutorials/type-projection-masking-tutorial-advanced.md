```markdown
---
title: "Type Projection with Auth Masking: Secure and Flexible API Design"
date: 2023-10-15
author: Jane Doe
tags: ["backend", "database design", "api design", "authorization", "security", "DDD"]
summary: "Learn how to apply authorization rules at the type projection level to mask sensitive fields in API responses. This tutorial covers the problem, solution, tradeoffs, and practical code examples in TypeScript/JavaScript with NestJS, Django, and Go."
---

# Type Projection with Auth Masking: Secure and Flexible API Design

As backend engineers, we build APIs that expose domain models to clients—whether they’re mobile apps, web services, or third-party integrations. But exposing *all* fields from your database to any client is a security risk. Some fields might be sensitive (e.g., `credit_card_number`, `salary`), while others might be irrelevant to certain users (e.g., a salesperson shouldn’t see their manager’s `department_budget`).

This is where **Type Projection with Auth Masking** comes in. It’s a design pattern that ensures your API responses are *both* secure *and* flexible: you define clear projections of domain models that clients can consume, and you mask fields based on the requesting user’s permissions. This approach contrasts with brute-force authorization checks (e.g., filtering queries or rejecting entire responses) by applying fine-grained control at the *response layer*.

In this post, I’ll walk you through:
1. The problem of unmasked sensitive data in API responses,
2. How Type Projection with Auth Masking solves it,
3. Practical implementations in TypeScript (NestJS), Python (Django), and Go,
4. Key tradeoffs and anti-patterns,
5. Best practices for maintainability.

---

## The Problem: Masking Not Applied to Response Fields

Let’s start with a concrete example. Imagine a `User` entity with fields like:
- `id` (public)
- `name` (public)
- `email` (public)
- `salary` (restricted to admins)
- `ssn` (highly sensitive, restricted to HR only).

If you follow common practices like **Open API/Swagger** or **GraphQL**, you might define your API like this:

```typescript
// NestJS (OpenAPI) or GraphQL schema
class User extends Object {} // or ModelDefinition
User.fields = {
  id: { type: 'string' },
  name: { type: 'string' },
  email: { type: 'string' },
  salary: { type: 'number', hidden: false }, // 🟡 Oops!
  ssn: { type: 'string', hidden: false },     // 🟡 Oops!
};
```

But if you don’t apply auth masking, every client gets *everything*—even unauthorized users:

```typescript
// Unauthorized request from a non-admin user (e.g., a customer)
getUser(userId) -> { id: "...", name: "...", email: "...", salary: "100000" } 🚨
```

This violates the principle of [least privilege](https://en.wikipedia.org/wiki/Least_privilege) and exposes sensitive data accidentally. Worse yet, if your schema is open (e.g., GraphQL), users might even *query* restricted fields:

```graphql
query {
  user(id: "123") {
    ssn # 💥 HR-only data!
  }
}
```

### Common Reactions and Pitfalls
- **"I’ll filter in the SQL query"** → Not always possible (e.g., joins or subqueries).
- **"I’ll use middleware"** → Overly broad; middleware can’t handle every auth edge case.
- **"I’ll just return `null` for unauthorized fields"** → Can confuse clients with inconsistent responses (e.g., a field might be `null` or missing entirely).

The root issue is that your domain model (`User`) and your API response model are often tightly coupled, exposing implementation details instead of controlled projections.

---

## The Solution: Type Projection with Auth Masking

The solution is to **decouple domain models from API projections**. You define *projection types* that:
1. Represent what a client *should* see (not what your DB stores).
2. Apply authorization rules to mask fields dynamically.

### Core Components

| Component               | Purpose                                                                 |
|-------------------------|-------------------------------------------------------------------------|
| **Domain Model**        | The raw data (e.g., `User` with all fields in the DB).                  |
| **Projection**          | A filtered/transformed subset of the domain model (e.g., `PublicUser`). |
| **Auth Masking Logic**  | Rules to determine which fields are visible to the current user.       |
| **Response Builder**    | Combines domain data with projections and masks fields.                 |

### Example Workflow
1. A user requests `/users/123`.
2. Your service fetches the `User` domain object.
3. An `AuthMaskingMiddleware` (or similar) determines the user’s permissions (e.g., admin, manager, employee).
4. A `UserProjection` factory returns a subset of fields (e.g., `PublicUser` or `ManagerUser`).
5. The masked response is returned.

---

## Implementation Guide

Let’s implement this pattern in three popular backends: **NestJS (TypeScript)**, **Django (Python)**, and **Go**.

---

### 1. NestJS (TypeScript)
#### Step 1: Define Domain and Projection Types
```typescript
// user.entity.ts
export class User {
  constructor(
    public readonly id: string,
    public name: string,
    public email: string,
    public salary: number,
    public ssn: string, // 🚨 Highly sensitive!
  ) {}
}

// user.projection.ts
export class PublicUser {
  constructor(
    public readonly id: string,
    public name: string,
    public email: string,
  ) {}
}

export class ManagerUser extends PublicUser {
  constructor(
    public readonly id: string,
    public name: string,
    public email: string,
    public teamSize: number, // Only for managers
  ) {
    super(id, name, email);
  }
}
```

#### Step 2: Add Auth Masking Logic
We’ll use a **decorator** to mark fields as restricted, then apply masking in a middleware.

```typescript
// auth.masking.decorator.ts
export const IsPublic = () => Reflect.metadata('auth:mask', { visible: true });
export const RequiresAdmin = () => Reflect.metadata('auth:mask', { role: 'admin' });
export const RequiresManager = () => Reflect.metadata('auth:mask', { role: 'manager' });

// Example usage on the User class:
class User {
  @IsPublic()
  id: string;

  @IsPublic()
  name: string;

  @IsPublic()
  email: string;

  @RequiresAdmin()
  salary: number;

  @RequiresManager()
  ssn: string;
}
```

#### Step 3: Create a Masking Middleware
```typescript
// auth.masking.middleware.ts
import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { User } from './user.entity';

@Injectable()
export class AuthMaskingMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction) {
    const user = req.user as User; // Assume AuthGuard sets this.

    // Mask sensitive fields based on user role.
    if (user.role !== 'admin' && user.salary) {
      user.salary = '****'; // Mask salary
    }

    if (user.role !== 'manager' && user.ssn) {
      user.ssn = null; // Or omit entirely.
    }

    next();
  }
}
```

#### Step 4: Apply Middleware and Return Projections
```typescript
// user.controller.ts
@Controller('users')
export class UserController {
  constructor(private userService: UserService) {}

  @Get(':id')
  async getUser(
    @Param('id') id: string,
    @CurrentUser() user: User,
  ) {
    const domainUser = await this.userService.findById(id);

    // Apply projection based on user role.
    if (user.role === 'admin') {
      return domainUser; // Full access.
    } else if (user.role === 'manager') {
      return new ManagerUser(domainUser.id, domainUser.name, domainUser.email, 5); // Team size example.
    } else {
      return new PublicUser(domainUser.id, domainUser.name, domainUser.email);
    }
  }
}
```

#### Tradeoffs in NestJS
- **Pros**: Clean separation of concerns; projections are explicit.
- **Cons**: Overuse of decorators can make code harder to debug. Middleware adds latency.

---

### 2. Django (Python)
Django’s ORM and class-based views make this pattern easier to implement.

#### Step 1: Define Models and Projections
```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    ssn = models.CharField(max_length=11)  # 🚨 Sensitive!

    class Meta:
        permissions = [
            ('view_salary', 'Can view salary'),
        ]
```

#### Step 2: Create a Projection Mixin
```python
# projections.py
from django.db.models import Model

class UserProjection:
    @classmethod
    def public(cls, user_profile: UserProfile) -> dict:
        return {
            'id': user_profile.user.id,
            'name': user_profile.user.get_full_name(),
            'email': user_profile.user.email,
        }

    @classmethod
    def manager(cls, user_profile: UserProfile) -> dict:
        return {
            **cls.public(user_profile),
            'team_size': 5,  # Example dynamic data.
        }
```

#### Step 3: Use Class-Based Views with Permission Checks
```python
# views.py
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from .models import UserProfile
from .projections import UserProjection

class CanViewSalary(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('userprofile.view_salary')

class UserDetailView(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()

    @action(detail=True, methods=['get'])
    @permission_classes([IsAuthenticated, CanViewSalary])
    def get_salary(self, request, pk=None):
        profile = self.get_object()
        return Response({
            **UserProjection.public(profile),
            'salary': profile.salary,
        })

    @action(detail=True, methods=['get'])
    def get_public(self, request, pk=None):
        profile = self.get_object()
        return Response(UserProjection.public(profile))
```

#### Tradeoffs in Django
- **Pros**: Built-in permission system; projections are flexible.
- **Cons**: Class-based views can become verbose for complex logic.

---

### 3. Go (Gin Framework)
Go’s structs and middleware make this pattern straightforward.

#### Step 1: Define Domain and Projections
```go
// user.go
type User struct {
    ID          string `json:"id"`
    Name        string `json:"name"`
    Email       string `json:"email"`
    Salary      float64 `json:"salary,omitempty"` // Omit if not visible
    SSN         string `json:"-"` // Omit entirely in JSON
    Role        string `json:"role"`
}

type PublicUser struct {
    ID    string `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

type ManagerUser struct {
    PublicUser
    TeamSize int `json:"team_size"`
}
```

#### Step 2: Add Middleware for Masking
```go
// auth.go
package middleware

import (
    "net/http"
    "github.com/gin-gonic/gin"
)

func AuthMaskingMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        user := c.GetString("user") // Assume AuthMiddleware sets this.

        // Mask SSN unless user is HR.
        if user != "hr" {
            c.Request.URL.Query().Set("mask_ssn", "true")
        }
    }
}
```

#### Step 3: Serialize with Projections
```go
// handler.go
func GetUser(c *gin.Context) {
    var user User
    if err := c.ShouldBindJSON(&user); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    // Apply projection based on user role.
    switch user.Role {
    case "admin":
        c.JSON(http.StatusOK, user)
    case "manager":
        c.JSON(http.StatusOK, ManagerUser{
            PublicUser: PublicUser{
                ID:   user.ID,
                Name: user.Name,
                Email: user.Email,
            },
            TeamSize: 5,
        })
    default:
        c.JSON(http.StatusOK, PublicUser{
            ID:   user.ID,
            Name: user.Name,
            Email: user.Email,
        })
    }
}
```

#### Tradeoffs in Go
- **Pros**: Explicit structs; middleware is lightweight.
- **Cons**: JSON tag manipulation can be brittle if projections change often.

---

## Common Mistakes to Avoid

1. **Overusing Projections**
   - *Mistake*: Creating a new projection for every role (e.g., `AdminUser`, `ManagerUser`, `EditorUser`).
   - *Fix*: Share common fields (e.g., `PublicUser`) and extend selectively. Use inheritance or composition.

2. **Ignoring Performance**
   - *Mistake*: Fetching the full domain model and masking in-memory for every request.
   - *Fix*: Pre-filter queries (e.g., exclude `salary` in `SELECT * FROM users WHERE salary IS NULL`).

3. **Hardcoding Permissions**
   - *Mistake*: Baking auth rules into projections (e.g., `AdminUser` always includes `ssn`).
   - *Fix*: Use a central permission system (e.g., RBAC) to determine visibility.

4. **Not Testing Edge Cases**
   - *Mistake*: Only testing happy paths (e.g., admin sees all fields).
   - *Fix*: Test unauthorized access (e.g., does a user get `null` or an error for restricted fields?).

5. **Tight Coupling with ORM**
   - *Mistake*: Assuming projections map 1:1 to DB columns.
   - *Fix*: Decouple projections from ORM fields (e.g., `display_name` vs. `first_name + last_name`).

---

## Key Takeaways

- **Type Projection** decouples your domain model from API responses, improving flexibility.
- **Auth Masking** applies security rules *at the response layer*, not just in queries or middleware.
- **Tradeoffs**:
  - *Pros*: Secure, flexible, and explicit.
  - *Cons*: Slightly more boilerplate; requires careful design.
- **Best Practices**:
  - Use decorators (TypeScript) or annotations (Java) to mark restricted fields.
  - Prefer composition over inheritance for projections (e.g., `ManagerUser` extends `PublicUser`).
  - Test projections with users of different roles.

---

## Conclusion: Security Through Projection

Type Projection with Auth Masking is a powerful way to design APIs that are both **secure** and **client-friendly**. By explicitly defining what clients should see—and masking the rest—you avoid accidental data leaks while keeping your codebase maintainable.

### When to Use This Pattern
- Your API serves multiple client types (e.g., admin dashboard vs. mobile app).
- You have sensitive fields that shouldn’t be exposed to all users.
- You want to future-proof your API (e.g., adding new fields won’t break existing clients).

### Alternatives to Consider
- **GraphQL**: Uses field-level permissions out of the box (but requires careful schema design).
- **REST with HATEOAS**: Uses links to resources instead of projections (but less flexible for masking).
- **Event Sourcing**: Projects are derived from events; useful for audit trails but adds complexity.

This pattern isn’t a silver bullet—it requires upfront design effort—but the payoff is cleaner APIs and fewer security headaches. Start small (e.g., mask one sensitive field), and iterate as your needs grow.

Happy projecting!
```

---
**Appendix**:
- [NestJS Auth Masking Demo](https://github.com/example/auth-masking-nestjs)
- [Django Projection Patterns](https://github.com/example/django-projections)
- [Go Auth Middleware Examples](https://github.com/example/go-auth-middleware)