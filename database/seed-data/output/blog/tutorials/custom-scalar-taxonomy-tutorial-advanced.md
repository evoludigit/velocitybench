```markdown
---
title: "Custom Scalar Taxonomies: Building Type-Safe APIs Without Reinventing the Wheel"
description: "How FraiseQL's custom scalar types improve API design by introducing domain-specific validation and type safety. A practical guide for backend engineers."
date: 2024-02-15
author: "Alex Carter"
---

# Custom Scalar Taxonomies: Building Type-Safe APIs Without Reinventing the Wheel

Over the past decade, backend development has seen a shift toward APIs that are not just functional but also semantically rich. However, many systems still default to using strings for all user-facing data—dates, currencies, IDs, geocoordinates—because they’re simple and seemingly flexible. The problem? This approach robs you of type safety, automatic validation, and clarity, forcing you to write repetitive boilerplate or rely on manual parsing. That’s where **custom scalar taxonomies** come in—a design pattern that introduces domain-specific validation and type safety while keeping APIs clean and maintainable.

FraiseQL, a next-generation query language for databases, addresses this exact pain point by offering **56 pre-defined custom scalar types** across 18 domain categories. These include temporal, geographic, network, financial, vector, and identifier types, all validated automatically at serialization boundaries. This means you can enforce constraints like "only ISO 8601 dates" or "valid IPv4 addresses" without writing a single custom validator. The result? APIs that are self-documenting, less error-prone, and easier to reason about.

In this post, we’ll explore how custom scalar taxonomies work, why they’re a game-changer for backend design, and how you can implement similar patterns in your own systems—whether using FraiseQL or building your own solutions.

---

## The Problem: Strings Are the Universal (Poor) Default

Before diving into solutions, let’s acknowledge the root cause: **strings are overused as a universal data type**. In most APIs, you’ll see something like this:

```json
{
  "user": {
    "id": "abc123",
    "created_at": "2023-10-15T08:30:00Z",
    "balance": "150.50",
    "location": "40.7128,-74.0060"
  }
}
```

At first glance, this seems innocuous. But consider the implications:

1. **No Validation**: The API accepts `created_at` as a string, so it could also accept `"tomorrow"` or `"last week"`. The client could send `"abc123"` for `balance`, and your application would have to parse and validate it—if it even notices.
2. **Error Handling**: Invalid data slips through, forcing you to add layers of validation logic (e.g., `if (dateString && !isIso8601(dateString)) { throw new Error("Invalid date"); }`).
3. **Type Safety**: Your IDE or language server can’t infer types from string literals, so autocompletion and refactoring tools struggle.
4. **Domain Misalignment**: `balance` is a monetary value, but your API treats it like a generic string. Where does the `$` go? What if the client sends `"€150"`? Your business logic now needs to handle currency parsing, formatting, and conversion.
5. **Schema Drift**: Over time, APIs accumulate undocumented quirks. For example, `"40.7128,-74.0060"` could be parsed as latitude/longitude, but what if the client sends `"40.7128 74.0060"` (space-separated)? Or `"40.7128,74.0060"` (no negative sign)?

This isn’t just about edge cases—it’s about the **cost of ambiguity**. Every time you treat data as a string, you’re betting that humans will always format it correctly. And we all know how well that bet pays off.

---

## The Solution: Custom Scalar Taxonomies

Custom scalar taxonomies introduce **domain-specific validation and type safety** by defining custom scalar types that replace or complement strings. These types enforce rules at the serialization boundary (e.g., when data is received or sent), ensuring that invalid data is rejected early and consistently.

### Core Principles
1. **Domain-Specific Constraints**: Each scalar type embodies the rules of its domain. For example:
   - `DateIso8601` ensures dates are formatted as `YYYY-MM-DDTHH:MM:SSZ`.
   - `Currency` enforces valid formats like `$150.50` or `€100`, including currency codes.
   - `IPv4` or `GeoCoordinates` validate network and location data, respectively.
2. **Automatic Validation**: The system rejects invalid data at serialization, often with descriptive errors (e.g., `"expected ISO 8601 date, got 'tomorrow'"`).
3. **Type Safety**: Your code can express intent clearly. For example:
   ```typescript
   const user: User = {
     id: UserId("abc123"),  // Explicitly a UserId type
     balance: Currency("$150.50"),  // Explicitly a Currency type
   };
   ```
4. **Separation of Concerns**: Validation logic is encapsulated in the scalar type, not scattered across your application.

### How It Works
In practice, custom scalar taxonomies are implemented via:
1. **Type Definitions**: Define new types with validation rules (e.g., regex, custom parsers).
2. **Serialization/Deserialization**: Convert between scalar types and their string representations.
3. **Error Handling**: Provide clear feedback when validation fails.
4. **API Contracts**: Explicitly document supported types in your API schemas.

---

## Implementation Guide: Building Your Own Custom Scalar Taxonomy

While FraiseQL provides a ready-made solution, you can implement custom scalar taxonomies in any backend system. Below, we’ll explore how to build this pattern from scratch in **Go**, **JavaScript/TypeScript**, and **Python**, with examples for common domains: dates, currencies, and identifiers.

---

### 1. Example: Date Validation in Go

#### Problem
You want to enforce ISO 8601 dates in your API but avoid manual parsing.

#### Solution
Define a `DateIso8601` type with validation.

```go
package main

