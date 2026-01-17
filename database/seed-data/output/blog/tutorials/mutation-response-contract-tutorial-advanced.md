```markdown
---
title: "Mutation Response Contract: Designing Consistent API Responses With Stored Procedures"
date: "2023-11-15"
tags: ["database", "api design", "patterns", "sql", "backend"]
series: ["Database & API Patterns"]
series_order: 3
---

# Mutation Response Contract: Designing Consistent API Responses With Stored Procedures

Imagine writing an API that handles complex business logic using stored procedures—only to discover that each procedure returns results in a wildly different format. One returns a JSON string, another spits out a CSV, and a third emits a stream of XML. Your client code becomes an unholy mess of `try/catch` blocks and conditional logic to parse, validate, and transform these inconsistently structured responses. **This is the problem Mutation Response Contract helps solve.**

The **Mutation Response Contract** pattern enforces a standardized schema for all responses returned by stored procedures (or other database-backed mutation operations). It ensures that every time a user invokes a procedure to create, update, or delete data, they get a response that adheres to a clear, documented contract. This consistency makes APIs easier to maintain, debug, and consume.

In this post, we’ll explore why this pattern matters, how to implement it, and common pitfalls to avoid. By the end, you’ll have a practical, repeatable approach to designing stored procedures that produce predictable, machine-readable outputs.

---

## The Problem: Wildcard Responses from Stored Procedures

Stored procedures are powerful—for wrapping business logic, enforcing constraints, and encapsulating database operations. However, their flexibility often leads to **response inconsistency**. Here’s what typically goes wrong:

1. **Ad-hoc Serialization:** Developers often dump raw result sets into JSON strings or CSV streams without considering how the response will be consumed. Example:
   ```sql
   CREATE PROCEDURE GetUserData() AS
   BEGIN
       SELECT * FROM Users WHERE Id = @UserId
       RETURN CAST(RESULT_SETS[0] AS NVARCHAR(MAX));
   END
   ```
   The client then has to manually parse the result, which leads to bugs and fragile code.

2. **Mixing Data and Metadata:** Some procedures return application-level data, while others include debug information or error codes in the same response. Example:
   ```sql
   CREATE PROCEDURE UpdateOrder(@OrderId INT) AS
   BEGIN
       UPDATE Orders SET Status = 'Processed' WHERE Id = @OrderId;
       IF @@ROWCOUNT = 0 RETURN 'Order not found';
       RETURN 'Success';
   END
   ```
   The response can’t be automatically validated against a schema.

3. **Different Formats for Similar Operations:** Even for similar operations (e.g., `CreateUser` vs. `CreateAdmin`), procedures might return different structures or omit key fields like timestamps or versioning data.

The result? **Tight coupling between the API layer and the database layer**, making refactoring painful and slowing down development.

---

## The Solution: Mutation Response Contract

The **Mutation Response Contract** pattern standardizes how stored procedures communicate with the outside world. At its core, it defines **three key principles**:

1. **Every procedure returns a response defined by a schema.**
   The schema includes:
   - A success/failure indicator (e.g., `status` field).
   - A standardized payload format (e.g., `data` field containing the result).
   - Optional metadata (e.g., `timestamp`, `version`).

2. **Procedures never return raw result sets directly.**
   Instead, they transform output into a consistent format (e.g., JSON, XML) or expose it via a table-valued function.

3. **Error responses are normalized.**
   All errors follow the same schema—e.g., `{ "status": "error", "error": { "code": "X", "message": "Y" } }`.

### Why This Works
- **Predictability:** Clients can trust that every procedure call will follow the same structure.
- **Automation:** Responses can be validated using tools like OpenAPI/Swagger or schema-aware libraries.
- **Separation of Concerns:** The database layer focuses on data integrity, while the API layer focuses on response formatting.

---

## Components of the Mutation Response Contract

### 1. Core Schema Definition
Define a response contract schema (e.g., in OpenAPI or as a table definition) that all procedures will adhere to. Example:

```yaml
# OpenAPI Schema Example
components:
  schemas:
    MutationResponse:
      type: object
      properties:
        status:
          type: string
          enum: ["success", "error"]
        data:
          type: object
          # Dynamic payload based on operation type
          # Example for `CreateUser`:
          # { "user": { "id": int, "email": string }, "timestamp": string }
        error:
          type: object
          if:
            properties:
              status:
                const: "error"
          then:
            properties:
              code:
                type: string
              message:
                type: string
```

### 2. Database Helper Functions
Create reusable SQL helper functions to format responses consistently. Here’s a helper table-valued function for generating response payloads:

```sql
CREATE FUNCTION dbo.GenerateResponse(
    @Status NVARCHAR(20),
    @Data NVARCHAR(MAX) = NULL,
    @ErrorCode NVARCHAR(50) = NULL,
    @ErrorMessage NVARCHAR(MAX) = NULL
)
RETURNS TABLE
AS
RETURN (
    SELECT
        Status = @Status,
        Data = CASE WHEN @Data IS NOT NULL THEN @Data ELSE NULL END,
        ErrorCode = CASE WHEN @ErrorCode IS NOT NULL THEN @ErrorCode ELSE NULL END,
        ErrorMessage = CASE WHEN @ErrorMessage IS NOT NULL THEN @ErrorMessage ELSE NULL END
);
```

### 3. Example Procedures
Now, rewrite procedures to use this contract. Here are two examples:

#### Example 1: Create User
```sql
CREATE PROCEDURE CreateUser(
    @Email NVARCHAR(255),
    @PasswordHash NVARCHAR(255)
)
AS
BEGIN
    DECLARE @UserId INT;

    BEGIN TRY
        INSERT INTO Users (Email, PasswordHash) VALUES (@Email, @PasswordHash);
        SET @UserId = SCOPE_IDENTITY();

        -- Format response as JSON (assuming JSON functions are available)
        DECLARE @Response JSON = (
            SELECT
                Status = 'success',
                Data = JSON_QUERY(
                    CONCAT('{ "user": { "id": ', CAST(@UserId AS NVARCHAR), ', "email": "', @Email, '" } }'
                )
            )
        );

        -- Return structured result
        SELECT * FROM dbo.GenerateResponse(
            @Status = 'success',
            @Data = JSON_MODIFY(@Response, '$.Data'),
            @ErrorCode = NULL,
            @ErrorMessage = NULL
        );
    END TRY
    BEGIN CATCH
        SELECT * FROM dbo.GenerateResponse(
            @Status = 'error',
            @ErrorCode = ERROR_NUMBER(),
            @ErrorMessage = ERROR_MESSAGE()
        );
    END CATCH
