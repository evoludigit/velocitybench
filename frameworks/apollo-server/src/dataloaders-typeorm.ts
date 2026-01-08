import DataLoader from 'dataloader';
import { In } from 'typeorm';
import { AppDataSource } from './db-typeorm.js';
import { User } from './entities/User.js';
import { Post } from './entities/Post.js';
import { Comment } from './entities/Comment.js';

export function createDataLoaders() {
  const userRepository = AppDataSource.getRepository(User);
  const postRepository = AppDataSource.getRepository(Post);
  const commentRepository = AppDataSource.getRepository(Comment);

  return {
    userLoader: new DataLoader<string, any>(async (ids) => {
      const users = await userRepository.find({
        where: { id: In(ids as string[]) },
      });

      const userMap = new Map(users.map((u) => [u.id, u.data]));
      return ids.map((id) => userMap.get(id) || null);
    }),

    postsByAuthorLoader: new DataLoader<string, any[]>(async (authorIds) => {
      // Query posts where author.id is in authorIds (JSONB query)
      const posts = await postRepository
        .createQueryBuilder('post')
        .where("post.data->>'author'->>'id' IN (:...authorIds)", { authorIds })
        .orderBy("post.data->>'createdAt'", 'DESC')
        .getMany();

      // Group by author ID
      const postsByAuthor = new Map<string, any[]>();
      authorIds.forEach((id) => postsByAuthor.set(id, []));

      posts.forEach((post) => {
        const authorId = post.data?.author?.id;
        if (authorId && postsByAuthor.has(authorId)) {
          postsByAuthor.get(authorId)!.push(post.data);
        }
      });

      return authorIds.map((id) => postsByAuthor.get(id) || []);
    }),

    commentsByPostLoader: new DataLoader<string, any[]>(async (postIds) => {
      // Query comments where post.id is in postIds (JSONB query)
      const comments = await commentRepository
        .createQueryBuilder('comment')
        .where("comment.data->>'post'->>'id' IN (:...postIds)", { postIds })
        .orderBy("comment.data->>'createdAt'", 'DESC')
        .getMany();

      // Group by post ID
      const commentsByPost = new Map<string, any[]>();
      postIds.forEach((id) => commentsByPost.set(id, []));

      comments.forEach((comment) => {
        const postId = comment.data?.post?.id;
        if (postId && commentsByPost.has(postId)) {
          commentsByPost.get(postId)!.push(comment.data);
        }
      });

      return postIds.map((id) => commentsByPost.get(id) || []);
    }),

    followerCountLoader: new DataLoader<string, number>(async (userIds) => {
      // This would query the followers table if it exists
      // For now, return 0 for all users
      return userIds.map(() => 0);
    }),
  };
}

export interface DataLoaders {
  userLoader: DataLoader<string, any>;
  postsByAuthorLoader: DataLoader<string, any[]>;
  commentsByPostLoader: DataLoader<string, any[]>;
  followerCountLoader: DataLoader<string, number>;
}
