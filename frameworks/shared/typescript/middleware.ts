/**
 * Middleware for automatic health check endpoint handling.
 *
 * Provides middleware factories for Express and Fastify that automatically
 * handle health check requests without requiring manual route definitions.
 */

import { Request, Response, NextFunction } from 'express';
import { FastifyRequest, FastifyReply } from 'fastify';
import { HealthCheckManager } from './health-check';
import { getHttpStatusCode, ProbeType } from './types';

/**
 * Express middleware for health check endpoints.
 *
 * Usage:
 *   import { expressHealthCheckMiddleware } from '@shared/middleware';
 *
 *   const healthManager = new HealthCheckManager({ ... });
 *   app.use(expressHealthCheckMiddleware(healthManager));
 */
export function expressHealthCheckMiddleware(healthManager: HealthCheckManager) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const path = req.path;

    // Check if this is a health check endpoint
    if (req.method === 'GET' && path.startsWith('/health')) {
      let probeType: ProbeType;

      if (path === '/health') {
        probeType = ProbeType.READINESS; // Default to readiness
      } else if (path === '/health/live') {
        probeType = ProbeType.LIVENESS;
      } else if (path === '/health/ready') {
        probeType = ProbeType.READINESS;
      } else if (path === '/health/startup') {
        probeType = ProbeType.STARTUP;
      } else {
        // Unknown health endpoint
        return res.status(404).json({ error: 'Unknown health endpoint' });
      }

      try {
        // Execute health check
        const result = await healthManager.probe(probeType);
        const statusCode = getHttpStatusCode(result.status, result.probe_type);

        return res.status(statusCode).json(result);
      } catch (error: any) {
        return res.status(503).json({
          status: 'down',
          error: `Health check error: ${error.message}`,
        });
      }
    }

    // Not a health check, pass to next middleware
    next();
  };
}

/**
 * Fastify plugin for health check endpoints.
 *
 * Usage:
 *   import { fastifyHealthCheckPlugin } from '@shared/middleware';
 *
 *   const healthManager = new HealthCheckManager({ ... });
 *   app.register(fastifyHealthCheckPlugin, { healthManager });
 */
export async function fastifyHealthCheckPlugin(
  fastify: any,
  options: { healthManager: HealthCheckManager }
) {
  const { healthManager } = options;

  // Register health check routes
  fastify.get('/health', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const result = await healthManager.probe('readiness');
      const statusCode = getHttpStatusCode(result.status, result.probe_type);
      reply.code(statusCode).send(result);
    } catch (error: any) {
      reply.code(503).send({
        status: 'down',
        error: `Health check error: ${error.message}`,
      });
    }
  });

  fastify.get('/health/live', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const result = await healthManager.probe('liveness');
      const statusCode = getHttpStatusCode(result.status, result.probe_type);
      reply.code(statusCode).send(result);
    } catch (error: any) {
      reply.code(503).send({
        status: 'down',
        error: `Health check error: ${error.message}`,
      });
    }
  });

  fastify.get('/health/ready', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const result = await healthManager.probe('readiness');
      const statusCode = getHttpStatusCode(result.status, result.probe_type);
      reply.code(statusCode).send(result);
    } catch (error: any) {
      reply.code(503).send({
        status: 'down',
        error: `Health check error: ${error.message}`,
      });
    }
  });

  fastify.get('/health/startup', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const result = await healthManager.probe('startup');
      const statusCode = getHttpStatusCode(result.status, result.probe_type);
      reply.code(statusCode).send(result);
    } catch (error: any) {
      reply.code(503).send({
        status: 'down',
        error: `Health check error: ${error.message}`,
      });
    }
  });
}