import (
	"errors"
	"fmt"
	"regexp"
	"time"
)

// DateIso8601 represents an ISO 8601 formatted date-time string.
// It implements the Stringer interface to enable easy printing.
type DateIso8601 struct {
	Time time.Time
}

// NewDateIso8601 creates a new DateIso8601 from an ISO 8601 string.
// Returns an error if the string is not valid.
func NewDateIso8601(dateStr string) (*DateIso8601, error) {
	// Regex to validate ISO 8601 (simplified; use a library like `github.com/kelindar/timeparser` for full support).
	re := regexp.MustCompile(`\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z`)
	if !re.MatchString(dateStr) {
		return nil, errors.New("invalid ISO 8601 date format")
	}

	// Parse the date.
	parsed, err := time.Parse(time.RFC3339, dateStr)
	if err != nil {
		return nil, fmt.Errorf("failed to parse date: %w", err)
	}

	return &DateIso8601{Time: parsed}, nil
}

// String converts the DateIso8601 back to its ISO 8601 string representation.
func (d *DateIso8601) String() string {
	return d.Time.Format(time.RFC3339)
}

// Example usage.
func main() {
	dateStr := "2023-10-15T08:30:00Z"
	date, err := NewDateIso8601(dateStr)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}
	fmt.Println("Valid date:", date) // Output: Valid date: 2023-10-15T08:30:00Z
}
```

#### Tradeoffs
- **Pros**:
  - Early validation catches errors at the API boundary.
  - Clear intent in your code (e.g., `*DateIso8601` vs. `string`).
- **Cons**:
  - Requires writing validation logic (or using a library).
  - Slightly more overhead for serialization/deserialization.

---

### 2. Example: Currency Validation in TypeScript

#### Problem
You need to handle currency values with validation for format, amount, and currency code.

#### Solution
Define a `Currency` type with parsers and formatters.

```typescript
// currency.ts
export type Currency = {
  amount: number;
  currencyCode: string;
};

export class InvalidCurrencyError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidCurrencyError";
  }
}

export function parseCurrency(currencyStr: string): Currency {
  // Regex to match formats like "$150.50", "€100", or "150.50 USD".
  const currencyRegex = /^(\$|€|\p{Sc})?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)(\s*\w{3})?$/u;
  if (!currencyRegex.test(currencyStr)) {
    throw new InvalidCurrencyError(`Invalid currency format: ${currencyStr}`);
  }

  // Extract amount and currency code.
  const amountStr = currencyStr.replace(/[^\d\.]/g, "");
  const currencyCodeMatch = currencyStr.match(/[\p{Sc}]\w{3}|USD$/u)?.pop()?.toUpperCase();

  const amount = parseFloat(amountStr);
  if (isNaN(amount)) {
    throw new InvalidCurrencyError(`Invalid amount: ${amountStr}`);
  }

  return {
    amount,
    currencyCode: currencyCodeMatch || "USD",
  };
}

// Example usage.
const balance = parseCurrency("$150.50");
console.log(balance); // { amount: 150.5, currencyCode: "USD" }
```

#### Tradeoffs
- **Pros**:
  - Enforces consistent currency formats.
  - Easily extendable (e.g., add locale-specific rules).
- **Cons**:
  - Regex can get complex for edge cases (e.g., `"1,000.50"` vs. `"1000.50"`).
  - Requires careful handling of locales (e.g., `1,000.50` vs. `1.000,50`).

---

### 3. Example: UUID Validation in Python

#### Problem
You want to enforce UUID v4 generation and validation in your API.

#### Solution
Use Python’s `uuid` module with custom validation.

```python
# uuid_types.py
import uuid
from typing import Optional

