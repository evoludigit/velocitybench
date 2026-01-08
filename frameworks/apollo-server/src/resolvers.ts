import { query, queryOne } from './db.js';
import { updateUserSchema } from './validation.js';
import type { DataLoaders } from './dataloaders.js';

interface Context {
  loaders: DataLoaders;
}

export const resolvers = {
  Query: {
    ping: () => 'pong',

    user: async (_: any, { id }: { id: string }, { loaders }: Context) => {
      return loaders.userLoader.load(id);
    },

    users: async (_: any, { limit }: { limit: number }) => {
      return query(
        `SELECT id, username, full_name, bio
         FROM benchmark.tb_user
         ORDER BY created_at DESC
         LIMIT $1`,
        [limit]
      );
    },

    post: async (_: any, { id }: { id: string }) => {
      return queryOne(
        `SELECT p.id, u.id as author_id, p.title, p.content, p.published as status
         FROM benchmark.tb_post p
         JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
         WHERE p.id = $1`,
        [id]
      );
    },

    posts: async (_: any, { limit }: { limit: number }) => {
      return query(
        `SELECT p.id, u.id as author_id, p.title, p.content, p.published as status
         FROM benchmark.tb_post p
         JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
         WHERE p.published = true
         ORDER BY p.created_at DESC
         LIMIT $1`,
        [limit]
      );
    },

    comment: async (_: any, { id }: { id: string }) => {
      return queryOne(
        `SELECT c.id, p.id as post_id, u.id as author_id, c.content
         FROM benchmark.tb_comment c
         JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
         JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
         WHERE c.id = $1`,
        [id]
      );
    },

    comments: async (_: any, { limit }: { limit: number }) => {
      return query(
        `SELECT c.id, p.id as post_id, u.id as author_id, c.content
         FROM benchmark.tb_comment c
         JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
         JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
         ORDER BY c.created_at DESC
         LIMIT $1`,
        [limit]
      );
    },
  },

  User: {
    fullName: (user: any) => user.full_name,

    posts: async (user: any, { limit }: { limit: number }, { loaders }: Context) => {
      const posts = await loaders.postsByAuthorLoader.load(user.id);
      return posts.slice(0, limit || 10);
    },

    followerCount: async (user: any, _: any, { loaders }: Context) => {
      return loaders.followerCountLoader.load(user.id);
    },
  },

  Post: {
    author: async (post: any, _: any, { loaders }: Context) => {
      return loaders.userLoader.load(post.author_id);
    },

    comments: async (post: any, { limit }: { limit: number }, { loaders }: Context) => {
      const comments = await loaders.commentsByPostLoader.load(post.id);
      return comments.slice(0, limit || 10);
    },
  },

  Comment: {
    author: async (comment: any, _: any, { loaders }: Context) => {
      return loaders.userLoader.load(comment.author_id);
    },
  },

  Mutation: {
    updateUser: async (_: any, args: any) => {
      // Validate input
      const { error } = updateUserSchema.validate(args);
      if (error) {
        throw new Error(`Validation Error: ${error.details[0].message}`);
      }

      const { id, fullName, bio } = args;
      const updates: string[] = [];
      const values: any[] = [];
      let paramIndex = 1;

      if (fullName !== undefined) {
        updates.push(`full_name = $${paramIndex++}`);
        values.push(fullName);
      }
      if (bio !== undefined) {
        updates.push(`bio = $${paramIndex++}`);
        values.push(bio);
      }

      if (updates.length > 0) {
        values.push(id);
        await query(
          `UPDATE benchmark.tb_user
           SET ${updates.join(', ')}, updated_at = NOW()
           WHERE id = $${paramIndex}`,
          values
        );
      }

      return queryOne(
        `SELECT id, username, full_name, bio
         FROM benchmark.tb_user WHERE id = $1`,
        [id]
      );
    },
  },
};
