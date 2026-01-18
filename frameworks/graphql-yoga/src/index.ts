import { createServer } from 'http';
import { createSchema, createYoga } from 'graphql-yoga';
import { createDataLoaders, DataLoaders } from './dataloaders.js';
import { pool } from './db.js';

// GraphQL Schema
const typeDefs = /* GraphQL */ `
  type Query {
    ping: String!
    user(id: ID!): User
    users(limit: Int = 10): [User!]!
    post(id: ID!): Post
    posts(limit: Int = 10): [Post!]!
    comment(id: ID!): Comment
  }

  type Mutation {
    updateUser(id: ID!, bio: String, fullName: String): User
  }

  type User {
    id: ID!
    username: String!
    fullName: String
    bio: String
    followerCount: Int!
    posts(limit: Int = 50): [Post!]!
  }

  type Post {
    id: ID!
    title: String!
    content: String
    author: User
    comments(limit: Int = 50): [Comment!]!
  }

  type Comment {
    id: ID!
    content: String!
    author: User
    post: Post
  }
`;

// Context type
interface GraphQLContext {
  loaders: DataLoaders;
}

// Resolvers
const resolvers = {
  Query: {
    ping: () => 'pong',

    user: async (_: unknown, { id }: { id: string }, ctx: GraphQLContext) => {
      const result = await pool.query(
        'SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = $1',
        [id]
      );
      if (result.rows.length === 0) return null;
      const row = result.rows[0];
      return {
        id: row.id,
        username: row.username,
        fullName: row.full_name,
        bio: row.bio,
      };
    },

    users: async (_: unknown, { limit }: { limit: number }) => {
      const safeLimit = Math.min(Math.max(limit, 1), 100);
      const result = await pool.query(
        'SELECT id, username, full_name, bio FROM benchmark.tb_user LIMIT $1',
        [safeLimit]
      );
      return result.rows.map((row) => ({
        id: row.id,
        username: row.username,
        fullName: row.full_name,
        bio: row.bio,
      }));
    },

    post: async (_: unknown, { id }: { id: string }) => {
      const result = await pool.query(
        `SELECT p.id, p.title, p.content, u.id as author_id
         FROM benchmark.tb_post p
         JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
         WHERE p.id = $1`,
        [id]
      );
      if (result.rows.length === 0) return null;
      const row = result.rows[0];
      return {
        id: row.id,
        title: row.title,
        content: row.content,
        authorId: row.author_id,
      };
    },

    posts: async (_: unknown, { limit }: { limit: number }) => {
      const safeLimit = Math.min(Math.max(limit, 1), 100);
      const result = await pool.query(
        `SELECT p.id, p.title, p.content, u.id as author_id
         FROM benchmark.tb_post p
         JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
         ORDER BY p.created_at DESC
         LIMIT $1`,
        [safeLimit]
      );
      return result.rows.map((row) => ({
        id: row.id,
        title: row.title,
        content: row.content,
        authorId: row.author_id,
      }));
    },

    comment: async (_: unknown, { id }: { id: string }) => {
      const result = await pool.query(
        `SELECT c.id, c.content, u.id as author_id, p.id as post_id
         FROM benchmark.tb_comment c
         JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
         JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
         WHERE c.id = $1`,
        [id]
      );
      if (result.rows.length === 0) return null;
      const row = result.rows[0];
      return {
        id: row.id,
        content: row.content,
        authorId: row.author_id,
        postId: row.post_id,
      };
    },
  },

  Mutation: {
    updateUser: async (
      _: unknown,
      { id, bio, fullName }: { id: string; bio?: string; fullName?: string }
    ) => {
      if (bio === undefined && fullName === undefined) {
        throw new Error('At least one of bio or fullName must be provided');
      }

      const updates: string[] = [];
      const params: (string | undefined)[] = [id];
      let paramIdx = 2;

      if (bio !== undefined) {
        updates.push(`bio = $${paramIdx}`);
        params.push(bio);
        paramIdx++;
      }
      if (fullName !== undefined) {
        updates.push(`full_name = $${paramIdx}`);
        params.push(fullName);
        paramIdx++;
      }

      if (updates.length > 0) {
        await pool.query(
          `UPDATE benchmark.tb_user SET ${updates.join(', ')}, updated_at = NOW() WHERE id = $1`,
          params
        );
      }

      const result = await pool.query(
        'SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = $1',
        [id]
      );
      if (result.rows.length === 0) return null;
      const row = result.rows[0];
      return {
        id: row.id,
        username: row.username,
        fullName: row.full_name,
        bio: row.bio,
      };
    },
  },

  User: {
    followerCount: () => 0,
    posts: async (
      parent: { id: string },
      { limit }: { limit: number },
      ctx: GraphQLContext
    ) => {
      const posts = await ctx.loaders.postsByAuthorLoader.load(parent.id);
      return posts.slice(0, Math.min(limit, 50)).map((post) => ({
        id: post.id,
        title: post.title,
        content: post.content,
        authorId: post.author_id,
      }));
    },
  },

  Post: {
    author: async (parent: { authorId: string }, _: unknown, ctx: GraphQLContext) => {
      if (!parent.authorId) return null;
      const user = await ctx.loaders.userLoader.load(parent.authorId);
      if (!user) return null;
      return {
        id: user.id,
        username: user.username,
        fullName: user.full_name,
        bio: user.bio,
      };
    },
    comments: async (
      parent: { id: string },
      { limit }: { limit: number },
      ctx: GraphQLContext
    ) => {
      const comments = await ctx.loaders.commentsByPostLoader.load(parent.id);
      return comments.slice(0, Math.min(limit, 50)).map((comment) => ({
        id: comment.id,
        content: comment.content,
        authorId: comment.author_id,
        postId: comment.post_id,
      }));
    },
  },

  Comment: {
    author: async (parent: { authorId: string }, _: unknown, ctx: GraphQLContext) => {
      if (!parent.authorId) return null;
      const user = await ctx.loaders.userLoader.load(parent.authorId);
      if (!user) return null;
      return {
        id: user.id,
        username: user.username,
        fullName: user.full_name,
        bio: user.bio,
      };
    },
    post: async (parent: { postId: string }, _: unknown, ctx: GraphQLContext) => {
      if (!parent.postId) return null;
      const post = await ctx.loaders.postLoader.load(parent.postId);
      if (!post) return null;
      return {
        id: post.id,
        title: post.title,
        content: post.content,
        authorId: post.author_id,
      };
    },
  },
};

// Create Yoga instance
const yoga = createYoga({
  schema: createSchema({
    typeDefs,
    resolvers,
  }),
  context: () => ({
    loaders: createDataLoaders(),
  }),
  graphqlEndpoint: '/graphql',
});

// Create HTTP server with health endpoint
const server = createServer(async (req, res) => {
  if (req.url === '/health') {
    try {
      await pool.query('SELECT 1');
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'healthy', framework: 'graphql-yoga' }));
    } catch (error) {
      res.writeHead(503, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'unhealthy', error: String(error) }));
    }
    return;
  }

  // Handle all other requests with Yoga
  yoga.handle(req, res);
});

const port = parseInt(process.env.PORT || '4000');

server.listen(port, () => {
  console.log(`🧘 GraphQL Yoga server ready at http://localhost:${port}/graphql`);
  console.log(`📊 Health endpoint at http://localhost:${port}/health`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Received SIGTERM, shutting down...');
  await pool.end();
  server.close();
  process.exit(0);
});
