import express, { Express } from 'express';
import { postgraphile, makePluginHook } from 'postgraphile';
import { getPool } from './db';

// Plugin hook for smart comments (reads @omit, @name, etc. from PostgreSQL comments)
const pluginHook = makePluginHook([
  // Smart comments plugin is built-in but we need to ensure it's enabled
]);

export function setupGraphQL(app: Express) {
  // PostGraphile middleware configuration
  app.use(
    postgraphile(
      getPool(),
      'benchmark', // PostgreSQL schema (VelocityBench benchmark schema)
      {
        // Performance & behavior
        watchPg: false,
        graphiql: false,
        enableQueryBatching: true,
        simpleCollections: 'both',

        // GraphQL configuration
        graphqlRoute: '/graphql',

        // Enable smart comments for @omit, @name, etc.
        ignoreRBAC: false,
        legacyRelations: 'omit',

        // Error handling
        showErrorStack: 'json',
        extendedErrors: ['hint', 'detail', 'errcode'],

        pluginHook,
      }
    )
  );

  return app;
}