class UUID:
    def __init__(self, uuid_str: Optional[str] = None):
        if uuid_str is None:
            # Generate a new UUID v4.
            self.value = uuid.uuid4()
        else:
            # Parse and validate the UUID.
            try:
                self.value = uuid.UUID(str(uuid_str))
            except ValueError as e:
                raise ValueError(f"Invalid UUID: {uuid_str}") from e

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"UUID('{self.value}')"

    @classmethod
    def from_string(cls, uuid_str: str) -> "UUID":
        return cls(uuid_str)

# Example usage.
user_id = UUID.from_string("550e8400-e29b-41d4-a716-446655440000")
print(user_id)  # Output: 550e8400-e29b-41d4-a716-446655440000

# Generate a new UUID.
new_id = UUID()
print(new_id)  # Output: e.g., "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed"
```

#### Tradeoffs
- **Pros**:
  - Enforces UUID v4 format strictly.
  - Easy to generate new UUIDs.
- **Cons**:
  - Limited to UUID (harder to extend to other identifier types).

---

## Common Pitfalls and How to Avoid Them

While custom scalar taxonomies are powerful, they’re not without challenges. Here are some common mistakes and how to avoid them:

### 1. Overcomplicating Validation
**Pitfall**: Writing overly complex regex or validation logic that’s hard to maintain.
**Solution**:
- Use existing libraries (e.g., `date-fns` for dates, `uuid` for UUIDs) where possible.
- Start simple and add complexity only when needed.
- Example: Don’t reinvent ISO 8601 parsing—use a library like [`timeparser`](https://github.com/kelindar/timeparser).

### 2. Ignoring Edge Cases
**Pitfall**: Validation that works for 99% of cases but fails on edge cases (e.g., `"1,000.50"` vs. `"1000.50"`).
**Solution**:
- Test with a variety of inputs, including malformed data.
- Document your expected formats clearly (e.g., `"Format: $150.50 or €100 (no commas)"`).

### 3. Poor Error Messages
**Pitfall**: Vague error messages like `"Invalid currency"` instead of `"Expected USD amount, got '150.50 EUR'"`.
**Solution**:
- Provide specific, actionable error messages (e.g., `"Invalid date format. Use YYYY-MM-DDTHH:MM:SSZ"`).

### 4. Neglecting Serialization
**Pitfall**: Assuming your custom type will serialize/deserialize correctly without explicit handling.
**Solution**:
- Define clear `toString()`/`fromString()` methods (or equivalent in your language).
- Example: In the Go `DateIso8601` example, `String()` ensures consistent serialization.

### 5. Inconsistent API Contracts
**Pitfall**: Mixing custom types with strings in the same API, creating ambiguity.
**Solution**:
- Stick to custom scalar types for all domain-specific data.
- Example: If you use `Currency` for balances, don’t accept strings like `"150"` or `"€150"` elsewhere.

---

## Key Takeaways

Here’s a quick checklist of lessons learned:
- **Strings are the enemy of type safety**. Replace them with domain-specific types where possible.
- **Validation at the boundary** (serialization/deserialization) catches errors early and reduces boilerplate.
- **Start small**. Pick 1-2 critical domains (e.g., dates, currencies) to implement first.
- **Leverage libraries**. Don’t reinvent the wheel—use existing parsers for dates, UUIDs, etc.
- **Communicate your expectations**. Document supported formats clearly in your API docs.
- **Tradeoffs matter**. Custom scalar types add complexity but reduce errors and improve maintainability.

---

## Conclusion

Custom scalar taxonomies are a small but powerful pattern for building type-safe APIs. By introducing domain-specific validation and explicit types, you reduce ambiguity, catch errors early, and make your code more maintainable. While FraiseQL provides a ready-made solution, you can implement similar patterns in any backend language or framework.

The key is to **start small**—pick one or two domains (dates, currencies, IDs) and gradually expand. Over time, your APIs will become more robust, your error rates will drop, and your team will thank you for the clarity.

---
### Further Reading
- [FraiseQL Documentation: Custom Scalar Types](https://fraise.dev/docs/custom-scalars)
- [Go’s `time` package documentation](https://pkg.go.dev/time)
- [TypeScript `Intl` and number formatting](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat)
- [Python’s `uuid` module](https://docs.python.org/3/library/uuid.html)

**Have you used custom scalar types in your APIs? What challenges did you face? Share your stories in the comments!**
```