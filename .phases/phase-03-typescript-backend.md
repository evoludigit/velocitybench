# Phase 3: TypeScript/Node.js Backend

## Objective

Build TypeScript-based backends using FraiseQL's TypeScript generator, creating Express, Fastify, and Apollo Server implementations that serve the same compiled schema as Python backends.

## Success Criteria

- [ ] Express + FraiseQL backend functional
- [ ] Fastify + FraiseQL backend functional
- [ ] Apollo Server + FraiseQL backend functional
- [ ] All share identical schema from Phase 1
- [ ] Common test suite passes
- [ ] Performance parity with Python backends
- [ ] TypeScript strict mode enabled
- [ ] All types generated from schema

## TDD Cycles

### Cycle 1: TypeScript Schema Generation

**RED**: Test TypeScript schema generator produces correct types
```typescript
// tests/typescript/test_schema_generation.ts
import { generateSchema } from '../fraiseql-schema/schema.fraiseql';

test('generates schema with correct types', async () => {
  const schema = await generateSchema();
  expect(schema.types).toBeDefined();
  expect(schema.types.User).toBeDefined();
  expect(schema.types.User.fields.id.type).toBe('Int!');
});

test('schema exports to json', async () => {
  const json = await exportSchemaJson('schema.json');
  expect(json.types).toBeDefined();
});
```

**GREEN**: Create minimal TypeScript schema
```typescript
// fraiseql-schema/schema.fraiseql.ts
import { Type, Query, Mutation, SchemaRegistry } from 'fraiseql';

@Type()
class User {
  id!: number;
  name!: string;
  email?: string;
}

@Type()
class Post {
  id!: number;
  title!: string;
  author!: User;
}

@Query(sqlSource = "v_users")
users(limit?: number): User[] { return []; }

@Mutation(sqlSource = "fn_create_user")
createUser(name: string, email: string): User { return new User(); }

export { SchemaRegistry };
```

**REFACTOR**: Add proper decorator implementations, metadata

**CLEANUP**: Verify schema exports to JSON correctly

---

### Cycle 2: Express + FraiseQL Integration

**RED**: Test Express serves FraiseQL GraphQL queries
```typescript
import request from 'supertest';
import { app } from '../frameworks/fraiseql-typescript/express/app';

describe('Express + FraiseQL', () => {
  it('executes graphql query', async () => {
    const response = await request(app)
      .post('/graphql')
      .send({ query: '{ users { id name } }' });

    expect(response.status).toBe(200);
    expect(response.body.data.users).toBeDefined();
  });

  it('supports mutations', async () => {
    const response = await request(app)
      .post('/graphql')
      .send({
        query: `mutation {
          createUser(name: "Test", email: "test@example.com") {
            id name
          }
        }`
      });

    expect(response.status).toBe(200);
    expect(response.body.data.createUser.id).toBeDefined();
  });
});
```

**GREEN**: Minimal Express + FraiseQL server
```typescript
// frameworks/fraiseql-typescript/express/app.ts
import express from 'express';
import { FraiseQLRuntime } from 'fraiseql-runtime';

export const app = express();
const runtime = new FraiseQLRuntime({
  schemaPath: 'schema.compiled.json'
});

app.use(express.json());

app.post('/graphql', async (req, res) => {
  const { query, variables } = req.body;
  try {
    const result = await runtime.execute(query, variables);
    res.json({ data: result });
  } catch (error) {
    res.status(400).json({ errors: [{ message: error.message }] });
  }
});

export default app;
```

**REFACTOR**: Add error handling, validation, middleware

**CLEANUP**: Remove debug logging, ensure clean exports

---

### Cycle 3: Fastify + FraiseQL Integration

**RED**: Test Fastify serves FraiseQL queries correctly
```typescript
import { build } from '../frameworks/fraiseql-typescript/fastify/app';

describe('Fastify + FraiseQL', () => {
  it('executes graphql query', async () => {
    const app = await build();
    const response = await app.inject({
      method: 'POST',
      url: '/graphql',
      payload: { query: '{ users { id } }' }
    });

    expect(response.statusCode).toBe(200);
  });
});
```

**GREEN**: Minimal Fastify + FraiseQL
```typescript
// frameworks/fraiseql-typescript/fastify/app.ts
import Fastify from 'fastify';
import { FraiseQLRuntime } from 'fraiseql-runtime';

export async function build() {
  const fastify = Fastify();
  const runtime = new FraiseQLRuntime({
    schemaPath: 'schema.compiled.json'
  });

  fastify.post('/graphql', async (request, reply) => {
    const result = await runtime.execute(
      request.body.query,
      request.body.variables
    );
    return { data: result };
  });

  return fastify;
}
```

**REFACTOR**: Add proper error handling, typings

**CLEANUP**: Ensure Fastify conventions followed

---

### Cycle 4: Apollo Server + FraiseQL Integration

