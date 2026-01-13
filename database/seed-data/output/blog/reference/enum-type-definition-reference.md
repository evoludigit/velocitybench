# **[Pattern] Enum Type Definition Reference Guide**

---

## **Overview**
The **Enum Type Definition** pattern enforces strict, reusable, and predictable status or category values across an API. Enums limit invalid inputs by restricting responses to predefined sets of values (e.g., `ACTIVE`, `INACTIVE`, `PENDING`). This pattern improves data consistency, reduces schema complexity, and simplifies validation across systems.

Use this pattern when:
- Defining standardized statuses (e.g., `OrderStatus`, `UserRole`).
- Enforcing controlled vocabulary for categorical data.
- Supporting multi-language or localized labels (via `title` or `description`).
- Collaborating with other teams/applications requiring consistent terminology.

Unlike hardcoded strings, enums ensure modularity and scalability.

---

## **Implementation Details**
### **Key Concepts**
| Term               | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Core Enum**      | A focused enum for a single domain (e.g., `PaymentStatus`).                |
| **Union Enum**     | A set of independent enums used interchangeably (e.g., `OrderStatus` and `TaskStatus` sharing `COMPLETED`). |
| **Extensibility**  | New values must be added via API updates (backward compatibility via `default` or graceful degradation). |
| **Validation**     | Clients enforce conformance via OpenAPI `enum` constraints or runtime checks. |

---
### **Implementation Guidance**
1. **Define Clarity**: Use clear, unique values (e.g., `SUCCESS` vs. `OK`).
2. **Exhaustive List**: Include all possible states, even unused ones (e.g., `DELETED`).
3. **Descriptions**: Document each value’s purpose via `description` fields.
4. **Localization**: For multilingual systems, use linked resource objects for translations.
5. **Versioning**: Treat enum definitions as part of API versioning; avoid breaking changes.

---
### **Backward Compatibility**
- **Allow Unused Values**: Clients may ignore new enums if backward compatibility is critical.
- **Default Values**: Specify a `default` value for optional fields.
- **Graceful Fallback**: Use a `type: "string"` with validation instead of strict `enum` if legacy systems exist.

---

## **Schema Reference**
### **Core Schema**
| Field           | Type      | Required | Description                                                                                             | Example Values                          |
|-----------------|-----------|----------|---------------------------------------------------------------------------------------------------------|-----------------------------------------|
| `enum`          | `string`  | Yes      | Predefined status category.                                                                        | `ACTIVE`, `PENDING`, `CANCELLED`        |
| `title`         | `string`  | No       | Human-readable label (optional for multilingual support).                                             | `User Status`                           |
| `description`   | `string`  | No       | Additional context for the enum value.                                                              | *"User profile is active."*               |
| `state`         | `object`  | No       | Nested metadata (e.g., `status: "final"`).                                                          | `{ "status": "final" }`                 |

---
### **Example Enum Definition**
```json
{
  "OrderStatus": {
    "$id": "https://api.example.com/schemas/OrderStatus",
    "type": "string",
    "title": "Order Status",
    "description": "Possible states of an order during processing.",
    "enum": [
      {
        "value": "CREATED",
        "description": "Order submitted but not processed."
      },
      {
        "value": "PROCESSING",
        "description": "Order is being fulfilled."
      },
      {
        "value": "SHIPPED",
        "description": "Order dispatched to carrier."
      },
      {
        "value": "DELIVERED",
        "description": "Order received by customer."
      },
      {
        "value": "CANCELLED",
        "description": "Order was cancelled by customer or admin."
      }
    ]
  }
}
```

---
### **Nested Enum Example**
```json
{
  "type": "object",
  "properties": {
    "user": {
      "type": "object",
      "properties": {
        "role": {
          "$ref": "#/components/schemas/UserRole"
        }
      }
    }
  },
  "components": {
    "schemas": {
      "UserRole": {
        "type": "string",
        "enum": ["ADMIN", "EDITOR", "VIEWER", "GUEST"]
      }
    }
  }
}
```

---
### **Extensions**
| Extension          | Use Case                                                                                      | Example                          |
|--------------------|---------------------------------------------------------------------------------------------|----------------------------------|
| `deprecated`       | Mark obsolete values for future removal.                                                     | `"deprecated": true`              |
| `eventTrigger`     | Define triggers for system actions (e.g., `SHIPPED` triggers `NotificationService`).        | `"eventTrigger": "shipment_alert"`|
| `group`            | Organize enums into logical categories (e.g., `customer_management`).                       | `"group": "auth"`                 |

---

## **Query Examples**
### **1. Single Enum Field**
**Request**:
```http
GET /users?status=ACTIVE
```
**Response**:
```json
{
  "users": [
    {
      "id": 123,
      "name": "Alice",
      "status": "ACTIVE"
    }
  ]
}
```

---
### **2. Enum in Response Payload**
**Request**:
```http
GET /orders/456
```
**Response**:
```json
{
  "id": 456,
  "status": {
    "$ref": "https://api.example.com/schemas/OrderStatus#/definitions/CREATED"
  },
  "details": {
    "description": "Order submitted but not processed."
  }
}
```

---
### **3. Enum in POST Request**
**Request Body**:
```json
{
  "eventType": "payment_processing",
  "status": "SUCCESS"
}
```
**Request Headers**:
```http
Content-Type: application/json
X-API-Key: your_key_here
```

---
### **4. Enum with Localization (Nested Resource)**
**Request**:
```http
GET /users/role?lang=en
```
**Response**:
```json
{
  "role": "EDITOR",
  "translations": [
    { "lang": "en", "label": "Editor" },
    { "lang": "es", "label": "Editora" }
  ]
}
```

