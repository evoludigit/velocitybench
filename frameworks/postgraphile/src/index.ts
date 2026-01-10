import express from 'express';
import cors from 'cors';
import { connectDatabase, closeDatabase, getPool } from './db';
import { setupGraphQL } from './middleware';

const PORT = parseInt(process.env.PORT || '4003', 10);

async function startServer() {
  const app = express();

  // Middleware
  app.use(cors());
  app.use(express.json());

  // Connect to database
  const connected = await connectDatabase();
  if (!connected) {
    process.exit(1);
  }

  // Setup GraphQL
  setupGraphQL(app);

  // Health check endpoint
  app.get('/health', async (req, res) => {
    try {
      const pool = getPool();
      const client = await pool.connect();
      await client.query('SELECT 1');
      client.release();
      res.json({ status: 'healthy', timestamp: new Date().toISOString() });
    } catch (err) {
      res.status(503).json({ status: 'unhealthy', error: String(err) });
    }
  });

  // Readiness check
  app.get('/ready', async (req, res) => {
    res.json({ status: 'ready' });
  });

  // Start server
  const server = app.listen(PORT, () => {
    console.log(`🚀 PostGraphile server listening on port ${PORT}`);
  });

  // Graceful shutdown
  process.on('SIGTERM', async () => {
    console.log('Shutting down gracefully...');
    server.close(async () => {
      await closeDatabase();
      process.exit(0);
    });
  });

  return server;
}

if (require.main === module) {
  startServer().catch((err) => {
    console.error('Failed to start server:', err);
    process.exit(1);
  });
}

export { startServer };
