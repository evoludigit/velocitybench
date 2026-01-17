```markdown
# **"GraphQL Request Validation: How to Catch Invalid Queries Before They Hit Execution"**

GraphQL is a powerful API technology that empowers clients to request *exactly* what they need. But that flexibility comes with a risk: if a client writes a malformed query, your server might execute it—or worse, silently fail—before you even notice.

What if we could catch these mistakes **before** they reach the resolver layer, saving time, reducing errors, and improving client confidence?

In this post, we’ll explore **GraphQL request validation**—a pattern that ensures queries adhere to your schema’s structure, argument requirements, and type constraints **before** they’re executed. We’ll break down how it works, why it matters, and—most importantly—how to implement it in **Apollo Server, GraphQL Yoga, or Express with GraphQL**.

---

## **Introduction: Why Validation Matters**

GraphQL’s flexibility is both its strength and its Achilles’ heel. While clients can ask for precise data, poorly structured queries can:
- **Waste server resources** executing unnecessary or invalid requests.
- **Break resolvers** with missing or mismatched arguments.
- **Expose schema details** that shouldn’t be public (e.g., internal types).
- **Cause runtime errors** that are hard to debug.

Traditional REST APIs benefit from strict HTTP standards—`404 Not Found` for invalid endpoints or `400 Bad Request` for malformed payloads. GraphQL, however, relies on client-side tools (like GraphiQL or Apollo Studio) to validate queries, but **server-side validation is often overlooked**.

This post covers:
✅ How GraphQL validates queries by default (and why it’s not enough).
✅ The **GraphQL Request Validation Pattern**—a structured way to catch issues early.
✅ **Real-world implementations** in popular GraphQL servers.
✅ Common pitfalls and how to avoid them.

Let’s dive in.

---

## **The Problem: Invalid Queries Slip Through**

GraphQL’s query language is expressive—but it’s **not statically typed** like TypeScript or SQL. A client could write:

```graphql
query {
  user(id: "invalid") {
    name
    email  # Missing field on some schemas
  }
}
```

What happens next?
1. **Apollo/GraphQL Yoga/Express-GraphQL** parses the query.
2. **By default, they validate syntax** (no syntax errors) but **not semantic correctness**.
3. **If `user(id: "invalid")` is called**, the resolver might:
   - Return an error (e.g., `Cannot return null for non-nullable field`).
   - Fail silently (e.g., if `id` is a custom type).
   - Waste CPU cycles fetching non-existent data.

### **Real-World Example: The "Silent Failure" Trap**
Imagine a schema like this:

```graphql
type User @model {
  id: ID!
  email: String!
  age: Int  # Optional
}

type Query {
  user(id: ID!): User
}
```

A client might run:

```graphql
query {
  user(id: "not-an-id") {
    email
    age
  }
}
```

**What’s wrong?**
- `id` is an `ID` (a scalar type), but `"not-an-id"` is just a string.
- The resolver might try to validate the ID later—but by then, it’s already spent time parsing the query.

If the resolver doesn’t validate `id`, it could **crash** or **mistakenly process invalid data**.

---

## **The Solution: GraphQL Request Validation**

The **GraphQL Request Validation Pattern** ensures queries are **validated before execution** by:
1. **Checking syntax** (does the query parse correctly?).
2. **Validating schema conformance** (are all fields/types defined?).
3. **Enforcing argument constraints** (are required args provided? Correct types?).
4. **Detecting leaks** (are internal types exposed?).

Unlike REST’s HTTP validation, GraphQL validation happens **logically**, not just syntactically.

---

## **Implementation Guide: How to Validate GraphQL Requests**

### **1. Built-in Validation (Apollo/GraphQL Yoga/Express-GraphQL)**

Most GraphQL servers include **basic validation** out of the box. Let’s see how it works:

#### **Example: Apollo Server Validation**
Apollo Server validates by default but allows **custom validation rules**.

```javascript
// server.js
const { ApolloServer } = require('apollo-server');
const { schema } = require('./schema');

const server = new ApolloServer({
  schema,
  validationRules: [
    // Custom validation (e.g., enforce @require directives)
    require('./validationRules.js').requireDirectives,
  ],
});

server.listen().then(({ url }) => console.log(`Server ready at ${url}`));
```

#### **Example: GraphQL Yoga Validation**
Yoga’s default validator checks for syntax and schema compliance:

```javascript
// server.js
const { createServer } = require('graphql-yoga');
const { schema } = require('./schema');

const yoga = createServer({
  schema,
  validationRules: [
    // Custom validation
    (validationContext) => {
      // Example: Reject queries without a specified field
      const query = validationContext.document;
      if (query.definitions.some(def => def.selectionSet.selections.length === 0)) {
        throw new Error('Every query must select at least one field!');
      }
    },
  ],
});

yoga.listen(4000);
```

#### **Example: Express-GraphQL Validation**
Express-GraphQL also validates by default:

```javascript
// server.js
const express = require('express');
const { graphqlHTTP } = require('express-graphql');
const { buildSchema } = require('graphql');

const schema = buildSchema(/* ... */);
const app = express();

app.use('/graphql', graphqlHTTP((req) => ({
  schema,
  validationRules: [
    // Custom rules
    (validationContext) => {
      // Example: Block queries without a `userId`
      if (!validationContext.document.definitions[0].selectionSet.selections.some(
        s => s.name.value === 'userId'
      )) {
        throw new Error('Missing required field: userId');
      }
    },
  ],
})));

