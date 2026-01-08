import express, { Request, Response, NextFunction } from 'express';
import { register, collectDefaultMetrics, Counter, Histogram } from 'prom-client';
import { initDatabase, User, Post, Comment } from './db.js';
import 'express-async-errors';
import { updateUserSchema } from './validation.js';

const app = express();
app.use(express.json());

// Initialize database
initDatabase();

// Prometheus metrics
collectDefaultMetrics();
const requestCounter = new Counter({
  name: 'express_orm_requests_total',
  help: 'Total REST requests (ORM)',
  labelNames: ['method', 'path', 'status'],
});
const requestDuration = new Histogram({
  name: 'express_orm_request_duration_seconds',
  help: 'REST request duration (ORM)',
  labelNames: ['method', 'path'],
});

// Middleware for metrics
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    requestCounter.inc({ method: req.method, path: req.path, status: res.statusCode.toString() });
    requestDuration.observe({ method: req.method, path: req.path }, duration);
  });
  next();
});

// Health endpoint
app.get('/health', async (req: Request, res: Response) => {
  try {
    await User.sequelize!.query('SELECT 1');
    res.json({ status: 'healthy', framework: 'express-orm' });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: String(error) });
  }
});

// Metrics endpoint
app.get('/metrics', async (req: Request, res: Response) => {
  res.set('Content-Type', register.contentType);
  res.send(await register.metrics());
});

// Ping endpoint
app.get('/ping', (req: Request, res: Response) => {
  res.json({ message: 'pong' });
});

// ============================================================================
// Users endpoints (ORM)
// ============================================================================

app.get('/users', async (req: Request, res: Response) => {
  const limit = parseInt(req.query.limit as string) || 10;
  const include = ((req.query.include as string) || '').split(',').filter(Boolean);

  const includeOptions: any[] = [];

  if (include.includes('posts')) {
    includeOptions.push({
      model: Post,
      as: 'posts',
      where: { published: true },
      limit: 10,
      order: [['created_at', 'DESC']],
    });
  }

  if (include.includes('followers')) {
    includeOptions.push({
      model: User,
      as: 'followers',
      through: { attributes: [] },
      limit: 10,
    });
  }

  if (include.includes('following')) {
    includeOptions.push({
      model: User,
      as: 'following',
      through: { attributes: [] },
      limit: 10,
    });
  }

  const users = await User.findAll({
    limit,
    order: [['created_at', 'DESC']],
    include: includeOptions,
  });

  res.json(users);
});

app.get('/users/:id', async (req: Request, res: Response) => {
  const { id } = req.params;
  const include = ((req.query.include as string) || '').split(',').filter(Boolean);

  const includeOptions: any[] = [];

  if (include.includes('posts')) {
    includeOptions.push({
      model: Post,
      as: 'posts',
      where: { published: true },
      limit: 10,
      order: [['created_at', 'DESC']],
    });
  }

  if (include.includes('followers')) {
    includeOptions.push({
      model: User,
      as: 'followers',
      through: { attributes: [] },
      limit: 10,
    });
  }

  if (include.includes('following')) {
    includeOptions.push({
      model: User,
      as: 'following',
      through: { attributes: [] },
      limit: 10,
    });
  }

  const user = await User.findByPk(id, {
    include: includeOptions,
  });

  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }

  res.json(user);
});

app.put('/users/:id', async (req: Request, res: Response) => {
  const { id } = req.params;

  // Validate request body
  const { error } = updateUserSchema.validate(req.body);
  if (error) {
    return res.status(400).json({
      error: 'Validation Error',
      message: error.details[0].message
    });
  }

  const { fullName, bio } = req.body;

  const user = await User.findByPk(id);
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }

  if (fullName !== undefined) user.full_name = fullName;
  if (bio !== undefined) user.bio = bio;

  await user.save();

  res.json(user);
});

// ============================================================================
// Posts endpoints (ORM)
// ============================================================================

app.get('/posts', async (req: Request, res: Response) => {
  const limit = parseInt(req.query.limit as string) || 10;
  const include = ((req.query.include as string) || '').split(',').filter(Boolean);

  const includeOptions: any[] = [];

  if (include.includes('author')) {
    includeOptions.push({
      model: User,
      as: 'author',
      attributes: ['id', 'username', 'full_name'],
    });
  }

  const posts = await Post.findAll({
    where: { published: true },
    limit,
    order: [['created_at', 'DESC']],
    include: includeOptions,
  });

  res.json(posts);
});

app.get('/posts/:id', async (req: Request, res: Response) => {
  const { id } = req.params;
  const include = ((req.query.include as string) || '').split(',').filter(Boolean);

  const includeOptions: any[] = [];

  if (include.includes('author')) {
    includeOptions.push({
      model: User,
      as: 'author',
      attributes: ['id', 'username', 'full_name'],
    });
  }

  if (include.includes('comments')) {
    includeOptions.push({
      model: Comment,
      as: 'comments',
      include: [{
        model: User,
        as: 'author',
        attributes: ['id', 'username'],
      }],
      limit: 20,
      order: [['created_at', 'DESC']],
    });
  }

  const post = await Post.findByPk(id, {
    include: includeOptions,
  });

  if (!post) {
    return res.status(404).json({ error: 'Post not found' });
  }

  res.json(post);
});

// ============================================================================
// Error handling middleware
// ============================================================================

// 404 handler for unmatched routes
app.use((req: Request, res: Response) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.method} ${req.path} not found`
  });
});

// Global error handling middleware
// eslint-disable-next-line @typescript-eslint/no-unused-vars
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error('Unhandled error:', err);

  // Don't leak error details in production
  const isDevelopment = process.env.NODE_ENV !== 'production';

  res.status(500).json({
    error: 'Internal Server Error',
    message: isDevelopment ? err.message : 'An unexpected error occurred',
    ...(isDevelopment && { stack: err.stack })
  });
});

// ============================================================================
// Start server
// ============================================================================

const PORT = parseInt(process.env.PORT || '8001');
app.listen(PORT, () => {
  console.log(`🚀 Express ORM server ready at http://localhost:${PORT}`);
});