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
        `SELECT id, fk_author, title, content, published as status
         FROM benchmark.tb_post
         WHERE id = $1`,
        [id]
      );
    },

    posts: async (_: any, { limit, published }: { limit: number; published?: boolean }, _ctx: Context, info: any) => {
      const selections: any[] = info?.fieldNodes?.[0]?.selectionSet?.selections ?? [];
      const wantAuthor = selections.some((s: any) => s.name?.value === 'author');
      if (wantAuthor) {
        if (published === undefined || published === null) {
          const rows = await query(
            `SELECT p.id, p.fk_author, p.title, p.content, p.published AS status,
                    u.id AS author_id, u.username, u.full_name, u.bio
             FROM benchmark.tb_post p
             JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
             ORDER BY p.created_at DESC
             LIMIT $1`,
            [limit]
          );
          return rows.map((r: any) => ({ ...r, _preloadedAuthor: { id: r.author_id, username: r.username, fullName: r.full_name, bio: r.bio } }));
        }
        const rows = await query(
          `SELECT p.id, p.fk_author, p.title, p.content, p.published AS status,
                  u.id AS author_id, u.username, u.full_name, u.bio
           FROM benchmark.tb_post p
           JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
           WHERE p.published = $2
           ORDER BY p.created_at DESC
           LIMIT $1`,
          [limit, published]
        );
        return rows.map((r: any) => ({ ...r, _preloadedAuthor: { id: r.author_id, username: r.username, fullName: r.full_name, bio: r.bio } }));
      }
      if (published === undefined || published === null) {
        return query(
          `SELECT id, fk_author, title, content, published as status
           FROM benchmark.tb_post
           ORDER BY created_at DESC
           LIMIT $1`,
          [limit]
        );
      }
      return query(
        `SELECT id, fk_author, title, content, published as status
         FROM benchmark.tb_post
         WHERE published = $2
         ORDER BY created_at DESC
         LIMIT $1`,
        [limit, published]
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
      return posts.slice(0, limit || 10).map((p: any) => ({
        id: p.id, fk_author: p.fk_author, title: p.title, content: p.content, status: p.status,
      }));
    },

    followerCount: async (user: any, _: any, { loaders }: Context) => {
      return loaders.followerCountLoader.load(user.id);
    },
  },

  Post: {
    author: async (post: any, _: any, { loaders }: Context) => {
      if (post._preloadedAuthor) return post._preloadedAuthor;
      return loaders.userByPkLoader.load(post.fk_author);
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

    post: async (comment: any, _: any, { loaders }: Context) => {
      return loaders.postLoader.load(comment.post_id);
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