**RED**: Test Apollo Server uses FraiseQL backend
```typescript
import { ApolloServer, gql } from 'apollo-server-express';
import { app } from '../frameworks/fraiseql-typescript/apollo/app';

describe('Apollo Server + FraiseQL', () => {
  it('executes query via FraiseQL', async () => {
    const response = await app._apollo.executeOperation({
      query: gql`{ users { id } }`
    });

    expect(response.data.users).toBeDefined();
  });
});
```

**GREEN**: Apollo Server with FraiseQL data source
```typescript
// frameworks/fraiseql-typescript/apollo/app.ts
import { ApolloServer } from 'apollo-server-express';
import express from 'express';
import { FraiseQLDataSource } from './datasource';

const app = express();
const server = new ApolloServer({
  typeDefs: readSchemaFromFraiseQL('schema.compiled.json'),
  resolvers: {
    Query: {
      users: async (_, args, { dataSources }) =>
        dataSources.fraiseql.query('users', args)
    }
  },
  dataSources: () => ({
    fraiseql: new FraiseQLDataSource('schema.compiled.json')
  })
});

await server.start();
server.applyMiddleware({ app });
```

**REFACTOR**: Add proper resolver delegation pattern

**CLEANUP**: Verify all resolvers use FraiseQL

---

### Cycle 5: Shared Test Suite for TypeScript

**RED**: All common tests pass against TypeScript backends
```typescript
// tests/common/test_parity.ts
describe.each([
  { framework: 'express', client: getExpressClient },
  { framework: 'fastify', client: getFastifyClient },
  { framework: 'apollo', client: getApolloClient }
])('$framework parity tests', ({ framework, client: getClient }) => {

  it('users query returns expected fields', async () => {
    const c = await getClient();
    const result = await c.query('{ users { id name email } }');
    expect(result.data.users).toBeDefined();
    expect(result.data.users[0]).toHaveProperty('id');
  });

  it('mutations create records', async () => {
    const c = await getClient();
    const result = await c.mutate(
      `mutation { createUser(name: "Test", email: "test@example.com") { id } }`
    );
    expect(result.data.createUser.id).toBeDefined();
  });
});
```

**GREEN**: Create test client factory
```typescript
// tests/common/typescript-client.ts
import request from 'supertest';

export class GraphQLClient {
  constructor(private app: any) {}

  async query(queryString: string, variables?: any) {
    const response = await request(this.app)
      .post('/graphql')
      .send({ query: queryString, variables });

    return response.body;
  }

  async mutate(mutationString: string, variables?: any) {
    return this.query(mutationString, variables);
  }
}
```

**REFACTOR**: Generalize for different server implementations

**CLEANUP**: Ensure all common tests pass

---

### Cycle 6: TypeScript Type Safety & Validation

**RED**: TypeScript strict mode with generated types
```typescript
// tests/typescript/test_type_safety.ts
import { User, Post } from '../generated/types';

test('generated types prevent invalid operations', () => {
  const user: User = { id: 1, name: 'Test' };

  // Should compile
  console.log(user.id);

  // @ts-expect-error - should not compile
  console.log(user.invalidField);
});

test('schema matches runtime types', async () => {
  const client = getExpressClient();
  const result = await client.query('{ users { id name } }');

  // Type check without assertion
  const users: User[] = result.data.users;
  expect(users[0].name).toEqual(expect.any(String));
});
```

**GREEN**: Generate types from schema
```typescript
// scripts/generate-types.ts
import { compileFromFile } from 'json-schema-to-typescript';

async function generateTypes() {
  const typescript = await compileFromFile('schema.compiled.json');
  fs.writeFileSync('generated/types.ts', typescript);
}
```

**REFACTOR**: Ensure generated types match schema exactly

**CLEANUP**: Verify type completeness

---

## Directory Structure (TypeScript)

```
frameworks/
└── fraiseql-typescript/
    ├── shared/
    │   ├── runtime.ts              # FraiseQL runtime wrapper
    │   ├── client.ts               # Test client
    │   ├── middleware.ts           # Auth, logging
    │   └── types.ts                # Generated types
    │
    ├── express/
    │   ├── app.ts                  # Express app
    │   ├── routes.ts               # Route definitions
    │   ├── package.json
    │   ├── tsconfig.json
    │   └── tests/
    │
    ├── fastify/
    │   ├── app.ts                  # Fastify server
    │   ├── plugins.ts              # Plugin setup
    │   ├── package.json
    │   └── tests/
    │
    └── apollo-server/
        ├── app.ts                  # Apollo server setup
        ├── datasource.ts           # FraiseQL data source
        ├── package.json
        └── tests/
```

## Build & Test Strategy

```bash
# Generate schema and types
npm run generate:schema
npm run generate:types

# Build all frameworks
npm run build:express
npm run build:fastify
npm run build:apollo

# Test all frameworks
npm test -- --coverage

# Performance benchmarks
npm run bench
```

## Dependencies

- Requires: Phase 1 (schema complete)
- Requires: FraiseQL TypeScript generator v2.0.0-a1+
- Blocks: Phase 7 (cross-language testing)

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- TypeScript strict mode required (`"strict": true`)
- All types generated from compiled schema
- No manual type definitions for API responses
- Common test suite validates parity with Python backends
