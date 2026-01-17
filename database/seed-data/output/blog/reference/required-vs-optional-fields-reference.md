**[Pattern] Required vs Optional Fields Reference Guide**

---

### **Overview**
The **Required vs Optional Fields** pattern enables API consumers to distinguish between mandatory and optional fields when submitting or updating data. This pattern improves usability by:
- Clarifying data constraints upfront (reducing validation errors).
- Supporting optional fields for flexible data structures.
- Aligning with REST conventions and semantic clarity.

This guide covers schema design, implementation, and usage examples.

---

### **Schema Reference**
Use this table to define field requirements in your API schemas (OpenAPI/Swagger, JSON Schema, or GraphQL):

| **Field**       | **Type**       | **Format**       | **Requirement** | **Description**                     |
|-----------------|----------------|------------------|------------------|-------------------------------------|
| `user_id`       | string         | UUID            | Required         | Unique identifier for the user.     |
| `email`         | string         | Email address   | Required         | Valid email address.                |
| `password`      | string         | Secure hash     | Required         | Encrypted password (min 8 chars).   |
| `first_name`    | string         | Alphanumeric    | Optional         | User's first name.                  |
| `last_name`     | string         | Alphanumeric    | Optional         | User's last name.                   |
| `address`       | object         | Nested schema   | Optional         | Contains `street`, `city`, etc.      |

#### **Key Semantics:**
- **`required`**: Fields **must** be provided (e.g., `user_id`, `email`).
- **`optional`**: Fields **may** be omitted (e.g., `first_name`).
- **`default`**: Optional fields can include a default value (e.g., `"status": "active"`).

---

### **Implementation Details**
#### **1. Schema Design**
- **OpenAPI/Swagger**:
  ```yaml
  components:
    schemas:
      UserCreate:
        type: object
        properties:
          user_id:
            type: string
            format: uuid
            example: "550e8400-e29b-41d4-a716-446655440000"
            required: true
          email:
            type: string
            format: email
            required: true
        ```
- **JSON Schema**:
  ```json
  {
    "type": "object",
    "required": ["user_id", "email"],
    "properties": {
      "first_name": { "type": "string", "optional": true }
    }
  }
  ```

#### **2. Validation**
- **Server-side**: Use libraries like:
  - **Node.js**: `joi`, `express-validator`.
  - **Python**: `Pydantic`, `marshmallow`.
  - **Go**: `gorilla/validator`.
- **Client-side**: Flag required fields with UI prompts (e.g., `*` alongside fields).

#### **3. Error Handling**
Return clear errors for missing required fields:
```json
{
  "errors": {
    "user_id": ["This field is required."],
    "email": ["Must be a valid email."]
  }
}
```

---

### **Query Examples**
#### **1. POST Request (Full Data)**
Send all fields (required + optional):
```http
POST /api/users
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### **2. POST Request (Minimal Data)**
Omit optional fields:
```http
POST /api/users
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com"
}
```

#### **3. PATCH Request (Update)**
Partially update data (optional fields can be omitted):
```http
PATCH /api/users/550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "first_name": "Jane"  // Only update optional field
}
```

#### **4. GraphQL Query**
Use `input` objects to define required fields:
```graphql
mutation CreateUser($user: UserInput!) {
  createUser(user: $user) {
    userId
    email
  }
}
```
Variables:
```json
{
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "Jane"  // Optional
  }
}
```

---

### **Edge Cases & Best Practices**
1. **Partial Updates**:
   - PATCH requests should allow omitting optional fields unless the API specifies otherwise.
2. **Fallback Defaults**:
   - Set defaults for optional fields (e.g., `"status": "draft"`).
3. **Nested Objects**:
   - Apply the pattern recursively (e.g., `address` has its own required/optional fields).
4. **Documentation**:
   - Clearly label required fields in API docs (e.g., **Required** vs. **Optional**).
   - Use tools like **Swagger UI** or **Redoc** to visualize schemas.

---
### **Related Patterns**
1. **[Default Values](https://api-patterns.com/default-values)**
   - Define fallback values for optional fields.
2. **[Conditional Fields](https://api-patterns.com/conditional-fields)**
   - Dynamically show/hide fields based on user role or data.
3. **[Pagination](https://api-patterns.com/pagination)**
   - Complementary for optional query parameters (e.g., `?limit=10`).
4. **[Error Handling](https://api-patterns.com/error-handling)**
   - Standardize error responses for required field violations.
5. **[Nested Resources](https://api-patterns.com/nested-resources)**
   - Apply required/optional semantics to nested data structures.

---
### **See Also**
- [RESTful API Design Best Practices](https://restfulapi.net/)
- [JSON Schema Draft 7](https://json-schema.org/)
- [OpenAPI Specification](https://spec.openapis.org/)