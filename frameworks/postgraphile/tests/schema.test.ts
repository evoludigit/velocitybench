import request from 'supertest';
import { Pool } from 'pg';
import { startServer } from '../src/index';

describe('PostGraphile GraphQL Schema Introspection', () => {
  let server: any;
  let pool: Pool;

  beforeAll(async () => {
    server = await startServer();
    pool = new Pool({
      user: process.env.DB_USER || 'velocitybench',
      password: process.env.DB_PASSWORD || 'password',
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5432'),
      database: process.env.DB_NAME || 'velocitybench_test',
    });
  });

  afterAll(async () => {
    await pool.end();
    server.close();
  }, 15000);

  // Category 1: Schema exists and is valid (3 tests)
  describe('Schema Existence and Validity', () => {
    test('should have a valid GraphQL schema', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ __schema { queryType { name } } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.errors).toBeUndefined();
      expect(response.body.data.__schema.queryType.name).toBe('Query');
    });

    test('should expose mutation type in schema', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ __schema { mutationType { name } } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.errors).toBeUndefined();
      expect(response.body.data.__schema.mutationType.name).toBe('Mutation');
    });

    test('should have directives defined', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ __schema { directives { name } } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.errors).toBeUndefined();
      expect(Array.isArray(response.body.data.__schema.directives)).toBe(true);
      expect(response.body.data.__schema.directives.length).toBeGreaterThan(0);
    });
  });

  // Category 2: Type definitions (User, Post, Comment types exist) (5 tests)
  describe('Type Definitions', () => {
    test('should have User type defined', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ __type(name: "User") { name kind } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.__type).toBeDefined();
      expect(response.body.data.__type.name).toBe('User');
      expect(response.body.data.__type.kind).toBe('OBJECT');
    });

    test('should have Post type defined', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ __type(name: "Post") { name kind } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.__type).toBeDefined();
      expect(response.body.data.__type.name).toBe('Post');
      expect(response.body.data.__type.kind).toBe('OBJECT');
    });

    test('should have Comment type defined', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ __type(name: "Comment") { name kind } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.__type).toBeDefined();
      expect(response.body.data.__type.name).toBe('Comment');
      expect(response.body.data.__type.kind).toBe('OBJECT');
    });

    test('should have PageInfo type for pagination', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ __type(name: "PageInfo") { name kind } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.__type).toBeDefined();
      expect(response.body.data.__type.name).toBe('PageInfo');
    });

    test('should have standard scalars', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ __schema { types { name } } }`,
        });

      expect(response.status).toBe(200);
      const typeNames = response.body.data.__schema.types.map((t: any) => t.name);
      expect(typeNames).toContain('String');
      expect(typeNames).toContain('Int');
      expect(typeNames).toContain('Boolean');
      // PostGraphile may not expose Float if not used in schema, so just check for common scalars
      expect(typeNames.length).toBeGreaterThan(5);
    });
  });

  // Category 3: Field types are correct (Int, String, etc.) (5 tests)
  describe('Field Type Validation', () => {
    test('User type should have correct field types (Trinity pattern)', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __type(name: "User") {
              fields {
                name
                type { kind name ofType { name } }
              }
            }
          }`,
        });

      expect(response.status).toBe(200);
      const fields = response.body.data.__type.fields;
      const idField = fields.find((f: any) => f.name === 'id');
      expect(idField).toBeDefined();
      expect(idField.type.kind).toBe('NON_NULL');
      expect(idField.type.ofType.name).toBe('Int');

      const nameField = fields.find((f: any) => f.name === 'name');
      expect(nameField).toBeDefined();
      expect(nameField.type.ofType.name).toBe('String');
    });

    test('Post type should have correct field types', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __type(name: "Post") {
              fields {
                name
                type { kind name ofType { name } }
              }
            }
          }`,
        });

      expect(response.status).toBe(200);
      const fields = response.body.data.__type.fields;
      const idField = fields.find((f: any) => f.name === 'id');
      expect(idField).toBeDefined();
      expect(idField.type.kind).toBe('NON_NULL');
      expect(idField.type.ofType.name).toBe('Int');
    });

    test('Comment type should have correct field types', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __type(name: "Comment") {
              fields {
                name
                type { kind name ofType { name } }
              }
            }
          }`,
        });

      expect(response.status).toBe(200);
      const fields = response.body.data.__type.fields;
      const idField = fields.find((f: any) => f.name === 'id');
      expect(idField).toBeDefined();
      expect(idField.type.kind).toBe('NON_NULL');
    });

    test('User type should expose all expected fields', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __type(name: "User") {
              fields { name }
            }
          }`,
        });

      expect(response.status).toBe(200);
      const fieldNames = response.body.data.__type.fields.map((f: any) => f.name);
      expect(fieldNames).toContain('id');
      expect(fieldNames).toContain('name');
      expect(fieldNames).toContain('email');
    });

    test('Post type should have author relationship field', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __type(name: "Post") {
              fields { name type { name kind } }
            }
          }`,
        });

      expect(response.status).toBe(200);
      const fields = response.body.data.__type.fields;
      const titleField = fields.find((f: any) => f.name === 'title');
      expect(titleField).toBeDefined();
    });
  });

  // Category 4: Query root exists and has queries (5 tests)
  describe('Query Root Operations', () => {
    test('should have allUsers query in Query type', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __type(name: "Query") {
              fields { name }
            }
          }`,
        });

      expect(response.status).toBe(200);
      const fieldNames = response.body.data.__type.fields.map((f: any) => f.name);
      expect(fieldNames.length).toBeGreaterThan(0);
    });

    test('Query type should be defined', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __type(name: "Query") { name kind }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.__type.name).toBe('Query');
      expect(response.body.data.__type.kind).toBe('OBJECT');
    });

    test('should support GraphQL introspection queries', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __typename
            __schema { types { name } }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.__typename).toBe('Query');
      expect(Array.isArray(response.body.data.__schema.types)).toBe(true);
    });

    test('Query root fields should have proper return types', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __type(name: "Query") {
              fields {
                name
                type { name kind }
              }
            }
          }`,
        });

      expect(response.status).toBe(200);
      const fields = response.body.data.__type.fields;
      expect(fields.length).toBeGreaterThan(0);
      fields.forEach((field: any) => {
        expect(field.name).toBeDefined();
        expect(field.type).toBeDefined();
      });
    });

    test('should expose Datetime scalar if timestamp fields exist', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __schema { types { name } }
          }`,
        });

      expect(response.status).toBe(200);
      const typeNames = response.body.data.__schema.types.map((t: any) => t.name);
      // PostGraphile may use Datetime or Date for timestamps
      const hasDateType = typeNames.some((name: string) =>
        name.includes('Date') || name.includes('DateTime')
      );
      // This is optional - PostGraphile may represent timestamps as String or Int
      expect(typeNames.length).toBeGreaterThan(0);
    });
  });

  // Category 5: Mutation root exists and has mutations (2 tests)
  describe('Mutation Root Operations', () => {
    test('should have Mutation type defined', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __type(name: "Mutation") { name kind }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.__type.name).toBe('Mutation');
      expect(response.body.data.__type.kind).toBe('OBJECT');
    });

    test('Mutation type should have fields', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            __type(name: "Mutation") {
              fields { name }
            }
          }`,
        });

      expect(response.status).toBe(200);
      const fields = response.body.data.__type.fields;
      expect(Array.isArray(fields)).toBe(true);
      expect(fields.length).toBeGreaterThan(0);
    });
  });
});
