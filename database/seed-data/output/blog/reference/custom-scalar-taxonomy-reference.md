---

# **[Pattern] Custom Scalar Taxonomy Reference Guide**
*FraiseQL – Type-Safe Data Modeling with Custom Scalars*

## **Overview**
FraiseQL’s **Custom Scalar Taxonomy** pattern standardizes 56 built-in scalar types across 18 domain categories to enforce type safety, validation, and consistency in API schemas. Unlike flexible JSON, FraiseQL scalars enforce structural rules (e.g., email validation for `EmailAddress`, date formatting for `ISO8601Date`) at serialization boundaries, reducing runtime errors.

These scalars integrate seamlessly with Fraise’s type inference and schema derivation, ensuring APIs align with business expectations. They’re ideal for:
- **Tiered data models** (e.g., `CurrencyCode` for monetary fields).
- **Domain-specific validation** (e.g., `IPv4` for network endpoints).
- **Interoperability** with external systems (e.g., `UUID` for IDs).

---

## **Schema Reference**
FraiseQL scalars are categorized by domain. Below is the reference table:

| **Domain**         | **Scalar Name**       | **Description**                                                                 | **Validation Rules**                                                                 | **Example Values**                     |
|--------------------|-----------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|----------------------------------------|
| **Temporal**       | `ISO8601Date`         | Standard date format (YYYY-MM-DD).                                            | Matches regex `^\d{4}-\d{2}-\d{2}$`; no time component.                           | `"2024-05-20"`                         |
|                    | `ISO8601Time`         | Time in 24-hour format (HH:MM:SS).                                            | Matches regex `^\d{2}:\d{2}:\d{2}$`.                                             | `"14:30:00"`                           |
|                    | `ISO8601DateTime`     | Combined date+time (ISO 8601).                                                  | Includes timezone (e.g., `Z`, `+05:30`).                                         | `"2024-05-20T14:30:00Z"`              |
|                    | `EpochTimestamp`      | Unix timestamp (seconds since 1970).                                           | Integer ≥ `0`; ≤ `2^63-1`.                                                       | `1716000000`                           |
|                    | `YearMonth`           | Year-month (YYYY-MM).                                                          | Matches regex `^\d{4}-\d{2}$`; no day.                                            | `"2024-05"`                            |
| **Geographic**     | `CountryCode`         | 2-letter ISO country code.                                                      | Validates against [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2). | `"US"`, `"DE"`                          |
|                    | `CityName`            | Standardized city name (with validation).                                       | Matches regex; linked to geographic database (optional).                           | `"New York"`                           |
|                    | `PostalCode`          | Country-specific postal code format.                                            | Regex varies by country (e.g., `^\d{5}$` for US).                                 | `"10001"`, `"D11 1AA"`                 |
| **Network**        | `IPv4`               | IPv4 address (dotted-decimal).                                                  | Validates format (e.g., `192.168.1.1`).                                          | `"8.8.8.8"`                            |
|                    | `IPv6`               | IPv6 address (hexadecimal).                                                     | Validates format (e.g., `2606:4700:4700::1111`).                                  | `"2001:db8::1"`                        |
|                    | `DomainName`          | Valid DNS-compliant domain (with TLD).                                          | Regex: `^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$`.                        | `"example.com"`                        |
| **Financial**      | `CurrencyCode`        | 3-letter ISO currency code.                                                     | Validates against [ISO 4217](https://www.iso.org/iso-4217-currency-codes.html).     | `"USD"`, `"EUR"`                        |
|                    | `Percentage`          | Numeric percentage (0–100).                                                     | Float/Int; ≥ `0`, ≤ `100`.                                                       | `98.5`, `100`                          |
| **Vectors**        | `Float32Vec`          | 32-bit floating-point vector.                                                   | Array of `float32` values (e.g., `[0.1, 0.2, 0.3]`).                              | `[1.0, 0.5, -0.2]`                     |
|                    | `Float64Vec`          | 64-bit floating-point vector.                                                   | Array of `float64` values.                                                       | `[1.0, 2.1e-5, 3.14]`                  |
| **Identifiers**    | `UUID`                | RFC 4122-compliant UUID v4.                                                     | Matches regex `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`.      | `"550e8400-e29b-41d4-a716-446655440000"` |
|                    | `EmailAddress`        | RFC 5322 compliant email.                                                       | Regex: `^[^\s@]+@[^\s@]+\.[^\s@]+$`.                                             | `"user@example.com"`                   |
|                    | `Slug`                | URL-friendly string (alphanumeric, hyphens, underscores).                       | No spaces or special chars (except `-`/`_`).                                       | `"product-name"`                        |
| **Text**           | `PhoneNumber`         | Country-specific phone number (ETSI E.164).                                    | Regex varies by country (e.g., `^\+1\d{10}$` for US).                             | `"+14155552671"`                       |
|                    | `HashSHA256`          | SHA-256 cryptographic hash.                                                     | Hex string (64 chars).                                                            | `"a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"` |
| **Business**       | `TaxID`               | Country-specific tax identifier (e.g., VAT).                                    | Regex tailored to jurisdiction (e.g., UK VAT: `^DE\d{12}$`).                       | `"DE123456789"`                        |
|                    | `ProductSKU`          | Standardized product SKU (alphanumeric, hyphens).                              | No spaces; length ≤ `50`.                                                         | `"FOO-2024-BLUE"`                      |
| **Miscellaneous**  | `Boolean`             | Strict `true`/`false` (no string coercion).                                    | Must be `true` or `false`.                                                       | `true`, `false`                         |
|                    | `Null`                | Explicit null value (avoids `null` in JSON).                                   | Literal `"null"` (case-insensitive).                                              | `"null"`                                |
|                    | `RegexPattern`        | User-defined regex (e.g., for custom validation).                               | Compiles to valid regex without errors.                                           | `"^[a-z]+$"`                            |

---

## **Query Examples**
### **1. Defining a Schema with Custom Scalars**
```graphql
type Order @model {
  id: UUID!
  customerEmail: EmailAddress!
  shippingAddress: {
    city: CityName!
    postalCode: PostalCode!
  }
  currency: CurrencyCode!
  createdAt: ISO8601DateTime!
}
```

### **2. Inserting Valid Data**
```graphql
mutation {
  insertOrder(
    data: {
      id: "550e8400-e29b-41d4-a716-446655440001"
      customerEmail: "user@example.com"
      shippingAddress: {
        city: "New York"
        postalCode: "10001"
      }
      currency: "USD"
      createdAt: "2024-05-20T14:30:00Z"
    }
  )
}
```

### **3. Querying with Scalar Validation**
```graphql
query {
  order(id: "550e8400-e29b-41d4-a716-446655440001") {
    id
    customerEmail
    shippingAddress {
      city
      postalCode
    }
  }
}
```

### **4. Error Handling (Invalid Input)**
If `postalCode` is malformed (e.g., `"INVALID"`), FraiseQL returns:
```json
{
  "errors": [
    {
      "path": ["shippingAddress", "postalCode"],
      "message": "Postal code must match pattern for US/Canada (e.g., '10001')."
    }
  ]
}
```

### **5. Using Vectors for Embeddings**
```graphql
type Product @model {
  name: String!
  embedding: Float32Vec!
}

query {
  similarProducts(threshold: 0.7) {
    name
    embedding
  }
}
```

---

## **Related Patterns**
1. **[FraiseQL Schema Inheritance]**
   - Extend custom scalars via interfaces (e.g., define `Cardinality` as `Int!` with `@min("1")`).
   - *Use case*: Reusable constraints (e.g., `@maxLength("50")` for `Slug`).

2. **[Domain-Specific Objects]**
   - Encapsulate scalars in objects (e.g., `Address` containing `CityName`, `PostalCode`).
   - *Example*:
     ```graphql
     type Address @model {
       city: CityName!
       postalCode: PostalCode!
     }
     ```

3. **[Scalar Enums]**
   - Pair scalars with enums for exhaustive options (e.g., `PaymentMethod: PaymentMethodEnum!` where `enum PaymentMethod` includes `CreditCard`, `PayPal`).
   - *Benefit*: Type-safe alternatives to strings.

4. **[Input Validation Pipelines]**
   - Combine scalars with custom functions (e.g., validate `TaxID` against a service API).
   - *Pattern*: `@validate` directive:
     ```graphql
     scalar TaxID @validate(url: "https://tax-api.example.com/validate")
     ```

5. **[JSON-to-Scalar Conversion]**
   - Use `@jsonScalar` to auto-convert JSON objects to scalars (e.g., parse `ISO8601DateTime` from a string).
   - *Example*:
     ```graphql
     type Event @model {
       date: ISO8601DateTime @jsonScalar(serde: "parse_iso8601")
     }
     ```

---

## **Key Considerations**
- **Performance**: Scalar validation occurs at serialization/deserialization (low overhead).
- **Extensibility**: Custom domains can be added via `@scalar` directive (requires type registration).
- **Tooling**: Use `fraise generate --scalars` to auto-generate OpenAPI/Swagger docs.
- **Migration**: Replace loose `String` fields with scalars incrementally (backward-compatible with `@jsonScalar`).