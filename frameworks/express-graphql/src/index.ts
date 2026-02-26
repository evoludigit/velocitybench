import express from 'express';
import { createHandler } from 'graphql-http/lib/use/express';
import {
  GraphQLSchema,
  GraphQLObjectType,
  GraphQLString,
  GraphQLInt,
  GraphQLID,
  GraphQLList,
  GraphQLNonNull,
} from 'graphql';
import { createDataLoaders, DataLoaders } from './dataloaders.js';
import { pool } from './db.js';

// Context type
interface GraphQLContext {
  loaders: DataLoaders;
}

// Forward references
let UserType: GraphQLObjectType;
let PostType: GraphQLObjectType;
let CommentType: GraphQLObjectType;

// User Type
UserType = new GraphQLObjectType({
  name: 'User',
  fields: () => ({
    id: { type: new GraphQLNonNull(GraphQLID) },
    username: { type: new GraphQLNonNull(GraphQLString) },
    fullName: { type: GraphQLString },
    bio: { type: GraphQLString },
    followerCount: {
      type: new GraphQLNonNull(GraphQLInt),
      resolve: () => 0,
    },
    posts: {
      type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(PostType))),
      args: { limit: { type: GraphQLInt, defaultValue: 50 } },
      resolve: async (parent: { id: string }, { limit }: { limit: number }, ctx: GraphQLContext) => {
        const posts = await ctx.loaders.postsByAuthorLoader.load(parent.id);
        return posts.slice(0, Math.min(limit, 50)).map((post: any) => ({
          id: post.id,
          title: post.title,
          content: post.content,
          authorId: post.author_id,
        }));
      },
    },
  }),
});

// Post Type
PostType = new GraphQLObjectType({
  name: 'Post',
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fields: (): any => ({
    id: { type: new GraphQLNonNull(GraphQLID) },
    title: { type: new GraphQLNonNull(GraphQLString) },
    content: { type: GraphQLString },
    author: {
      type: UserType,
      resolve: async (parent: { authorId: string }, _: unknown, ctx: GraphQLContext) => {
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
    },
    comments: {
      type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(CommentType))),
      args: { limit: { type: GraphQLInt, defaultValue: 50 } },
      resolve: async (parent: { id: string }, { limit }: { limit: number }, ctx: GraphQLContext) => {
        const comments = await ctx.loaders.commentsByPostLoader.load(parent.id);
        return comments.slice(0, Math.min(limit, 50)).map((comment: any) => ({
          id: comment.id,
          content: comment.content,
          authorId: comment.author_id,
          postId: comment.post_id,
        }));
      },
    },
  }),
});

// Comment Type
CommentType = new GraphQLObjectType({
  name: 'Comment',
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fields: (): any => ({
    id: { type: new GraphQLNonNull(GraphQLID) },
    content: { type: new GraphQLNonNull(GraphQLString) },
    author: {
      type: UserType,
      resolve: async (parent: { authorId: string }, _: unknown, ctx: GraphQLContext) => {
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
    },
    post: {
      type: PostType,
      resolve: async (parent: { postId: string }, _: unknown, ctx: GraphQLContext) => {
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
  }),
});

// Query Type
const QueryType = new GraphQLObjectType({
  name: 'Query',
  fields: {
    ping: {
      type: new GraphQLNonNull(GraphQLString),
      resolve: () => 'pong',
    },
    user: {
      type: UserType,
      args: { id: { type: new GraphQLNonNull(GraphQLID) } },
      resolve: async (_: unknown, { id }: { id: string }) => {
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
    users: {
      type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(UserType))),
      args: { limit: { type: GraphQLInt, defaultValue: 10 } },
      resolve: async (_: unknown, { limit }: { limit: number }) => {
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
    },
    post: {
      type: PostType,
      args: { id: { type: new GraphQLNonNull(GraphQLID) } },
      resolve: async (_: unknown, { id }: { id: string }) => {
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
    },
    posts: {
      type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(PostType))),
      args: { limit: { type: GraphQLInt, defaultValue: 10 } },
      resolve: async (_: unknown, { limit }: { limit: number }) => {
        const safeLimit = Math.min(Math.max(limit, 1), 100);
        const result = await pool.query(
          `SELECT p.id, p.title, p.content, u.id as author_id
           FROM benchmark.tb_post p
           JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
           ORDER BY p.created_at DESC
           LIMIT $1`,
          [safeLimit]
        );
        return result.rows.map((row: any) => ({
          id: row.id,
          title: row.title,
          content: row.content,
          authorId: row.author_id,
        }));
      },
    },
    comment: {
      type: CommentType,
      args: { id: { type: new GraphQLNonNull(GraphQLID) } },
      resolve: async (_: unknown, { id }: { id: string }) => {
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
  },
});

// Mutation Type
const MutationType = new GraphQLObjectType({
  name: 'Mutation',
  fields: {
    updateUser: {
      type: UserType,
      args: {
        id: { type: new GraphQLNonNull(GraphQLID) },
        bio: { type: GraphQLString },
        fullName: { type: GraphQLString },
      },
      resolve: async (
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
  },
});

// Create Schema
const schema = new GraphQLSchema({
  query: QueryType,
  mutation: MutationType,
});

// Create Express app
const app = express();

// Health check endpoint
app.get('/health', async (_req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'healthy', framework: 'express-graphql' });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: String(error) });
  }
});

// GraphQL endpoint using graphql-http
app.use(
  '/graphql',
  createHandler({
    schema,
    context: () => ({
      loaders: createDataLoaders(),
    }),
  })
);

// Start server
const port = parseInt(process.env.PORT || '4000');

app.listen(port, () => {
  console.log(`🚀 Express-GraphQL server ready at http://localhost:${port}/graphql`);
  console.log(`📊 Health endpoint at http://localhost:${port}/health`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Received SIGTERM, shutting down...');
  await pool.end();
  process.exit(0);
});
