import express, { Request, Response, NextFunction } from 'express';
import { register, collectDefaultMetrics, Counter, Histogram } from 'prom-client';
import { pool, query, queryOne } from './db.js';
import 'express-async-errors';
import { updateUserSchema } from './validation.js';

const app = express();
app.use(express.json());

// Prometheus metrics
collectDefaultMetrics();
const requestCounter = new Counter({
  name: 'express_requests_total',
  help: 'Total REST requests',
  labelNames: ['method', 'path', 'status'],
});
const requestDuration = new Histogram({
  name: 'express_request_duration_seconds',
  help: 'REST request duration',
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
    await pool.query('SELECT 1');
    res.json({ status: 'healthy', framework: 'express-rest' });
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
// Users endpoints
// ============================================================================

app.get('/users', async (req: Request, res: Response) => {
  const limit = parseInt(req.query.limit as string) || 10;
  const users = await query(
    `SELECT id, username, full_name, bio
     FROM benchmark.tb_user
     ORDER BY created_at DESC
     LIMIT $1`,
    [limit]
  );
  res.json(users);
});

app.get('/users/:id', async (req: Request, res: Response) => {
  const { id } = req.params;
  const include = ((req.query.include as string) || '').split(',').filter(Boolean);

  const user = await queryOne(
    `SELECT id, username, full_name, bio
     FROM benchmark.tb_user WHERE id = $1`,
    [id]
  );

  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }

  const result: any = { ...user };

  // Include relationships based on query parameter
  if (include.includes('posts')) {
    result.posts = await query(
      `SELECT p.id, p.title, p.content FROM benchmark.tb_post p
       WHERE p.fk_author = (SELECT pk_user FROM benchmark.tb_user WHERE id = $1)
       AND p.published = true
       ORDER BY p.created_at DESC LIMIT 10`,
      [id]
    );
  }

  if (include.includes('followers')) {
    const followers = await query(
      `SELECT u.id, u.username FROM benchmark.tb_user u
       JOIN benchmark.tb_user_follows f ON u.pk_user = f.fk_follower
       WHERE f.fk_following = (SELECT pk_user FROM benchmark.tb_user WHERE id = $1)
       LIMIT 10`,
      [id]
    );
    result.followers = followers;
  }

  if (include.includes('following')) {
    const following = await query(
      `SELECT u.id, u.username FROM benchmark.tb_user u
       JOIN benchmark.tb_user_follows f ON u.pk_user = f.fk_following
       WHERE f.fk_follower = (SELECT pk_user FROM benchmark.tb_user WHERE id = $1)
       LIMIT 10`,
      [id]
    );
    result.following = following;
  }

  res.json(result);
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

  const user = await queryOne(
    `SELECT id, username, full_name, bio
     FROM benchmark.tb_user WHERE id = $1`,
    [id]
  );

  res.json(user);
});

// ============================================================================
// Posts endpoints
// ============================================================================

app.get('/posts', async (req: Request, res: Response) => {
  const limit = parseInt(req.query.limit as string) || 10;
  const include = ((req.query.include as string) || '').split(',').filter(Boolean);

  const posts = await query(
    `SELECT p.id, u.id as author_id, p.title, p.content, p.published as status
     FROM benchmark.tb_post p
     JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
     WHERE p.published = true
     ORDER BY p.created_at DESC
     LIMIT $1`,
    [limit]
  );

  if (include.includes('author')) {
    const authorIds = [...new Set(posts.map((p: any) => p.author_id))];
    const authors = await query(
      `SELECT id, username, full_name
       FROM benchmark.tb_user WHERE id = ANY($1)`,
      [authorIds]
    );
    const authorMap = new Map(authors.map((a: any) => [a.id, a]));
    posts.forEach((p: any) => {
      p.author = authorMap.get(p.author_id);
    });
  }

  res.json(posts);
});

app.get('/posts/:id', async (req: Request, res: Response) => {
  const { id } = req.params;
  const include = ((req.query.include as string) || '').split(',').filter(Boolean);

  const post = await queryOne(
    `SELECT p.id, u.id as author_id, p.title, p.content, p.published as status
     FROM benchmark.tb_post p
     JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
     WHERE p.id = $1`,
    [id]
  );

  if (!post) {
    return res.status(404).json({ error: 'Post not found' });
  }

  const result: any = { ...post };

  if (include.includes('author')) {
    result.author = await queryOne(
      `SELECT id, username, full_name
       FROM benchmark.tb_user WHERE id = $1`,
      [(post as any).author_id]
    );
  }

  if (include.includes('comments')) {
    result.comments = await query(
      `SELECT c.id, c.content, u.id as author_id, u.username as author_username
       FROM benchmark.tb_comment c
       JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
       WHERE c.fk_post = (SELECT pk_post FROM benchmark.tb_post WHERE id = $1)
       ORDER BY c.created_at DESC LIMIT 20`,
      [id]
    );
  }

  res.json(result);
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

const PORT = parseInt(process.env.PORT || '8005');
app.listen(PORT, () => {
  console.log(`🚀 Express REST server ready at http://localhost:${PORT}`);
});
