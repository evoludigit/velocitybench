import { AppDataSource } from './db.js';
import { DataLoaders } from './dataloaders.js';
import { updateUserSchema } from './validation.js';
import { User } from './entities/User.js';
import { Post } from './entities/Post.js';
import { Comment } from './entities/Comment.js';

interface Context {
  dataLoaders: DataLoaders;
}

const userRepository = AppDataSource.getRepository(User);
const postRepository = AppDataSource.getRepository(Post);
const commentRepository = AppDataSource.getRepository(Comment);

export const resolvers = {
  Query: {
    ping: () => 'pong',

    user: async (_: any, { id }: { id: string }) => {
      return userRepository.findOne({
        where: { id },
      });
    },

    users: async (_: any, { limit }: { limit: number }) => {
      return userRepository.find({
        order: { created_at: 'DESC' },
        take: limit,
      });
    },

    post: async (_: any, { id }: { id: string }) => {
      return postRepository.findOne({
        where: { id },
        // Remove relations - let field resolvers handle with DataLoaders
      });
    },

    posts: async (_: any, { limit }: { limit: number }) => {
      return postRepository.find({
        where: { published: true },
        order: { created_at: 'DESC' },
        take: limit,
        // Remove relations - let field resolvers handle with DataLoaders
      });
    },

    comment: async (_: any, { id }: { id: string }) => {
      return commentRepository.findOne({
        where: { id },
        // Remove relations - let field resolvers handle with DataLoaders
      });
    },

    comments: async (_: any, { limit }: { limit: number }) => {
      return commentRepository.find({
        order: { created_at: 'DESC' },
        take: limit,
        // Remove relations - let field resolvers handle with DataLoaders
      });
    },
  },

  Mutation: {
    updateUser: async (_: any, { id, fullName, bio }: { id: string, fullName?: string, bio?: string }) => {
      // Validate input
      const { error } = updateUserSchema.validate({ id, fullName, bio });
      if (error) {
        throw new Error(`Validation Error: ${error.details[0].message}`);
      }
      const user = await userRepository.findOneBy({ id });
      if (!user) {
        throw new Error('User not found');
      }

      if (fullName !== undefined) user.full_name = fullName;
      if (bio !== undefined) user.bio = bio;

      await userRepository.save(user);
      return user;
    },
  },

  User: {
    posts: async (user: any, args: { limit?: number }, context: Context) => {
      const posts = await context.dataLoaders.postsByAuthorLoader.load(user.pk_user);
      const actualLimit = args.limit || 50;
      if (posts.length > actualLimit) {
        return posts.slice(0, actualLimit);
      }
      return posts;
    },
  },

  Post: {
    author: async (post: any, _: any, context: Context) => {
      return context.dataLoaders.userLoader.load(post.fk_author);
    },

    comments: async (post: any, args: { limit?: number }, context: Context) => {
      const comments = await context.dataLoaders.commentsByPostLoader.load(post.pk_post);
      const actualLimit = args.limit || 50;
      if (comments.length > actualLimit) {
        return comments.slice(0, actualLimit);
      }
      return comments;
    },
  },

  Comment: {
    author: async (comment: any, _: any, context: Context) => {
      return context.dataLoaders.userLoader.load(comment.fk_author);
    },

    post: async (comment: any, _: any, context: Context) => {
      return context.dataLoaders.postLoader.load(comment.fk_post);
    },
  },
};