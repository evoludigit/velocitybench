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
  password: process.env.DB_PASSWORD ?? (() => { throw new Error('DB_PASSWORD env var is required'); })(),
  entities: [User, Post, Comment],
  synchronize: false, // Don't auto-create tables, use existing schema
  logging: false,
  poolSize: 50,
});

// Initialize database connection
export async function initDatabase() {
  try {
    await AppDataSource.initialize();
    console.log('Database connection established successfully.');
  } catch (error) {
    console.error('Unable to connect to the database:', error);
    throw error;
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Received SIGTERM, closing database connection...');
  await AppDataSource.destroy();
  process.exit(0);
});