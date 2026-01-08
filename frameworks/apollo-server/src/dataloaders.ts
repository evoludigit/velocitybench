import DataLoader from 'dataloader';
import { query } from './db.js';

interface User {
  id: string;
  username: string;
  full_name: string | null;
  bio: string | null;
}

interface Post {
  id: string;
  author_id: string;
  title: string;
  content: string | null;
  status: string;
}

interface Comment {
  id: string;
  post_id: string;
  author_id: string;
  content: string;
}

export function createDataLoaders() {
  return {
    // Batch load users by ID
    userLoader: new DataLoader<string, User | null>(async (ids) => {
      const users = await query<User>(
        `SELECT id, username, full_name, bio
         FROM benchmark.tb_user
         WHERE id = ANY($1)`,
        [ids]
      );
      const userMap = new Map(users.map((u) => [u.id, u]));
      return ids.map((id) => userMap.get(id) || null);
    }),

    // Batch load posts by author ID
    postsByAuthorLoader: new DataLoader<string, Post[]>(async (authorIds) => {
      const posts = await query<Post>(
        `SELECT p.id, u.id as author_id, p.title, p.content, p.published as status
         FROM benchmark.tb_post p
         JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
         WHERE u.id = ANY($1)
         ORDER BY p.created_at DESC
         LIMIT 100`,
        [authorIds]
      );
      const postMap = new Map<string, Post[]>();
      for (const post of posts) {
        if (!postMap.has(post.author_id)) {
          postMap.set(post.author_id, []);
        }
        postMap.get(post.author_id)!.push(post);
      }
      return authorIds.map((id) => postMap.get(id) || []);
    }),

    // Batch load comments by post ID
    commentsByPostLoader: new DataLoader<string, Comment[]>(async (postIds) => {
      const comments = await query<Comment>(
        `SELECT c.id, p.id as post_id, u.id as author_id, c.content
         FROM benchmark.tb_comment c
         JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
         JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
         WHERE p.id = ANY($1)
         ORDER BY c.created_at DESC
         LIMIT 100`,
        [postIds]
      );
      const commentMap = new Map<string, Comment[]>();
      for (const comment of comments) {
        if (!commentMap.has(comment.post_id)) {
          commentMap.set(comment.post_id, []);
        }
        commentMap.get(comment.post_id)!.push(comment);
      }
      return postIds.map((id) => commentMap.get(id) || []);
    }),

    // Batch load follower counts (placeholder - no follows table in db)
    followerCountLoader: new DataLoader<string, number>(async (userIds) => {
      // Return 0 for all users since tb_user_follows table doesn't exist
      return userIds.map(() => 0);
    }),
  };
}

export type DataLoaders = ReturnType<typeof createDataLoaders>;