---
### **5. Validation Error (Invalid Enum)**
**Request**:
```http
POST /orders
Content-Type: application/json
{
  "status": "UNKNOWN_STATUS"
}
```
**Response (400 Bad Request)**:
```json
{
  "error": "Invalid enum value for field 'status'; allowed values are CREATED, PROCESSING, DELIVERED."
}
```

---

## **Related Patterns**
| Pattern                     | Description                                                                                     | Use Case                                   |
|-----------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------|
| **[Data Type Consistency]** | Standardize data formats (e.g., UUIDs, timestamps) for interoperability.                        | Global API design.                         |
| **[Localization]**           | Support multilingual labels and descriptions for enums.                                       | Multi-country deployments.                  |
| **[Versioning]**             | Manage enum changes via API versioning to avoid breaking clients.                            | Long-term system integration.               |
| **[Event-Driven Enum]**      | Pair enums with event triggers (e.g., `status=DELIVERED` → `order_delivered` event).            | Real-time notifications.                   |
| **[Composite Enums]**        | Combine multiple enum types into a single field (e.g., `OrderStatus & CustomerTier`).         | Complex filtering.                         |
| **[OpenAPI Validation]**     | Use OpenAPI/Swagger `enum` constraints for client-side validation.                            | Schema-first development.                  |

---
### **Examples of Related Use Cases**
1. **Event-Driven Enum**:
   - Define an enum like `eventType` with values tied to microservices.
   ```json
   { "eventType": "payment_failed", "status": "FAILED" }
   ```
   - Trigger: `payment_failed` event → `ReconciliationService`.

2. **Composite Enum**:
   ```json
   {
     "order": {
       "status": { "value": "SHIPPED", "customerTier": ["PREMIUM", "STANDARD"] }
     }
   }
   ```

3. **Localization + Enum**:
   ```json
   {
     "role": "VIEWER",
     "translations": [
       { "lang": "fr", "label": "Voyeur" }
     ]
   }
   ```

---
## **Best Practices**
1. **Avoid Overuse**: Use enums only for categorical states, not for dynamic data (e.g., free-text fields).
2. **Document Exhaustively**: Include descriptions for all values, including rare states.
3. **Support Versioning**: Tag enum definitions with API versions to manage breaking changes.
4. **Client-Side Validation**: Enforce enum compliance via OpenAPI tools (e.g., Swagger Codegen).
5. **Deprecation Strategy**: Use `deprecated: true` + `reason` for phase-out values.

---
## **Anti-Patterns**
| **Pattern**               | **Problem**                                                                                     | **Solution**                                      |
|---------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------|
| Hardcoded Strings         | Inconsistent values across systems (e.g., `1` vs. `active`).                                    | Use enums with descriptions.                      |
| Overly Granular Enums     | Excessive values (e.g., 50+ states) → complex logic.                                           | Merge similar states (e.g., `ACTIVE`/`INACTIVE`). |
| No Backward Compatibility | Removing old enum values breaks existing clients.                                               | Add `default` values or graceful fallbacks.        |
| Static Enum Definitions   | Enums locked to a single language.                                                              | Support nested `translations` or external lookup. |

---
## **Tools & Libraries**
| Tool/Library               | Purpose                                                                                     |
|----------------------------|---------------------------------------------------------------------------------------------|
| **Swagger/OpenAPI**        | Define enums in schema with `enum` arrays.                                                  |
| **JSON Schema**            | Validate enum values at runtime.                                                             |
| **GraphQL**                | Use `enum` types in GraphQL schemas.                                                        |
| **Postman/Newman**         | Test enum values via Collections and environment variables.                                  |
| **Zod (TypeScript)**       | Runtime validation of enums.                                                               |
| **Apache Avro/Protobuf**   | Schema evolution for enums in distributed systems.                                           |

---
## **Example in Different Languages**
### **Python (Pydantic)**
```python
from pydantic import BaseModel, Field
from enum import Enum

class OrderStatus(str, Enum):
    CREATED = "CREATED"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"

class Order(BaseModel):
    id: int
    status: OrderStatus = Field(..., description="Order processing state.")
```

---
### **JavaScript (TypeScript)**
```typescript
enum OrderStatus {
  CREATED = "CREATED",
  SHIPPED = "SHIPPED",
  CANCELLED = "CANCELLED"
}

interface Order {
  status: OrderStatus;
  details: { description: string };
}
```

---
### **Go**
```go
package models

type OrderStatus string

const (
	CREATED    OrderStatus = "CREATED"
	SHIPPED    OrderStatus = "SHIPPED"
	CANCELLED  OrderStatus = "CANCELLED"
)

type Order struct {
	Status    OrderStatus
	Details   string
}
```

---
## **Troubleshooting**
| Issue                          | Root Cause                          | Solution                                      |
|---------------------------------|-------------------------------------|-----------------------------------------------|
| **Invalid Enum Value**         | Client submits unlisted value.       | Validate via schema (e.g., OpenAPI `enum`).   |
| **Deprecated Value Used**      | Older system depends on obsolete enum.| Add fallback or deprecation notice.           |
| **Missing Localization**        | Enum labels not supported in target language. | Extend with `translations` field.             |
| **Enum Evolution Conflicts**    | New values break client parsing.    | Version enums or use feature flags.           |

---
## **Further Reading**
- [OpenAPI Spec: Enumeration](https://swagger.io/specification/)
- [JSON Schema Draft-7 Enums](https://json-schema.org/understanding-json-schema/reference/enum.html)
- [ASTM Pattern for Enums](https://www.astm.org/standards-books/pdfs/ENM0300.pdf) (for enterprise systems)
- [Event-Driven Architecture with Enums](https://www.eventstore.com/blog/event-driven-architecture-with-enums)

---
**Version**: 1.2
**Last Updated**: [Insert Date]
**Maintainer**: [Your Team/Organization]