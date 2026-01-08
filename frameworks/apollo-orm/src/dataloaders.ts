import DataLoader from 'dataloader';
import { AppDataSource } from './db.js';
import { User, Post, Comment } from './entities/index.js';

export interface DataLoaders {
  userLoader: DataLoader<number, User | null>;
  postLoader: DataLoader<number, Post | null>;
  postsByAuthorLoader: DataLoader<number, Post[]>;
  commentsByPostLoader: DataLoader<number, Comment[]>;
}

export function createDataLoaders(): DataLoaders {
  const userRepository = AppDataSource.getRepository(User);
  const postRepository = AppDataSource.getRepository(Post);
  const commentRepository = AppDataSource.getRepository(Comment);

  return {
    userLoader: new DataLoader(
      async (keys: readonly number[]): Promise<(User | null)[]> => {
        const users = await userRepository
          .createQueryBuilder('user')
          .where('user.pk_user IN (:...keys)', { keys })
          .getMany();

        const userMap = new Map<number, User>();
        users.forEach(user => userMap.set(user.pk_user, user));

        return keys.map(key => userMap.get(key) || null);
      },
      { cache: false }
    ),

    postLoader: new DataLoader(
      async (keys: readonly number[]): Promise<(Post | null)[]> => {
        const posts = await postRepository
          .createQueryBuilder('post')
          .where('post.pk_post IN (:...keys)', { keys })
          .getMany();

        const postMap = new Map<number, Post>();
        posts.forEach(post => postMap.set(post.pk_post, post));

        return keys.map(key => postMap.get(key) || null);
      },
      { cache: false }
    ),

    postsByAuthorLoader: new DataLoader(
      async (keys: readonly number[]): Promise<Post[][]> => {
        const posts = await postRepository
          .createQueryBuilder('post')
          .where('post.fk_author IN (:...keys)', { keys })
          .andWhere('post.published = true')
          .orderBy('post.created_at', 'DESC')
          .getMany();

        const postsByAuthor = new Map<number, Post[]>();
        keys.forEach(key => postsByAuthor.set(key, []));

        posts.forEach(post => {
          const authorPosts = postsByAuthor.get(post.fk_author);
          if (authorPosts) {
            authorPosts.push(post);
          }
        });

        return keys.map(key => postsByAuthor.get(key) || []);
      },
      { cache: false }
    ),

    commentsByPostLoader: new DataLoader(
      async (keys: readonly number[]): Promise<Comment[][]> => {
        const comments = await commentRepository
          .createQueryBuilder('comment')
          .where('comment.fk_post IN (:...keys)', { keys })
          .orderBy('comment.created_at', 'DESC')
          .getMany();

        const commentsByPost = new Map<number, Comment[]>();
        keys.forEach(key => commentsByPost.set(key, []));

        comments.forEach(comment => {
          const postComments = commentsByPost.get(comment.fk_post);
          if (postComments) {
            postComments.push(comment);
          }
        });

        return keys.map(key => commentsByPost.get(key) || []);
      },
      { cache: false }
    ),


  };
}