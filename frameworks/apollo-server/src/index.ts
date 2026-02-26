import 'reflect-metadata';
import { ApolloServer } from '@apollo/server';
import { register, collectDefaultMetrics, Counter, Histogram } from 'prom-client';
import express from 'express';
import { typeDefs } from './schema.js';
import { resolvers } from './resolvers.js';
import { createDataLoaders } from './dataloaders.js';
import { pool } from './db.js';

// Prometheus metrics
collectDefaultMetrics();

const requestCounter = new Counter({
  name: 'apollo_requests_total',
  help: 'Total GraphQL requests',
  labelNames: ['operation'],
});

const requestDuration = new Histogram({
  name: 'apollo_request_duration_seconds',
  help: 'GraphQL request duration',
  labelNames: ['operation'],
});

// Create Express app
const app = express();

// Health endpoint
app.get('/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'healthy', framework: 'apollo-server' });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: String(error) });
  }
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.send(await register.metrics());
});

// Create Apollo Server
const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [
    {
      async requestDidStart() {
        const start = Date.now();
        return {
          async willSendResponse(requestContext) {
            const duration = (Date.now() - start) / 1000;
            const operation = requestContext.operationName || 'unknown';
            requestCounter.inc({ operation });
            requestDuration.observe({ operation }, duration);
          },
        };
      },
    },
  ],
});

// Start server and apply GraphQL endpoint
async function main() {
  await server.start();

  // Simple GraphQL endpoint without expressMiddleware
  app.use('/graphql', express.json());
  app.post('/graphql', async (req, res) => {
    try {
      const result = await server.executeOperation(req.body, {
        contextValue: { loaders: createDataLoaders() }
      });

      if (result.body.kind === 'single') {
        res.json(result.body.singleResult);
      } else {
        res.json(result.body);
      }
    } catch (error) {
      res.status(400).json({ errors: [{ message: String(error) }] });
    }
  });

  const PORT = parseInt(process.env.PORT || '4002');
  app.listen(PORT, () => {
    console.log(`🚀 Apollo Server ready at http://localhost:${PORT}/graphql`);
    console.log(`📊 Health endpoint at http://localhost:${PORT}/health`);
    console.log(`📊 Metrics endpoint at http://localhost:${PORT}/metrics`);
  });
}

main().catch(err => {
  console.error('Failed to start server:', err);
  process.exit(1);
});
