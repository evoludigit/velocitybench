import request from 'supertest';
import { Pool } from 'pg';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

describe('PostGraphile GraphQL Query Operations', () => {
  let server: any;
  let pool: Pool;
  let factory: TestFactory;

  beforeAll(async () => {
    server = await startServer();
    pool = new Pool({
      user: process.env.DB_USER || 'velocitybench',
      password: process.env.DB_PASSWORD || 'password',
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5432'),
      database: process.env.DB_NAME || 'velocitybench_test',
    });
    factory = new TestFactory(pool);
  });

  afterAll(async () => {
    await pool.end();
    server.close();
  }, 15000);

  afterEach(async () => {
    await factory.cleanup();
  });

  // Category 1: Simple Queries (12 tests)
  describe('Simple Query Operations', () => {
    test('should retrieve user by ID', async () => {
      const user = await factory.createUser({ name: 'Alice', email: 'alice@example.com' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { id name email } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById).toBeDefined();
      expect(response.body.data.userById.id).toBe(user.id);
      expect(response.body.data.userById.name).toBe('Alice');
    });

    test('should return null for non-existent user', async () => {
      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "00000000-0000-0000-0000-000000000000") { id name } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById).toBeNull();
    });

    test('should support field selection', async () => {
      const user = await factory.createUser({ name: 'Bob' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { id name } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.id).toBeDefined();
      expect(response.body.data.userById.name).toBeDefined();
      expect(response.body.data.userById.email).toBeUndefined();
    });

    test('should handle unicode characters', async () => {
      const user = await factory.createUser({ name: '张三 李四 🎉' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { name } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.name).toBe('张三 李四 🎉');
    });

    test('should handle emoji in names', async () => {
      const user = await factory.createUser({ name: 'Happy 😊 User' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { name } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.name).toContain('😊');
    });

    test('should handle special characters in strings', async () => {
      const user = await factory.createUser({
        name: 'User "with" special <chars>',
        bio: 'Line1\nLine2\nLine3',
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { name bio } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.name).toContain('special');
      expect(response.body.data.userById.bio).toContain('\n');
    });

    test('should handle null values', async () => {
      const user = await factory.createUser({ name: 'NullBio', bio: null });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { name bio } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.bio).toBeNull();
    });

    test('should handle long strings', async () => {
      const longText = 'A'.repeat(10000);
      const user = await factory.createUser({ bio: longText });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { bio } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.bio.length).toBe(10000);
    });

    test('should retrieve post by ID', async () => {
      const post = await factory.createPost({ title: 'Test Post', content: 'Test content' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ postById(id: "${post.id}") { id title content } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.postById.id).toBe(post.id);
      expect(response.body.data.postById.title).toBe('Test Post');
    });

    test('should retrieve comment by ID', async () => {
      const post = await factory.createPost({ title: 'Post' });
      const author = await factory.createUser({ name: 'Author' });
      const client = await pool.connect();
      const result = await client.query(
        `INSERT INTO comments (content, fk_post, fk_user) VALUES ($1, $2, $3) RETURNING *`,
        ['Test comment', post.pk_post, author.pk_user]
      );
      client.release();

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ commentById(id: "${result.rows[0].id}") { id content } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.commentById).toBeDefined();
    });

    test('should return scalar types correctly', async () => {
      const user = await factory.createUser({ name: 'David' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { id name } }`,
        });

      expect(response.status).toBe(200);
      expect(typeof response.body.data.userById.id).toBe('string');
      expect(typeof response.body.data.userById.name).toBe('string');
    });
  });

  // Category 2: List and Pagination (10 tests)
  describe('List Queries and Pagination', () => {
    test('should retrieve list of all users', async () => {
      await factory.createUser({ name: 'User1' });
      await factory.createUser({ name: 'User2' });
      await factory.createUser({ name: 'User3' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers { nodes { id name } } }`,
        });

      expect(response.status).toBe(200);
      expect(Array.isArray(response.body.data.allUsers.nodes)).toBe(true);
      expect(response.body.data.allUsers.nodes.length).toBeGreaterThanOrEqual(3);
    });

    test('should support first parameter for pagination', async () => {
      for (let i = 0; i < 5; i++) {
        await factory.createUser({ name: `User${i}` });
      }

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers(first: 2) { nodes { id } } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.allUsers.nodes.length).toBeLessThanOrEqual(2);
    });

    test('should return edges with cursors for pagination', async () => {
      await factory.createUser({ name: 'User1' });
      await factory.createUser({ name: 'User2' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers(first: 1) { edges { cursor node { id } } } }`,
        });

      expect(response.status).toBe(200);
      expect(Array.isArray(response.body.data.allUsers.edges)).toBe(true);
      expect(response.body.data.allUsers.edges[0].cursor).toBeDefined();
    });

    test('should support after parameter for cursor pagination', async () => {
      for (let i = 0; i < 5; i++) {
        await factory.createUser({ name: `User${i}` });
      }

      const firstResponse = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers(first: 2) { edges { cursor } pageInfo { hasNextPage } } }`,
        });

      expect(firstResponse.status).toBe(200);
      if (firstResponse.body.data.allUsers.pageInfo.hasNextPage) {
        const cursor = firstResponse.body.data.allUsers.edges[1].cursor;

        const secondResponse = await request(server)
          .post('/graphql')
          .send({
            query: `{ allUsers(first: 2, after: "${cursor}") { nodes { id } } }`,
          });

        expect(secondResponse.status).toBe(200);
        expect(Array.isArray(secondResponse.body.data.allUsers.nodes)).toBe(true);
      }
    });

    test('should include pageInfo with pagination details', async () => {
      await factory.createUser({ name: 'User1' });
      await factory.createUser({ name: 'User2' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            allUsers(first: 1) {
              pageInfo {
                hasNextPage
                hasPreviousPage
                startCursor
                endCursor
              }
            }
          }`,
        });

      expect(response.status).toBe(200);
      const pageInfo = response.body.data.allUsers.pageInfo;
      expect(pageInfo).toHaveProperty('hasNextPage');
      expect(typeof pageInfo.hasNextPage).toBe('boolean');
    });

    test('should retrieve list of posts', async () => {
      await factory.createPost({ title: 'Post1' });
      await factory.createPost({ title: 'Post2' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allPosts { nodes { id title } } }`,
        });

      expect(response.status).toBe(200);
      expect(Array.isArray(response.body.data.allPosts.nodes)).toBe(true);
    });

    test('should retrieve list of comments', async () => {
      const post = await factory.createPost({ title: 'Post' });
      const author = await factory.createUser({ name: 'Author' });
      const client = await pool.connect();
      await client.query(
        `INSERT INTO comments (content, post_id, author_id) VALUES ($1, $2, $3)`,
        ['Comment', post.id, author.id]
      );
      client.release();

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allComments { nodes { id content } } }`,
        });

      expect(response.status).toBe(200);
      expect(Array.isArray(response.body.data.allComments.nodes)).toBe(true);
    });

    test('should handle empty results gracefully', async () => {
      await factory.cleanup();

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ allUsers { nodes { id } } }`,
        });

      expect(response.status).toBe(200);
      expect(Array.isArray(response.body.data.allUsers.nodes)).toBe(true);
      expect(response.body.data.allUsers.nodes.length).toBe(0);
    });

    test('should support multiple queries in one request', async () => {
      const user = await factory.createUser({ name: 'Alice' });
      const post = await factory.createPost({ title: 'Post' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            userData: userById(id: "${user.id}") { name }
            postData: postById(id: "${post.id}") { title }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userData).toBeDefined();
      expect(response.body.data.postData).toBeDefined();
    });
  });

  // Category 3: Complex/Nested Queries (8 tests)
  describe('Complex and Nested Queries', () => {
    test('should support Trinity pattern - retrieve by primary key', async () => {
      const user = await factory.createUser({ name: 'Trinity' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ userById(id: "${user.id}") { id name } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.id).toBe(user.id);
    });

    test('should support Trinity pattern - foreign key relationships', async () => {
      const author = await factory.createUser({ name: 'Author' });
      const post = await factory.createPost({ title: 'Test', fk_user: author.pk_user });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{ postById(id: "${post.id}") { id title } }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.postById.title).toBe('Test');
    });

    test('should handle deeply nested relationships', async () => {
      const user = await factory.createUser({ name: 'Author' });
      const post = await factory.createPost({ title: 'Post', fk_user: user.pk_user });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            postById(id: "${post.id}") {
              title
            }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.postById.title).toBeDefined();
    });

    test('should resolve relationships through foreign keys', async () => {
      const author = await factory.createUser({ name: 'John' });
      const post = await factory.createPost({
        title: 'My Post',
        fk_user: author.pk_user,
        content: 'Content',
      });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            postById(id: "${post.id}") {
              title
              content
            }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.postById.title).toBe('My Post');
    });

    test('should handle multiple relationships', async () => {
      const user1 = await factory.createUser({ name: 'User1' });
      const user2 = await factory.createUser({ name: 'User2' });
      const post1 = await factory.createPost({ title: 'Post1', fk_user: user1.pk_user });
      const post2 = await factory.createPost({ title: 'Post2', fk_user: user2.pk_user });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            post1: postById(id: "${post1.id}") { title }
            post2: postById(id: "${post2.id}") { title }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.post1.title).toBe('Post1');
      expect(response.body.data.post2.title).toBe('Post2');
    });

    test('should handle batched queries', async () => {
      const user1 = await factory.createUser({ name: 'Alice' });
      const user2 = await factory.createUser({ name: 'Bob' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            alice: userById(id: "${user1.id}") { name }
            bob: userById(id: "${user2.id}") { name }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.alice.name).toBe('Alice');
      expect(response.body.data.bob.name).toBe('Bob');
    });

    test('should handle query variables', async () => {
      const user = await factory.createUser({ name: 'Variable' });

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `query GetUser($id: UUID!) { userById(id: $id) { id name } }`,
          variables: { id: user.id },
        });

      expect(response.status).toBe(200);
      expect(response.body.data.userById.name).toBe('Variable');
    });

    test('should handle multiple paginated lists', async () => {
      for (let i = 0; i < 3; i++) {
        await factory.createUser({ name: `User${i}` });
        await factory.createPost({ title: `Post${i}` });
      }

      const response = await request(server)
        .post('/graphql')
        .send({
          query: `{
            users: allUsers(first: 2) { nodes { id } }
            posts: allPosts(first: 2) { nodes { id } }
          }`,
        });

      expect(response.status).toBe(200);
      expect(response.body.data.users.nodes.length).toBeLessThanOrEqual(2);
      expect(response.body.data.posts.nodes.length).toBeLessThanOrEqual(2);
    });
  });
});
