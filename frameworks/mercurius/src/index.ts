import Fastify from 'fastify';
import mercurius from 'mercurius';
import { createDataLoaders, DataLoaders } from './dataloaders.js';
import { pool } from './db.js';

// GraphQL Schema
const schema = /* GraphQL */ `
  type Query {
    ping: String!
    user(id: ID!): User
    users(limit: Int = 10): [User!]!
    post(id: ID!): Post
    posts(limit: Int = 10, published: Boolean): [Post!]!
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
      return result.rows.map((row: any) => ({
        id: row.id,
        username: row.username,
        fullName: row.full_name,
        bio: row.bio,
      }));
    },

    post: async (_: unknown, { id }: { id: string }) => {
      const result = await pool.query(
        `SELECT id, fk_author, title, content
         FROM benchmark.tb_post
         WHERE id = $1`,
        [id]
      );
      if (result.rows.length === 0) return null;
      const row = result.rows[0];
      return {
        id: row.id,
        title: row.title,
        content: row.content,
        fkAuthor: row.fk_author,
      };
    },

    posts: async (_: unknown, { limit, published }: { limit: number; published?: boolean }) => {
      const safeLimit = Math.min(Math.max(limit, 1), 100);
      let result;
      if (published === undefined || published === null) {
        result = await pool.query(
          `SELECT id, fk_author, title, content
           FROM benchmark.tb_post
           ORDER BY created_at DESC
           LIMIT $1`,
          [safeLimit]
        );
      } else {
        result = await pool.query(
          `SELECT id, fk_author, title, content
           FROM benchmark.tb_post
           WHERE published = $2
           ORDER BY created_at DESC
           LIMIT $1`,
          [safeLimit, published]
        );
      }
      return result.rows.map((row: any) => ({
        id: row.id,
        title: row.title,
        content: row.content,
        fkAuthor: row.fk_author,
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
      return posts.slice(0, Math.min(limit, 50)).map((post: any) => ({
        id: post.id,
        title: post.title,
        content: post.content,
        fkAuthor: post.fk_author,
      }));
    },
  },

  Post: {
    author: async (parent: { fkAuthor: number }, _: unknown, ctx: GraphQLContext) => {
      if (!parent.fkAuthor) return null;
      const user = await ctx.loaders.userByPkLoader.load(parent.fkAuthor);
      if (!user) return null;
      return {
        id: (user as any).id,
        username: (user as any).username,
        fullName: (user as any).full_name,
        bio: (user as any).bio,
      };
    },
    comments: async (
      parent: { id: string },
      { limit }: { limit: number },
      ctx: GraphQLContext
    ) => {
      const comments = await ctx.loaders.commentsByPostLoader.load(parent.id);
      return comments.slice(0, Math.min(limit, 50)).map((comment: any) => ({
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
        fkAuthor: (post as any).fk_author,
      };
    },
  },
};

// Create Fastify instance
const app = Fastify({
  logger: true,
});

// Register Mercurius
// eslint-disable-next-line @typescript-eslint/no-explicit-any
app.register(mercurius, {
  schema,
  resolvers: resolvers as any,
  context: () => ({
    loaders: createDataLoaders(),
  }),
  graphiql: false, // Disable for benchmarks
});

// Health check endpoint
app.get('/health', async (_request, reply) => {
  try {
    await pool.query('SELECT 1');
    return { status: 'healthy', framework: 'mercurius' };
  } catch (error) {
    reply.code(503);
    return { status: 'unhealthy', error: String(error) };
  }
});

// Start server
const port = parseInt(process.env.PORT || '4000');

app.listen({ port, host: '0.0.0.0' }, (err, address) => {
  if (err) {
    app.log.error(err);
    process.exit(1);
  }
  console.log(`🚀 Mercurius server ready at ${address}/graphql`);
  console.log(`📊 Health endpoint at ${address}/health`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Received SIGTERM, shutting down...');
  await pool.end();
  await app.close();
  process.exit(0);
});
