import express, { Express } from 'express';
import { postgraphile } from 'postgraphile';
import { getPool } from './db';

export function setupGraphQL(app: Express) {
  // PostGraphile middleware configuration
  app.use(
    postgraphile(
      getPool(),
      'public', // PostgreSQL schema
      {
        // Performance & behavior
        watchPg: false,
        graphiql: false,
        enableQueryBatching: true,
        simpleCollections: 'both',

        // GraphQL configuration
        graphqlRoute: '/graphql',

        // Error handling
        showErrorStack: 'json',
        extendedErrors: ['hint', 'detail', 'errcode'],

        // Plugins (skip to improve performance)
      }
    )
  );

  return app;
}
