import 'reflect-metadata';
import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { register, collectDefaultMetrics, Counter, Histogram } from 'prom-client';
import http from 'http';
import { typeDefs } from './schema.js';
import { resolvers } from './resolvers.js';
import { initDatabase, AppDataSource } from './db.js';
import { createDataLoaders } from './dataloaders.js';

// Prometheus metrics
collectDefaultMetrics();

const requestCounter = new Counter({
  name: 'apollo_orm_requests_total',
  help: 'Total GraphQL requests (ORM)',
  labelNames: ['operation'],
});

const requestDuration = new Histogram({
  name: 'apollo_orm_request_duration_seconds',
  help: 'GraphQL request duration (ORM)',
  labelNames: ['operation'],
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

// Initialize database and start server
async function startServer() {
  try {
    await initDatabase();

    // Start server on port 4004 (GraphQL)
    const { url } = await startStandaloneServer(server, {
      listen: { port: 4004 },
       context: async () => {
         // Provide DataLoaders for N+1 query prevention
         return {
           dataLoaders: createDataLoaders(),
         };
       },
    });

    console.log(`🚀 Apollo ORM Server ready at ${url}`);

    // Health & Metrics endpoints (separate HTTP server on port 4005)
    const metricsServer = http.createServer(async (req, res) => {
      if (req.url === '/health') {
        try {
          // Simple health check using TypeORM
          const userCount = await AppDataSource.getRepository('User').count();
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ status: 'healthy', framework: 'apollo-orm', userCount }));
        } catch (error) {
          res.writeHead(503, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ status: 'unhealthy', error: String(error) }));
        }
      } else if (req.url === '/metrics') {
        res.writeHead(200, { 'Content-Type': register.contentType });
        res.end(await register.metrics());
      } else {
        res.writeHead(404);
        res.end();
      }
    });

    metricsServer.listen(4005, () => {
      console.log('📊 Metrics server ready at http://localhost:4005');
    });

  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();