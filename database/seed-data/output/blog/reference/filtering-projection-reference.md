# **[Pattern] API Request/Response Filtering & Projection Reference Guide**

---
## **1. Overview**
Clients frequently require only specific fields from API responses rather than entire object payloads, which improves performance, reduces bandwidth, and enhances API usability. **Filtering & Projection** patterns allow clients to specify which data to request, enabling efficient data retrieval. Common implementations include:

- **GraphQL** – Clients define exact data requirements in queries.
- **Sparse Fieldsets** – Clients explicitly list requested fields (e.g., `?fields=id,name`).
- **Query Parameters** – Clients use standardized parameters (e.g., `?projection=name,email`).

This pattern reduces unnecessary data transfer while maintaining flexibility for different client needs.

---

## **2. Key Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                 | **Example**                                  |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| **Projection**         | Specifies which fields should be included in the response.                                                                                                                                                   | `GET /users?projection=id,name`              |
| **Filtering**          | Restricts responses to objects matching predefined criteria (e.g., `?age>25`).                                                                                                                               | `GET /users?age=gt:25`                       |
| **Sparse Fieldsets**   | Clients explicitly list requested fields, ensuring only relevant data is returned.                                                                                                                               | `?fields=firstName,lastName,email`           |
| **GraphQL**            | Clients define exact response shape in a declarative query language.                                                                                                                                         | `{ user(id: "123") { name, email } }`        |
| **Pagination**         | Often paired with projection to limit result sets (e.g., `?limit=10&offset=0`).                                                                                                                              | `GET /products?fields=name,price&limit=5`    |

---

## **3. Implementation Strategies**
### **3.1 Sparse Fieldsets (Parameter-Based Projection)**
Clients pass a comma-separated list of allowed fields via query parameters.

#### **Schema Reference**
| **Parameter** | **Type**   | **Description**                                                                 | **Example**                     |
|---------------|------------|---------------------------------------------------------------------------------|---------------------------------|
| `fields`      | String[]   | Specifies allowed fields in the response (whitelist).                          | `?fields=id,name,email`          |
| `include`     | String[]   | Optional subtree inclusion (nested objects).                                   | `?include=address.city`          |
| `exclude`     | String[]   | Optional fields to exclude (blacklist).                                        | `?exclude=password`              |

#### **Query Examples**
```http
# Basic projection
GET /users?fields=id,name,email

# Including nested fields
GET /users?fields=id,profile{name,age}

# Excluding sensitive data
GET /users?exclude=password&fields=id,name
```

#### **Server-Side Constraints**
- **Whitelist Enforcement**: Only fields explicitly listed in `fields` are returned.
- **Validation**: Ensure no invalid fields are allowed (e.g., `?fields=secret` → `400 Bad Request`).

---

### **3.2 GraphQL (Declarative Querying)**
Clients define precise data requirements using GraphQL syntax.

#### **Schema Reference**
| **Node**         | **Description**                                                                                     |
|------------------|-----------------------------------------------------------------------------------------------------|
| `Query`          | Root node for all operations (e.g., `GET /graphql`).                                               |
| `UserFields`     | Supported fields (e.g., `id`, `name`, `email`). Chained with `{ }`.                              |
| `Filters`        | Conditions (e.g., `where: { age: { gt: 25 } }`).                                                   |
| `Pagination`     | `first`, `after`, `last` tokens (relay cursor-based pagination).                                  |

#### **Query Examples**
```graphql
# Fetch user with specific fields
query {
  user(id: "123") {
    name
    email
  }
}

# Filtered list with pagination
query {
  users(where: { age: { gt: 25 } }, first: 10) {
    edges {
      node { id name }
    }
  }
}
```

#### **Server-Side Constraints**
- **Introspection**: Enable GraphQL introspection (`/graphql`) to explore schema.
- **Depth Limiting**: Prevent overly nested queries (e.g., `maxDepth: 3`).
- **Complexity Analysis**: Reject queries exceeding a defined cost threshold.

---

### **3.3 RESTful Query Parameters (Simplified Projection)**
Standardized query parameters for lightweight filtering/projection.

#### **Schema Reference**
| **Parameter** | **Type**   | **Description**                                                                                     | **Example**                     |
|---------------|------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `?projection` | String[]   | Comma-separated list of fields to include (e.g., `name,email`).                                      | `?projection=name,email`        |
| `?filter`     | String     | Key-value pair filtering (e.g., `status=active`).                                                   | `?filter=status=active`         |
| `?sort`       | String     | Sort order (e.g., `?sort=-createdAt`).                                                               | `?sort=asc:id`                  |