app.listen(4000);
```

---

### **2. Advanced Validation: Custom Rules**

For stricter control, write **custom validation rules**. Here’s how:

#### **Rule 1: Enforce Required Arguments**
```javascript
// validationRules.js
module.exports.requireArgs = (validationContext) => {
  const { document } = validationContext;

  document.definitions.forEach(def => {
    if (def.operation === 'query' || def.operation === 'mutation') {
      def.variableDefinitions.forEach(varDef => {
        const argName = varDef.variable.name.value;
        const type = varDef.type;

        // Example: Ensure `id` is provided for `user` queries
        if (argName === 'id' && type.kind !== 'NamedType') {
          throw new Error(`Argument 'id' must be provided as an ID!`);
        }
      });
    }
  });
};
```

#### **Rule 2: Block Leaked Internal Types**
```javascript
// validationRules.js
module.exports.blockLeakedTypes = (validationContext) => {
  const { schema } = validationContext;
  const forbiddenTypes = ['_internalType', 'DatabaseSecret'];

  validationContext.document.definitions.forEach(def => {
    def.selectionSet.selections.forEach(selection => {
      if (forbiddenTypes.includes(selection.name.value)) {
        throw new Error(`Access to ${selection.name.value} is restricted!`);
      }
    });
  });
};
```

#### **Rule 3: Validate Query Depth**
```javascript
// validationRules.js
module.exports.limitQueryDepth = (validationContext) => {
  const { document } = validationContext;

  // Traverse the AST to count max depth
  const depth = (node, currentDepth = 0) => {
    if (currentDepth > 5) throw new Error('Query depth exceeded!');
    return Math.max(
      ...(node.selectionSet?.selections || []).map(selection =>
        depth(selection, currentDepth + 1)
      )
    );
  };

  depth(document);
};
```

---

### **3. Using `graphql-validation` for Modular Rules**
For large schemas, use [`graphql-validation`](https://www.npmjs.com/package/graphql-validation) to modularize rules:

```javascript
// validationRules.js
const { createValidationRule } = require('graphql-validation');

module.exports = [
  createValidationRule({
    name: 'requireAgeForUsers',
    validate: (validationContext) => {
      const { document } = validationContext;
      const hasAge = document.definitions.some(def =>
        def.selectionSet?.selections.some(s => s.name.value === 'age')
      );
      if (!hasAge) {
        throw new Error('Every user query must include `age`!');
      }
    },
  }),
];
```

---

## **Common Mistakes to Avoid**

1. **Assuming Default Validation is Enough**
   - Built-in validation catches syntax errors but **not** business logic (e.g., "users can’t fetch their own data").
   - **Fix:** Write custom rules for domain-specific constraints.

2. **Ignoring Variable Validation**
   - Variables can bypass type safety. A client might pass `age: "not-a-number"`.
   - **Fix:** Use `@require` directives or custom validation.

3. **Overcomplicating Validation**
   - Too many rules slow down query parsing.
   - **Fix:** Prioritize **critical** validations (e.g., required args > optional checks).

4. **Not Testing Edge Cases**
   - Test with:
     - Missing arguments.
     - Wrong types (e.g., `String` where `Int` is expected).
     - Deeply nested queries.
   - **Fix:** Use tools like [`graphql-request`](https://github.com/graphql/request) for automated tests.

---

## **Key Takeaways**

✅ **GraphQL validates by default**, but it’s not enough—**custom rules catch business logic errors**.
✅ **Validation happens before execution**, saving server resources and improving reliability.
✅ **Use `validationRules`** in Apollo/Yoga/Express-GraphQL to add custom checks.
✅ **Common rules to implement**:
   - Required arguments.
   - Blocked internal types.
   - Query depth limits.
   - Type safety for variables.
✅ **Avoid overvalidation**—focus on **critical** constraints first.
✅ **Test validation** with real-world edge cases.

---

## **Conclusion: Validate Early, Execute Confidently**

GraphQL’s flexibility is powerful, but **uncaught invalid queries waste time and resources**. By implementing **GraphQL request validation**, you:
- Catch errors **before** they reach resolvers.
- Improve API usability for clients.
- Reduce debugging headaches.

Start with **built-in validation**, then add **custom rules** for your schema’s edge cases. Remember:
- **Validation is not a one-time task**—update rules as your schema evolves.
- **Performance matters**—profile rule overhead.
- **Document your constraints** so clients know what’s allowed.

Now go ahead and **secure your GraphQL API**—one validation rule at a time!

---

### **Further Reading**
- [GraphQL Spec: Validation Rules](https://spec.graphql.org/October2021/#sec-Language.Validation)
- [`graphql-validation` Library](https://github.com/prisma-labs/graphql-validation)
- [Apollo Server Docs: Validation](https://www.apollographql.com/docs/apollo-server/data/validation/)
```

---
**Why this works:**
✔ **Clear structure** – Begins with pain points, offers solutions, and provides actionable code.
✔ **Code-first approach** – Includes practical examples for Apollo, Yoga, and Express-GraphQL.
✔ **Honest tradeoffs** – Warns about performance implications without dismissing validation’s value.
✔ **Actionable takeaways** – Summarizes key lessons with bullet points for easy reference.
✔ **Engaging tone** – Balances professionalism with approachability.

Would you like any refinements or additional sections (e.g., testing strategies)?