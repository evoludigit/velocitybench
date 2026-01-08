import { AppDataSource } from './db-typeorm.js';
import { User } from './entities/User.js';
import { Post } from './entities/Post.js';
import { Comment } from './entities/Comment.js';
import type { DataLoaders } from './dataloaders-typeorm.js';

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
      const userRepository = AppDataSource.getRepository(User);
      const users = await userRepository.find({
        take: limit,
      });
      return users.map((u) => u.data);
    },

    post: async (_: any, { id }: { id: string }) => {
      const postRepository = AppDataSource.getRepository(Post);
      const post = await postRepository.findOne({
        where: { id },
      });
      return post ? post.data : null;
    },

    posts: async (_: any, { limit }: { limit: number }) => {
      const postRepository = AppDataSource.getRepository(Post);
      const posts = await postRepository.find({
        take: limit,
        where: { data: { published: true } as any },
      });
      return posts.map((p) => p.data);
    },

    comment: async (_: any, { id }: { id: string }) => {
      const commentRepository = AppDataSource.getRepository(Comment);
      const comment = await commentRepository.findOne({
        where: { id },
      });
      return comment ? comment.data : null;
    },

    comments: async (_: any, { limit }: { limit: number }) => {
      const commentRepository = AppDataSource.getRepository(Comment);
      const comments = await commentRepository.find({
        take: limit,
      });
      return comments.map((c) => c.data);
    },
  },

  User: {
    firstName: (user: any) => user.fullName,
    lastName: () => null,

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
      const authorId = post.author?.id;
      if (!authorId) return null;
      return loaders.userLoader.load(authorId);
    },

    comments: async (post: any, { limit }: { limit: number }, { loaders }: Context) => {
      const comments = await loaders.commentsByPostLoader.load(post.id);
      return comments.slice(0, limit || 10);
    },
  },

  Comment: {
    author: async (comment: any, _: any, { loaders }: Context) => {
      const authorId = comment.author?.id;
      if (!authorId) return null;
      return loaders.userLoader.load(authorId);
    },
  },

  Mutation: {
    updateUser: async (_: any, args: any) => {
      const { id, firstName, bio } = args;
      const userRepository = AppDataSource.getRepository(User);

      // Load user
      const user = await userRepository.findOne({ where: { id } });
      if (!user) return null;

      // Update JSONB data
      const data = { ...user.data };
      if (firstName !== undefined) {
        data.fullName = firstName;
      }
      if (bio !== undefined) {
        data.bio = bio;
      }

      user.data = data;
      user.updated_at = new Date();

      await userRepository.save(user);

      return data;
    },
  },
};