#### **Query Examples**
```http
# Project only name/email
GET /users?projection=name,email

# Filter active users, sorted by name
GET /users?filter=active=true&sort=name

# Paginated results
GET /users?projection=id,name&limit=10&offset=0
```

#### **Server-Side Constraints**
- **Field Whitelisting**: Validate `projection` against allowed fields.
- **Operator Support**: Support `eq`, `gt`, `lt` (e.g., `?filter=age=gt:30`).

---

## **4. Best Practices**
| **Guideline**                          | **Recommendation**                                                                                     |
|----------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Default Behavior**                   | Return minimal fields by default unless projection is specified.                                      |
| **Error Handling**                     | Return `400 Bad Request` for invalid field lists or queries.                                           |
| **Performance**                        | Cache projected responses when possible (e.g., Redis).                                                |
| **Documentation**                      | Clearly list supported fields in API docs (e.g., Swagger/OpenAPI).                                   |
| **GraphQL-Specific**                   | Implement rate limiting to prevent abuse.                                                            |
| **REST-Specific**                      | Use consistent naming (e.g., `?fields=` vs. `?projection=`).                                           |

---

## **5. Query Examples (Comparative)**
| **Pattern**       | **Request**                                                                                     | **Response**                                                                                     |
|-------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Sparse Fieldset** | `GET /users?fields=id,name,email`                                                              | `{ "id": 1, "name": "Alice", "email": "alice@example.com" }`     |
| **GraphQL**       | `query { user(id: "123") { name email } }`                                                      | Same structured response as above.                                                              |
| **REST Projection** | `GET /users?projection=name,email`                                                              | `{ "name": "Alice", "email": "alice@example.com" }` (minimalist) |

---

## **6. Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **Use Case**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Pagination]**                 | Limits result sets via `limit`/`offset` or cursor-based pagination.                               | Large datasets where full results are impractical.                                               |
| **[Caching]**                    | Stores projected responses to reduce server load.                                                 | High-traffic APIs with repeated projections.                                                     |
| **[GraphQL Subscriptions]**      | Real-time updates for projected data streams.                                                      | Live dashboards or notifications.                                                                |
| **[Request Validation]**         | Ensures queries conform to schema rules (e.g., no circular references in GraphQL).                | Security and reliability.                                                                        |
| **[Rate Limiting]**              | Controls query frequency to prevent abuse (e.g., GraphQL complexity-based limits).                  | Protection against excessive data requests.                                                      |
| **[HATEOAS]**                     | Links in responses enable dynamic exploration of projections.                                     | Discoverable APIs where clients may not know available fields.                                   |

---
## **7. Tools & Libraries**
| **Technology**   | **Description**                                                                                     | **Links**                                                                                       |
|------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **GraphQL**      | [Apollo Server](https://www.apollographql.com/docs/apollo-server/), [Hasura](https://hasura.io/) | Server-side GraphQL implementations.                                                            |
| **Sparse Fieldsets** | [Spring Data REST](https://spring.io/projects/spring-data-rest), [Django REST Framework](https://www.django-rest-framework.org/) | REST framework support.                                                                          |
| **Validation**   | [Zod](https://github.com/colinhacks/zod) (TypeScript), [Pydantic](https://pydantic.dev/) (Python) | Query parameter validation.                                                                        |
| **Caching**      | [Redis](https://redis.io/), [Varnish](https://varnish-cache.org/)                                  | Cache projected API responses.                                                                  |

---
## **8. Troubleshooting**
| **Issue**                          | **Root Cause**                                                                               | **Solution**                                                                                     |
|------------------------------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **400 Bad Request**               | Invalid field list or query syntax.                                                          | Check API docs for allowed fields; validate input.                                                |
| **Performance Degradation**       | Unoptimized projection queries (e.g., deeply nested GraphQL).                                 | Implement complexity analysis; use denormalized caches (e.g., Redis).                           |
| **Over-Fetching**                  | Client requests unnecessary fields.                                                           | Use sparse fieldsets or GraphQL to reduce payload size.                                          |
| **Under-Fetching**                 | Client misses required fields.                                                                | Document all available fields; provide default projections.                                      |

---
## **9. See Also**
- **[GraphQL Spec](https://spec.graphql.org/)** – Official GraphQL documentation.
- **[REST API Best Practices](https://restfulapi.net/)** – Guidelines for REST projections.
- **[Field Projection in Django REST](https://www.django-rest-framework.org/api-guide/filtering/#field-lookups)** – Example implementation.