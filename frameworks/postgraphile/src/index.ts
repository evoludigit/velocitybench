import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import express from 'express';
import { Pool } from 'pg';
import { postgraphile } from 'postgraphile';
import { grafserv } from 'postgraphile/grafserv/express/v4';
import preset, { connectionString } from './graphile.config';

const PORT = parseInt(process.env.PORT || '4000', 10);

// PostGraphile version reported by /health so benchmark runs record it.
// The package doesn't export ./package.json, so read it from disk
// (resolve lands on dist/index.js; the manifest is two levels up).
const POSTGRAPHILE_VERSION: string = JSON.parse(
  readFileSync(
    join(require.resolve('postgraphile'), '..', '..', 'package.json'),
    'utf8'
  )
).version;

// Small dedicated pool for liveness checks — keeps the GraphQL pool
// (managed by makePgService) free of health traffic.
const healthPool = new Pool({ connectionString, max: 2 });

async function startServer() {
  const app = express();

  app.get('/health', async (_req, res) => {
    try {
      const client = await healthPool.connect();
      await client.query('SELECT 1');
      client.release();
      res.json({
        status: 'healthy',
        version: POSTGRAPHILE_VERSION,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      res.status(503).json({ status: 'unhealthy', error: String(err) });
    }
  });

  app.get('/ready', (_req, res) => {
    res.json({ status: 'ready' });
  });

  const server = createServer(app);
  const pgl = postgraphile(preset);
  const serv = pgl.createServ(grafserv);
  await serv.addTo(app, server);

  server.listen(PORT, () => {
    console.log(
      `🚀 PostGraphile v${POSTGRAPHILE_VERSION} listening on port ${PORT}`
    );
  });

  process.on('SIGTERM', () => {
    console.log('Shutting down gracefully...');
    server.close(async () => {
      await serv.release();
      await healthPool.end();
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
