import 'reflect-metadata';
import { DataSource } from 'typeorm';
import { User } from './entities/User.js';
import { Post } from './entities/Post.js';
import { Comment } from './entities/Comment.js';

export const AppDataSource = new DataSource({
  type: 'postgres',
  host: process.env.DB_HOST || 'postgres',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'velocitybench_benchmark',
  username: process.env.DB_USER || 'benchmark',
  password: process.env.DB_PASSWORD || 'benchmark123',
  schema: 'benchmark',
  entities: [User, Post, Comment],
  synchronize: false, // Never use in production
  logging: false,
  // Connection pool settings
  poolSize: 50,
  extra: {
    max: 50,
    min: 10,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
  },
});

export async function initializeDataSource() {
  if (!AppDataSource.isInitialized) {
    await AppDataSource.initialize();
  }
  return AppDataSource;
}
