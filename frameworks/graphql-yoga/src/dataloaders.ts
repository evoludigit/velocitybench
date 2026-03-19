import DataLoader from 'dataloader';
import { pool } from './db.js';

interface User {
  id: string;
  username: string;
  full_name: string | null;
  bio: string | null;
}

interface Post {
  id: string;
  fk_author: number;
  title: string;
  content: string | null;
}

interface Comment {
  id: string;
  post_id: string;
  author_id: string;
  content: string;
}

export function createDataLoaders() {
  return {
    // Batch load users by UUID
    userLoader: new DataLoader<string, User | null>(async (ids) => {
      const result = await pool.query(
        `SELECT id, username, full_name, bio
         FROM benchmark.tb_user
         WHERE id = ANY($1)`,
        [ids as string[]]
      );
      const userMap = new Map(result.rows.map((u: User) => [u.id, u]));
      return ids.map((id) => userMap.get(id) || null);
    }),

    // Batch load users by integer pk_user (for Post.author)
    userByPkLoader: new DataLoader<number, User | null>(async (pks) => {
      const result = await pool.query(
        `SELECT pk_user, id, username, full_name, bio
         FROM benchmark.tb_user
         WHERE pk_user = ANY($1::int[])`,
        [pks as number[]]
      );
      const userMap = new Map(result.rows.map((u: any) => [u.pk_user, u]));
      return pks.map((pk) => userMap.get(pk) || null);
    }),

    // Batch load posts by ID
    postLoader: new DataLoader<string, Post | null>(async (ids) => {
      const result = await pool.query(
        `SELECT id, fk_author, title, content
         FROM benchmark.tb_post
         WHERE id = ANY($1)`,
        [ids as string[]]
      );
      const postMap = new Map(result.rows.map((p: Post) => [p.id, p]));
      return ids.map((id) => postMap.get(id) || null);
    }),

    // Batch load posts by author UUID (for User.posts field)
    postsByAuthorLoader: new DataLoader<string, Post[]>(async (authorIds) => {
      const result = await pool.query(
        `SELECT p.id, p.fk_author, u.id as author_uuid, p.title, p.content
         FROM benchmark.tb_post p
         JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
         WHERE u.id = ANY($1)
         ORDER BY p.created_at DESC`,
        [authorIds as string[]]
      );
      const postMap = new Map<string, Post[]>();
      for (const post of result.rows as any[]) {
        if (!postMap.has(post.author_uuid)) {
          postMap.set(post.author_uuid, []);
        }
        postMap.get(post.author_uuid)!.push({ id: post.id, fk_author: post.fk_author, title: post.title, content: post.content });
      }
      return authorIds.map((id) => postMap.get(id) || []);
    }),

    // Batch load comments by post ID
    commentsByPostLoader: new DataLoader<string, Comment[]>(async (postIds) => {
      const result = await pool.query(
        `SELECT c.id, p.id as post_id, u.id as author_id, c.content
         FROM benchmark.tb_comment c
         JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
         JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
         WHERE p.id = ANY($1)
         ORDER BY c.created_at DESC`,
        [postIds as string[]]
      );
      const commentMap = new Map<string, Comment[]>();
      for (const comment of result.rows as Comment[]) {
        if (!commentMap.has(comment.post_id)) {
          commentMap.set(comment.post_id, []);
        }
        commentMap.get(comment.post_id)!.push(comment);
      }
      return postIds.map((id) => commentMap.get(id) || []);
    }),
  };
}

export type DataLoaders = ReturnType<typeof createDataLoaders>;