END;
```

#### Example 2: Update Order Status
```sql
CREATE PROCEDURE UpdateOrderStatus(
    @OrderId INT,
    @NewStatus NVARCHAR(50)
)
AS
BEGIN
    DECLARE @RowsAffected INT;

    BEGIN TRY
        UPDATE Orders
        SET Status = @NewStatus
        WHERE Id = @OrderId;

        SET @RowsAffected = @@ROWCOUNT;

        -- Return status and updated record
        DECLARE @UpdatedOrder JSON = (
            SELECT
                Status = 'success',
                Data = JSON_QUERY(
                    CONCAT('{ "affectedRows": ', CAST(@RowsAffected AS NVARCHAR),
                    ', "order": { "id": ', CAST(@OrderId AS NVARCHAR), ', "status": "', @NewStatus, '" } }'
                )
            )
        );

        SELECT * FROM dbo.GenerateResponse(
            @Status = 'success',
            @Data = JSON_MODIFY(@UpdatedOrder, '$.Data'),
            @ErrorCode = NULL,
            @ErrorMessage = NULL
        );
    END TRY
    BEGIN CATCH
        SELECT * FROM dbo.GenerateResponse(
            @Status = 'error',
            @ErrorCode = ERROR_NUMBER(),
            @ErrorMessage = ERROR_MESSAGE()
        );
    END CATCH
END;
```

---

## Implementation Guide

### Step 1: Define Your Response Schema
Start by documenting the response structure. For example:
```
{
  "status": "success" | "error",
  "data": {
    "[operation-specific-fields]": "[values]"
  },
  "error": {
    "code": "[error-code]",
    "message": "[error-message]"
  }
}
```

### Step 2: Add the Helper Function
```sql
-- Place this in a reusable schema like dbo
CREATE FUNCTION dbo.GenerateResponse(...) AS ...
```

### Step 3: Rewrite Procedures
Replace raw return statements with calls to `GenerateResponse`. Example:
```sql
-- Old:
SELECT UserId, Email FROM Users WHERE Id = @UserId

-- New:
SELECT * FROM dbo.GenerateResponse(
    @Status = 'success',
    @Data = JSON_CONTAINS(...) -- Transform result into contract-compliant JSON
);
```

### Step 4: Validate Client-Side
Ensure your API layer validates responses against the schema. Example in C#:
```csharp
public class MutationResponse
{
    public string Status { get; set; }
    public dynamic Data { get; set; }
    public string ErrorCode { get; set; }
    public string ErrorMessage { get; set; }
}

public void HandleResponse(object response)
{
    var result = JsonConvert.DeserializeObject<MutationResponse>(response);
    if (result.Status == "error")
    {
        throw new ApiException(result.ErrorCode, result.ErrorMessage);
    }
}
```

### Step 5: Document the Contract
Publish the schema (e.g., via OpenAPI docs) so consumers know what to expect. Example:
```yaml
paths:
  /api/users:
    post:
      summary: Create a new user
      responses:
        200:
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MutationResponse'
```

---

## Common Mistakes to Avoid

1. **Forgetting Error Handling**
   Always wrap procedures in `TRY/CATCH` to ensure errors follow the contract. Skipping this leads to inconsistent error formats.

2. **Overcomplicating the Response**
   Resist the urge to include unnecessary fields (e.g., debug logs). Keep the contract focused on what the client needs.

3. **Ignoring Performance**
   JSON serialization and formatting can impact performance. Use efficient methods (e.g., bulk operations) for large datasets.

4. **Not Updating the Contract**
   A response contract must evolve with your application. Refactor procedures before the contract becomes a bottleneck.

5. **Assuming Schema Flexibility**
   While JSON allows dynamic fields, enforce a strict schema to avoid runtime surprises. For example, reject requests that include unexpected keys.

---

## Key Takeaways

- **Standardization > Flexibility:** A consistent response contract simplifies debugging and maintenance.
- **Schema First:** Design the response schema before writing procedures.
- **Reuse Helper Functions:** Avoid duplicating response generation logic.
- **Validate Everything:** Enforce the contract both in the database and on the client side.
- **Document Thoroughly:** Make the contract visible to API consumers.

---

## Conclusion

The Mutation Response Contract pattern transforms stored procedures from black boxes into predictable, well-behaved API endpoints. By enforcing a standardized response format, you reduce friction in your stack, improve reliability, and make your APIs easier to extend. While there’s an upfront investment in defining and implementing the contract, the long-term benefits—fewer bugs, faster debugging, and happier consumers—make it a worthwhile tradeoff.

**Next Steps:**
1. Start with a single critical procedure and apply the pattern.
2. Gradually migrate other procedures while maintaining backward compatibility.
3. Automate contract enforcement with tools like Swagger or Spectral.

Now go forth and design APIs that feel as robust as their database backbones!

---
```